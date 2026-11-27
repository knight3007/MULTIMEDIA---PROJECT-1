using System;
using System.Collections.Generic;

namespace MP1.Game
{
    /// <summary>
    /// Vocabulary scheduler (G-007-R3, D-051). Items are dealt in deck cycles: each cycle is a seeded shuffle of
    /// <b>all</b> eligible items without replacement, so N items over k×N spawns appear exactly k times each. A
    /// partial last cycle is the only source of unequal counts. Constraints kept from spec §3: never the same item on
    /// two active meteors (postpone instead), never the item just issued when another choice exists, and items
    /// distinct within a wave of <c>itemsPerWave</c> spawns whenever the pack has at least that many items.
    /// Works on item IDs only, so pack data stays immutable. (Before R3 each wave drew 10 of a fresh shuffle, so with
    /// 15 items some words never appeared in 30 spawns.)
    /// </summary>
    public class VocabularyDeck
    {
        readonly List<string> ids;
        readonly Random rng;
        readonly int perWave, total;
        readonly List<string> cycle = new List<string>();
        readonly List<string> waveIssued = new List<string>();
        string lastIssued, previousIssued;

        public int Issued { get; private set; }
        public int Seed { get; }
        public int Total => total;
        public bool Exhausted => Issued >= total;
        /// <summary>1-based number of the deck cycle the last issued item came from (0 before the first draw).</summary>
        public int Cycle { get; private set; }
        public int LastIssuedCycle { get; private set; }
        public int Count => ids.Count;

        public VocabularyDeck(IEnumerable<string> itemIds, int seed, int itemsPerWave, int totalSpawns)
        {
            ids = new List<string>(new HashSet<string>(itemIds ?? Array.Empty<string>()));
            ids.Sort(StringComparer.Ordinal); // input order must not change the seeded sequence
            Seed = seed;
            rng = new Random(seed);
            perWave = Math.Max(1, itemsPerWave);
            total = ids.Count == 0 ? 0 : Math.Max(0, totalSpawns);
        }

        /// <summary>Next item for a spawn, or null when exhausted or when every candidate is already on screen (postpone).</summary>
        public string Next(ICollection<string> activeIds)
        {
            if (Exhausted || ids.Count == 0) return null;
            if (waveIssued.Count >= perWave) waveIssued.Clear();
            if (cycle.Count == 0) Refill();
            bool Active(string id) => activeIds != null && activeIds.Contains(id);
            int pick = Find(id => !Active(id) && id != lastIssued && !waveIssued.Contains(id));
            if (pick < 0) pick = Find(id => !Active(id) && id != lastIssued);
            if (pick < 0) pick = Find(id => !Active(id));
            if (pick < 0) return null; // every remaining item of this cycle is on screen: postpone, nothing is skipped
            string chosen = cycle[pick];
            cycle.RemoveAt(pick);
            previousIssued = lastIssued;
            lastIssued = chosen;
            waveIssued.Add(chosen);
            LastIssuedCycle = Cycle;
            Issued++;
            return chosen;
        }

        /// <summary>Undo the last <see cref="Next"/> when the spawn had to be postponed (no free lane): the item goes back to the front of its cycle.</summary>
        public void Requeue(string id)
        {
            if (id == null || id != lastIssued) return;
            cycle.Insert(0, id);
            waveIssued.Remove(id);
            lastIssued = previousIssued;
            Issued--;
        }

        int Find(Predicate<string> ok)
        {
            for (int i = 0; i < cycle.Count; i++) if (ok(cycle[i])) return i;
            return -1;
        }

        void Refill()
        {
            var shuffled = new List<string>(ids);
            for (int i = shuffled.Count - 1; i > 0; i--)
            {
                int j = rng.Next(i + 1);
                (shuffled[i], shuffled[j]) = (shuffled[j], shuffled[i]);
            }
            // Items already used in the current wave go last, so a wave that spans two cycles stays distinct.
            foreach (var id in shuffled) if (!waveIssued.Contains(id)) cycle.Add(id);
            foreach (var id in shuffled) if (waveIssued.Contains(id)) cycle.Add(id);
            Cycle++;
        }
    }
}
