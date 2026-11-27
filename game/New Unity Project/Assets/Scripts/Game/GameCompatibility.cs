using System.Collections.Generic;
using MP1.Content;

namespace MP1.Game
{
    /// <summary>
    /// Configuration-specific eligibility (GAMEPLAY spec §2–3). Starts from items that are already gameplay-eligible
    /// (pack readiness is never bypassed or changed) and removes item/configuration pairs that would be unanswerable
    /// or ambiguous. Never switches the player's chosen modes; it only reports what is excluded and why.
    /// </summary>
    public static class GameCompatibility
    {
        public sealed class Result
        {
            public readonly List<LearningItem> Usable = new List<LearningItem>();
            /// <summary>Excluded item with a short player-facing reason.</summary>
            public readonly List<KeyValuePair<LearningItem, string>> Excluded = new List<KeyValuePair<LearningItem, string>>();
            public string BlockReason;
            public bool CanStart => BlockReason == null;
        }

        public static Result Check(IList<LearningItem> eligible, GameConfig c, LearningMode mode)
        {
            var r = new Result();
            string Key(LearningItem it) => AnswerChecker.Normalize(it.SourceText, mode);
            string First(LearningItem it) => BlankPuzzle.Split(it.SourceText) is string[] u && u.Length > 0 ? u[0] : "";

            // Clues that more than one distinct answer shares make the question ambiguous.
            var clueAnswers = new Dictionary<string, HashSet<string>>();
            foreach (var it in eligible)
            {
                string clue = ClueKey(it, c, mode, First);
                if (clue == null) continue;
                if (!clueAnswers.TryGetValue(clue, out var set)) clueAnswers[clue] = set = new HashSet<string>();
                set.Add(Key(it));
            }

            foreach (var it in eligible)
            {
                string why = null;
                if (c.Answer == AnswerMode.FillInTheBlank && !BlankPuzzle.Supports(it.SourceText)) why = "từ quá ngắn để điền chỗ trống";
                else if (ClueKey(it, c, mode, First) is string clue && clueAnswers[clue].Count > 1) why = "gợi ý trùng với từ khác";
                if (why == null) r.Usable.Add(it); else r.Excluded.Add(new KeyValuePair<LearningItem, string>(it, why));
            }

            if (r.Usable.Count < c.MinEligibleItems)
                r.BlockReason = $"Cấu hình này chỉ có {r.Usable.Count} từ dùng được; cần ít nhất {c.MinEligibleItems}. Hãy đổi Gợi ý hoặc Kiểu trả lời.";
            return r;
        }

        /// <summary>What the player sees as the clue; two different answers with the same key are ambiguous.</summary>
        static string ClueKey(LearningItem it, GameConfig c, LearningMode mode, System.Func<LearningItem, string> first)
        {
            string meaning = AnswerChecker.Normalize(it.Meaning, LearningMode.EnglishToVietnamese);
            return c.Hint == HintMode.NoHint ? meaning : meaning + "\u0001" + AnswerChecker.Normalize(first(it), mode);
        }
    }
}
