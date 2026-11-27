using System.Collections;
using System.IO;
using System.Linq;
using MP1.Content;
using MP1.Game;
using MP1.Library;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace MP1.Tests
{
    /// <summary>G-007 configuration, difficulty, hint, answer and targeting modes against the owner-reviewed v47 pack (read-only).</summary>
    public class GameConfigFlowTests
    {
        const string V47 = "reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v47_reviewed/content_pack.json";
        const string B001 = "tests/fixtures/b001/content_pack_states.json";

        static PackReport Load(string relative)
        {
            string repo = VocabularyLibraryController.RepoRoot;
            if (repo == null) Assert.Ignore("repository not reachable");
            var r = ContentPackReader.Load(Path.Combine(repo, relative));
            if (!r.Ok) Assert.Ignore("pack missing: " + relative);
            return PackEligibility.Evaluate(r.Pack);
        }

        static GameConfig Fast(Difficulty d = Difficulty.Normal, HintMode h = HintMode.TextOnly, AnswerMode a = AnswerMode.FullWord, TargetingMode t = TargetingMode.Hybrid)
        {
            var c = new GameConfig { Hint = h, Answer = a, Targeting = t }.WithDifficulty(d);
            c.FirstSpawnDelay = 0.05f; c.MinSpawnInterval = 0.15f;
            return c;
        }

        static MeteorDefenseController Game => Object.FindFirstObjectByType<MeteorDefenseController>();
        static GameSetupController Setup => Object.FindFirstObjectByType<GameSetupController>();

        static IEnumerator StartGame(LearningMode mode, GameConfig config)
        {
            LearningSession.Select(Load(V47), mode);
            MeteorDefenseController.ConfigOverride = config;
            yield return SceneManager.LoadSceneAsync(GameEntry.SceneName);
            Camera.main.aspect = 16f / 9f; // target resolutions are 16:9; headless runners default to 4:3
            float until = Time.realtimeSinceStartup + 20f; // image modes preload pictures first
            while ((Game.Session == null || Game.Session.State == SessionState.Ready) && Game.StartError == null && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsNull(Game.StartError);
        }

        static IEnumerator WaitActive(int n)
        {
            float until = Time.realtimeSinceStartup + 10f;
            while (Game.Active.Count < n && Time.realtimeSinceStartup < until) yield return null;
            yield return null;
            Assert.GreaterOrEqual(Game.Active.Count, n, "meteors spawned");
        }

        [TearDown]
        public void Reset()
        {
            MeteorDefenseController.ConfigOverride = null;
            GameConfig.Selected = new GameConfig();
            Time.timeScale = 1f;
            AudioListener.pause = false;
        }

        /// <summary>Whole configuration matrix on real v47 data, without running sessions: every usable item can be answered.</summary>
        [Test]
        public void V47CompatibilityMatrixIsAnswerableForEveryConfiguration()
        {
            var report = Load(V47);
            var log = new System.Text.StringBuilder("G007_MATRIX\n");
            foreach (LearningMode mode in System.Enum.GetValues(typeof(LearningMode)))
            {
                LearningSession.Select(report, mode);
                foreach (HintMode h in System.Enum.GetValues(typeof(HintMode)))
                foreach (AnswerMode a in System.Enum.GetValues(typeof(AnswerMode)))
                foreach (Difficulty d in System.Enum.GetValues(typeof(Difficulty)))
                foreach (TargetingMode t in System.Enum.GetValues(typeof(TargetingMode)))
                {
                    var c = new GameConfig { Hint = h, Answer = a, Targeting = t }.WithDifficulty(d);
                    var r = GameCompatibility.Check(LearningSession.EligibleItems, c, mode);
                    Assert.AreEqual(LearningSession.EligibleItems.Count, r.Usable.Count + r.Excluded.Count, "every item accounted for");
                    foreach (var it in r.Usable)
                    {
                        if (a == AnswerMode.FillInTheBlank)
                        {
                            var p = BlankPuzzle.Create(it.SourceText, c.HiddenRatio, 7);
                            Assert.IsNotNull(p, it.SourceText);
                            Assert.That(p.HiddenCount, Is.InRange(1, BlankPuzzle.SelectableCount(it.SourceText) - 1));
                            Assert.IsTrue(p.Matches(p.Missing(), it.SourceText, mode), $"{it.SourceText} {d}");
                        }
                        else Assert.IsTrue(AnswerChecker.Matches(it.SourceText, it.SourceText, mode));
                    }
                    if (d == Difficulty.Normal && t == TargetingMode.Hybrid)
                        log.AppendLine($"{LearningModes.Id(mode)} {h} {a}: usable {r.Usable.Count}/{LearningSession.EligibleItems.Count} start={r.CanStart}"
                            + (r.Excluded.Count > 0 ? " excluded: " + string.Join("; ", r.Excluded.Select(e => e.Key.SourceText + " (" + e.Value + ")")) : ""));
                }
            }
            Debug.Log(log.ToString());
        }

        [UnityTest]
        public IEnumerator SetupShowsPackCountsPreviewAndPassesTheChoiceToTheGame()
        {
            LearningSession.Select(Load(V47), LearningMode.EnglishToVietnamese);
            yield return SceneManager.LoadSceneAsync(GameEntry.SetupScene);
            yield return null;
            var s = Setup;
            Assert.IsTrue(s.StartButton.interactable);
            Assert.AreEqual(LearningSession.EligibleItems.Count, s.Compat.Usable.Count, "v47 TextOnly/FullWord keeps every eligible word");
            var before = s.Sample;
            Assert.IsNotNull(before);
            s.SetDifficulty(Difficulty.Hard);
            s.SetAnswer(AnswerMode.FillInTheBlank);
            s.SetTargeting(TargetingMode.Manual);
            var answer = Object.FindObjectsByType<TMPro.TextMeshProUGUI>().Single(t => t.name == "Answer");
            StringAssert.Contains("_", answer.text, "preview shows the blank pattern");
            s.StartGame();
            yield return null; yield return null;
            Assert.AreEqual(GameEntry.SceneName, SceneManager.GetActiveScene().name);
            var c = Game.Config;
            Assert.AreEqual((Difficulty.Hard, 3, 4, AnswerMode.FillInTheBlank, TargetingMode.Manual), (c.Difficulty, c.StartingHp, c.MaxConcurrent, c.Answer, c.Targeting));
            Assert.AreEqual(3, Game.Session.Hp);
            Game.Restart();
            yield return null; yield return null;
            Assert.AreEqual(Difficulty.Hard, Game.Config.Difficulty, "Replay keeps the configuration");
        }

        [UnityTest]
        public IEnumerator SetupBlocksFixturesAndMissingSelectionWithAReason()
        {
            LearningSession.Clear();
            yield return SceneManager.LoadSceneAsync(GameEntry.SetupScene);
            yield return null;
            Assert.IsFalse(Setup.StartButton.interactable);
            LearningSession.Select(Load(B001), LearningMode.JapaneseToVietnamese);
            yield return SceneManager.LoadSceneAsync(GameEntry.SetupScene);
            yield return null;
            Assert.IsFalse(Setup.StartButton.interactable);
            var status = Object.FindObjectsByType<TMPro.TextMeshProUGUI>().Single(t => t.name == "Status");
            StringAssert.Contains("kiểm thử", status.text);
            Object.FindObjectsByType<Button>().Single(b => b.name == "BackButton").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("VocabularyLibrary", SceneManager.GetActiveScene().name, "Back returns to pack selection");
        }

        [UnityTest]
        public IEnumerator FillInTheBlankAcceptsOnlyMissingUnitsAndPuzzleSurvivesTab([Values] LearningMode mode)
        {
            yield return StartGame(mode, Fast(a: AnswerMode.FillInTheBlank));
            yield return WaitActive(2);
            var g = Game;
            var a = g.Active.Single(m => m.Id == g.Target);
            Assert.IsNotNull(a.Puzzle);
            string shown = a.Puzzle.Display();
            g.TypeDraft("z");
            g.TabForTests();
            g.SelectTarget(a.Id);
            Assert.AreEqual(shown, a.Puzzle.Display(), "puzzle not regenerated on target switch");
            Assert.AreEqual("z", g.CurrentInput, "draft kept on its meteor");
            Assert.IsFalse(g.Submit(a.Item.SourceText), "the full word is not the blank answer");
            Assert.IsTrue(g.Submit(a.Puzzle.Missing()));
            Assert.AreEqual(MeteorState.Destroyed, g.Session.StateOf(a.Id));
        }

        [UnityTest]
        public IEnumerator TextHintsShowMeaningAndFirstUnitOnlyWhenChosenAndNoImages([Values] HintMode hint)
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese, Fast(h: hint));
            yield return WaitActive(2);
            foreach (var m in Game.Active)
            {
                StringAssert.Contains(m.Item.Meaning, m.Clue.text);
                string first = System.Globalization.StringInfo.GetNextTextElement(m.Item.SourceText, 0);
                Assert.AreEqual(hint == HintMode.TextOnly, m.Clue.text.Contains(first + "</noparse>…"), "first-unit hint only in Nghĩa + chữ đầu");
                Assert.AreEqual(0, m.GetComponentsInChildren<SpriteRenderer>().Count(r => r.name == "Picture"), "no image hints in gameplay (D-043)");
            }
        }

        [UnityTest]
        public IEnumerator ManualNeedsTabAndAutoIgnoresTab()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Fast(t: TargetingMode.Manual));
            yield return WaitActive(2);
            Assert.AreEqual(-1, Game.Target, "Manual never acquires by itself");
            Game.TypeDraft("abc");
            Assert.AreEqual("", Game.CurrentInput, "nothing typed without a target");
            Game.TabForTests();
            var urgent = Game.Active.OrderBy(m => m.BottomY).ThenBy(m => m.SpawnOrder).First();
            Assert.AreEqual(urgent.Id, Game.Target);
            var t = Game.Active.Single(m => m.Id == Game.Target);
            Assert.IsTrue(Game.Submit(t.Item.SourceText));
            yield return null;
            Assert.AreEqual(-1, Game.Target, "released, not re-acquired");

            yield return StartGame(LearningMode.EnglishToVietnamese, Fast(t: TargetingMode.Auto));
            yield return WaitActive(2);
            int before = Game.Target;
            Assert.GreaterOrEqual(before, 0);
            Game.TabForTests();
            Assert.AreEqual(before, Game.Target, "Tab disabled in Auto");
        }

        [UnityTest]
        public IEnumerator ExpertUsesItsLimitsAndEveryMeteorSpawnsBelowTheHud([Values] HintMode hint)
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese, Fast(Difficulty.Expert, hint, AnswerMode.FillInTheBlank));
            Assert.AreEqual(2, Game.Session.Hp);
            float safeTop = SpawnLayout.SafeTop(Camera.main.orthographicSize);
            var seen = new System.Collections.Generic.HashSet<int>();
            float until = Time.realtimeSinceStartup + 8f;
            while (Time.realtimeSinceStartup < until && Game.Session.State == SessionState.Playing)
            {
                Assert.LessOrEqual(Game.Active.Count, 5, "Expert max concurrent");
                foreach (var m in Game.Active)
                    if (seen.Add(m.Id))
                    {
                        Assert.LessOrEqual(m.transform.position.y + m.StackTop, safeTop + 0.01f, "whole hint stack below the HUD at spawn");
                        float halfW = Camera.main.orthographicSize * Camera.main.aspect;
                        Assert.LessOrEqual(Mathf.Abs(m.transform.position.x) + m.LabelWidth / 2f, halfW, "long Fill labels stay on screen");
                    }
                yield return null;
            }
            // Label-overlap avoidance (spec §4) postpones spawns, so fewer than 5 can be on screen.
            Assert.GreaterOrEqual(seen.Count, 2);
        }

        [UnityTest]
        public IEnumerator RapidCorrectAnswersSpeakOnlyTheNewestWord()
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese, Fast());
            yield return WaitActive(3);
            LearningItem last = null;
            for (int i = 0; i < 3; i++)
            {
                var t = Game.Active.Single(m => m.Id == Game.Target);
                last = t.Item;
                Assert.IsTrue(Game.Submit(t.Item.SourceText));
                yield return null;
            }
            float until = Time.realtimeSinceStartup + 5f;
            while (Game.LastSpoken != last && Time.realtimeSinceStartup < until) yield return null;
            yield return new WaitForSeconds(0.3f);
            Assert.AreEqual(last.ItemId, Game.LastSpoken.ItemId, "a late older clip never replaces the newest");
            Assert.IsTrue(Game.Speech.isPlaying, "one speech source; the newest clip is the one playing");
        }
    }
}
