using MP1.Content;

namespace MP1.Game
{
    /// <summary>Start gate for Meteor Defense (spec §2/§6: valid pack, chosen mode, at least ten usable items for the chosen configuration; no developer fixtures).</summary>
    public static class GameEntry
    {
        public const string SceneName = "MeteorDefense";
        /// <summary>G-007 configuration step between the library and the game.</summary>
        public const string SetupScene = "GameSetup";

        /// <summary>Null when a game can start with the current <see cref="LearningSession"/>; otherwise a reason for the player.</summary>
        public static string WhyCannotStart(GameConfig config)
        {
            if (!LearningSession.HasSelection) return "Chưa chọn Content Pack. Vào Thư viện từ vựng, chọn pack và chế độ học.";
            if (PackAudience.IsDeveloperFixture(LearningSession.Pack, LearningSession.Pack.ManifestPath))
                return "Pack kiểm thử dành cho nhà phát triển không dùng để chơi.";
            int n = LearningSession.EligibleItems.Count;
            if (n < config.MinEligibleItems)
                return $"Cần ít nhất {config.MinEligibleItems} từ dùng được cho {LearningModes.Label(LearningSession.Mode)}; pack này có {n}.";
            return GameCompatibility.Check(LearningSession.EligibleItems, config, LearningSession.Mode).BlockReason;
        }
    }

    /// <summary>Player-facing Vietnamese names and one-line explanations for the G-007 options.</summary>
    public static class GameLabels
    {
        public static string Name(Difficulty d) => d switch { Difficulty.Easy => "Dễ", Difficulty.Normal => "Thường", Difficulty.Hard => "Khó", _ => "Chuyên gia" };
        public static string Name(HintMode h) => h == HintMode.NoHint ? "Chỉ nghĩa" : "Nghĩa + chữ đầu";
        public static string Name(AnswerMode a) => a == AnswerMode.FullWord ? "Gõ cả từ" : "Điền chỗ trống";
        public static string Name(TargetingMode t) => t switch { TargetingMode.Hybrid => "Tự động + Tab", TargetingMode.Auto => "Tự động", _ => "Thủ công (Tab)" };

        public static string Explain(GameConfig c) =>
            $"<b>{Name(c.Difficulty)}</b>: {c.StartingHp} HP, thiên thạch rơi {c.BaseFallSeconds:0} s, tối đa {c.MaxConcurrent} cùng lúc, cứ {c.MinSpawnInterval:0} s một thiên thạch. 30 thiên thạch mỗi ván.\n" +
            $"<b>{Name(c.Hint)}</b>: " + (c.Hint == HintMode.NoHint ? "chỉ hiện nghĩa tiếng Việt." : "nghĩa tiếng Việt và chữ đầu của đáp án.") + "\n" +
            $"<b>{Name(c.Answer)}</b>: " + (c.Answer == AnswerMode.FullWord ? "gõ đầy đủ từ cần học." :
                $"ẩn khoảng {c.HiddenRatio:P0} chữ cái, chỉ gõ các chữ còn thiếu theo thứ tự trái → phải.") + "\n" +
            $"<b>{Name(c.Targeting)}</b>: " + (c.Targeting switch
            {
                TargetingMode.Hybrid => "tự nhắm thiên thạch gần phòng tuyến nhất; Tab để đổi.",
                TargetingMode.Auto => "luôn tự nhắm thiên thạch nguy hiểm nhất; giữ mục tiêu khi đang gõ; không dùng Tab.",
                _ => "không tự nhắm; nhấn Tab để chọn và đổi mục tiêu.",
            });

        public static string Summary(GameConfig c) => $"{Name(c.Difficulty)} · {Name(c.Hint)} · {Name(c.Answer)} · {Name(c.Targeting)}";

        public static string TargetHelp(TargetingMode t) => t switch
        {
            TargetingMode.Hybrid => "Tự nhắm · Tab đổi mục tiêu",
            TargetingMode.Auto => "Tự nhắm mục tiêu nguy hiểm nhất",
            _ => "Tab chọn / đổi mục tiêu",
        };
    }
}
