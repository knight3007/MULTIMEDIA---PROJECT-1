namespace MP1.Content
{
    /// <summary>
    /// Developer fixtures (G-006, D-036) are contract/test packs, not user content: packs stored under
    /// <c>tests/fixtures</c> or <c>ContentPackFixtures</c>, or carrying simulated <c>fixture-simulator</c> evidence.
    /// They stay on disk and testable but are hidden from the default Library and never start production gameplay.
    /// The manifest's <c>test_only</c> flag alone is not used: the owner-reviewed v47 pack inherits test_only=true
    /// from its import workbook and is the intended gameplay content.
    /// </summary>
    public static class PackAudience
    {
        public static bool IsDeveloperFixture(ContentPack pack, string manifestPath)
        {
            string p = (manifestPath ?? pack?.ManifestPath ?? "").Replace('\\', '/').ToLowerInvariant();
            if (p.Contains("/tests/fixtures/") || p.Contains("/contentpackfixtures/")) return true;
            if (pack == null) return false;
            foreach (var it in pack.Items)
                foreach (var e in it.Evidence)
                    if (e.Reviewer == "fixture-simulator") return true;
            return false;
        }
    }
}
