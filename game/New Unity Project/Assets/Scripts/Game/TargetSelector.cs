using System.Collections.Generic;

namespace MP1.Game
{
    /// <summary>What targeting needs to know about an active meteor.</summary>
    public struct TargetCandidate
    {
        public int Id, SpawnOrder;
        public float DistanceToLine; // world units above the defense line; smaller = more urgent
        public TargetCandidate(int id, int spawnOrder, float distance) { Id = id; SpawnOrder = spawnOrder; DistanceToLine = distance; }
    }

    /// <summary>
    /// Spec §4: auto target = nearest the defense line, ties by earlier spawn. Once typing begins the target stays.
    /// Tab cycles through active meteors in danger order. Returns -1 when there is nothing to target.
    /// </summary>
    public static class TargetSelector
    {
        public static List<TargetCandidate> DangerOrder(IEnumerable<TargetCandidate> active)
        {
            var list = new List<TargetCandidate>(active);
            list.Sort((a, b) => a.DistanceToLine != b.DistanceToLine ? a.DistanceToLine.CompareTo(b.DistanceToLine) : a.SpawnOrder.CompareTo(b.SpawnOrder));
            return list;
        }

        /// <summary>
        /// Keeps the current target while it exists (LOCKED/TYPING only change via Tab), so typed text never lands on
        /// another meteor; with no valid target, acquires the most urgent one.
        /// </summary>
        public static int Resolve(int current, IEnumerable<TargetCandidate> active)
        {
            var order = DangerOrder(active);
            if (order.Count == 0) return -1;
            return order.Exists(c => c.Id == current) ? current : order[0].Id;
        }

        /// <summary>
        /// G-007 targeting modes. Hybrid = <see cref="Resolve(int, IEnumerable{TargetCandidate})"/>. Auto follows the most
        /// urgent meteor but never leaves one the player is typing into. Manual never acquires on its own: a removed
        /// target leaves no target until Tab.
        /// </summary>
        public static int Resolve(int current, IEnumerable<TargetCandidate> active, TargetingMode mode, bool typing)
        {
            var order = DangerOrder(active);
            bool alive = order.Exists(c => c.Id == current);
            switch (mode)
            {
                case TargetingMode.Manual: return alive ? current : -1;
                case TargetingMode.Auto: return alive && typing ? current : order.Count > 0 ? order[0].Id : -1;
                default: return alive ? current : order.Count > 0 ? order[0].Id : -1;
            }
        }

        public static bool TabAllowed(TargetingMode mode) => mode != TargetingMode.Auto;

        public static int Cycle(int current, IEnumerable<TargetCandidate> active)
        {
            var order = DangerOrder(active);
            if (order.Count == 0) return -1;
            int i = order.FindIndex(c => c.Id == current);
            return order[(i + 1) % order.Count].Id; // i == -1 gives the most urgent
        }
    }
}
