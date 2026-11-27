using System.Collections.Generic;
using System.Diagnostics;
using System.IO;
using System.Linq;
using MP1.Content;
using MP1.Core;
using NUnit.Framework;
using UnityEngine;

namespace MP1.Tests
{
    public class StrictJsonTests
    {
        [Test]
        public void ParsesUnicodeIntegersAndKeepsNullDistinctFromMissing()
        {
            var o = (Dictionary<string, object>)StrictJson.Parse("{\"a\":\"信号機 · Đèn \\u0110\",\"n\":9007199254740991,\"x\":null,\"f\":1.5}");
            Assert.AreEqual("信号機 · Đèn Đ", o["a"]);
            Assert.AreEqual(9007199254740991L, o["n"]);
            Assert.IsTrue(o.ContainsKey("x") && o["x"] == null);
            Assert.IsFalse(o.ContainsKey("y"));
            Assert.AreEqual(1.5, o["f"]);
        }

        [TestCase("{\"a\":1,\"a\":2}")]
        [TestCase("{\"a\":1} x")]
        [TestCase("{\"a\":}")]
        [TestCase("[1,2")]
        [TestCase("{'a':1}")]
        [TestCase("")]
        public void RejectsInvalidJson(string json)
        {
            Assert.Throws<StrictJson.JsonException>(() => StrictJson.Parse(json));
        }
    }

    public class ContentPackReaderTests
    {
        [Test]
        public void ValidPackKeepsIdentityAndUnicode()
        {
            using (var b = new TestPackBuilder())
            {
                b.AddItem("ready", "Traffic light", "信号機", "Đèn giao thông");
                b.AddItem("needs_review", "Eat", "食べる", "Ăn");
                var r = ContentPackReader.Load(b.Write());
                Assert.AreEqual(PackLoadState.Valid, r.State, string.Join("\n", r.Errors));
                Assert.AreEqual("pack-11111111-1111-4111-8111-111111111111", r.Pack.PackId);
                Assert.AreEqual(3, r.Pack.PackVersion);
                Assert.AreEqual("item-00000001-aaaa-4aaa-8aaa-000000000001", r.Pack.Items[0].ItemId);
                Assert.AreEqual("信号機", r.Pack.Items[0].Japanese);
                Assert.AreEqual("Đèn giao thông", r.Pack.Items[0].Vietnamese);
                Assert.AreEqual("needs_review", r.Pack.Items[1].Status, "status kept as stored");
                Assert.IsTrue(r.Pack.IsDualAudio);
            }
        }

        [Test]
        public void MissingManifestMalformedAndUnsupportedAreDistinct()
        {
            Assert.AreEqual(PackLoadState.MissingManifest, ContentPackReader.Load(Path.Combine(Path.GetTempPath(), "nope", "content_pack.json")).State);
            Assert.AreEqual(PackLoadState.Malformed, ContentPackReader.Parse("{\"contract_version\":1,", "x").State);
            Assert.AreEqual(PackLoadState.Malformed, ContentPackReader.Parse("[]", "x").State);
            Assert.AreEqual(PackLoadState.UnsupportedVersion, ContentPackReader.Parse("{\"contract_version\":2,\"items\":[]}", "x").State);
            Assert.AreEqual(PackLoadState.Invalid, ContentPackReader.Parse("{\"items\":[]}", "x").State, "no version at all");
        }

        static PackLoadState StateAfter(System.Action<TestPackBuilder, Dictionary<string, object>> mutate)
        {
            using (var b = new TestPackBuilder())
            {
                var item = b.AddItem("ready", "Apple", "りんご", "Quả táo");
                mutate(b, item);
                return ContentPackReader.Load(b.Write()).State;
            }
        }

        [Test]
        public void StructuralViolationsRejectThePack()
        {
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => i.Remove("vietnamese")), "missing required field");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => i["target_sense"] = 5L), "wrong type");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => i["colour"] = "x"), "unknown core field");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => b.Pack["typo"] = 1L), "unknown pack field");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => i["status"] = "done"), "unknown status");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => i["item_id"] = "item-1"), "bad item id");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => b.Items.Add(i)), "duplicate item id");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => b.Items.Clear()), "empty pack");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => b.Pack.Remove("pack_id")), "missing pack id");
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => i["audio"] = b.Asset(TestPackBuilder.Mp3, "mp3", "audio/mpeg")), "audio must alias audio_japanese");
            Assert.AreEqual(PackLoadState.Valid, StateAfter((b, i) => i["extensions"] = new Dictionary<string, object> { { "note", "x" } }), "item extensions allowed");
        }

        [TestCase("../outside.png")]
        [TestCase("assets/../../outside.png")]
        [TestCase("C:/Windows/win.png")]
        [TestCase("/etc/passwd.png")]
        [TestCase("\\\\server\\share\\a.png")]
        [TestCase("assets\\aa.png")]
        [TestCase("file:///c:/a.png")]
        [TestCase("https://example.com/a.png")]
        [TestCase("assets/a.png?x=1")]
        [TestCase("assets/%2e%2e/a.png")]
        public void UnsafeMediaPathsRejectThePack(string path)
        {
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => ((Dictionary<string, object>)i["image"])["path"] = path));
        }

        [Test]
        public void ExtensionMustMatchMimeAndHash()
        {
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => ((Dictionary<string, object>)i["image"])["mime_type"] = "image/jpeg"));
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => ((Dictionary<string, object>)i["image"])["sha256"] = new string('a', 64)));
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) => ((Dictionary<string, object>)i["image"])["mime_type"] = "image/gif"));
        }

        [Test]
        public void LanguageModesMustMatchContractMapping()
        {
            Assert.AreEqual(PackLoadState.Invalid, StateAfter((b, i) =>
                ((Dictionary<string, object>)((Dictionary<string, object>)((Dictionary<string, object>)b.Pack["extensions"])["language_modes"])["ENGLISH_TO_VIETNAMESE"])["audio"] = "audio_japanese"));
        }
    }

    public class PackEligibilityTests
    {
        [Test]
        public void OnlyReadyItemsWithVerifiedMediaAreEligibleAndCountsStayDistinct()
        {
            using (var b = new TestPackBuilder())
            {
                b.AddItem("ready", "Apple", "りんご", "Quả táo");
                b.AddItem("needs_review", "Eat", "食べる", "Ăn");
                b.AddItem("failed", "Car", "車", "Xe hơi");
                b.AddItem("pending", "Dog", "犬", "Con chó");
                b.AddItem("processing", "Cat", "猫", "Con mèo");
                var rep = PackEligibility.Evaluate(ContentPackReader.Load(b.Write()).Pack);
                Assert.AreEqual(5, rep.Total);
                Assert.AreEqual((1, 1, 1, 1, 1), (rep.Ready, rep.NeedsReview, rep.Failed, rep.Pending, rep.Processing));
                Assert.AreEqual(1, rep.EligibleEnglish);
                Assert.AreEqual(1, rep.EligibleJapanese);
                Assert.AreEqual(PackSummary.Valid, rep.Summary);
                Assert.IsFalse(rep.Items[1].EligibleEnglish || rep.Items[1].EligibleJapanese, "needs_review never eligible");
            }
        }

        [Test]
        public void MissingOrCorruptMediaDisablesTheReadyItem()
        {
            using (var b = new TestPackBuilder())
            {
                var gone = b.AddItem("ready", "Apple", "りんご", "Quả táo");
                var bad = b.AddItem("ready", "Eat", "食べる", "Ăn");
                File.Delete(Path.Combine(b.Root, (string)((Dictionary<string, object>)gone["image"])["path"]));
                File.WriteAllBytes(Path.Combine(b.Root, (string)((Dictionary<string, object>)bad["audio_english"])["path"]), new byte[TestPackBuilder.Mp3.Length + 1]);
                var rep = PackEligibility.Evaluate(ContentPackReader.Load(b.Write()).Pack);
                Assert.AreEqual(0, rep.EligibleEnglish);
                Assert.AreEqual(1, rep.EligibleJapanese, "corrupt EN audio does not block JA");
                Assert.AreEqual(2, rep.ReadyUnplayable);
                Assert.AreEqual(1, rep.MissingMediaFiles);
                Assert.AreEqual(PackSummary.MissingMedia, rep.Summary);
                StringAssert.Contains("thiếu tệp", string.Join(";", rep.Items[0].Reasons));
            }
        }

        [Test]
        public void ReadyWithBrokenPrerequisitesIsNotTrusted()
        {
            using (var b = new TestPackBuilder())
            {
                var item = b.AddItem("ready", "Apple", "りんご", "Quả táo");
                item["review_status"] = "pending";
                var rep = PackEligibility.Evaluate(ContentPackReader.Load(b.Write()).Pack);
                Assert.AreEqual(1, rep.Ready, "reported as stored");
                Assert.AreEqual(0, rep.EligibleEnglish + rep.EligibleJapanese);
                Assert.AreEqual(1, rep.ReadyUnplayable);
            }
        }

        [Test]
        public void LegacySingleAudioPackSupportsJapaneseOnly()
        {
            using (var b = new TestPackBuilder(dual: false))
            {
                b.AddItem("ready", "Apple", "りんご", "Quả táo", dual: false);
                var rep = PackEligibility.Evaluate(ContentPackReader.Load(b.Write()).Pack);
                Assert.AreEqual(0, rep.EligibleEnglish, "no audio_english: never substitute Japanese audio");
                Assert.AreEqual(1, rep.EligibleJapanese);
            }
        }

        [Test]
        public void PackWithNoReadyItemsHasZeroEligible()
        {
            using (var b = new TestPackBuilder())
            {
                b.AddItem("needs_review", "Apple", "りんご", "Quả táo");
                var rep = PackEligibility.Evaluate(ContentPackReader.Load(b.Write()).Pack);
                Assert.AreEqual(PackSummary.NoEligibleItems, rep.Summary);
            }
        }
    }

    public class MediaSafetyTests
    {
        [Test]
        public void ResolvesInsidePackWithSpacesAndUnicodeInTheRoot()
        {
            using (var b = new TestPackBuilder("Thư mục có dấu 日本 pack"))
            {
                var item = b.AddItem("ready", "Apple", "りんご", "Quả táo");
                var pack = ContentPackReader.Load(b.Write()).Pack;
                string full = MediaSafety.Resolve(pack.RootDir, pack.Items[0].Image, out string err);
                Assert.IsNull(err);
                Assert.IsTrue(File.Exists(full));
                Assert.IsNull(MediaSafety.VerifyBytes(full, pack.Items[0].Image));
                Assert.AreEqual(1, PackEligibility.Evaluate(pack).EligibleJapanese);
            }
        }

        [Test]
        public void SelectsLanguageSpecificAudio()
        {
            using (var b = new TestPackBuilder())
            {
                var item = b.AddItem("ready", "Apple", "りんご", "Quả táo");
                var it = ContentPackReader.Load(b.Write()).Pack.Items[0];
                Assert.AreEqual(((Dictionary<string, object>)item["audio_english"])["sha256"], it.AudioFor(Content.LearningMode.EnglishToVietnamese).Sha256);
                Assert.AreEqual(((Dictionary<string, object>)item["audio_japanese"])["sha256"], it.AudioFor(Content.LearningMode.JapaneseToVietnamese).Sha256);
                Assert.AreNotEqual(it.AudioEnglish.Sha256, it.JapaneseAudio.Sha256);
            }
        }

        [Test]
        public void WrongMagicBytesAreRejected()
        {
            var a = new MediaAsset { MimeType = "image/png" };
            Assert.IsFalse(MediaSafety.MagicMatches("image/png", TestPackBuilder.Mp3, TestPackBuilder.Mp3.Length));
            Assert.IsTrue(MediaSafety.MagicMatches("audio/wav", TestPackBuilder.Wav, TestPackBuilder.Wav.Length));
            Assert.IsTrue(MediaSafety.MagicMatches("audio/mpeg", TestPackBuilder.Mp3, TestPackBuilder.Mp3.Length));
        }

        [Test]
        public void JunctionedAssetsFolderIsRejected()
        {
            if (Application.platform != RuntimePlatform.WindowsEditor) Assert.Ignore("Windows junction test");
            using (var outside = new TestPackBuilder())
            using (var b = new TestPackBuilder())
            {
                var item = b.AddItem("ready", "Apple", "りんご", "Quả táo");
                string manifest = b.Write();
                // Move the real assets elsewhere and replace the folder with a junction pointing there.
                string target = Path.Combine(outside.Root, "real_assets");
                Directory.Move(Path.Combine(b.Root, "assets"), target);
                var p = Process.Start(new ProcessStartInfo("cmd.exe", $"/c mklink /J \"{Path.Combine(b.Root, "assets")}\" \"{target}\"") { CreateNoWindow = true, UseShellExecute = false });
                p.WaitForExit();
                if (!Directory.Exists(Path.Combine(b.Root, "assets"))) Assert.Ignore("mklink /J unavailable");
                var pack = ContentPackReader.Load(manifest).Pack;
                Assert.IsNull(MediaSafety.Resolve(pack.RootDir, pack.Items[0].Image, out string err));
                StringAssert.Contains("symlink", err);
                Assert.AreEqual(0, PackEligibility.Evaluate(pack).EligibleJapanese);
                Directory.Delete(Path.Combine(b.Root, "assets")); // remove the junction itself, not the target
            }
        }
    }

    public class DiscoveryAndSessionTests
    {
        [Test]
        public void FindsManifestsAndUserPaths()
        {
            using (var b = new TestPackBuilder())
            {
                b.AddItem("ready", "Apple", "りんご", "Quả táo");
                string m = b.Write("content_pack_states.json");
                var found = PackDiscovery.Find(new[] { Path.GetDirectoryName(b.Root) });
                Assert.Contains(Path.GetFullPath(m), found);
                Assert.AreEqual(Path.GetFullPath(m), PackDiscovery.ResolveUserPath(b.Root), "folder with one manifest");
                Assert.AreEqual(Path.GetFullPath(m), PackDiscovery.ResolveUserPath("\"" + m + "\""), "quoted file path");
                Assert.IsNull(PackDiscovery.ResolveUserPath(Path.Combine(b.Root, "missing")));
                Assert.IsFalse(PackDiscovery.IsManifestName("content.json"));
            }
        }

        [Test]
        public void SessionSeparatesGameplayItemsFromPreviews()
        {
            using (var b = new TestPackBuilder())
            {
                b.AddItem("ready", "Apple", "りんご", "Quả táo");
                b.AddItem("needs_review", "Eat", "食べる", "Ăn");
                var rep = PackEligibility.Evaluate(ContentPackReader.Load(b.Write()).Pack);
                LearningSession.Select(rep, Content.LearningMode.JapaneseToVietnamese);
                Assert.AreEqual(1, LearningSession.EligibleItems.Count);
                Assert.AreEqual(1, LearningSession.PreviewOnlyItems.Count);
                var li = LearningSession.EligibleItems[0];
                Assert.AreEqual(("りんご", "Quả táo", "item-00000001-aaaa-4aaa-8aaa-000000000001"), (li.SourceText, li.Meaning, li.ItemId));
                Assert.AreEqual(rep.Pack.Items[0].JapaneseAudio, li.Audio);
                Assert.IsFalse(LearningSession.PreviewOnlyItems[0].GameplayEligible);
                LearningSession.Clear();
            }
        }
    }

    /// <summary>Read-only checks against real packs in the repository (never modified).</summary>
    public class RealPackTests
    {
        static string Repo => MediaPaths.FindUpwards(Application.dataPath, Path.Combine("tests", "fixtures", "b001", "content_pack_states.json"), File.Exists) is string p
            ? Path.GetFullPath(Path.Combine(Path.GetDirectoryName(p), "..", "..", "..")) : null;

        [Test]
        public void ContractFixtureHasOneJapaneseEligibleItem()
        {
            if (Repo == null) Assert.Ignore("repo fixtures not found");
            var r = ContentPackReader.Load(Path.Combine(Repo, "tests", "fixtures", "b001", "content_pack_states.json"));
            Assert.AreEqual(PackLoadState.Valid, r.State, string.Join("\n", r.Errors));
            var rep = PackEligibility.Evaluate(r.Pack);
            Assert.AreEqual((5, 1, 1, 1, 1, 1), (rep.Total, rep.Ready, rep.NeedsReview, rep.Failed, rep.Pending, rep.Processing));
            Assert.AreEqual(0, rep.EligibleEnglish, "legacy fixture has no audio_english");
            Assert.AreEqual(1, rep.EligibleJapanese, string.Join("; ", rep.Items.First(i => i.Item.Status == "ready").Reasons));
        }

        [Test]
        public void ExcelSmokePackV46LoadsWithNoGameplayItems()
        {
            if (Repo == null) Assert.Ignore("repo fixtures not found");
            var r = ContentPackReader.Load(Path.Combine(Repo, Media.MediaProbe.PackRelative));
            Assert.AreEqual(PackLoadState.Valid, r.State, string.Join("\n", r.Errors));
            var rep = PackEligibility.Evaluate(r.Pack);
            Assert.AreEqual((15, 15, 0), (rep.Total, rep.NeedsReview, rep.EligibleEnglish + rep.EligibleJapanese));
            Assert.AreEqual(0, rep.MissingMediaFiles);
        }
    }
}
