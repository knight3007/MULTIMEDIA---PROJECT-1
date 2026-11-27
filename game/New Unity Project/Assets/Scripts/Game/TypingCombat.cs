using System.Collections.Generic;
using System.Text;
using MP1.Content;

namespace MP1.Game
{
    /// <summary>
    /// G-007-R2 character-based combat for one meteor (D-044). The answer the player must type is split into Unicode
    /// text elements: the whole term in Full Word, only the missing units in Fill-in-the-Blank. Every committed input
    /// change is compared with that answer from the start; the correct prefix decides damage. Damage only ever grows
    /// (Hits is a high-water mark), so Backspace + retype or repeated identical input never deals damage twice.
    /// Spaces and punctuation must still be typed in Full Word but do not count as shots. Completion is reported only
    /// when the whole input equals the answer; the controller then runs the existing full-answer validator as the gate.
    /// </summary>
    public sealed class TypingCombat
    {
        public struct Step
        {
            public int NewHits;      // newly confirmed answer units (lasers to fire)
            public bool Error;       // a wrong unit just appeared or wrong text grew
            public bool Complete;    // input equals the whole answer
        }

        readonly string[] expected;
        readonly bool[] counts;
        readonly LearningMode mode;
        string last;
        int lastLength;
        bool lastHadError;

        public int Required { get; }
        public int Hits { get; private set; }
        public float Fraction => Required == 0 ? 1f : Hits / (float)Required;
        public int Remaining => Required - Hits;

        public TypingCombat(IList<string> expectedUnits, LearningMode mode)
        {
            this.mode = mode;
            expected = new string[expectedUnits.Count];
            counts = new bool[expected.Length];
            for (int i = 0; i < expected.Length; i++)
            {
                expected[i] = expectedUnits[i];
                counts[i] = BlankPuzzle.Selectable(expected[i]);
                if (counts[i]) Required++;
            }
        }

        /// <summary>What this meteor's answer is: the whole term, or the puzzle's missing units in order.</summary>
        public static TypingCombat For(string sourceText, BlankPuzzle puzzle, LearningMode mode)
        {
            if (puzzle == null) return new TypingCombat(BlankPuzzle.Split(sourceText), mode);
            var missing = new List<string>();
            for (int i = 0; i < puzzle.Units.Length; i++) if (puzzle.Hidden[i]) missing.Add(puzzle.Units[i]);
            return new TypingCombat(missing, mode);
        }

        /// <summary>Feed the committed input text (never an unfinished IME composition). Unchanged input yields nothing.</summary>
        public Step Update(string input)
        {
            var step = new Step();
            input = (input ?? "").Normalize(NormalizationForm.FormC);
            if (input == last) return step;
            last = input;

            var units = BlankPuzzle.Split(input);
            int i = 0, correct = 0;
            while (i < units.Length && i < expected.Length && Same(units[i], expected[i]))
            {
                if (counts[i]) correct++;
                i++;
            }
            bool error = i < units.Length;
            step.Error = error && (!lastHadError || units.Length > lastLength);
            lastHadError = error;
            lastLength = units.Length;

            if (correct > Hits) { step.NewHits = correct - Hits; Hits = correct; }
            step.Complete = !error && i == expected.Length;
            return step;
        }

        bool Same(string typed, string want) => mode == LearningMode.EnglishToVietnamese
            ? typed.ToLowerInvariant() == want.ToLowerInvariant()
            : typed == want; // Japanese: exact stored script, no Kana/Kanji or width substitution
    }
}
