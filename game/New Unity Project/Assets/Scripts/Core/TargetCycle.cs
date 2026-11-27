namespace MP1.Core
{
    public static class TargetCycle
    {
        /// <summary>Next unresolved index after <paramref name="current"/>, wrapping; current if it is the only one left; -1 if none.</summary>
        public static int Next(int current, bool[] resolved)
        {
            if (resolved == null || resolved.Length == 0) return -1;
            int n = resolved.Length;
            for (int k = 1; k <= n; k++)
            {
                int i = ((current + k) % n + n) % n;
                if (!resolved[i]) return i;
            }
            return -1;
        }
    }
}
