using System.Text;

namespace MP1.Sandbox
{
    /// <summary>PROTOTYPE ONLY: exact-match check for the sandbox. The real answer rules live in the Gameplay spec (later phase).</summary>
    public static class SandboxAnswer
    {
        public static bool Matches(string input, string expected)
        {
            if (input == null || expected == null) return false;
            string a = input.Trim().Normalize(NormalizationForm.FormC).ToLowerInvariant();
            string b = expected.Trim().Normalize(NormalizationForm.FormC).ToLowerInvariant();
            return a.Length > 0 && a == b;
        }
    }
}
