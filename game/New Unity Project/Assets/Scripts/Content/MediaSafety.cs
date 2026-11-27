using System;
using System.IO;
using System.Security.Cryptography;
using System.Text.RegularExpressions;

namespace MP1.Content
{
    /// <summary>
    /// Safe media references (content_pack_v1.md "Offline storage and safe references"): the only accepted form is
    /// pack-relative <c>assets/&lt;sha256&gt;.png|jpg|mp3|wav</c> with the extension matching the MIME type. This
    /// excludes absolute, drive, UNC, file/http, "..", backslash, query, fragment and percent-encoded paths.
    /// Resolution also refuses reparse points (symlinks, junctions) so nothing can escape the pack root.
    /// </summary>
    public static class MediaSafety
    {
        static readonly Regex AssetPath = new Regex("^assets/([0-9a-f]{64})\\.(png|jpg|mp3|wav)$");

        public static string MimeForExtension(string ext)
        {
            switch (ext)
            {
                case "png": return "image/png";
                case "jpg": return "image/jpeg";
                case "mp3": return "audio/mpeg";
                case "wav": return "audio/wav";
                default: return null;
            }
        }

        /// <summary>Checks the declared reference only (no disk access). Returns null when it is acceptable.</summary>
        public static string CheckDeclared(MediaAsset a)
        {
            if (a == null) return "thiếu asset";
            if (string.IsNullOrEmpty(a.Path)) return "thiếu path";
            var m = AssetPath.Match(a.Path);
            if (!m.Success) return $"path '{a.Path}' không đúng dạng assets/<sha256>.<png|jpg|mp3|wav>";
            if (a.Sha256 != null && m.Groups[1].Value != a.Sha256) return "tên tệp không khớp sha256";
            if (a.MimeType != null && MimeForExtension(m.Groups[2].Value) != a.MimeType) return "đuôi tệp không khớp mime_type";
            return null;
        }

        /// <summary>Full local path for a declared asset, or null with a reason. Never follows a reparse point.</summary>
        public static string Resolve(string packRoot, MediaAsset a, out string error)
        {
            error = CheckDeclared(a);
            if (error != null) return null;
            if (string.IsNullOrEmpty(packRoot)) { error = "pack chưa có thư mục gốc"; return null; }
            string root = Path.GetFullPath(packRoot).TrimEnd(Path.DirectorySeparatorChar, Path.AltDirectorySeparatorChar) + Path.DirectorySeparatorChar;
            string full = Path.GetFullPath(Path.Combine(root, a.Path.Replace('/', Path.DirectorySeparatorChar)));
            if (!full.StartsWith(root, StringComparison.OrdinalIgnoreCase)) { error = "đường dẫn ra ngoài pack"; return null; }
            string assetsDir = Path.Combine(root, "assets");
            if (IsReparsePoint(assetsDir) || IsReparsePoint(full)) { error = "từ chối symlink/junction trong pack"; return null; }
            return full;
        }

        static bool IsReparsePoint(string path)
        {
            try
            {
                if (!File.Exists(path) && !Directory.Exists(path)) return false;
                return (File.GetAttributes(path) & FileAttributes.ReparsePoint) != 0;
            }
            catch (Exception) { return true; } // unreadable attributes: treat as unsafe
        }

        /// <summary>Checks existence, declared size, magic bytes and SHA-256. Returns null when the bytes match.</summary>
        public static string VerifyBytes(string fullPath, MediaAsset a)
        {
            try
            {
                if (fullPath == null || !File.Exists(fullPath)) return "thiếu tệp";
                var info = new FileInfo(fullPath);
                if (info.Length != a.SizeBytes) return $"kích thước {info.Length} khác khai báo {a.SizeBytes}";
                using (var fs = File.OpenRead(fullPath))
                {
                    var head = new byte[12];
                    int n = fs.Read(head, 0, head.Length);
                    if (!MagicMatches(a.MimeType, head, n)) return "nội dung không khớp mime_type";
                    fs.Position = 0;
                    using (var sha = SHA256.Create())
                    {
                        string hex = BitConverter.ToString(sha.ComputeHash(fs)).Replace("-", "").ToLowerInvariant();
                        if (hex != a.Sha256) return "sha256 không khớp";
                    }
                }
                return null;
            }
            catch (Exception e) { return "không đọc được tệp: " + e.GetType().Name; }
        }

        public static bool MagicMatches(string mime, byte[] h, int n)
        {
            switch (mime)
            {
                case "image/png": return n >= 8 && h[0] == 0x89 && h[1] == 0x50 && h[2] == 0x4E && h[3] == 0x47 && h[4] == 0x0D && h[5] == 0x0A && h[6] == 0x1A && h[7] == 0x0A;
                case "image/jpeg": return n >= 3 && h[0] == 0xFF && h[1] == 0xD8 && h[2] == 0xFF;
                case "audio/wav": return n >= 12 && h[0] == 'R' && h[1] == 'I' && h[2] == 'F' && h[3] == 'F' && h[8] == 'W' && h[9] == 'A' && h[10] == 'V' && h[11] == 'E';
                case "audio/mpeg": return n >= 3 && ((h[0] == 'I' && h[1] == 'D' && h[2] == '3') || (h[0] == 0xFF && (h[1] & 0xE0) == 0xE0));
                default: return false;
            }
        }
    }
}
