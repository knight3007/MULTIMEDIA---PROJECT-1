using System.Linq;
using MP1.Game;
using NUnit.Framework;

namespace MP1.Tests
{
    /// <summary>G-008 waves, combo/score, typos and per-item results (D-046, D-047, D-049; owner O1/O3).</summary>
    public class G008SessionTests
    {
        static MeteorDefenseSession Playing(Difficulty d = Difficulty.Normal, int hp = 4, int spawns = 30)
        {
            var c = new GameConfig().WithDifficulty(d);
            c.StartingHp = hp; c.SessionSpawns = spawns;
            var s = new MeteorDefenseSession(c);
            s.Start();
            return s;
        }

        [Test]
        public void ScoreUsesDifficultyAndCappedCombo()
        {
            var s = Playing();
            var gained = Enumerable.Range(0, 7).Select(i => { int before = s.Score; s.ResolveCorrect(s.Spawn("w" + i)); return s.Score - before; }).ToArray();
            CollectionAssert.AreEqual(new[] { 150, 165, 180, 195, 210, 225, 225 }, gained, "Normal x1.5, +0.1 per previous correct, cap +0.5");
            Assert.AreEqual((7, 7), (s.Combo, s.MaxCombo));
            var e = Playing(Difficulty.Expert);
            e.ResolveCorrect(e.Spawn("a"));
            Assert.AreEqual(300, e.Score);
            Assert.AreEqual(100, Playing(Difficulty.Easy).Config.PointsFor(0));
            Assert.AreEqual(450, e.Config.PointsFor(9));
        }

        [Test]
        public void WrongEnterAndBreachResetComboButNeverReduceScore()
        {
            var s = Playing(hp: 5);
            int a = s.Spawn("a"); s.ResolveCorrect(a);
            int b = s.Spawn("b"); s.ResolveCorrect(b);
            int c = s.Spawn("c");
            s.RegisterWrong(c);
            Assert.AreEqual((0, 2, 315), (s.Combo, s.MaxCombo, s.Score));
            s.ResolveCorrect(c);
            Assert.AreEqual(465, s.Score, "combo restarted at 0: +150");
            int d = s.Spawn("d");
            s.RegisterBreach(d);
            Assert.AreEqual((0, 465), (s.Combo, s.Score));
            Assert.IsFalse(s.ResolveCorrect(c), "score once");
            Assert.AreEqual(465, s.Score);
        }

        [Test]
        public void CharacterHitsAndTyposAreStatisticsOnly()
        {
            var s = Playing();
            int a = s.Spawn("a"); s.ResolveCorrect(a);
            int b = s.Spawn("b");
            s.RegisterHits(b, 3);
            s.RegisterTypo(b);
            Assert.AreEqual((150, 1, 1), (s.Score, s.Combo, s.Correct), "no score or combo from characters (O1)");
            Assert.AreEqual((3, 1), (s.HitUnits, s.Typos));
            Assert.AreEqual(0.75, s.TypingAccuracy.Value, 1e-9);
            s.ResolveCorrect(b);
            Assert.AreEqual(150 + 165, s.Score);
            Assert.IsTrue(s.Items["b"].Weak, "a typo marks the word for review (O3)");
            Assert.IsFalse(s.Items["a"].Weak);
            Assert.IsFalse(s.RegisterTypo(b), "resolved meteor ignores typos");
        }

        [Test]
        public void NextWaveWaitsUntilThePreviousWaveResolves()
        {
            var s = Playing(hp: 12);
            var ids = Enumerable.Range(0, 10).Select(i => s.Spawn("w" + i)).ToList();
            Assert.AreEqual((1, 1), (s.WavesStarted, s.NextWave));
            Assert.IsFalse(s.CanSpawn, "wave 2 blocked while wave 1 has active meteors");
            Assert.AreEqual(-1, s.Spawn("x"));
            for (int i = 0; i < 9; i++) s.ResolveCorrect(ids[i]);
            Assert.IsFalse(s.AtWaveBoundary);
            s.RegisterBreach(ids[9]);
            Assert.IsTrue(s.AtWaveBoundary, "breaches also finish a wave");
            Assert.IsTrue(s.CanSpawn);
            s.Spawn("y");
            Assert.AreEqual((2, 3), (s.WavesStarted, s.WaveCount));
            Assert.IsFalse(s.AtWaveBoundary);
        }

        [Test]
        public void WaveScalingKeepsTheLongWordAllowance()
        {
            var c = new GameConfig().WithDifficulty(Difficulty.Expert);
            string longWord = new string('a', 12);
            Assert.AreEqual(c.FallSeconds(longWord), c.FallSeconds(longWord, 0), 1e-4);
            Assert.AreEqual((10f + 2.4f) / 1.21f, c.FallSeconds(longWord, 2), 1e-4, "allowance first, then 10% per wave");
            Assert.AreEqual(4f * 0.9025f, c.SpawnInterval(2), 1e-4);
            Assert.AreEqual(5, c.MaxConcurrent, "cap unchanged by waves");
        }

        [Test]
        public void ResultsDeduplicateItemsAcrossWavesAndExcludeAborted()
        {
            var s = Playing(hp: 1, spawns: 30);
            Assert.IsNull(s.WordAccuracy, "no resolved meteors: shown as a dash");
            int a1 = s.Spawn("a"); s.ResolveCorrect(a1);
            int a2 = s.Spawn("a"); int b = s.Spawn("b");
            s.RegisterWrong(a2);
            s.RegisterBreach(a2); // HP 1 -> 0: Game Over, b aborted
            Assert.AreEqual(SessionState.GameOver, s.State);
            Assert.AreEqual((1, 1, 1), (s.Items["a"].Correct, s.Items["a"].Missed, s.Items["a"].WrongEnter), "one row per item");
            Assert.IsFalse(s.Items.ContainsKey("b"), "aborted meteor is not an outcome");
            Assert.AreEqual(0.5, s.WordAccuracy.Value, 1e-9);
            Assert.AreEqual((MeteorState?)MeteorState.Aborted, s.StateOf(b));
        }

        [Test]
        public void CoverageHandlesPacksLargerThanTheSession()
        {
            var ids = Enumerable.Range(0, 40).Select(i => $"item-{i:00}").ToList();
            var deck = new VocabularyDeck(ids, 5, 10, 30);
            var s = Playing(hp: 12);
            for (int i = 0; i < 30; i++)
            {
                int m = s.Spawn(deck.Next(null));
                if (i % 3 == 0) s.RegisterBreach(m); else s.ResolveCorrect(m);
                if (s.State != SessionState.Playing && i < 29) Assert.Fail("ended early");
            }
            Assert.AreEqual((30, 20, 10), (s.UniqueSeen, s.UniqueCorrect, s.ReviewCount), "30 distinct of 40: no item repeated before the cycle ends");
            Assert.AreEqual(0.75, MeteorDefenseSession.Coverage(s.UniqueSeen, 40).Value, 1e-9);
            Assert.IsNull(MeteorDefenseSession.Coverage(0, 0));
        }

        [Test]
        public void DeckCyclesAdvanceOnlyWhenExhaustedNotPerWave()
        {
            var deck = new VocabularyDeck(Enumerable.Range(0, 12).Select(i => $"i{i:00}"), 9, 10, 30);
            var cycles = Enumerable.Range(0, 30).Select(_ => { deck.Next(null); return deck.LastIssuedCycle; }).ToList();
            CollectionAssert.AreEqual(Enumerable.Repeat(1, 12).Concat(Enumerable.Repeat(2, 12)).Concat(Enumerable.Repeat(3, 6)).ToList(), cycles);
        }

        [Test]
        public void DevBotsNeverTargetThePlayerHistory()
        {
            Assert.IsNull(LearningHistory.Target(null, devBot: true));
            Assert.AreEqual("tmp.jsonl", LearningHistory.Target("tmp.jsonl", devBot: true), "tests use isolated storage");
            Assert.AreEqual(LearningHistory.DefaultPath, LearningHistory.Target(null, devBot: false));
        }

        [Test]
        public void DurationCountsOnlyPlayingTime()
        {
            var s = Playing();
            s.Tick(2.0);
            s.Pause(); s.Tick(5.0); s.Resume();
            s.Tick(1.5);
            s.Abandon(); s.Tick(9.0);
            Assert.AreEqual(3.5, s.ActiveSeconds, 1e-9);
        }
    }
}
