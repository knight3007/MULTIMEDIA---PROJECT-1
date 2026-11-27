using System;
using System.IO;

namespace MP1.Core
{
    /// <summary>Path helpers for the G-003.8 media probe. Not the G-004 Content Pack runtime.</summary>
    public static class MediaPaths
    {
        /// <summary>Walks up from <paramref name="start"/> looking for <paramref name="relative"/>; returns the full path or null.</summary>
        public static string FindUpwards(string start, string relative, Func<string, bool> exists, int maxLevels = 8)
        {
            string dir = start;
            for (int i = 0; i <= maxLevels && !string.IsNullOrEmpty(dir); i++)
            {
                string candidate = Path.Combine(dir, relative);
                if (exists(candidate)) return Path.GetFullPath(candidate);
                dir = Path.GetDirectoryName(dir);
            }
            return null;
        }

        /// <summary>Resolves a pack-relative asset path; rejects rooted paths and anything escaping the pack folder.</summary>
        public static string ResolveAsset(string packDir, string relativePath)
        {
            if (string.IsNullOrEmpty(packDir) || string.IsNullOrWhiteSpace(relativePath)) return null;
            if (Path.IsPathRooted(relativePath)) return null;
            string root = Path.GetFullPath(packDir).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar;
            string full = Path.GetFullPath(Path.Combine(root, relativePath));
            return full.StartsWith(root, StringComparison.OrdinalIgnoreCase) ? full : null;
        }
    }
}
