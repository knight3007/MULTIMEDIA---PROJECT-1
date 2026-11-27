using System;

namespace MP1.Core
{
    /// <summary>Command-line switches used only for G-003 build verification (captures, perf logs).</summary>
    public static class DevArgs
    {
        public static string Get(string[] args, string name)
        {
            if (args == null) return null;
            for (int i = 0; i < args.Length - 1; i++)
                if (string.Equals(args[i], name, StringComparison.OrdinalIgnoreCase)) return args[i + 1];
            return null;
        }

        public static bool Has(string[] args, string name) => args != null && Array.Exists(args, a => string.Equals(a, name, StringComparison.OrdinalIgnoreCase));

        public static float GetFloat(string[] args, string name, float fallback)
        {
            string v = Get(args, name);
            return v != null && float.TryParse(v, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out var f) ? f : fallback;
        }
    }
}
