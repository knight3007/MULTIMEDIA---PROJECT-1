using System.Collections.Generic;

namespace MP1.Content
{
    public sealed class ItemReport
    {
        public PackItem Item;
        public bool ReadyInvariant;          // status ready AND the contract's ready prerequisites hold
        public bool EligibleEnglish, EligibleJapanese;
        public bool MediaProblem;            // a declared file is missing/corrupt
        public List<string> Reasons = new List<string>();
        public bool EligibleFor(LearningMode m) => m == LearningMode.EnglishToVietnamese ? EligibleEnglish : EligibleJapanese;
    }

    public enum PackSummary { Valid, MissingMedia, NoEligibleItems }

    public sealed class PackReport
    {
        public ContentPack Pack;
        public List<ItemReport> Items = new List<ItemReport>();
        public int Total, Pending, Processing, NeedsReview, Ready, Failed, ReadyUnplayable, EligibleEnglish, EligibleJapanese, MissingMediaFiles;
        public double EvaluateMs;
        public int EligibleFor(LearningMode m) => m == LearningMode.EnglishToVietnamese ? EligibleEnglish : EligibleJapanese;

        public PackSummary Summary =>
            EligibleEnglish + EligibleJapanese > 0 ? (ReadyUnplayable > 0 ? PackSummary.MissingMedia : PackSummary.Valid)
            : ReadyUnplayable > 0 || MissingMediaFiles > 0 ? PackSummary.MissingMedia : PackSummary.NoEligibleItems;
    }

    /// <summary>
    /// Gameplay eligibility from the contract: the runtime uses <c>ready</c> items only, and only when the ready
    /// prerequisites still hold (both assets, technical pass, four quality passes with matching evidence, review
    /// approved with content_review evidence, no errors) and the files verify by size, type and SHA-256.
    /// Statuses are reported as stored; nothing is promoted or rewritten.
    /// </summary>
    public static class PackEligibility
    {
        public static PackReport Evaluate(ContentPack pack)
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var r = new PackReport { Pack = pack, Total = pack.Items.Count };
            bool dual = pack.IsDualAudio;
            foreach (var it in pack.Items)
            {
                switch (it.Status)
                {
                    case "pending": r.Pending++; break;
                    case "processing": r.Processing++; break;
                    case "needs_review": r.NeedsReview++; break;
                    case "ready": r.Ready++; break;
                    case "failed": r.Failed++; break;
                }
                var ir = new ItemReport { Item = it };
                r.Items.Add(ir);
                r.MissingMediaFiles += CountMissing(pack, it);
                if (it.Status != "ready") { ir.Reasons.Add($"status {it.Status}"); continue; }

                ir.ReadyInvariant = CheckReadyInvariant(it, dual, ir.Reasons);
                if (!ir.ReadyInvariant) { r.ReadyUnplayable++; continue; }

                bool imageOk = Verify(pack, it.Image, "image", ir);
                foreach (var mode in LearningModes.All)
                {
                    var audio = it.AudioFor(mode);
                    bool textOk = !string.IsNullOrWhiteSpace(it.SourceText(mode)) && !string.IsNullOrWhiteSpace(it.Vietnamese);
                    bool audioOk = audio != null && Verify(pack, audio, LearningModes.Fields(mode).audio, ir);
                    if (audio == null) ir.Reasons.Add($"{LearningModes.Id(mode)}: thiếu {LearningModes.Fields(mode).audio}");
                    bool ok = imageOk && audioOk && textOk;
                    if (mode == LearningMode.EnglishToVietnamese) ir.EligibleEnglish = ok; else ir.EligibleJapanese = ok;
                }
                if (ir.MediaProblem) r.ReadyUnplayable++;
                if (ir.EligibleEnglish) r.EligibleEnglish++;
                if (ir.EligibleJapanese) r.EligibleJapanese++;
            }
            r.EvaluateMs = sw.Elapsed.TotalMilliseconds;
            return r;
        }

        static bool Verify(ContentPack pack, MediaAsset a, string field, ItemReport ir)
        {
            string full = MediaSafety.Resolve(pack.RootDir, a, out string err);
            if (full != null) err = MediaSafety.VerifyBytes(full, a);
            if (err == null) return true;
            ir.MediaProblem = true;
            ir.Reasons.Add($"{field}: {err}");
            return false;
        }

        static int CountMissing(ContentPack pack, PackItem it)
        {
            int n = 0;
            foreach (var a in new[] { it.Image, it.Audio, it.AudioEnglish, it.AudioJapanese })
            {
                if (a == null || a == it.Audio && it.AudioJapanese != null) continue; // alias counted once
                string full = MediaSafety.Resolve(pack.RootDir, a, out _);
                if (full == null || !System.IO.File.Exists(full)) n++;
            }
            return n;
        }

        /// <summary>Contract transition needs_review → ready prerequisites, re-checked because the runtime must not trust a bad snapshot.</summary>
        public static bool CheckReadyInvariant(PackItem it, bool dualAudio, List<string> reasons)
        {
            int before = reasons.Count;
            if (it.Image == null) reasons.Add("ready nhưng thiếu image");
            if (dualAudio)
            {
                if (it.AudioEnglish == null) reasons.Add("ready nhưng thiếu audio_english");
                if (it.JapaneseAudio == null) reasons.Add("ready nhưng thiếu audio_japanese");
            }
            else if (it.Audio == null) reasons.Add("ready nhưng thiếu audio");
            if (it.TechnicalIntegrity != "pass") reasons.Add("technical_integrity chưa pass");
            if (it.ReviewStatus != "approved") reasons.Add("review_status chưa approved");
            if (it.ErrorCount != 0) reasons.Add("ready nhưng còn errors");
            if (it.SemanticCorrectness != "pass" || it.ImageRelevance != "pass" || it.ImageVisualQuality != "pass" || it.AudioPronunciation != "pass")
                reasons.Add("chưa đủ 4 tiêu chí chất lượng pass");
            if (!HasEvidence(it, "semantic_correctness", null)) reasons.Add("thiếu evidence semantic_correctness");
            if (!HasEvidence(it, "image_relevance", it.Image?.Sha256)) reasons.Add("thiếu evidence image_relevance khớp ảnh");
            if (!HasEvidence(it, "image_visual_quality", it.Image?.Sha256)) reasons.Add("thiếu evidence image_visual_quality khớp ảnh");
            if (!HasAudioEvidence(it)) reasons.Add("thiếu evidence audio_pronunciation khớp âm thanh");
            if (!HasEvidence(it, "content_review", null, anyHash: true)) reasons.Add("approved nhưng thiếu evidence content_review");
            return reasons.Count == before;
        }

        static bool HasEvidence(PackItem it, string dim, string sha, bool anyHash = false)
        {
            foreach (var e in it.Evidence)
                if (e.Dimension == dim && (anyHash || e.AssetSha256 == sha)) return true;
            return false;
        }

        static bool HasAudioEvidence(PackItem it)
        {
            foreach (var e in it.Evidence)
                if (e.Dimension == "audio_pronunciation" && e.AssetSha256 != null &&
                    (e.AssetSha256 == it.JapaneseAudio?.Sha256 || e.AssetSha256 == it.AudioEnglish?.Sha256)) return true;
            return false;
        }
    }
}
