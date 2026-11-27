using System;
using System.Collections.Generic;
using System.IO;

namespace MP1.Content
{
    /// <summary>
    /// Local pack discovery (G-004, no documented convention existed): a pack is a folder holding a manifest named
    /// <c>content_pack.json</c> or <c>content_pack_*.json</c> next to its <c>assets/</c> folder. Search roots are
    /// passed in by the caller; the user can also open any manifest or folder path directly.
    /// </summary>
    public static class PackDiscovery
    {
        static readonly HashSet<string> SkipDirs = new HashSet<string>(StringComparer.OrdinalIgnoreCase)
            { "assets", "Library", "Temp", "Logs", ".git", "node_modules", "__pycache__", ".venv", "Builds", "PackageCache" };

        public static bool IsManifestName(string fileName) =>
            fileName.Equals("content_pack.json", StringComparison.OrdinalIgnoreCase) ||
            (fileName.StartsWith("content_pack_", StringComparison.OrdinalIgnoreCase) && fileName.EndsWith(".json", StringComparison.OrdinalIgnoreCase));

        public static List<string> Find(IEnumerable<string> roots, int maxDepth = 6)
        {
            var found = new List<string>();
            var seen = new HashSet<string>(StringComparer.OrdinalIgnoreCase);
            foreach (var root in roots)
                if (!string.IsNullOrEmpty(root) && Directory.Exists(root)) Walk(Path.GetFullPath(root), 0, maxDepth, found, seen);
            found.Sort(StringComparer.OrdinalIgnoreCase);
            return found;
        }

        static void Walk(string dir, int depth, int maxDepth, List<string> found, HashSet<string> seen)
        {
            try
            {
                if ((File.GetAttributes(dir) & FileAttributes.ReparsePoint) != 0) return; // never follow links during scans
                foreach (var f in Directory.EnumerateFiles(dir, "content_pack*.json"))
                    if (IsManifestName(Path.GetFileName(f)) && seen.Add(f)) found.Add(f);
                if (depth >= maxDepth) return;
                foreach (var d in Directory.EnumerateDirectories(dir))
                    if (!SkipDirs.Contains(Path.GetFileName(d))) Walk(d, depth + 1, maxDepth, found, seen);
            }
            catch (UnauthorizedAccessException) { }
            catch (IOException) { }
        }

        /// <summary>Accepts a manifest path or a folder containing exactly one manifest. Returns null if neither.</summary>
        public static string ResolveUserPath(string input)
        {
            if (string.IsNullOrWhiteSpace(input)) return null;
            string p = input.Trim().Trim('"');
            if (File.Exists(p)) return Path.GetFullPath(p);
            if (!Directory.Exists(p)) return null;
            var list = new List<string>();
            foreach (var f in Directory.EnumerateFiles(p, "content_pack*.json")) if (IsManifestName(Path.GetFileName(f))) list.Add(f);
            return list.Count == 1 ? Path.GetFullPath(list[0]) : null;
        }
    }
}
