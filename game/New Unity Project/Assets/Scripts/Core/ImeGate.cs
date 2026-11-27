namespace MP1.Core
{
    /// <summary>Game shortcuts (Tab, Enter, Escape) must not fire while an IME composition is still uncommitted.</summary>
    public static class ImeGate
    {
        public static bool ShortcutAllowed(string compositionString) => string.IsNullOrEmpty(compositionString);
    }
}
