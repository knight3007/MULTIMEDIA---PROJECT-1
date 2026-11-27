using System;
using System.Collections;
using System.IO;
using UnityEngine;
using UnityEngine.Networking;

namespace MP1.Content
{
    /// <summary>
    /// On-demand media for any feature: resolves a pack asset safely, re-verifies its bytes, then loads it.
    /// Nothing is preloaded; callers destroy the previous texture/clip when they replace it.
    /// </summary>
    public static class PackMediaLoader
    {
        public static IEnumerator LoadTexture(ContentPack pack, MediaAsset asset, Action<Texture2D, string, double> done)
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            string full = Check(pack, asset, out string err);
            if (full == null) { done(null, err, sw.Elapsed.TotalMilliseconds); yield break; }
            var tex = new Texture2D(2, 2, TextureFormat.RGBA32, false) { name = asset.Sha256.Substring(0, 12) };
            bool ok;
            try { ok = tex.LoadImage(File.ReadAllBytes(full), true); }
            catch (Exception e) { ok = false; err = e.GetType().Name; }
            if (!ok) { UnityEngine.Object.Destroy(tex); done(null, err ?? "không giải mã được ảnh", sw.Elapsed.TotalMilliseconds); yield break; }
            done(tex, null, sw.Elapsed.TotalMilliseconds);
        }

        public static IEnumerator LoadClip(ContentPack pack, MediaAsset asset, Action<AudioClip, string, double> done)
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            string full = Check(pack, asset, out string err);
            if (full == null) { done(null, err, sw.Elapsed.TotalMilliseconds); yield break; }
            var type = asset.MimeType == "audio/wav" ? AudioType.WAV : AudioType.MPEG;
            using (var req = UnityWebRequestMultimedia.GetAudioClip(new Uri(full).AbsoluteUri, type))
            {
                yield return req.SendWebRequest();
                if (req.result != UnityWebRequest.Result.Success) { done(null, "lỗi tải âm thanh: " + req.error, sw.Elapsed.TotalMilliseconds); yield break; }
                var clip = DownloadHandlerAudioClip.GetContent(req);
                if (clip == null || clip.length <= 0f) { done(null, "âm thanh rỗng hoặc không giải mã được", sw.Elapsed.TotalMilliseconds); yield break; }
                done(clip, null, sw.Elapsed.TotalMilliseconds);
            }
        }

        static string Check(ContentPack pack, MediaAsset asset, out string err)
        {
            if (pack == null || asset == null) { err = "mục này không có tệp media"; return null; }
            string full = MediaSafety.Resolve(pack.RootDir, asset, out err);
            if (full == null) return null;
            err = MediaSafety.VerifyBytes(full, asset);
            return err == null ? full : null;
        }
    }
}
