using System.Collections;
using System.Globalization;
using System.IO;
using System.Linq;
using MP1.Content;
using MP1.Game;
using MP1.Library;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;

namespace MP1.Tests
{
    /// <summary>G-007-R2 character-based combat (D-044) against the owner-reviewed v47 pack (read-only).</summary>
    public class TypingCombatFlowTests
    {
        const string V47 = "reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v47_reviewed/content_pack.json";

        static IEnumerator StartGame(LearningMode mode, AnswerMode answer = AnswerMode.FullWord)
        {
            string repo = VocabularyLibraryController.RepoRoot;
            if (repo == null) Assert.Ignore("repository not reachable");
            var r = ContentPackReader.Load(Path.Combine(repo, V47));
            if (!r.Ok) Assert.Ignore("v47 missing");
            LearningSession.Select(PackEligibility.Evaluate(r.Pack), mode);
            MeteorDefenseController.ConfigOverride = new GameConfig { Answer = answer, FirstSpawnDelay = 0.05f, MinSpawnInterval = 0.15f, BaseFallSeconds = 40f };
            yield return SceneManager.LoadSceneAsync(GameEntry.SceneName);
            Camera.main.aspect = 16f / 9f;
            float until = Time.realtimeSinceStartup + 8f;
            while (G.Active.Count < 2 && Time.realtimeSinceStartup < until) yield return null;
            yield return null;
            Assert.GreaterOrEqual(G.Active.Count, 2);
        }

        static MeteorDefenseController G => Object.FindFirstObjectByType<MeteorDefenseController>();
        static MeteorView TargetView => G.Active.Single(m => m.Id == G.Target);
        static string[] Units(string s) => BlankPuzzle.Split(s);
        static string Prefix(string s, int n) => string.Concat(Units(s).Take(n));

        [TearDown]
        public void Reset()
        {
            MeteorDefenseController.ConfigOverride = null;
            Time.timeScale = 1f;
            AudioListener.pause = false;
        }

        [UnityTest]
        public IEnumerator EachCorrectCharacterFiresOnceAndTheLastDestroysWithoutEnter([Values] LearningMode mode)
        {
            yield return StartGame(mode);
            var m = TargetView;
            string word = m.Item.SourceText;
            int shots = m.Combat.Required;
            for (int i = 1; i <= Units(word).Length; i++)
            {
                int before = G.LasersFired;
                G.TypeDraft(Prefix(word, i));
                bool counts = BlankPuzzle.Selectable(Units(word)[i - 1]);
                Assert.AreEqual(before + (counts ? 1 : 0), G.LasersFired, $"one shot per answer unit ({i})");
                if (i < Units(word).Length) Assert.AreEqual(MeteorState.Active, G.Session.StateOf(m.Id));
            }
            Assert.AreEqual(MeteorState.Destroyed, G.Session.StateOf(m.Id), "auto-destroyed on the last correct unit");
            Assert.AreEqual((150, 1, 0), (G.Session.Score, G.Session.Correct, G.Session.WrongAttempts), "score once");
            Assert.IsFalse(G.Submit(word), "cannot score the same meteor again");
            Assert.AreEqual(150, G.Session.Score);
            float until = Time.realtimeSinceStartup + 5f;
            while (G.LastSpoken?.ItemId != m.Item.ItemId && Time.realtimeSinceStartup < until) yield return null;
            Assert.AreEqual(m.Item.ItemId, G.LastSpoken.ItemId, "pronunciation after destruction");
            Assert.AreEqual(shots, m.Combat.Hits);
        }

        [UnityTest]
        public IEnumerator WrongUnitDealsNoDamageAndBackspaceRetypeCannotFarm()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese);
            var m = TargetView;
            string w = m.Item.SourceText;
            G.TypeDraft(Prefix(w, 1));
            int lasers = G.LasersFired;
            G.TypeDraft(Prefix(w, 1) + "#");
            Assert.AreEqual((1, lasers), (m.Combat.Hits, G.LasersFired), "wrong unit: no damage, no shot");
            Assert.AreEqual(0, G.Session.WrongAttempts, "typing feedback is not a wrong Enter");
            G.TypeDraft(Prefix(w, 1) + "#");
            G.TypeDraft("");
            G.TypeDraft(Prefix(w, 1));
            Assert.AreEqual((1, lasers), (m.Combat.Hits, G.LasersFired), "backspace + retype gives nothing");
            yield return null;
            Assert.AreEqual(MeteorState.Active, G.Session.StateOf(m.Id));
        }

        [UnityTest]
        public IEnumerator PasteCountsAllUnitsButCapsTheVisibleBeams()
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese);
            var m = G.Active.OrderByDescending(v => v.Combat.Required).First();
            G.SelectTarget(m.Id);
            int n = Mathf.Min(4, Units(m.Item.SourceText).Length - 1);
            int lasers = G.LasersFired;
            G.TypeDraft(Prefix(m.Item.SourceText, n));
            Assert.AreEqual(Units(m.Item.SourceText).Take(n).Count(BlankPuzzle.Selectable), m.Combat.Hits, "committed multi-unit text counts fully");
            Assert.LessOrEqual(G.LasersFired - lasers, 3, "bounded visual effect");
            yield return null;
        }

        [UnityTest]
        public IEnumerator UnfinishedImeCompositionDealsNoDamageUntilCommitted()
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese);
            var m = TargetView;
            G.TestComposition = "ri"; // IME still composing
            G.TypeDraft(Prefix(m.Item.SourceText, 1));
            Assert.AreEqual(0, m.Combat.Hits, "no damage while the IME composes");
            G.TestComposition = "";
            yield return null; yield return null;
            Assert.AreEqual(BlankPuzzle.Selectable(Units(m.Item.SourceText)[0]) ? 1 : 0, m.Combat.Hits, "applied once committed");
            G.TestComposition = null;
        }

        [UnityTest]
        public IEnumerator TabKeepsDamageOnItsMeteorAndTheShipAimsAtTheNewTarget()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese);
            var a = TargetView;
            G.TypeDraft(Prefix(a.Item.SourceText, 2));
            int hitsA = a.Combat.Hits;
            G.TabForTests();
            var b = TargetView;
            Assert.AreNotEqual(a.Id, b.Id);
            Assert.AreEqual(0, b.Combat.Hits, "progress never moves to another meteor");
            G.TypeDraft(Prefix(b.Item.SourceText, 1));
            Assert.AreEqual(hitsA, a.Combat.Hits, "A keeps its damage");
            yield return new WaitForSeconds(0.5f); // aim turns at 540°/s; frame count is meaningless headless
            Vector3 dir = (b.SpriteRoot.position - G.Ship.position).normalized;
            float clamped = Mathf.Abs(Vector2.SignedAngle(Vector2.up, dir)) > 75f ? 0.7f : 0.97f;
            Assert.Greater(Vector3.Dot(G.Ship.up, dir), clamped, "ship turned toward the new target");
            G.SelectTarget(a.Id);
            Assert.AreEqual(Prefix(a.Item.SourceText, 2), G.CurrentInput, "A's draft restored");
        }

        [UnityTest]
        public IEnumerator FillInTheBlankShootsOnlyTheMissingUnits()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, AnswerMode.FillInTheBlank);
            var m = TargetView;
            string missing = m.Puzzle.Missing();
            Assert.AreEqual(Units(missing).Length, m.Combat.Required);
            int lasers = G.LasersFired;
            for (int i = 1; i <= Units(missing).Length; i++) G.TypeDraft(Prefix(missing, i));
            Assert.AreEqual(lasers + Units(missing).Length, G.LasersFired);
            Assert.AreEqual(MeteorState.Destroyed, G.Session.StateOf(m.Id));
            yield return null;
        }

        [UnityTest]
        public IEnumerator BreachedTargetCancelsItsBeamsSafelyAndPauseBlocksDamage()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese);
            var a = TargetView;
            var other = G.Active.First(v => v.Id != a.Id);
            G.TypeDraft(Prefix(a.Item.SourceText, 3)); // up to three staggered beams
            G.ForceToLine(a);
            yield return null; yield return null;
            Assert.AreEqual(MeteorState.Breached, G.Session.StateOf(a.Id));
            yield return new WaitForSeconds(0.4f);
            Assert.AreEqual(0, other.Combat.Hits, "a beam never damages another meteor");
            int t = G.Target;
            G.Pause();
            int hits = G.Active.Single(v => v.Id == t).Combat.Hits;
            G.TypeDraft(Prefix(G.Active.Single(v => v.Id == t).Item.SourceText, 2));
            Assert.AreEqual(hits, G.Active.Single(v => v.Id == t).Combat.Hits, "no damage while paused");
            G.Resume();
        }

        [UnityTest]
        public IEnumerator ReplayStartsEveryMeteorWithoutDamage()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese);
            G.TypeDraft(Prefix(TargetView.Item.SourceText, 2));
            G.Restart();
            yield return null; yield return null;
            Camera.main.aspect = 16f / 9f;
            float until = Time.realtimeSinceStartup + 5f;
            while (G.Active.Count < 1 && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(G.Active.All(v => v.Combat.Hits == 0));
            Assert.AreEqual((0, 0), (G.Session.Score, G.LasersFired));
        }
    }
}
