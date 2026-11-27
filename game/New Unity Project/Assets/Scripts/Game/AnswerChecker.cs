using System.Text;
using MP1.Content;

namespace MP1.Game
{
    /// <summary>
    /// Full Word comparison (GAMEPLAY spec §3): NFC + trim on both sides. English ignores letter case but keeps
    /// interior spaces and punctuation. Japanese must match the stored script exactly: no Kana/Kanji, Hiragana/Katakana,
    /// width or long-vowel substitution, and no Romaji. Fill-in-the-Blank (G-007) will reconstruct the full answer and
    /// call the same <see cref="Matches"/>.
    /// </summary>
    public static class AnswerChecker
    {
        public static string Normalize(string s, LearningMode mode)
        {
            if (s == null) return "";
            string n = s.Normalize(NormalizationForm.FormC).Trim();
            return mode == LearningMode.EnglishToVietnamese ? n.ToLowerInvariant() : n;
        }

        public static bool Matches(string input, string expected, LearningMode mode)
        {
            string a = Normalize(input, mode), b = Normalize(expected, mode);
            return a.Length > 0 && a == b;
        }
    }
}
