using System;
using System.Collections.Generic;
using System.Globalization;
using System.Text;
using MP1.Content;

namespace MP1.Game
{
    /// <summary>
    /// Fill-in-the-Blank puzzle (GAMEPLAY spec §3). The term is NFC-normalised and split into Unicode text elements, so
    /// combining marks, small Kana, Kanji and ー stay whole. Spaces and punctuation are shown and never blanked. At least
    /// one unit is hidden and one stays visible. The player types only the hidden units, left to right; the full term is
    /// rebuilt and compared with <see cref="AnswerChecker.Matches"/>. Generated once per meteor from a seed, so it is
    /// stable while the meteor lives and reproducible from the session seed.
    /// </summary>
    public sealed class BlankPuzzle
    {
        public const string Blank = "_";
        public readonly string[] Units;
        public readonly bool[] Hidden;
        public int HiddenCount { get; }

        BlankPuzzle(string[] units, bool[] hidden)
        {
            Units = units; Hidden = hidden;
            foreach (bool h in hidden) if (h) HiddenCount++;
        }

        public static string[] Split(string term)
        {
            var list = new List<string>();
            var e = StringInfo.GetTextElementEnumerator((term ?? "").Normalize(NormalizationForm.FormC));
            while (e.MoveNext()) list.Add(e.GetTextElement());
            return list.ToArray();
        }

        /// <summary>Letters and digits (Kana, Kanji and ー are letters) can be blanked; spaces and punctuation cannot.</summary>
        public static bool Selectable(string unit) => unit.Length > 0 && char.IsLetterOrDigit(unit, 0);

        public static int SelectableCount(string term)
        {
            int n = 0;
            foreach (var u in Split(term)) if (Selectable(u)) n++;
            return n;
        }

        /// <summary>Spec: a puzzle needs one hidden and one visible unit, so at least two selectable units.</summary>
        public static bool Supports(string term) => SelectableCount(term) >= 2;

        /// <summary>Null when the term is too short. Hidden count = ratio of selectable units, rounded, clamped to [1, n-1].</summary>
        public static BlankPuzzle Create(string term, float ratio, int seed)
        {
            var units = Split(term);
            var pool = new List<int>();
            for (int i = 0; i < units.Length; i++) if (Selectable(units[i])) pool.Add(i);
            if (pool.Count < 2) return null;
            int hide = Math.Max(1, Math.Min(pool.Count - 1, (int)Math.Round(ratio * pool.Count, MidpointRounding.AwayFromZero)));
            var rng = new Random(seed);
            for (int i = pool.Count - 1; i > 0; i--) { int j = rng.Next(i + 1); (pool[i], pool[j]) = (pool[j], pool[i]); }
            var hidden = new bool[units.Length];
            for (int k = 0; k < hide; k++) hidden[pool[k]] = true;
            return new BlankPuzzle(units, hidden);
        }

        public const char Gap = ' '; // en space between units so adjacent blanks stay countable

        /// <summary>Pattern for display: units separated by en spaces, a real space shown as two em spaces, typed units fill blanks in order.</summary>
        public string Display(string typed = "")
        {
            var fill = Split(typed?.Trim() ?? "");
            var sb = new StringBuilder();
            int f = 0;
            for (int i = 0; i < Units.Length; i++)
            {
                if (i > 0) sb.Append(Gap);
                if (char.IsWhiteSpace(Units[i], 0)) { sb.Append("  "); continue; }
                sb.Append(Hidden[i] ? (f < fill.Length ? fill[f++] : Blank) : Units[i]);
            }
            return sb.ToString();
        }

        /// <summary>The full term with typed units in the hidden positions, or null when the unit count is wrong.</summary>
        public string Rebuild(string typed)
        {
            var fill = Split((typed ?? "").Normalize(NormalizationForm.FormC).Trim());
            if (fill.Length != HiddenCount) return null;
            var sb = new StringBuilder();
            int f = 0;
            for (int i = 0; i < Units.Length; i++) sb.Append(Hidden[i] ? fill[f++] : Units[i]);
            return sb.ToString();
        }

        /// <summary>The expected missing units in order (for tests and the dev bot).</summary>
        public string Missing()
        {
            var sb = new StringBuilder();
            for (int i = 0; i < Units.Length; i++) if (Hidden[i]) sb.Append(Units[i]);
            return sb.ToString();
        }

        public bool Matches(string typed, string term, LearningMode mode) => Rebuild(typed) is string full && AnswerChecker.Matches(full, term, mode);
    }
}
