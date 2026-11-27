using System;

namespace MP1.Core
{
    /// <summary>Session-only reduced-motion flag (G-003 test switch, not the S11 Settings persistence).</summary>
    public static class MotionSettings
    {
        static bool reduced = Array.IndexOf(Environment.GetCommandLineArgs(), "-reducedMotion") >= 0;
        public static event Action Changed;
        public static bool Reduced
        {
            get => reduced;
            set { if (reduced == value) return; reduced = value; Changed?.Invoke(); }
        }
    }
}
