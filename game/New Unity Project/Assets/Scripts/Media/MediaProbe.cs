using System;
using System.Collections;
using System.IO;
using MP1.Core;
using MP1.Dev;
using TMPro;
using UnityEngine;
using UnityEngine.Networking;
using UnityEngine.UI;

namespace MP1.Media
{
    /// <summary>
    /// G-003.8 media probe: loads one image and the EN/JA pronunciation clips of the first item in the private,
    /// test-only Content Pack v46 straight from disk (nothing copied into Assets, no status change), plus a
    /// missing-file and an invalid-path case. NOT the G-004 Content Pack runtime: minimal fields, no validation.
    /// </summary>
    public class MediaProbe : MonoBehaviour
    {
        public const string PackRelative = "reports/EXCEL_15_SMOKE/run-bc2d5460-d9d6-4cef-8cae-1a9601ae7291/content_pack_v46/content_pack.json";

        [SerializeField] RawImage image;
        [SerializeField] TMP_Text itemInfo, status;
        [SerializeField] Button playEnglish, playJapanese, missingFile, invalidPath;

        [Serializable] class MediaRef { public string path; }
        [Serializable] class Item { public string english, japanese, vietnamese, status; public MediaRef image, audio, audio_english; }
        [Serializable] class Pack { public string pack_id; public bool test_only; public Item[] items; }

        AudioSource source;
        string packDir;
        Item item;

        void Start()
        {
            source = gameObject.AddComponent<AudioSource>();
            source.playOnAwake = false;
            playEnglish.onClick.AddListener(() => StartCoroutine(PlayAudio(item?.audio_english?.path, "EN")));
            playJapanese.onClick.AddListener(() => StartCoroutine(PlayAudio(item?.audio?.path, "JA")));
            missingFile.onClick.AddListener(() => StartCoroutine(LoadImage("assets/does_not_exist.jpg", true)));
            invalidPath.onClick.AddListener(() => StartCoroutine(LoadImage("../../../outside_pack.jpg", true)));

            string manifest = DevArgs.Get(DevCommandLine.Args, "-contentPack") is string dir
                ? Path.Combine(dir, "content_pack.json")
                : MediaPaths.FindUpwards(Application.dataPath, PackRelative, File.Exists);
            if (manifest == null || !File.Exists(manifest)) { Report("Không tìm thấy Content Pack thử nghiệm v46. Dùng -contentPack <thư mục>.", true); return; }
            packDir = Path.GetDirectoryName(manifest);
            try
            {
                var pack = JsonUtility.FromJson<Pack>(File.ReadAllText(manifest));
                item = pack.items != null && pack.items.Length > 0 ? pack.items[0] : null;
                itemInfo.text = item == null ? "Pack không có mục nào." :
                    $"<size=150%>{item.english} · {item.japanese}</size>\n{item.vietnamese}\n<color=#F2D4A7>status: {item.status} · test_only: {pack.test_only} · chỉ dùng thử, chưa duyệt</color>";
            }
            catch (Exception e) { Report($"Không đọc được content_pack.json: {e.Message}", true); return; }
            StartCoroutine(LoadImage(item?.image?.path, false));
            if (DevArgs.Has(DevCommandLine.Args, "-g003MediaSelfTest")) StartCoroutine(SelfTest());
        }

        IEnumerator LoadImage(string relative, bool expectFailure)
        {
            string path = MediaPaths.ResolveAsset(packDir, relative);
            if (path == null) { Report($"Từ chối đường dẫn ngoài pack: {relative}", !expectFailure); Log("image-invalid-path", relative, "rejected"); yield break; }
            if (!File.Exists(path)) { Report($"Thiếu tệp ảnh: {relative} · hiển thị trạng thái thiếu ảnh, không thay thế.", !expectFailure); Log("image-missing", relative, "handled"); yield break; }
            using (var req = UnityWebRequestTexture.GetTexture(new Uri(path).AbsoluteUri))
            {
                yield return req.SendWebRequest();
                if (req.result != UnityWebRequest.Result.Success) { Report($"Lỗi tải ảnh: {req.error}", true); Log("image", relative, "error " + req.error); yield break; }
                var tex = DownloadHandlerTexture.GetContent(req);
                image.texture = tex;
                var fit = image.GetComponent<AspectRatioFitter>();
                if (fit != null) fit.aspectRatio = tex.width / (float)tex.height;
                Report($"Đã tải ảnh {tex.width}×{tex.height} từ pack (needs_review).", false);
                Log("image", relative, $"loaded {tex.width}x{tex.height}");
            }
        }

        IEnumerator PlayAudio(string relative, string lang)
        {
            string path = MediaPaths.ResolveAsset(packDir, relative);
            if (path == null || !File.Exists(path)) { Report($"Thiếu âm thanh {lang}.", true); Log("audio-" + lang, relative, "missing"); yield break; }
            using (var req = UnityWebRequestMultimedia.GetAudioClip(new Uri(path).AbsoluteUri, AudioType.MPEG))
            {
                yield return req.SendWebRequest();
                if (req.result != UnityWebRequest.Result.Success) { Report($"Lỗi tải âm thanh {lang}: {req.error}", true); Log("audio-" + lang, relative, "error " + req.error); yield break; }
                var clip = DownloadHandlerAudioClip.GetContent(req);
                source.Stop();
                source.clip = clip;
                source.Play();
                yield return new WaitForSeconds(0.3f);
                bool running = source.isPlaying && source.timeSamples > 0;
                Report($"Âm thanh {lang}: {clip.length:F2}s, {clip.frequency} Hz · {(running ? "đang phát" : "không phát được")}", !running);
                Log("audio-" + lang, relative, $"length={clip.length:F2}s freq={clip.frequency} channels={clip.channels} isPlaying={source.isPlaying} timeSamples={source.timeSamples}");
            }
        }

        IEnumerator SelfTest()
        {
            yield return new WaitForSeconds(1.5f);
            yield return PlayAudio(item?.audio_english?.path, "EN");
            yield return new WaitForSeconds(1.3f);
            yield return PlayAudio(item?.audio?.path, "JA");
            yield return new WaitForSeconds(1.5f);
            yield return LoadImage("assets/does_not_exist.jpg", true);
            yield return LoadImage("../../../outside_pack.jpg", true);
            Debug.Log("G003_MEDIA selftest done");
        }

        void Report(string message, bool isError)
        {
            status.text = message;
            status.color = isError ? new Color32(255, 155, 155, 255) : new Color32(184, 240, 210, 255);
        }

        static void Log(string kind, string path, string result) => Debug.Log($"G003_MEDIA {kind} path={path} result={result}");
    }
}
