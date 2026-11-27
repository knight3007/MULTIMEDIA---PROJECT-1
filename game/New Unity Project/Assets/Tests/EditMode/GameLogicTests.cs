using System.Collections.Generic;
using System.Linq;
using MP1.Content;
using MP1.Game;
using NUnit.Framework;

namespace MP1.Tests
{
    public class VocabularyDeckTests
    {
        static List<string> Ids(int n) => Enumerable.Range(0, n).Select(i => $"item-{i:00}").ToList();

        [Test]
        public void FifteenItemsOverThirtySpawnsAppearExactlyTwiceInTwoCycles()
        {
            var deck = new VocabularyDeck(Ids(15), seed: 7, itemsPerWave: 10, totalSpawns: 30);
            var issued = new List<string>();
            var cycles = new List<int>();
            for (int i = 0; i < 30; i++) { issued.Add(deck.Next(new List<string>())); cycles.Add(deck.LastIssuedCycle); }
            Assert.IsTrue(deck.Exhausted);
            Assert.IsNull(deck.Next(new List<string>()), "finite session");
            Assert.IsTrue(issued.All(id => id != null));
            Assert.IsTrue(issued.GroupBy(x => x).All(g => g.Count() == 2), "every item exactly twice");
            Assert.AreEqual(15, issued.Distinct().Count());
            CollectionAssert.AreEquivalent(Ids(15), issued.Take(15).ToList(), "cycle 1 is a shuffle without replacement");
            CollectionAssert.AreEquivalent(Ids(15), issued.Skip(15).ToList(), "cycle 2 likewise");
            Assert.IsTrue(cycles.Take(15).All(c => c == 1) && cycles.Skip(15).All(c => c == 2));
            for (int w = 0; w < 3; w++) Assert.AreEqual(10, issued.Skip(w * 10).Take(10).Distinct().Count(), $"wave {w} distinct across the cycle boundary");
            for (int i = 1; i < issued.Count; i++) Assert.AreNotEqual(issued[i - 1], issued[i], "no immediate repeat");
        }

        /// <summary>Simulated play: random lane postponements (Requeue), up to 3 meteors on screen resolving in random order.</summary>
        [TestCase(10, 30, 7)]
        [TestCase(12, 30, 11)]
        [TestCase(15, 30, 3)]
        [TestCase(15, 30, 99)]
        [TestCase(20, 30, 5)]
        [TestCase(30, 30, 8)]
        [TestCase(31, 30, 2)]
        public void PostponedSpawnsNeverLoseCoverageForAnyPackSize(int n, int total, int seed)
        {
            var deck = new VocabularyDeck(Ids(n), seed, 10, total);
            var rnd = new System.Random(seed * 13 + n);
            var active = new List<string>();
            var spawned = new List<string>();
            int guard = 0;
            while (spawned.Count < total && guard++ < 10000)
            {
                if (active.Count > 0 && (active.Count >= 3 || rnd.NextDouble() < 0.4)) active.RemoveAt(rnd.Next(active.Count)); // a meteor resolves
                string id = deck.Next(active);
                if (id == null) continue;
                Assert.IsFalse(active.Contains(id), "never two active meteors with the same item");
                if (rnd.NextDouble() < 0.3) { deck.Requeue(id); continue; } // no free lane: postponed
                active.Add(id);
                spawned.Add(id);
            }
            Assert.AreEqual(total, spawned.Count);
            Assert.AreEqual(total, deck.Issued, "counter counts only successful spawns");
            var counts = Ids(n).Select(i => spawned.Count(s => s == i)).ToList();
            int full = total / n;
            Assert.IsTrue(counts.All(c => c == full || c == full + 1), $"balanced: {string.Join(",", counts)}");
            Assert.AreEqual(System.Math.Min(n, total), counts.Count(c => c > 0), "every item appears when the session is at least one cycle long");
            if (total % n == 0) Assert.IsTrue(counts.All(c => c == full), "whole cycles: exactly equal");
        }

        [Test]
        public void SameSeedSameOrderInputOrderIrrelevant()
        {
            var a = new VocabularyDeck(Ids(12), 42, 10, 20);
            var ids = Ids(12); ids.Reverse();
            var b = new VocabularyDeck(ids, 42, 10, 20);
            for (int i = 0; i < 20; i++) Assert.AreEqual(a.Next(null), b.Next(null));
        }

        [Test]
        public void NeverIssuesAnItemAlreadyOnScreenAndPostponesWhenAllAreActive()
        {
            var deck = new VocabularyDeck(Ids(3), 1, 10, 30);
            var active = new List<string>();
            for (int i = 0; i < 3; i++)
            {
                string id = deck.Next(active);
                Assert.IsFalse(active.Contains(id));
                active.Add(id);
            }
            Assert.IsNull(deck.Next(active), "small pack: postpone instead of duplicating");
            Assert.AreEqual(3, deck.Issued);
        }

        [Test]
        public void RequeueUndoesAPostponedSpawn()
        {
            var a = new VocabularyDeck(Ids(12), 3, 10, 30);
            var b = new VocabularyDeck(Ids(12), 3, 10, 30);
            string first = a.Next(null);
            a.Requeue(first);
            Assert.AreEqual(0, a.Issued);
            for (int i = 0; i < 30; i++) Assert.AreEqual(b.Next(null), a.Next(null), "same sequence as if never drawn");
        }

        [Test]
        public void EmptyDatasetIsSafe()
        {
            var deck = new VocabularyDeck(new string[0], 1, 10, 30);
            Assert.AreEqual(0, deck.Total);
            Assert.IsTrue(deck.Exhausted);
            Assert.IsNull(deck.Next(null));
        }
    }

    public class AnswerCheckerTests
    {
        const LearningMode EN = LearningMode.EnglishToVietnamese, JA = LearningMode.JapaneseToVietnamese;

        [Test]
        public void EnglishIgnoresCaseAndOuterSpaceButKeepsInnerSpacesAndPunctuation()
        {
            Assert.IsTrue(AnswerChecker.Matches("  Traffic Light ", "traffic light", EN));
            Assert.IsFalse(AnswerChecker.Matches("trafficlight", "traffic light", EN));
            Assert.IsFalse(AnswerChecker.Matches("traffic  light", "traffic light", EN), "no guessing of alternate spacing");
            Assert.IsFalse(AnswerChecker.Matches("dont", "don't", EN), "punctuation required");
            Assert.IsTrue(AnswerChecker.Matches("cafe\u0301", "café", EN), "NFC");
            Assert.IsFalse(AnswerChecker.Matches("", "a", EN));
            Assert.IsFalse(AnswerChecker.Matches("   ", "a", EN));
            Assert.IsFalse(AnswerChecker.Matches(null, "a", EN));
        }

        [Test]
        public void JapaneseRequiresTheStoredScript()
        {
            Assert.IsTrue(AnswerChecker.Matches("しんごうき", "しんごうき", JA));
            Assert.IsTrue(AnswerChecker.Matches(" はブラシ ", "はブラシ", JA));
            Assert.IsFalse(AnswerChecker.Matches("信号機", "しんごうき", JA), "no Kanji/Kana substitution");
            Assert.IsFalse(AnswerChecker.Matches("シンゴウキ", "しんごうき", JA), "no Katakana/Hiragana substitution");
            Assert.IsFalse(AnswerChecker.Matches("ﾊﾟｲﾅｯﾌﾟﾙ", "パイナップル", JA), "no width substitution");
            Assert.IsFalse(AnswerChecker.Matches("shingouki", "しんごうき", JA), "no Romaji");
            Assert.IsTrue(AnswerChecker.Matches("ハ\u309Aイ", "パイ", JA), "NFC composes the handakuten");
        }
    }

    public class TargetSelectorTests
    {
        static TargetCandidate C(int id, int order, float d) => new TargetCandidate(id, order, d);

        [Test]
        public void AutoPicksNearestLineThenEarlierSpawn()
        {
            Assert.AreEqual(2, TargetSelector.Resolve(-1, new[] { C(1, 0, 5f), C(2, 1, 2f), C(3, 2, 4f) }));
            Assert.AreEqual(1, TargetSelector.Resolve(-1, new[] { C(1, 0, 2f), C(2, 1, 2f) }), "tie: earlier spawn");
            Assert.AreEqual(-1, TargetSelector.Resolve(5, new TargetCandidate[0]), "no target");
        }

        [Test]
        public void CurrentTargetStaysWhileItExistsAndIsReacquiredWhenGone()
        {
            var active = new[] { C(1, 0, 1f), C(2, 1, 8f) };
            Assert.AreEqual(2, TargetSelector.Resolve(2, active), "no automatic jump to a more urgent meteor");
            Assert.AreEqual(1, TargetSelector.Resolve(9, active), "destroyed/breached target: most urgent remaining");
        }

        [Test]
        public void TabCyclesInDangerOrder()
        {
            var active = new[] { C(1, 0, 6f), C(2, 1, 2f), C(3, 2, 4f) };
            Assert.AreEqual(3, TargetSelector.Cycle(2, active));
            Assert.AreEqual(1, TargetSelector.Cycle(3, active));
            Assert.AreEqual(2, TargetSelector.Cycle(1, active), "wraps");
            Assert.AreEqual(2, TargetSelector.Cycle(-1, active));
            Assert.AreEqual(-1, TargetSelector.Cycle(1, new TargetCandidate[0]));
        }
    }

    public class MeteorDefenseSessionTests
    {
        static MeteorDefenseSession Playing(int hp = 4, int spawns = 30)
        {
            var s = new MeteorDefenseSession(new GameConfig { StartingHp = hp, SessionSpawns = spawns });
            s.Start();
            return s;
        }

        [Test]
        public void CorrectScoresOnceAndWrongDoesNotDestroyOrHurt()
        {
            var s = Playing();
            int m = s.Spawn("a");
            Assert.IsTrue(s.RegisterWrong(m));
            Assert.AreEqual((MeteorState?)MeteorState.Active, s.StateOf(m));
            Assert.AreEqual((4, 0, 1), (s.Hp, s.Score, s.WrongAttempts));
            Assert.IsTrue(s.ResolveCorrect(m));
            Assert.IsFalse(s.ResolveCorrect(m), "duplicate submission");
            Assert.IsFalse(s.RegisterBreach(m), "destroyed meteor cannot damage");
            Assert.AreEqual((150, 1, 4, 0), (s.Score, s.Correct, s.Hp, s.Missed));
            Assert.AreEqual(1, s.WrongAttemptsByItem["a"]);
        }

        [Test]
        public void BreachCostsOneHpOnceAndGameOverAbortsTheRest()
        {
            var s = Playing(hp: 2);
            int a = s.Spawn("a"), b = s.Spawn("b"), c = s.Spawn("c");
            Assert.IsTrue(s.RegisterBreach(a));
            Assert.IsFalse(s.RegisterBreach(a), "once");
            Assert.AreEqual(1, s.Hp);
            Assert.IsTrue(s.RegisterBreach(b));
            Assert.AreEqual((0, SessionState.GameOver), (s.Hp, s.State));
            Assert.AreEqual((MeteorState?)MeteorState.Aborted, s.StateOf(c));
            Assert.IsFalse(s.RegisterBreach(c), "no damage after game over");
            Assert.IsFalse(s.ResolveCorrect(c), "no score after game over");
            Assert.AreEqual(-1, s.Spawn("d"), "no spawning after game over");
            Assert.AreEqual((0, 2), (s.Hp, s.Missed));
        }

        [Test]
        public void VictoryWhenAllSpawnEventsResolveWithHpLeft()
        {
            var s = Playing(hp: 3, spawns: 3);
            int a = s.Spawn("a"), b = s.Spawn("b"), c = s.Spawn("c");
            Assert.AreEqual(-1, s.Spawn("d"), "session length reached");
            s.ResolveCorrect(a); s.RegisterBreach(b);
            Assert.AreEqual(SessionState.Playing, s.State);
            s.ResolveCorrect(c);
            Assert.AreEqual(SessionState.Victory, s.State);
            Assert.AreEqual((300, 2, 1, 2), (s.Score, s.Correct, s.Missed, s.Hp)); // breach resets combo: 150 + 150 (Normal x1.5)
        }

        [Test]
        public void PauseBlocksInputAndAbandonEndsWithoutVictory()
        {
            var s = Playing();
            int a = s.Spawn("a");
            s.Pause();
            Assert.IsFalse(s.ResolveCorrect(a));
            Assert.IsFalse(s.RegisterWrong(a));
            Assert.IsFalse(s.RegisterBreach(a));
            Assert.AreEqual(-1, s.Spawn("b"));
            s.Resume();
            Assert.IsTrue(s.ResolveCorrect(a));
            s.Abandon();
            Assert.AreEqual(SessionState.Abandoned, s.State);
            Assert.IsTrue(s.IsOver);
        }

        [Test]
        public void ReadySessionAcceptsNothingUntilStarted()
        {
            var s = new MeteorDefenseSession(new GameConfig());
            Assert.AreEqual(-1, s.Spawn("a"));
            s.Start();
            Assert.AreEqual(0, s.Spawn("a"));
        }
    }

    public class LaneChooserTests
    {
        static readonly float[] Lanes = { -7f, -3.5f, 0f, 3.5f, 7f };

        [Test]
        public void EmptySkyUsesEveryLaneNotJustTheFirst()
        {
            var rng = new System.Random(5);
            var used = new HashSet<int>();
            for (int i = 0; i < 200; i++) used.Add(LaneChooser.Choose(Lanes, 2f, new LaneOccupant[0], 6f, () => (float)rng.NextDouble()));
            Assert.AreEqual(5, used.Count, "random tie-break must reach all lanes (regression: MaxValue clearance always chose lane 0)");
        }

        [Test]
        public void LanesThatWouldOverlapLabelsAreSkippedOrSpawnPostponed()
        {
            var near = new[] { new LaneOccupant(0f, 6f, 3f) };
            for (int i = 0; i < 50; i++)
            {
                int lane = LaneChooser.Choose(Lanes, 3f, near, 6f, () => 0.5f);
                Assert.AreNotEqual(2, lane, "same lane as a meteor near the spawn row");
                Assert.Greater(System.Math.Abs(Lanes[lane]), 3.29f);
            }
            var far = new[] { new LaneOccupant(0f, -2f, 3f) };
            Assert.AreEqual(0, LaneChooser.Choose(new[] { 0f }, 3f, far, 6f, () => 0f), "meteors far below do not block the only lane");
            var crowded = new[] { new LaneOccupant(-7f, 6f, 6f), new LaneOccupant(0f, 6f, 6f), new LaneOccupant(7f, 6f, 6f) };
            Assert.AreEqual(-1, LaneChooser.Choose(Lanes, 6f, crowded, 6f, () => 0f), "no room: postpone");
        }
    }

    public class GameConfigAndAudienceTests
    {
        [Test]
        public void LongTermsFallSlowerUpToTheCap()
        {
            var c = new GameConfig();
            Assert.AreEqual(15.6f, c.FallSeconds("pineapple"), 1e-4, "9 units: +0.6");
            Assert.AreEqual(15f, c.FallSeconds("castle"), 1e-4);
            Assert.AreEqual(15f + 0.6f * 5, c.FallSeconds("traffic light"), 1e-4, "13 units");
            Assert.AreEqual(23f, c.FallSeconds(new string('a', 100)), 1e-4, "cap +8 s");
        }

        [Test]
        public void DeveloperFixturesAreRecognisedByLocationOrSimulatedEvidence()
        {
            Assert.IsTrue(PackAudience.IsDeveloperFixture(null, "D:/repo/tests/fixtures/b001/content_pack_states.json"));
            Assert.IsTrue(PackAudience.IsDeveloperFixture(null, @"D:\repo\game\New Unity Project\ContentPackFixtures\x\content_pack.json"));
            Assert.IsFalse(PackAudience.IsDeveloperFixture(null, "D:/repo/reports/EXCEL_15_SMOKE/run/content_pack_v47_reviewed/content_pack.json"));
            var pack = new ContentPack();
            pack.Items.Add(new PackItem { Evidence = { new QualityEvidence { Reviewer = "fixture-simulator" } } });
            Assert.IsTrue(PackAudience.IsDeveloperFixture(pack, "D:/elsewhere/content_pack.json"));
        }
    }
}
