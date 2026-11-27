using System.Collections;
using System.IO;
using System.Linq;
using MP1.Content;
using MP1.Game;
using MP1.Library;
using MP1.UI;
using NUnit.Framework;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace MP1.Tests
{
    /// <summary>Keeps every PlayMode session's learning history out of the real persistentDataPath.</summary>
    [SetUpFixture]
    public class PlayModeHistorySandbox
    {
        public static string Dir;

        [OneTimeSetUp]
        public void Redirect()
        {
            Dir = Path.Combine(Path.GetTempPath(), "mp1_playmode_history_" + System.Guid.NewGuid().ToString("N"));
            MeteorDefenseController.HistoryPathOverride = Path.Combine(Dir, "sessions_v1.jsonl");
        }

        [OneTimeTearDown]
        public void Clean()
        {
            MeteorDefenseController.HistoryPathOverride = null;
            if (Directory.Exists(Dir)) Directory.Delete(Dir, true);
        }
    }

    /// <summary>G-008 waves, combo/score, speech slot, results, review and history against the reviewed v47 pack.</summary>
    public class G008FlowTests
    {
        const string V47 = "reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v47_reviewed/content_pack.json";

        static MeteorDefenseController G => Object.FindFirstObjectByType<MeteorDefenseController>();
        static MeteorView TargetView => G.Active.FirstOrDefault(m => m.Id == G.Target);

        static IEnumerator StartGame(LearningMode mode, GameConfig cfg, int minActive = 1)
        {
            string repo = VocabularyLibraryController.RepoRoot;
            if (repo == null) Assert.Ignore("repository not reachable");
            var r = ContentPackReader.Load(Path.Combine(repo, V47));
            if (!r.Ok) Assert.Ignore("v47 missing");
            LearningSession.Select(PackEligibility.Evaluate(r.Pack), mode);
            MeteorDefenseController.ConfigOverride = cfg;
            yield return SceneManager.LoadSceneAsync(GameEntry.SceneName);
            Camera.main.aspect = 16f / 9f;
            float until = Time.realtimeSinceStartup + 8f;
            while (G.Active.Count < minActive && Time.realtimeSinceStartup < until) yield return null;
            Assert.GreaterOrEqual(G.Active.Count, minActive);
        }

        static GameConfig Short(int spawns, int perWave, float wavePause = 0.3f, int max = 3) => new GameConfig
        {
            SessionSpawns = spawns, ItemsPerWave = perWave, WavePauseSeconds = wavePause, MaxConcurrent = max,
            FirstSpawnDelay = 0.05f, MinSpawnInterval = 0.1f, BaseFallSeconds = 40f, StartingHp = 3
        };

        static void Kill(MeteorView m) { G.SelectTarget(m.Id); G.TypeDraft(m.Item.SourceText); }

        [TearDown]
        public void Reset()
        {
            MeteorDefenseController.ConfigOverride = null;
            VocabularyPreviewController.ReviewItemIds = null;
            Time.timeScale = 1f;
            AudioListener.pause = false;
        }

        [UnityTest]
        public IEnumerator ThreeWavesGateSpawnsScoreWithComboAndWriteOneHistoryLine()
        {
            int before = LearningHistory.Read(MeteorDefenseController.HistoryPathOverride).Count;
            yield return StartGame(LearningMode.EnglishToVietnamese, Short(6, 2));
            bool bannerSeen = false;
            float until = Time.realtimeSinceStartup + 20f;
            while (G.Session.State == SessionState.Playing && Time.realtimeSinceStartup < until)
            {
                Assert.LessOrEqual(G.Session.Spawned, G.Session.Resolved / 2 * 2 + 2, "next wave waits for the previous one");
                bannerSeen |= G.WaveBannerVisible && G.Session.WavesStarted >= 1 && G.Session.Resolved == 2;
                if (TargetView is MeteorView t) Kill(t);
                yield return null;
            }
            Assert.AreEqual(SessionState.Victory, G.Session.State);
            Assert.IsTrue(bannerSeen, "wave 2 banner shown during the transition");
            Assert.AreEqual((3, 3), (G.Session.WavesStarted, G.Session.WaveCount));
            Assert.AreEqual(150 + 165 + 180 + 195 + 210 + 225, G.Session.Score, "Normal x1.5 with combo, awarded once per meteor");
            Assert.AreEqual(6, G.Session.MaxCombo);
            Assert.IsTrue(G.EndPanelVisible);
            StringAssert.Contains("×6", G.ResultsText());
            StringAssert.Contains("Đợt 3 / 3", G.ResultsText());
            Assert.IsNull(G.HistoryError);
            var all = LearningHistory.Read(MeteorDefenseController.HistoryPathOverride);
            Assert.AreEqual(before + 1, all.Count, "exactly one history line per session");
            Assert.AreEqual(("Victory", 6, 6), (all.Last().outcome, all.Last().correct, all.Last().max_combo));
            Object.FindObjectsByType<Button>().Single(b => b.name == "Replay").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual((0, 0, 0), (G.Session.Score, G.Session.Combo, G.Session.MaxCombo), "replay resets combo and score");
        }

        [UnityTest]
        public IEnumerator PauseFreezesTheWaveTransition()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Short(4, 2, wavePause: 1f), minActive: 2);
            foreach (var m in G.Active.ToList()) Kill(m);
            yield return null; yield return null;
            Assert.IsTrue(G.Session.AtWaveBoundary);
            Assert.IsTrue(G.WaveBannerVisible);
            G.Pause();
            yield return new WaitForSecondsRealtime(1.5f);
            Assert.AreEqual(2, G.Session.Spawned, "no spawn while paused");
            G.Resume();
            float until = Time.realtimeSinceStartup + 4f;
            while (G.Session.Spawned == 2 && Time.realtimeSinceStartup < until) yield return null;
            Assert.Greater(G.Session.Spawned, 2, "wave 2 starts after the remaining pause");
            Assert.IsFalse(G.WaveBannerVisible);
        }

        [UnityTest]
        public IEnumerator RapidKillsKeepOnePendingWordInTheSelectedLanguage()
        {
            yield return StartGame(LearningMode.JapaneseToVietnamese, Short(30, 10), minActive: 3);
            float until = Time.realtimeSinceStartup + 5f;
            while (!G.Active.All(m => G.ClipCached(m.Item.ItemId)) && Time.realtimeSinceStartup < until) yield return null;
            var three = G.Active.Take(3).ToList();
            foreach (var m in three) Kill(m);
            Assert.IsTrue(G.SpeechPending, "words 2 and 3 share one pending slot");
            Assert.AreEqual(1, G.SpeechesStarted, "first word playing, not interrupted");
            until = Time.realtimeSinceStartup + 5f;
            while (G.SpeechPending && Time.realtimeSinceStartup < until) yield return null;
            Assert.AreEqual(2, G.SpeechesStarted, "word 2 was replaced; never more than one waiting");
            var last = three[2].Item;
            if (G.LastSpoken.ItemId == last.ItemId)
                Assert.AreSame(LearningSession.EligibleItems.Single(i => i.ItemId == last.ItemId).Audio, G.LastSpoken.Audio, "selected-language clip");
            Assert.AreEqual(150 + 165 + 180, G.Session.Score);
        }

        [UnityTest]
        public IEnumerator ReviewOpensThePreviewWithOnlyWeakWordsOfTheSamePack()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Short(2, 2), minActive: 2);
            var a = G.Active[0]; var b = G.Active[1];
            G.SelectTarget(a.Id);
            G.TypeDraft(a.Item.SourceText.Substring(0, 1) + "#");
            G.TypeDraft(a.Item.SourceText);
            G.ForceToLine(b);
            float until = Time.realtimeSinceStartup + 3f;
            while (!G.EndPanelVisible && Time.realtimeSinceStartup < until) yield return null;
            Assert.AreEqual(SessionState.Victory, G.Session.State);
            CollectionAssert.AreEquivalent(new[] { a.Item.ItemId, b.Item.ItemId }, G.WeakItemIds(), "typo + missed");
            var review = Object.FindObjectsByType<Button>().Single(x => x.name == "EndReview");
            Assert.IsTrue(review.interactable);
            var pack = LearningSession.Pack;
            review.onClick.Invoke();
            yield return null; yield return null;
            var preview = Object.FindFirstObjectByType<VocabularyPreviewController>();
            Assert.IsNotNull(preview, "review reuses the Vocabulary Preview, no Flashcard");
            Assert.IsTrue(preview.InReview);
            Assert.AreEqual(2, preview.Count);
            Assert.AreSame(pack, LearningSession.Pack);
            Assert.AreEqual(LearningMode.EnglishToVietnamese, LearningSession.Mode);
            Assert.AreEqual(GameEntry.SetupScene, Object.FindFirstObjectByType<SceneNav>().BackScene);
            Assert.IsNull(VocabularyPreviewController.ReviewItemIds, "filter consumed once");
        }

        /// <summary>
        /// Genuine lane deferral: slow meteors fill the five lanes, so spawns are postponed (Requeue) until a kill frees
        /// a lane. All 15 words must still appear exactly twice and never twice on screen (D-051).
        /// </summary>
        [UnityTest]
        public IEnumerator DeferredSpawnsKeepEveryWordAndBalance()
        {
            Random.InitState(1234);
            var cfg = Short(30, 10, max: 8);
            cfg.BaseFallSeconds = 400f; cfg.MinSpawnInterval = 0.05f;
            yield return StartGame(LearningMode.EnglishToVietnamese, cfg);
            int handled = 0;
            float until = Time.realtimeSinceStartup + 90f;
            while (G.Session.State == SessionState.Playing && Time.realtimeSinceStartup < until)
            {
                var onScreen = G.Active.Select(m => m.Item.ItemId).ToList();
                Assert.AreEqual(onScreen.Count, onScreen.Distinct().Count(), "no duplicate word on screen");
                bool blocked = G.PostponedSpawns > handled || (!G.Session.CanSpawn && G.Active.Count > 0);
                if (blocked && G.Active.Count > 0) { handled = G.PostponedSpawns; Kill(G.Active.OrderBy(m => m.Id).First()); }
                yield return null;
            }
            Assert.AreEqual(SessionState.Victory, G.Session.State);
            Assert.Greater(G.PostponedSpawns, 0, "lanes really ran out at least once");
            Assert.AreEqual(15, G.Session.Items.Count);
            Assert.IsTrue(G.Session.Items.Values.All(r => r.Correct == 2), "every word exactly twice despite deferrals");
            Assert.AreEqual((30, 30), (G.Session.Spawned, G.Deck.Issued), "counters count successful spawns only");
            StringAssert.StartsWith(PlayModeHistorySandbox.Dir, G.HistoryPath, "isolated temporary history");
            StringAssert.Contains("gặp <b>15 / 15</b> (100%)", G.ResultsText());
            Debug.Log($"G008_TEST deferred={G.PostponedSpawns}");
        }

        [UnityTest]
        public IEnumerator BreachFlashesRedAndShakesBrieflyThenRestores()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Short(30, 10));
            Vector3 home = Camera.main.transform.position;
            G.ForceToLine(G.Active[0]);
            yield return null; yield return null;
            Assert.Greater(G.DamageFlashAlpha, 0.05f, "red overlay visible");
            Assert.AreEqual(1, G.Session.Missed);
            yield return new WaitForSeconds(0.6f);
            Assert.AreEqual(0f, G.DamageFlashAlpha, 1e-4, "overlay faded out");
            Assert.AreEqual(home, Camera.main.transform.position, "camera back home after the shake");
        }

        [UnityTest]
        public IEnumerator CleanRunDisablesReview()
        {
            yield return StartGame(LearningMode.EnglishToVietnamese, Short(2, 2), minActive: 2);
            foreach (var m in G.Active.ToList()) Kill(m);
            float until = Time.realtimeSinceStartup + 3f;
            while (!G.EndPanelVisible && Time.realtimeSinceStartup < until) yield return null;
            Assert.AreEqual(0, G.WeakItemIds().Count);
            Assert.IsFalse(Object.FindObjectsByType<Button>().Single(x => x.name == "EndReview").interactable);
            StringAssert.Contains("100%", G.ResultsText());
        }
    }
}
