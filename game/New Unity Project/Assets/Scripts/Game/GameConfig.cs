using System;

namespace MP1.Game
{
    public enum Difficulty { Easy, Normal, Hard, Expert }
    /// <summary>GAMEPLAY spec §2 text hint rows. Image hints are not used in gameplay (owner, D-043); images stay in the Library.</summary>
    public enum HintMode { NoHint, TextOnly }
    public enum AnswerMode { FullWord, FillInTheBlank }
    /// <summary>Hybrid = G-006 behaviour (auto acquire + Tab). Auto = no Tab. Manual = Tab only, no auto acquire.</summary>
    public enum TargetingMode { Hybrid, Auto, Manual }

    /// <summary>
    /// The single source of Meteor Defense settings: player choices (difficulty, hint, answer, targeting) plus the
    /// numeric tuning they imply. Numbers are the PROVISIONAL columns of GAMEPLAY_MECHANICS_SPEC_v0.1 §5 (D-037/D-038),
    /// not approved balance. G-008 adds waves, combo and score multipliers (D-046/D-047, PROPOSED).
    /// </summary>
    [Serializable]
    public class GameConfig
    {
        public Difficulty Difficulty = Difficulty.Normal;
        public HintMode Hint = HintMode.TextOnly;
        public AnswerMode Answer = AnswerMode.FullWord;
        public TargetingMode Targeting = TargetingMode.Hybrid;

        public int StartingHp = 4;
        public float BaseFallSeconds = 15f;      // spawn to defense line for terms up to LengthAllowanceUnits
        public int LengthAllowanceUnits = 8;
        public float SecondsPerExtraUnit = 0.6f;
        public float MaxExtraSeconds = 8f;
        public float MinSpawnInterval = 6f;
        public float FirstSpawnDelay = 1.5f;
        public int MaxConcurrent = 3;
        public float HiddenRatio = 0.5f;         // Fill-in-the-Blank only
        public float ScoreMultiplier = 1.5f;     // difficulty multiplier, spec §5
        public int SessionSpawns = 30;           // spec: 3 waves x 10 spawn events
        public int ItemsPerWave = 10;
        public int PointsPerCorrect = 100;       // base points before difficulty and combo multipliers
        public int WaveCount = 3;
        public float WavePauseSeconds = 3f;
        public float WaveFallSpeedup = 1.1f;     // each wave falls 10% faster than the previous one
        public float WaveSpawnFactor = 0.95f;    // each wave's minimum spawn interval is 5% shorter
        public int ComboCapSteps = 5;            // combo bonus 0.1 per previous consecutive correct, capped at +0.5
        public float SpeechStaleSeconds = 1.5f;  // a waiting pronunciation older than this is dropped (D-048)
        public int MinEligibleItems = 10;        // spec: no Start below ten distinct eligible items

        /// <summary>Choices carried between Library, Configuration, gameplay and Replay (no persistence beyond the app run).</summary>
        public static GameConfig Selected = new GameConfig();

        /// <summary>Spec §5 table. Player modes are kept; only the difficulty numbers change.</summary>
        public GameConfig WithDifficulty(Difficulty d)
        {
            var c = Clone();
            c.Difficulty = d;
            switch (d)
            {
                case Difficulty.Easy: c.Set(5, 18f, 7f, 2, 0.25f, 1f); break;
                case Difficulty.Normal: c.Set(4, 15f, 6f, 3, 0.5f, 1.5f); break;
                case Difficulty.Hard: c.Set(3, 12f, 5f, 4, 0.75f, 2f); break;
                case Difficulty.Expert: c.Set(2, 10f, 4f, 5, 0.9f, 3f); break;
            }
            return c;
        }

        void Set(int hp, float fall, float spawn, int max, float hidden, float mult)
        {
            StartingHp = hp; BaseFallSeconds = fall; MinSpawnInterval = spawn; MaxConcurrent = max; HiddenRatio = hidden; ScoreMultiplier = mult;
        }

        /// <summary>Fall time grows for long terms so they stay answerable (spec §5).</summary>
        public float FallSeconds(string term)
        {
            int units = string.IsNullOrEmpty(term) ? 0 : new System.Globalization.StringInfo(term).LengthInTextElements;
            float extra = Math.Min(Math.Max(0, units - LengthAllowanceUnits) * SecondsPerExtraUnit, MaxExtraSeconds);
            return BaseFallSeconds + extra;
        }

        /// <summary>Wave modifier after the long-word allowance (spec §5): wave 0 is the base, each later wave 10% faster.</summary>
        public float FallSeconds(string term, int wave) => FallSeconds(term) / (float)Math.Pow(WaveFallSpeedup, Math.Max(0, wave));

        public float SpawnInterval(int wave) => MinSpawnInterval * (float)Math.Pow(WaveSpawnFactor, Math.Max(0, wave));

        /// <summary>Spec §5: round(base x difficulty x (1 + min(0.1 x combo, 0.5))), rounded once, half away from zero.</summary>
        public int PointsFor(int comboBefore)
        {
            int steps = Math.Min(Math.Max(0, comboBefore), ComboCapSteps);
            return (int)Math.Round((decimal)PointsPerCorrect * (decimal)ScoreMultiplier * (10 + steps) / 10m, MidpointRounding.AwayFromZero);
        }

        public bool ShowsFirstUnit => Hint == HintMode.TextOnly;

        public GameConfig Clone() => (GameConfig)MemberwiseClone();
    }
}
