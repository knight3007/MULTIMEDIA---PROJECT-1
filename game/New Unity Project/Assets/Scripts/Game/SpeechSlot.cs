namespace MP1.Game
{
    /// <summary>
    /// D-048 pronunciation policy: play now when idle; while busy keep only the newest request in one pending slot;
    /// when the current clip ends play it only if it is still fresh. Backlog is never more than one word.
    /// Time is the caller's scaled time, so Pause does not age a waiting request.
    /// </summary>
    public sealed class SpeechSlot<T> where T : class
    {
        readonly float staleSeconds;
        T pending;
        float requestedAt;

        public SpeechSlot(float staleSeconds) { this.staleSeconds = staleSeconds; }

        public bool HasPending => pending != null;
        public int Replaced { get; private set; }
        public int Dropped { get; private set; }

        /// <summary>Returns the item to play immediately, or null when it was parked in the pending slot.</summary>
        public T Request(T item, float now, bool busy)
        {
            if (item == null) return null;
            if (!busy && pending == null) return item;
            if (pending != null) Replaced++;
            pending = item;
            requestedAt = now;
            return null;
        }

        /// <summary>Call while idle: the pending item if still fresh, else null (a stale one is dropped).</summary>
        public T Poll(float now, bool busy)
        {
            if (busy || pending == null) return null;
            var p = pending;
            pending = null;
            if (now - requestedAt <= staleSeconds) return p;
            Dropped++;
            return null;
        }

        public void Clear() => pending = null;
    }
}
