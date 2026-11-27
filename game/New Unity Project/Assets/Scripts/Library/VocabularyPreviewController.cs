using System.Collections.Generic;
using MP1.Content;
using TMPro;
using UnityEngine;
using UnityEngine.UI;

namespace MP1.Library
{
    /// <summary>
    /// G-004 owner verification preview, not the Flashcard feature: shows items from the shared
    /// <see cref="LearningSession"/>, the shared image and the selected language's audio, loaded on demand.
    /// Review mode also lists non-ready items, each clearly marked as not usable in gameplay.
    /// </summary>
    public class VocabularyPreviewController : MonoBehaviour
    {
        public static bool ShowReviewItems;
        /// <summary>G-008 review from Results: only these item IDs of the same pack and language; null = whole library.</summary>
        public static HashSet<string> ReviewItemIds;
        HashSet<string> review;
        public bool InReview => review != null;

        [SerializeField] RawImage image;
        [SerializeField] TMP_Text sourceText, meaningText, info, counter, itemTag, mediaStatus, emptyText;
        [SerializeField] Button prevButton, nextButton, playButton, englishButton, japaneseButton;

        readonly List<LearningItem> items = new List<LearningItem>();
        int index;
        Texture2D texture;
        AudioClip clip;
        AudioSource source;

        public int Count => items.Count;
        public int Index => index;
        public LearningItem Current => items.Count > 0 ? items[index] : null;
        public string MediaStatusText => mediaStatus.text;
        public AudioSource Source => source;

        void Start()
        {
            source = gameObject.AddComponent<AudioSource>();
            source.playOnAwake = false;
            review = ReviewItemIds;
            ReviewItemIds = null; // one review visit; the filter never leaks into a later Library visit
            if (review != null && FindAnyObjectByType<UI.SceneNav>() is UI.SceneNav nav) nav.SetBack(Game.GameEntry.SetupScene);
            prevButton.onClick.AddListener(() => Show(index - 1));
            nextButton.onClick.AddListener(() => Show(index + 1));
            playButton.onClick.AddListener(Play);
            englishButton.onClick.AddListener(() => SwitchMode(LearningMode.EnglishToVietnamese));
            japaneseButton.onClick.AddListener(() => SwitchMode(LearningMode.JapaneseToVietnamese));
            Rebuild();
            if (Core.DevArgs.Has(Dev.DevCommandLine.Args, "-g004Play")) Invoke(nameof(Play), 1f); // build verification only
        }

        void Update()
        {
            if (Input.GetKeyDown(KeyCode.LeftArrow)) Show(index - 1);
            if (Input.GetKeyDown(KeyCode.RightArrow)) Show(index + 1);
        }

        public void SwitchMode(LearningMode mode)
        {
            if (!LearningSession.HasSelection) return;
            LearningSession.Select(LearningSession.Report, mode);
            Rebuild();
        }

        void Rebuild()
        {
            items.Clear();
            if (LearningSession.HasSelection)
            {
                items.AddRange(LearningSession.EligibleItems);
                if (ShowReviewItems && review == null) items.AddRange(LearningSession.PreviewOnlyItems);
                if (review != null) items.RemoveAll(it => !review.Contains(it.ItemId));
            }
            var rep = LearningSession.Report;
            englishButton.interactable = rep != null && (ShowReviewItems || rep.EligibleEnglish > 0) && LearningSession.Mode != LearningMode.EnglishToVietnamese;
            japaneseButton.interactable = rep != null && (ShowReviewItems || rep.EligibleJapanese > 0) && LearningSession.Mode != LearningMode.JapaneseToVietnamese;
            if (review != null) englishButton.interactable = japaneseButton.interactable = false; // review keeps the played language
            emptyText.gameObject.SetActive(items.Count == 0);
            emptyText.text = rep == null ? "Chưa chọn pack. Quay lại Thư viện để chọn." : "Không có mục nào cho chế độ này.";
            Show(0);
        }

        public void Show(int i)
        {
            if (items.Count == 0)
            {
                sourceText.text = meaningText.text = info.text = counter.text = itemTag.text = mediaStatus.text = "";
                SetTexture(null);
                prevButton.interactable = nextButton.interactable = playButton.interactable = false;
                return;
            }
            index = (i % items.Count + items.Count) % items.Count;
            var it = items[index];
            prevButton.interactable = nextButton.interactable = items.Count > 1;
            playButton.interactable = it.Audio != null;
            sourceText.text = $"<noparse>{it.SourceText}</noparse>";
            meaningText.text = $"<noparse>{it.Meaning}</noparse>";
            counter.text = (review != null ? "ÔN TẬP · " : "") + $"{index + 1} / {items.Count} · {LearningModes.Label(LearningSession.Mode)}";
            itemTag.text = it.GameplayEligible
                ? "<color=#83E2B1>DÙNG ĐƯỢC CHO GAME · ready, media đã kiểm tra</color>"
                : $"<color=#F2D4A7>CHỈ XEM ĐỂ KIỂM TRA · status {it.Status} · không đưa vào game</color>";
            info.text = $"<noparse>{it.ItemId}</noparse>\npack v{it.PackVersion} · {LearningModes.Id(LearningSession.Mode)}";
            mediaStatus.text = "Đang tải ảnh…";
            SetTexture(null);
            StartCoroutine(PackMediaLoader.LoadTexture(LearningSession.Pack, it.Image, (tex, err, ms) =>
            {
                if (Current != it) { if (tex) Destroy(tex); return; } // user already moved on
                SetTexture(tex);
                mediaStatus.text = tex ? $"Ảnh {tex.width}×{tex.height} ({ms:F0} ms)" : $"<color=#FF9B9B>Ảnh: {err}</color>";
                Debug.Log($"G004_MEDIA image item={it.ItemId} result={(tex ? $"{tex.width}x{tex.height}" : err)} ms={ms:F1}");
            }));
        }

        void SetTexture(Texture2D tex)
        {
            if (texture != null && texture != tex) Destroy(texture); // release the replaced image
            texture = tex;
            image.texture = tex;
            image.enabled = tex != null;
            var fit = image.GetComponent<AspectRatioFitter>();
            if (fit != null && tex != null) fit.aspectRatio = tex.width / (float)tex.height;
        }

        public void Play()
        {
            var it = Current;
            if (it?.Audio == null) return;
            StartCoroutine(PackMediaLoader.LoadClip(LearningSession.Pack, it.Audio, (c, err, ms) =>
            {
                if (c == null) { mediaStatus.text = $"<color=#FF9B9B>Âm thanh: {err}</color>"; Debug.Log($"G004_MEDIA audio item={it.ItemId} result={err}"); return; }
                source.Stop();
                if (clip != null && clip != c) Destroy(clip); // release the replaced clip
                clip = c;
                source.clip = c;
                source.Play();
                mediaStatus.text = $"Đang phát {LearningModes.Label(LearningSession.Mode).Split(' ')[0]} · {c.length:F2}s ({ms:F0} ms)";
                Debug.Log($"G004_MEDIA audio item={it.ItemId} mode={LearningModes.Id(LearningSession.Mode)} length={c.length:F2}s isPlaying={source.isPlaying} ms={ms:F1}");
            }));
        }

        void OnDestroy()
        {
            if (texture != null) Destroy(texture);
            if (clip != null) Destroy(clip);
        }
    }
}
