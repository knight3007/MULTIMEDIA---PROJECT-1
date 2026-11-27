using System;
using System.Collections.Generic;
using System.Globalization;
using System.IO;
using System.Security.Cryptography;
using System.Text;

namespace MP1.Tests
{
    /// <summary>Builds deterministic Content Pack v1 fixtures with real file bytes and hashes in a temp folder.</summary>
    public sealed class TestPackBuilder : IDisposable
    {
        public static readonly byte[] Png = { 0x89, 0x50, 0x4E, 0x47, 0x0D, 0x0A, 0x1A, 0x0A, 0, 0, 0, 13, 0x49, 0x48, 0x44, 0x52, 1, 2, 3 };
        public static readonly byte[] Mp3 = { (byte)'I', (byte)'D', (byte)'3', 4, 0, 0, 0, 0, 0, 0, 9, 9 };
        public static readonly byte[] Wav = { (byte)'R', (byte)'I', (byte)'F', (byte)'F', 4, 0, 0, 0, (byte)'W', (byte)'A', (byte)'V', (byte)'E', 1, 2 };

        public readonly string Root;
        public readonly Dictionary<string, object> Pack;
        public readonly List<object> Items = new List<object>();
        int counter;

        public TestPackBuilder(string folderName = null, bool dual = true)
        {
            Root = Path.Combine(Path.GetTempPath(), "mp1_g004", folderName ?? Guid.NewGuid().ToString("N"));
            if (Directory.Exists(Root)) Directory.Delete(Root, true);
            Directory.CreateDirectory(Path.Combine(Root, "assets"));
            Pack = new Dictionary<string, object>
            {
                { "contract_version", 1L }, { "pack_id", "pack-11111111-1111-4111-8111-111111111111" }, { "pack_version", 3L },
                { "import_id", "imp-22222222-2222-4222-8222-222222222222" }, { "test_only", true }, { "items", Items }
            };
            if (dual)
                Pack["extensions"] = new Dictionary<string, object> { { "language_modes", new Dictionary<string, object>
                {
                    { "ENGLISH_TO_VIETNAMESE", new Dictionary<string, object> { { "source", "english" }, { "translation", "vietnamese" }, { "audio", "audio_english" } } },
                    { "JAPANESE_TO_VIETNAMESE", new Dictionary<string, object> { { "source", "japanese" }, { "translation", "vietnamese" }, { "audio", "audio_japanese" } } },
                } } };
        }

        public Dictionary<string, object> Asset(byte[] content, string ext, string mime, bool write = true)
        {
            var bytes = new byte[content.Length + 1];
            Buffer.BlockCopy(content, 0, bytes, 0, content.Length);
            bytes[bytes.Length - 1] = (byte)(++counter); // unique bytes per asset, so unique hashes
            string sha;
            using (var h = SHA256.Create()) sha = BitConverter.ToString(h.ComputeHash(bytes)).Replace("-", "").ToLowerInvariant();
            string rel = $"assets/{sha}.{ext}";
            if (write) File.WriteAllBytes(Path.Combine(Root, rel), bytes);
            return new Dictionary<string, object> { { "path", rel }, { "mime_type", mime }, { "sha256", sha }, { "size_bytes", (long)bytes.Length }, { "source", null } };
        }

        /// <summary>Adds an item; <paramref name="status"/> "ready" gets a full, contract-valid ready state.</summary>
        public Dictionary<string, object> AddItem(string status, string en, string ja, string vi, bool dual = true)
        {
            int n = Items.Count + 1;
            var image = Asset(Png, "png", "image/png");
            var ja_audio = Asset(Mp3, "mp3", "audio/mpeg");
            var en_audio = dual ? Asset(Mp3, "mp3", "audio/mpeg") : null;
            bool ready = status == "ready";
            string pass = ready ? "pass" : "unknown";
            var evidence = new List<object>();
            if (ready)
            {
                evidence.Add(Ev("semantic_correctness", null));
                evidence.Add(Ev("image_relevance", (string)image["sha256"]));
                evidence.Add(Ev("image_visual_quality", (string)image["sha256"]));
                evidence.Add(Ev("audio_pronunciation", (string)ja_audio["sha256"]));
                evidence.Add(Ev("content_review", null));
            }
            var item = new Dictionary<string, object>
            {
                { "item_id", $"item-{n:00000000}-aaaa-4aaa-8aaa-{n:000000000000}" }, { "source_row", (long)(n + 1) },
                { "english", en }, { "japanese", ja }, { "vietnamese", vi }, { "target_sense", null },
                { "status", status }, { "review_status", ready ? "approved" : "pending" },
                { "quality", new Dictionary<string, object> { { "semantic_correctness", pass }, { "image_relevance", pass }, { "image_visual_quality", pass }, { "audio_pronunciation", pass }, { "evidence", evidence } } },
                { "technical_integrity", status == "pending" || status == "processing" ? "unknown" : "pass" },
                { "distribution", new Dictionary<string, object> { { "status", "unknown" }, { "evidence", null } } },
                { "image", status == "pending" ? null : image }, { "audio", status == "pending" ? null : ja_audio },
                { "errors", status == "failed" ? new List<object> { new Dictionary<string, object> { { "stage", "image" }, { "code", "x" }, { "message", "m" }, { "retryable", true } } } : new List<object>() },
            };
            if (dual && status != "pending") { item["audio_japanese"] = ja_audio; item["audio_english"] = en_audio; }
            Items.Add(item);
            return item;
        }

        static Dictionary<string, object> Ev(string dim, string sha) =>
            new Dictionary<string, object> { { "dimension", dim }, { "reviewer", "test" }, { "basis", "unit test" }, { "asset_sha256", sha } };

        public string Write(string fileName = "content_pack.json")
        {
            string path = Path.Combine(Root, fileName);
            File.WriteAllText(path, ToJson(Pack), new UTF8Encoding(false));
            return path;
        }

        public static string ToJson(object v)
        {
            switch (v)
            {
                case null: return "null";
                case bool b: return b ? "true" : "false";
                case long l: return l.ToString(CultureInfo.InvariantCulture);
                case int i: return i.ToString(CultureInfo.InvariantCulture);
                case string s: return "\"" + s.Replace("\\", "\\\\").Replace("\"", "\\\"") + "\"";
                case Dictionary<string, object> o:
                    var parts = new List<string>();
                    foreach (var kv in o) parts.Add(ToJson(kv.Key) + ":" + ToJson(kv.Value));
                    return "{" + string.Join(",", parts) + "}";
                case List<object> a:
                    var items = new List<string>();
                    foreach (var x in a) items.Add(ToJson(x));
                    return "[" + string.Join(",", items) + "]";
                default: throw new ArgumentException(v.GetType().Name);
            }
        }

        public void Dispose()
        {
            try { if (Directory.Exists(Root)) Directory.Delete(Root, true); } catch (IOException) { }
        }
    }
}
