using System.Collections;
using System.Linq;
using MP1.Background;
using MP1.Content;
using MP1.Library;
using NUnit.Framework;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace MP1.Tests
{
    /// <summary>G-004 UI flow against the real repository packs and the ContentPackFixtures error states.</summary>
    public class LibraryFlowTests
    {
        static Button Btn(string name) => Object.FindObjectsByType<Button>().Single(b => b.name == name);
        static string Txt(string name) => Object.FindObjectsByType<TMP_Text>().Single(t => t.name == name).text;

        static IEnumerator OpenLibrary()
        {
            yield return SceneManager.LoadSceneAsync("MainMenu");
            yield return null;
            Btn("Library").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("VocabularyLibrary", SceneManager.GetActiveScene().name);
            float until = Time.realtimeSinceStartup + 60f;
            while (VocabularyLibraryController.Cache == null && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsNotNull(VocabularyLibraryController.Cache, "scan finished");
            yield return null;
        }

        static VocabularyLibraryController.Entry Find(string pathPart) =>
            VocabularyLibraryController.Cache.FirstOrDefault(e => e.ManifestPath.Replace('\\', '/').Contains(pathPart));

        [UnityTest]
        public IEnumerator LibraryListsRealPacksWithActualCounts()
        {
            yield return OpenLibrary();
            Assert.Greater(Object.FindObjectsByType<Button>().Count(b => b.name == "PackRow"), 0, "rows shown");
            var v46 = Find("EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v46/content_pack.json");
            if (v46 == null) Assert.Ignore("repository packs not reachable");
            Object.FindFirstObjectByType<VocabularyLibraryController>().Select(v46);
            yield return null;
            StringAssert.Contains("Tổng mục: <b>15</b>", Txt("DetailCounts"));
            StringAssert.Contains("needs_review: <b>15</b>", Txt("DetailCounts"));
            Assert.IsFalse(Btn("ModeEnglish").interactable, "no ready items, so no gameplay mode");
            Assert.IsFalse(Btn("ModeJapanese").interactable);
            Assert.IsTrue(Btn("ReviewPreview").interactable);
            Assert.GreaterOrEqual(Object.FindFirstObjectByType<GalaxyBackground>().StarCount, 480, "approved R1 background kept");
        }

        [UnityTest]
        public IEnumerator ErrorStatesAreReportedNotHidden()
        {
            yield return OpenLibrary();
            var lib = Object.FindFirstObjectByType<VocabularyLibraryController>();
            var cases = new (string folder, PackLoadState state, string label)[]
            {
                ("ContentPackFixtures/invalid_json/", PackLoadState.Malformed, "lỗi JSON"),
                ("ContentPackFixtures/unsupported_v2/", PackLoadState.UnsupportedVersion, "chưa hỗ trợ"),
                ("ContentPackFixtures/empty_items/", PackLoadState.Invalid, "không hợp lệ"),
            };
            foreach (var c in cases)
            {
                var e = Find(c.folder);
                Assert.IsNotNull(e, c.folder);
                Assert.AreEqual(c.state, e.Load.State);
                lib.Select(e);
                yield return null;
                StringAssert.Contains(c.label, Txt("DetailStatus"));
                Assert.IsFalse(Btn("ModeEnglish").interactable || Btn("ModeJapanese").interactable || Btn("ReviewPreview").interactable);
            }
            var missing = Find("ContentPackFixtures/missing_media/");
            Assert.AreEqual(PackSummary.MissingMedia, missing.Report.Summary);
            Assert.AreEqual(1, missing.Report.ReadyUnplayable);
        }

        [UnityTest]
        public IEnumerator JapaneseModePreviewLoadsImageAndPlaysJapaneseAudioThenGoesBack()
        {
            yield return OpenLibrary();
            var fixture = Find("tests/fixtures/b001/content_pack_states.json");
            if (fixture == null) Assert.Ignore("repository fixture not reachable");
            Object.FindFirstObjectByType<VocabularyLibraryController>().Select(fixture);
            yield return null;
            Assert.IsFalse(Btn("ModeEnglish").interactable, "legacy fixture: no English audio");
            Assert.IsTrue(Btn("ModeJapanese").interactable);
            Btn("ModeJapanese").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("VocabularyPreview", SceneManager.GetActiveScene().name);
            var preview = Object.FindFirstObjectByType<VocabularyPreviewController>();
            Assert.AreEqual(1, preview.Count);
            Assert.AreEqual("りんご", preview.Current.SourceText);
            Assert.AreEqual("quả táo", preview.Current.Meaning);
            Assert.IsTrue(preview.Current.GameplayEligible);
            Assert.AreEqual(LearningSession.Pack.Items.First(i => i.Status == "ready").JapaneseAudio, preview.Current.Audio, "Japanese audio selected");
            float until = Time.realtimeSinceStartup + 5f;
            while (!preview.MediaStatusText.StartsWith("Ảnh") && Time.realtimeSinceStartup < until) yield return null;
            StringAssert.StartsWith("Ảnh", preview.MediaStatusText, "image loaded");
            preview.Play();
            until = Time.realtimeSinceStartup + 5f;
            while (!preview.Source.isPlaying && Time.realtimeSinceStartup < until) yield return null;
            Assert.IsTrue(preview.Source.isPlaying, "audio playing");
            Assert.AreEqual(1, LearningSession.EligibleItems.Count, "shared dataset holds only the eligible item");
            Btn("BackButton").onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("VocabularyLibrary", SceneManager.GetActiveScene().name, "Back follows the flow: preview -> library");
        }

        [UnityTest]
        public IEnumerator BrokenAndUnreadyPacksAreHiddenByDefaultNotDeleted()
        {
            VocabularyLibraryController.ShowAll = false;
            yield return OpenLibrary();
            var lib = Object.FindFirstObjectByType<VocabularyLibraryController>();
            lib.Select(null);
            Btn("BackButton").onClick.Invoke(); // re-enter so the list is drawn without a hidden selection
            yield return null; yield return null;
            Btn("Library").onClick.Invoke();
            yield return null; yield return null;
            int usable = VocabularyLibraryController.Cache.Count(VocabularyLibraryController.Usable);
            int shown = Object.FindObjectsByType<Button>().Count(b => b.name == "PackRow");
            Assert.AreEqual(usable, shown, "only usable packs listed by default");
            Assert.Less(shown, VocabularyLibraryController.Cache.Count, "some packs hidden");
            Btn("ShowAllPacks").onClick.Invoke();
            yield return null;
            Assert.AreEqual(VocabularyLibraryController.Cache.Count, Object.FindObjectsByType<Button>().Count(b => b.name == "PackRow"), "toggle shows every pack");
            Btn("ShowAllPacks").onClick.Invoke();
            yield return null;
            VocabularyLibraryController.ShowAll = false;
        }

        /// <summary>G-004-R1: the owner-reviewed v47 pack is fully playable; every image and both audio tracks decode.</summary>
        [UnityTest]
        public IEnumerator ReviewedV47PackIsFullyEligibleAndAllMediaDecodes()
        {
            yield return OpenLibrary();
            var v47 = Find("EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v47_reviewed/content_pack.json");
            if (v47 == null) Assert.Ignore("reviewed pack not present");
            var r = v47.Report;
            Assert.AreEqual((15, 15, 15, 15, 0), (r.Total, r.Ready, r.EligibleEnglish, r.EligibleJapanese, r.ReadyUnplayable));
            int images = 0, clips = 0;
            foreach (var ir in r.Items)
            {
                var it = ir.Item;
                yield return PackMediaLoader.LoadTexture(r.Pack, it.Image, (tex, err, ms) => { Assert.IsNotNull(tex, err); images++; Object.Destroy(tex); });
                foreach (var mode in LearningModes.All)
                    yield return PackMediaLoader.LoadClip(r.Pack, it.AudioFor(mode), (clip, err, ms) => { Assert.IsNotNull(clip, err); Assert.Greater(clip.length, 0.2f); clips++; Object.Destroy(clip); });
            }
            Assert.AreEqual((15, 30), (images, clips));
            LearningSession.Select(r, LearningMode.JapaneseToVietnamese);
            Assert.AreEqual(15, LearningSession.EligibleItems.Count);
            Assert.AreEqual(0, LearningSession.PreviewOnlyItems.Count);
            LearningSession.Select(r, LearningMode.EnglishToVietnamese);
            Assert.IsTrue(LearningSession.EligibleItems.All(i => i.Audio == r.Pack.Items.First(p => p.ItemId == i.ItemId).AudioEnglish), "English audio only in EN-VI");
        }

        [UnityTest]
        public IEnumerator ReviewPreviewMarksNonReadyItemsAndSwitchesLanguage()
        {
            yield return OpenLibrary();
            var v46 = Find("EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v46/content_pack.json");
            if (v46 == null) Assert.Ignore("repository packs not reachable");
            Object.FindFirstObjectByType<VocabularyLibraryController>().Select(v46);
            yield return null;
            Btn("ReviewPreview").onClick.Invoke();
            yield return null; yield return null;
            var preview = Object.FindFirstObjectByType<VocabularyPreviewController>();
            Assert.AreEqual(15, preview.Count);
            Assert.IsFalse(preview.Current.GameplayEligible);
            StringAssert.Contains("CHỈ XEM ĐỂ KIỂM TRA", Txt("ItemTag"));
            Assert.AreEqual(0, LearningSession.EligibleItems.Count, "review items never enter the gameplay dataset");
            string english = preview.Current.SourceText;
            preview.SwitchMode(Content.LearningMode.JapaneseToVietnamese);
            yield return null;
            Assert.AreNotEqual(english, preview.Current.SourceText, "Japanese text after switching");
            Assert.AreEqual(LearningSession.Pack.Items[0].JapaneseAudio, preview.Current.Audio);
            preview.Show(1);
            Assert.AreEqual(1, preview.Index);
        }
    }
}
