using System.Collections.Generic;

namespace MP1.Game
{
    public enum SessionState { Ready, Playing, Paused, Victory, GameOver, Abandoned }
    public enum MeteorState { Active, Destroyed, Breached, Aborted }

    /// <summary>Per-item outcome across the whole session (an item can appear in several waves).</summary>
    public sealed class ItemRecord
    {
        public int Correct, Missed, WrongEnter, Typos;
        /// <summary>Review subset (spec §6 + owner O3): missed, wrong Enter or at least one wrong character.</summary>
        public bool Weak => Missed > 0 || WrongEnter > 0 || Typos > 0;
    }

    /// <summary>
    /// Pure session rules (GAMEPLAY spec §4-6): one terminal outcome per meteor, one score per correct answer,
    /// one HP per breach in call order, HP never negative, Game Over aborts the rest, Victory after all spawn events
    /// resolve with HP left. Every method is a no-op outside Playing, so late input after the end changes nothing.
    /// G-008 (D-046/D-047/D-049): waves of ItemsPerWave spawns, the next wave only after the previous one resolves;
    /// combo and difficulty-multiplied points only when a meteor is destroyed; character hits and typos are statistics.
    /// </summary>
    public class MeteorDefenseSession
    {
        readonly GameConfig config;
        readonly Dictionary<int, MeteorState> meteors = new Dictionary<int, MeteorState>();
        readonly Dictionary<int, string> itemOf = new Dictionary<int, string>();
        public readonly Dictionary<string, int> WrongAttemptsByItem = new Dictionary<string, int>();
        public readonly List<string> MissedItems = new List<string>();
        public readonly Dictionary<string, ItemRecord> Items = new Dictionary<string, ItemRecord>();
        readonly HashSet<string> seen = new HashSet<string>();
        int nextId;

        public SessionState State { get; private set; } = SessionState.Ready;
        public int Hp { get; private set; }
        public int Score { get; private set; }
        public int Correct { get; private set; }
        public int WrongAttempts { get; private set; }
        public int Missed { get; private set; }
        public int Spawned { get; private set; }
        public int Combo { get; private set; }
        public int MaxCombo { get; private set; }
        public int LastPoints { get; private set; }
        public int HitUnits { get; private set; }
        public int Typos { get; private set; }
        public double ActiveSeconds { get; private set; }
        int PerWave => System.Math.Max(1, config.ItemsPerWave);
        /// <summary>Waves started so far (1-based for display); 0 before the first spawn.</summary>
        public int WavesStarted => (Spawned + PerWave - 1) / PerWave;
        public int WaveCount => (config.SessionSpawns + PerWave - 1) / PerWave;
        /// <summary>0-based wave of the next spawn; drives fall and spawn scaling.</summary>
        public int NextWave => Spawned / PerWave;
        /// <summary>True between waves: the last wave's spawns are all resolved and another wave remains.</summary>
        public bool AtWaveBoundary => State == SessionState.Playing && Spawned > 0 && Spawned < config.SessionSpawns && Spawned % PerWave == 0 && Resolved >= Spawned;
        /// <summary>Spec §6 word accuracy: correct / (correct + missed); null when nothing resolved. Aborted are excluded.</summary>
        public double? WordAccuracy => Resolved == 0 ? (double?)null : (double)Correct / Resolved;
        /// <summary>Character-level accuracy, shown separately: hit units / (hit units + typo events).</summary>
        /// <summary>Distinct items that actually spawned (encountered), answered correctly, and needing review.</summary>
        public int UniqueSeen => seen.Count;
        public int UniqueCorrect { get { int n = 0; foreach (var r in Items.Values) if (r.Correct > 0) n++; return n; } }
        public int ReviewCount { get { int n = 0; foreach (var r in Items.Values) if (r.Weak) n++; return n; } }
        /// <summary>Share of the usable vocabulary encountered this session; below 1 when the pack is larger than the session.</summary>
        public static double? Coverage(int seenCount, int usable) => usable <= 0 ? (double?)null : (double)seenCount / usable;
        public double? TypingAccuracy => HitUnits + Typos == 0 ? (double?)null : (double)HitUnits / (HitUnits + Typos);
        public int Resolved => Correct + Missed;
        public int SessionSpawns => config.SessionSpawns;
        public GameConfig Config => config;
        public bool IsOver => State == SessionState.Victory || State == SessionState.GameOver || State == SessionState.Abandoned;

        public MeteorDefenseSession(GameConfig config)
        {
            this.config = config;
            Hp = config.StartingHp;
        }

        public void Start() { if (State == SessionState.Ready) State = SessionState.Playing; }
        public void Pause() { if (State == SessionState.Playing) State = SessionState.Paused; }
        public void Resume() { if (State == SessionState.Paused) State = SessionState.Playing; }
        public void Abandon() { if (State == SessionState.Playing || State == SessionState.Paused) { State = SessionState.Abandoned; AbortActive(); } }

        /// <summary>A new wave may not spawn while the previous wave still has active meteors (spec §5).</summary>
        public bool CanSpawn => State == SessionState.Playing && Spawned < config.SessionSpawns && !(Spawned > 0 && Spawned % PerWave == 0 && Resolved < Spawned);

        /// <summary>Session duration: only time spent Playing counts (no Pause, no results).</summary>
        public void Tick(double seconds) { if (State == SessionState.Playing && seconds > 0) ActiveSeconds += seconds; }

        ItemRecord Rec(string item) => Items.TryGetValue(item, out var r) ? r : Items[item] = new ItemRecord();

        /// <summary>Correct character units dealt to an active meteor: statistics only, never score or combo.</summary>
        public void RegisterHits(int id, int units) { if (State == SessionState.Playing && StateOf(id) == MeteorState.Active && units > 0) HitUnits += units; }

        /// <summary>Wrong character (TypingCombat error): counted per item; no HP, score or combo change (owner O1).</summary>
        public bool RegisterTypo(int id)
        {
            if (State != SessionState.Playing || StateOf(id) != MeteorState.Active) return false;
            Typos++;
            Rec(itemOf[id]).Typos++;
            return true;
        }

        /// <summary>Registers a new active meteor for an item; returns its id, or -1 if spawning is not allowed.</summary>
        public int Spawn(string itemId)
        {
            if (!CanSpawn || itemId == null) return -1;
            int id = nextId++;
            meteors[id] = MeteorState.Active;
            itemOf[id] = itemId;
            seen.Add(itemId);
            Spawned++;
            return id;
        }

        public MeteorState? StateOf(int id) => meteors.TryGetValue(id, out var s) ? s : (MeteorState?)null;
        public string ItemOf(int id) => itemOf.TryGetValue(id, out var s) ? s : null;

        /// <summary>Correct answer: destroys the meteor and scores exactly once. False if not active or not playing.</summary>
        public bool ResolveCorrect(int id)
        {
            if (State != SessionState.Playing || StateOf(id) != MeteorState.Active) return false;
            meteors[id] = MeteorState.Destroyed;
            Correct++;
            LastPoints = config.PointsFor(Combo);
            Score += LastPoints;
            Combo++;
            if (Combo > MaxCombo) MaxCombo = Combo;
            Rec(itemOf[id]).Correct++;
            CheckVictory();
            return true;
        }

        /// <summary>Wrong Enter: counted, no HP loss, meteor stays active.</summary>
        public bool RegisterWrong(int id)
        {
            if (State != SessionState.Playing || StateOf(id) != MeteorState.Active) return false;
            WrongAttempts++;
            string item = itemOf[id];
            WrongAttemptsByItem[item] = WrongAttemptsByItem.TryGetValue(item, out int n) ? n + 1 : 1;
            Rec(item).WrongEnter++;
            Combo = 0;
            return true;
        }

        /// <summary>Meteor reached the defense line: one missed item and one HP, once.</summary>
        public bool RegisterBreach(int id)
        {
            if (State != SessionState.Playing || StateOf(id) != MeteorState.Active) return false;
            meteors[id] = MeteorState.Breached;
            Missed++;
            MissedItems.Add(itemOf[id]);
            Rec(itemOf[id]).Missed++;
            Combo = 0;
            Hp = System.Math.Max(0, Hp - 1);
            if (Hp == 0)
            {
                State = SessionState.GameOver;
                AbortActive();
                return true;
            }
            CheckVictory();
            return true;
        }

        void CheckVictory()
        {
            if (Resolved >= config.SessionSpawns && Hp > 0) State = SessionState.Victory;
        }

        void AbortActive()
        {
            var ids = new List<int>(meteors.Keys);
            foreach (var id in ids) if (meteors[id] == MeteorState.Active) meteors[id] = MeteorState.Aborted;
        }
    }
}
