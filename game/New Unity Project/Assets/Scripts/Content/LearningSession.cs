using System.Collections.Generic;

namespace MP1.Content
{
    /// <summary>One vocabulary entry for the selected mode, ready for Flashcard (G-005) and Meteor Defense (G-006).</summary>
    public sealed class LearningItem
    {
        public string PackId, ItemId, Status;
        public long PackVersion;
        public string SourceText, Meaning;
        public MediaAsset Image, Audio;      // shared image; audio of the selected language only
        public bool GameplayEligible;        // false only for explicitly requested review previews
    }

    /// <summary>
    /// The single shared dataset across scenes: the pack loaded once by the library, the selected mode and the
    /// items derived from it. Features read <see cref="EligibleItems"/>; review previews never enter it.
    /// </summary>
    public static class LearningSession
    {
        public static PackReport Report { get; private set; }
        public static ContentPack Pack => Report?.Pack;
        public static LearningMode Mode { get; private set; }
        public static bool HasSelection => Report != null;
        public static List<LearningItem> EligibleItems { get; } = new List<LearningItem>();
        /// <summary>Non-gameplay items shown only by the owner verification preview when requested.</summary>
        public static List<LearningItem> PreviewOnlyItems { get; } = new List<LearningItem>();

        public static void Select(PackReport report, LearningMode mode)
        {
            Report = report;
            Mode = mode;
            EligibleItems.Clear();
            PreviewOnlyItems.Clear();
            if (report == null) return;
            foreach (var ir in report.Items)
            {
                var it = ir.Item;
                var li = new LearningItem
                {
                    PackId = report.Pack.PackId, PackVersion = report.Pack.PackVersion, ItemId = it.ItemId, Status = it.Status,
                    SourceText = it.SourceText(mode), Meaning = it.Vietnamese, Image = it.Image, Audio = it.AudioFor(mode),
                    GameplayEligible = ir.EligibleFor(mode)
                };
                (li.GameplayEligible ? EligibleItems : PreviewOnlyItems).Add(li);
            }
        }

        public static void Clear()
        {
            Report = null;
            EligibleItems.Clear();
            PreviewOnlyItems.Clear();
        }
    }
}
