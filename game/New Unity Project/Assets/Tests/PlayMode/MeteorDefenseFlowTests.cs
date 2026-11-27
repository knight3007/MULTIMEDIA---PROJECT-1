using System.Collections;
using System.IO;
using System.Linq;
using MP1.Content;
using MP1.Core;
using MP1.Game;
using MP1.Library;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace MP1.Tests
{
    /// <summary>G-006 Meteor Defense against the owner-reviewed v47 pack (read-only).</summary>
    public class MeteorDefenseFlowTests
    {
        const string V47 = "reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v47_reviewed/content_pack.json";
        const string B001 = "tests/fixtures/b001/content_pack_states.json";

        static string Repo => VocabularyLibraryController.RepoRoot;

        static PackReport Load(string relative)
        {
            if (Repo == null) Assert.Ignore("repository not reachable");
            var r = ContentPackReader.Load(Path.Combine(Repo, relative));
            if (!r.Ok) Assert.Ignore("pack missing: " + relative);
            return PackEligibility.Evaluate(r.Pack);
        }

        static GameConfig Fast(int spawns = 30, int hp = 4) => new GameConfig
        {
            FirstSpawnDelay = 0.05f, MinSpawnInterval = 0.15f, MaxConcurrent = 3, SessionSpawns = spawns, StartingHp = hp
        };

        static Button Btn(string name) => Object.FindObjectsByType<Button>().Single(b => b.name == name);

        static IEnumerator StartGame(LearningMode mode, GameConfig config)
        {
            LearningSession.Select(Load(V47), mode);
            MeteorDefenseController.ConfigOverride = config;
            yield return SceneManager.LoadSceneAsync(GameEntry.SceneName);
            Camera.main.aspect = 16f / 9f; // target resolutions are 16:9; headless runners default to 4:3 (narrower lanes)
            yield return null;
        }

        static MeteorDefenseController Game => Object.FindFirstObjectByType<MeteorDefenseController>();

        static IEnumerator WaitActive(int n)
        {
            float until = Time.realtimeSinceStartup + 8f;
            while (Game.Active.Count < n && Time.realtimeSinceStartup < until) yield return null;
            yield return null;
            Assert.GreaterOrEqual(Game.Active.Count, n, $"meteors spawned (camera aspect {Camera.main.aspect:F2})");
        }

        [TearDown]
        public void Reset()
        {
            MeteorDefenseController.ConfigOverride = null;
            GameConfig.Selected = new GameConfig();
            Time.timeScale = 1f;
            AudioListener.pause = false;
            MotionSettings.Reduced = false;
        }

        [UnityTest]
        public IEnumerator UsesRealReviewedWordsInBothModesWithoutDuplicates([Values] LearningMode mode)
        {
            yield return StartGame(mode, Fast());
            yield return WaitActive(3);
            var g = Game;
            Assert.IsNull(g.StartError);
            var pack = LearningSession.Pack;
            Assert.AreEqual(3, g.Active.Select(m => m.Item.ItemId).Distinct().Count(), "no simultaneous duplicates");
            foreach (var m in g.Active)
            {
                var it = pack.Items.Single(i => i.ItemId == m.Item.ItemId);
                Assert.AreEqual("ready", it.Status);
                Assert.AreEqual(it.SourceText(mode), m.Item.SourceText, "real pack text for the mode");
                StringAssert.Contains(it.Vietnamese, m.Clue.text, "Vietnamese clue above the meteor");
                Assert.AreEqual(0f, Mathf.DeltaAngle(0, m.Clue.transform.eulerAngles.z), 0.01f, "upright label");
            }
            var urgent = g.Active.OrderBy(m => m.BottomY).ThenBy(m => m.SpawnOrder).First();
            Assert.AreEqual(urgent.Id, g.Target, "auto target = nearest the defense line");
        }

        [UnityTest]
        public IEnumerator CorrectAnswerDestroysOnlyTheTargetOnceAndPlaysItsLanguage([Values] LearningMode mode)
        {
            yield return StartGame(mode, Fast());
            yield return WaitActive(2);
            var g = Game;
            var target = g.Active.Single(m => m.Id == g.Target);
            var other = g.Active.First(m => m.Id != g.Target);
            Assert.IsTrue(g.Submit(target.Item.SourceText));
            Assert.IsFalse(g.Active.Contains(target), "removed");
            Assert.IsTrue(g.Active.Contains(other), "other meteor untouched");
            Assert.AreEqual((150, 1), (g.Session.Score, g.Session.Correct));
            Assert.AreEqual((MeteorState?)MeteorState.Destroyed, g.Session.StateOf(target.Id));
            g.SelectTarget(target.Id);
            Assert.IsFalse(g.Submit(target.Item.SourceText), "a destroyed meteor cannot score twice");
            Assert.AreEqual(150, g.Session.Score);
            float until = Time.realtimeSinceStartup + 5f;
            while (g.LastSpoken == null && Time.realtimeSinceStartup < until) yield return null;
            Assert.AreEqual(target.Item.ItemId, g.LastSpoken.ItemId);
            var packItem = LearningSession.Pack.Items.Single(i => i.ItemId == target.Item.ItemId);
            Assert.AreEqual(packItem.AudioFor(mode).Sha256, g.LastSpoken.Audio.Sha256, "pronunciation of the chosen language");
            Assert.AreNotEqual(packItem.AudioFor(mode == LearningMode.EnglishToVietnamese ? LearningMode.JapaneseToVietnamese : LearningMode.EnglishToVietnamese).Sha256, g.LastSpoken.Audio.Sha256);
            Assert.IsTrue(g.Speech.isPlaying);
        }

        [UnityTest]
        public IEnumerator WrongAnswerKeepsMeteorAndHpAndEmptyInputIsIgnored()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Fast());
            yield return WaitActive(1);
            var g = Game;
            int target = g.Target;
            Assert.IsFalse(g.Submit("definitely wrong"));
            Assert.IsFalse(g.Submit("   "));
            Assert.AreEqual((1, 4, 0), (g.Session.WrongAttempts, g.Session.Hp, g.Session.Score), "empty input is not an attempt");
            Assert.AreEqual((MeteorState?)MeteorState.Active, g.Session.StateOf(target));
            Assert.AreEqual(target, g.Target, "target kept for another try");
        }

        [UnityTest]
        public IEnumerator TabKeepsADraftPerMeteorAndNeverMovesText()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Fast());
            yield return WaitActive(2);
            var g = Game;
            int a = g.Target;
            g.TypeDraft("pi");
            g.TabForTests();
            int b = g.Target;
            Assert.AreNotEqual(a, b);
            Assert.AreEqual("", g.CurrentInput, "the new target starts empty");
            g.TypeDraft("x");
            g.SelectTarget(a);
            Assert.AreEqual("pi", g.CurrentInput, "draft restored");
            Assert.AreEqual("x", g.DraftOf(b));
            string bAnswer = g.Active.Single(m => m.Id == b).Item.SourceText;
            Assert.IsFalse(g.Submit(bAnswer), "B's answer typed while A is locked is checked against A only");
            Assert.AreEqual((MeteorState?)MeteorState.Active, g.Session.StateOf(b), "B not destroyed by an answer meant for it while A was locked");
        }

        [UnityTest]
        public IEnumerator BreachCostsOneHpOnceAndReacquiresTarget()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Fast());
            yield return WaitActive(2);
            var g = Game;
            var target = g.Active.Single(m => m.Id == g.Target);
            g.TypeDraft("partial");
            g.ForceToLine(target);
            yield return null; yield return null;
            Assert.AreEqual((3, 1), (g.Session.Hp, g.Session.Missed));
            Assert.AreEqual((MeteorState?)MeteorState.Breached, g.Session.StateOf(target.Id));
            Assert.IsFalse(g.Active.Contains(target));
            Assert.AreNotEqual(target.Id, g.Target, "reacquired");
            Assert.AreEqual("", g.DraftOf(target.Id), "the lost meteor's draft is gone, not transferred");
            Assert.IsFalse(g.Session.RegisterBreach(target.Id), "no second damage");
        }

        [UnityTest]
        public IEnumerator PauseFreezesMovementAndBlocksInputThenResumes()
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese, Fast());
            yield return WaitActive(1);
            var g = Game;
            var m = g.Active[0];
            Btn("PauseButton").onClick.Invoke();
            Assert.IsTrue(g.PausePanelVisible);
            Assert.AreEqual(0f, Time.timeScale);
            float y = m.transform.position.y;
            int spawned = g.Session.Spawned;
            yield return new WaitForSecondsRealtime(0.4f);
            Assert.AreEqual(y, m.transform.position.y, 1e-5, "frozen");
            Assert.AreEqual(spawned, g.Session.Spawned, "spawn timer frozen");
            Assert.IsFalse(g.Submit(m.Item.SourceText), "no answers while paused");
            Btn("Resume").onClick.Invoke();
            Assert.AreEqual(SessionState.Playing, g.Session.State);
            Assert.AreEqual(1f, Time.timeScale);
            yield return new WaitForSeconds(0.2f);
            Assert.Less(m.transform.position.y, y, "moving again");
        }

        [UnityTest]
        public IEnumerator BackDuringPlayPausesInsteadOfLeaving()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Fast());
            yield return WaitActive(1);
            Btn("BackButton").onClick.Invoke();
            yield return null;
            Assert.AreEqual(GameEntry.SceneName, SceneManager.GetActiveScene().name);
            Assert.AreEqual(SessionState.Paused, Game.Session.State);
            Btn("MenuFromPause").onClick.Invoke();
            Assert.AreEqual(SessionState.Paused, Game.Session.State, "first press only asks for confirmation");
            Btn("MenuFromPause").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("MainMenu", SceneManager.GetActiveScene().name);
            Assert.AreEqual(1f, Time.timeScale);
        }

        [UnityTest]
        public IEnumerator GameOverEndsTheSessionAndStopsSpawning()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Fast(hp: 1));
            yield return WaitActive(2);
            var g = Game;
            g.ForceToLine(g.Active[0]);
            yield return null; yield return null;
            Assert.AreEqual(SessionState.GameOver, g.Session.State);
            Assert.IsTrue(g.EndPanelVisible);
            Assert.AreEqual(0, g.Active.Count, "remaining meteors aborted");
            int spawned = g.Session.Spawned;
            yield return new WaitForSeconds(0.5f);
            Assert.AreEqual(spawned, g.Session.Spawned, "no spawning after game over");
            Assert.AreEqual((0, 1), (g.Session.Hp, g.Session.Missed));
        }

        [UnityTest]
        public IEnumerator VictoryAfterEverySpawnEventIsResolvedThenReplay()
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese, Fast(spawns: 3));
            var g = Game;
            float until = Time.realtimeSinceStartup + 10f;
            while (g.Session.State == SessionState.Playing && Time.realtimeSinceStartup < until)
            {
                if (g.Target >= 0) g.Submit(g.Active.Single(m => m.Id == g.Target).Item.SourceText);
                yield return null;
            }
            Assert.AreEqual(SessionState.Victory, g.Session.State);
            Assert.AreEqual((3, 150 + 165 + 180, 4), (g.Session.Correct, g.Session.Score, g.Session.Hp));
            Assert.IsTrue(g.EndPanelVisible);
            Btn("Replay").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreNotSame(g, Game, "fresh scene");
            Assert.AreEqual((0, SessionState.Playing), (Game.Session.Score, Game.Session.State));
        }

        [UnityTest]
        public IEnumerator CannotStartWithoutSelectionOrWithDeveloperFixture()
        {
            LearningSession.Clear();
            yield return SceneManager.LoadSceneAsync(GameEntry.SceneName);
            yield return null;
            Assert.IsTrue(Game.ErrorPanelVisible);
            Assert.IsNull(Game.Session);
            LearningSession.Select(Load(B001), LearningMode.JapaneseToVietnamese);
            yield return SceneManager.LoadSceneAsync(GameEntry.SceneName);
            yield return null;
            Assert.IsTrue(Game.ErrorPanelVisible, "developer fixture blocked");
            StringAssert.Contains("kiểm thử", Game.StartError);
            Btn("ErrorLibrary").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("VocabularyLibrary", SceneManager.GetActiveScene().name);
        }

        [UnityTest]
        public IEnumerator MainMenuPlayLeadsToLibraryWhosePlayButtonsAreGated()
        {
            yield return SceneManager.LoadSceneAsync("MainMenu");
            yield return null;
            Btn("PlayGame").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("VocabularyLibrary", SceneManager.GetActiveScene().name);
            float until = Time.realtimeSinceStartup + 60f;
            while (VocabularyLibraryController.Cache == null && Time.realtimeSinceStartup < until) yield return null;
            var lib = Object.FindFirstObjectByType<VocabularyLibraryController>();
            var cache = VocabularyLibraryController.Cache;
            var v47 = cache.FirstOrDefault(e => e.ManifestPath.Replace('\\', '/').EndsWith(V47));
            var b001 = cache.FirstOrDefault(e => e.ManifestPath.Replace('\\', '/').EndsWith(B001));
            if (v47 == null || b001 == null) Assert.Ignore("repository packs not reachable");
            Assert.IsTrue(VocabularyLibraryController.Usable(v47));
            Assert.IsFalse(VocabularyLibraryController.Usable(b001), "developer fixture hidden by default");
            lib.Select(b001);
            Assert.IsFalse(Btn("PlayJapanese").interactable, "fixture cannot start production play");
            lib.Select(v47);
            Assert.IsTrue(Btn("PlayEnglish").interactable && Btn("PlayJapanese").interactable);
            Btn("PlayJapanese").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual(GameEntry.SetupScene, SceneManager.GetActiveScene().name, "G-007: configuration step first");
            Btn("StartGame").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual(GameEntry.SceneName, SceneManager.GetActiveScene().name);
            Assert.AreEqual(LearningMode.JapaneseToVietnamese, Game.Mode);
            Assert.IsNull(Game.StartError);
        }
    }
}
