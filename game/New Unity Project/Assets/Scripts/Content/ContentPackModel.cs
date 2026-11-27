using System.Collections.Generic;

namespace MP1.Content
{
    /// <summary>Learning modes and their exact contract identifiers (content_pack_v1.md, private dual-language extension).</summary>
    public enum LearningMode { EnglishToVietnamese, JapaneseToVietnamese }

    public static class LearningModes
    {
        public const string EnglishId = "ENGLISH_TO_VIETNAMESE";
        public const string JapaneseId = "JAPANESE_TO_VIETNAMESE";
        public static readonly LearningMode[] All = { LearningMode.EnglishToVietnamese, LearningMode.JapaneseToVietnamese };

        public static string Id(LearningMode m) => m == LearningMode.EnglishToVietnamese ? EnglishId : JapaneseId;
        public static string Label(LearningMode m) => m == LearningMode.EnglishToVietnamese ? "English → Tiếng Việt" : "日本語 → Tiếng Việt";

        /// <summary>Canonical field mapping the contract requires: (source text, translation, audio asset field).</summary>
        public static (string source, string translation, string audio) Fields(LearningMode m) =>
            m == LearningMode.EnglishToVietnamese ? ("english", "vietnamese", "audio_english") : ("japanese", "vietnamese", "audio_japanese");
    }

    public sealed class MediaAsset
    {
        public string Path, MimeType, Sha256;
        public long SizeBytes;
    }

    public sealed class QualityEvidence
    {
        public string Dimension, Reviewer, AssetSha256;
    }

    /// <summary>One vocabulary item exactly as the manifest states it. Status is never changed by the runtime.</summary>
    public sealed class PackItem
    {
        public string ItemId, English, Japanese, Vietnamese, TargetSense;
        public long SourceRow;
        public string Status, ReviewStatus, TechnicalIntegrity, DistributionStatus;
        public string SemanticCorrectness, ImageRelevance, ImageVisualQuality, AudioPronunciation;
        public List<QualityEvidence> Evidence = new List<QualityEvidence>();
        public MediaAsset Image, Audio, AudioEnglish, AudioJapanese;
        public bool HasDualAudioFields;   // item carries audio_english / audio_japanese keys
        public int ErrorCount;

        /// <summary>Legacy <c>audio</c> is an exact alias of <c>audio_japanese</c>.</summary>
        public MediaAsset JapaneseAudio => AudioJapanese ?? Audio;
        public MediaAsset AudioFor(LearningMode m) => m == LearningMode.EnglishToVietnamese ? AudioEnglish : JapaneseAudio;
        public string SourceText(LearningMode m) => m == LearningMode.EnglishToVietnamese ? English : Japanese;
    }

    public sealed class ContentPack
    {
        public long ContractVersion, PackVersion;
        public string PackId, ImportId;
        public bool TestOnly;
        public bool HasLanguageModes;     // pack.extensions.language_modes present
        public List<PackItem> Items = new List<PackItem>();
        public string ManifestPath, RootDir;

        /// <summary>Dual-language packs require both audio assets for needs_review/ready.</summary>
        public bool IsDualAudio
        {
            get
            {
                if (HasLanguageModes) return true;
                foreach (var it in Items) if (it.HasDualAudioFields) return true;
                return false;
            }
        }
    }

    public enum PackLoadState { Valid, MissingManifest, Malformed, UnsupportedVersion, Invalid }

    public sealed class PackLoadResult
    {
        public PackLoadState State;
        public ContentPack Pack;
        public List<string> Errors = new List<string>();
        public string ManifestPath;
        public bool Ok => State == PackLoadState.Valid;
    }
}
