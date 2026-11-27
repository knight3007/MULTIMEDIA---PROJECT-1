using System.Collections.Generic;
using System.IO;
using System.Text;
using System.Threading.Tasks;
using MP1.Content;
using MP1.Core;
using MP1.Dev;
using MP1.UI;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace MP1.Library
{
    /// <summary>
    /// G-004 Vocabulary Library (S02): discovers local packs, shows real counts and validation state, and selects a
    /// pack + learning mode into <see cref="LearningSession"/>. Packs are parsed once per session and cached.
    /// </summary>
    public class VocabularyLibraryController : MonoBehaviour
    {
        public sealed class Entry
        {
            public string ManifestPath;
            public PackLoadResult Load;
            public PackReport Report;
            public double LoadMs;
        }

        [SerializeField] RectTransform listContent;
        [SerializeField] Button rowTemplate;
        [SerializeField] TMP_Text listState, detailTitle, detailStatus, detailCounts, detailMeta, dropHint;
        [SerializeField] Button englishButton, japaneseButton, reviewButton, openButton, rescanButton, showAllButton, playEnglishButton, playJapaneseButton;
        [SerializeField] TMP_Text playHint;
        [SerializeField] TMP_InputField pathInput;

        public static readonly Color RowColor = new Color32(16, 40, 60, 255);
        public static readonly Color SelectedRowColor = new Color32(22, 98, 122, 255);
        public static List<Entry> Cache { get; private set; }
        /// <summary>Owner choice (G-004-R1): hide broken/unusable packs by default instead of deleting run evidence.</summary>
        public static bool ShowAll;
        /// <summary>Set by Main Menu "Chơi game": the library is the pack + language step before Meteor Defense.</summary>
        public static bool OpenedForPlay;
        public static bool IsFixture(Entry e) => PackAudience.IsDeveloperFixture(e.Load.Pack, e.ManifestPath);
        /// <summary>Default view (D-035/D-036): only packs with gameplay-eligible items that are not developer fixtures.</summary>
        public static bool Usable(Entry e) => e.Report != null && e.Report.EligibleEnglish + e.Report.EligibleJapanese > 0 && !IsFixture(e);
        static Entry selected;
        Task<List<Entry>> scan;
        Task<Entry> opening;
        readonly List<Button> rows = new List<Button>();
        readonly List<Entry> rowEntries = new List<Entry>();

        public static string RepoRoot => MediaPaths.FindUpwards(Application.dataPath, Path.Combine("tests", "fixtures", "b001", "content_pack_states.json"), File.Exists) is string p
            ? Path.GetFullPath(Path.Combine(Path.GetDirectoryName(p), "..", "..", "..")) : null;

        /// <summary>User drop folder plus, when run from the repository, the folders that already hold packs.</summary>
        public static List<string> SearchRoots()
        {
            var roots = new List<string> { Path.Combine(Application.persistentDataPath, "ContentPacks") };
            if (DevArgs.Get(DevCommandLine.Args, "-contentPackRoot") is string extra) roots.Add(extra);
            string project = Path.GetFullPath(Path.Combine(Application.dataPath, ".."));
            if (Directory.Exists(Path.Combine(project, "ContentPackFixtures"))) roots.Add(Path.Combine(project, "ContentPackFixtures"));
            // A standalone build sits in <project>/Builds/<name>/: its data folder is one level deeper.
            string buildProject = Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", ".."));
            if (Directory.Exists(Path.Combine(buildProject, "ContentPackFixtures"))) roots.Add(Path.Combine(buildProject, "ContentPackFixtures"));
            if (RepoRoot is string repo)
                foreach (var d in new[] { "reports", "docker-output", Path.Combine("tests", "fixtures", "b001") }) roots.Add(Path.Combine(repo, d));
            return roots;
        }

        static Entry LoadEntry(string manifest)
        {
            var sw = System.Diagnostics.Stopwatch.StartNew();
            var e = new Entry { ManifestPath = manifest, Load = ContentPackReader.Load(manifest) };
            if (e.Load.Ok) e.Report = PackEligibility.Evaluate(e.Load.Pack);
            e.LoadMs = sw.Elapsed.TotalMilliseconds;
            return e;
        }

        void Start()
        {
            englishButton.onClick.AddListener(() => OpenPreview(LearningMode.EnglishToVietnamese, false));
            japaneseButton.onClick.AddListener(() => OpenPreview(LearningMode.JapaneseToVietnamese, false));
            reviewButton.onClick.AddListener(() => OpenPreview(LearningMode.EnglishToVietnamese, true));
            openButton.onClick.AddListener(OpenTypedPath);
            rescanButton.onClick.AddListener(() => { Cache = null; StartScan(); });
            showAllButton.onClick.AddListener(() => { ShowAll = !ShowAll; ShowList(); });
            playEnglishButton.onClick.AddListener(() => PlayGame(LearningMode.EnglishToVietnamese));
            playJapaneseButton.onClick.AddListener(() => PlayGame(LearningMode.JapaneseToVietnamese));
            rowTemplate.gameObject.SetActive(false);
            dropHint.text = $"Thư mục pack của người dùng: <noparse>{Path.Combine(Application.persistentDataPath, "ContentPacks")}</noparse>";
            if (Cache == null) StartScan(); else ShowList();
            ShowDetail(selected);
        }

        void StartScan()
        {
            listState.text = "Đang tìm và kiểm tra Content Pack…";
            ClearRows();
            var roots = SearchRoots();
            string auto = DevArgs.Get(DevCommandLine.Args, "-g004Pack");
            scan = Task.Run(() =>
            {
                var sw = System.Diagnostics.Stopwatch.StartNew();
                var manifests = PackDiscovery.Find(roots);
                if (auto != null && PackDiscovery.ResolveUserPath(auto) is string a && !manifests.Contains(a)) manifests.Insert(0, a);
                var list = new List<Entry>();
                foreach (var m in manifests) list.Add(LoadEntry(m));
                Debug.Log($"G004_PERF scan manifests={manifests.Count} totalMs={sw.Elapsed.TotalMilliseconds:F0}");
                return list;
            });
        }

        void Update()
        {
            if (scan != null && scan.IsCompleted)
            {
                Cache = scan.IsFaulted ? new List<Entry>() : scan.Result;
                if (scan.IsFaulted) Debug.LogException(scan.Exception);
                scan = null;
                foreach (var e in Cache) Debug.Log($"G004_PERF pack={Short(e)} state={e.Load.State} items={e.Report?.Total ?? 0} ready={e.Report?.Ready ?? 0} en={e.Report?.EligibleEnglish ?? 0} ja={e.Report?.EligibleJapanese ?? 0} loadMs={e.LoadMs:F1}");
                ShowList();
                AutoSelect();
            }
            if (opening != null && opening.IsCompleted)
            {
                var e = opening.Result;
                opening = null;
                if (!Cache.Exists(c => string.Equals(c.ManifestPath, e.ManifestPath, System.StringComparison.OrdinalIgnoreCase))) Cache.Insert(0, e);
                ShowList();
                Select(e);
            }
        }

        void AutoSelect()
        {
            string auto = DevArgs.Get(DevCommandLine.Args, "-g004Pack");
            if (auto == null || !(PackDiscovery.ResolveUserPath(auto) is string m)) return;
            var e = Cache.Find(c => string.Equals(c.ManifestPath, m, System.StringComparison.OrdinalIgnoreCase));
            if (e == null) return;
            Select(e);
            string preview = DevArgs.Get(DevCommandLine.Args, "-g004Preview");
            var mode = string.Equals(DevArgs.Get(DevCommandLine.Args, "-g004Mode"), "JA", System.StringComparison.OrdinalIgnoreCase) ? LearningMode.JapaneseToVietnamese : LearningMode.EnglishToVietnamese;
            if (preview != null && e.Report != null) OpenPreview(mode, preview == "review");
            string play = DevArgs.Get(DevCommandLine.Args, "-g006Play");
            if (play != null && e.Report != null) PlayGame(string.Equals(play, "JA", System.StringComparison.OrdinalIgnoreCase) ? LearningMode.JapaneseToVietnamese : LearningMode.EnglishToVietnamese);
        }

        void OpenTypedPath()
        {
            string m = PackDiscovery.ResolveUserPath(pathInput.text);
            if (m == null) { listState.text = "Không thấy manifest content_pack*.json tại đường dẫn này (hoặc thư mục có nhiều manifest)."; return; }
            listState.text = "Đang mở pack…";
            opening = Task.Run(() => LoadEntry(m));
        }

        void ClearRows()
        {
            foreach (var r in rows) Destroy(r.gameObject);
            rows.Clear();
            rowEntries.Clear();
        }

        void ShowList()
        {
            ClearRows();
            if (Cache == null) return;
            int usable = Cache.FindAll(Usable).Count, hidden = Cache.Count - usable;
            SetLabel(showAllButton, ShowAll ? "Chỉ hiện pack dùng được" : $"Hiện cả pack lỗi / chưa sẵn sàng / kiểm thử ({hidden})");
            listState.text = Cache.Count == 0 ? "Chưa có Content Pack nào. Chép thư mục pack vào thư mục người dùng bên dưới, hoặc nhập đường dẫn."
                : ShowAll ? $"Tất cả {Cache.Count} pack (dữ liệu thật từ manifest)."
                : usable == 0 ? $"Chưa có pack nào dùng được cho game. {hidden} pack lỗi hoặc chưa sẵn sàng đang ẩn."
                : $"{(OpenedForPlay ? "Chọn pack rồi bấm ▶ Chơi · " : "")}{usable} pack dùng được · {hidden} pack lỗi, chưa sẵn sàng hoặc kiểm thử đang ẩn.";
            foreach (var e in Cache)
            {
                if (!ShowAll && !Usable(e) && e != selected) continue;
                var row = Instantiate(rowTemplate, listContent);
                row.gameObject.SetActive(true);
                row.name = "PackRow";
                row.GetComponentInChildren<TMP_Text>().text = RowText(e);
                var entry = e;
                row.onClick.AddListener(() => Select(entry));
                rows.Add(row);
                rowEntries.Add(entry);
            }
            if (rows.Count > 0) EventSystem.current.SetSelectedGameObject(rows[0].gameObject);
            MarkSelected();
        }

        static string Short(Entry e) => e.Load.Pack != null ? $"{e.Load.Pack.PackId.Substring(0, 13)}… v{e.Load.Pack.PackVersion}" : Path.GetFileName(Path.GetDirectoryName(e.ManifestPath));

        static string Where(Entry e)
        {
            string repo = RepoRoot, p = e.ManifestPath;
            return repo != null && p.StartsWith(repo, System.StringComparison.OrdinalIgnoreCase) ? p.Substring(repo.Length).TrimStart('\\', '/').Replace('\\', '/') : p;
        }

        static string StateLabel(Entry e)
        {
            switch (e.Load.State)
            {
                case PackLoadState.MissingManifest: return "<color=#FF9B9B>Không đọc được manifest</color>";
                case PackLoadState.Malformed: return "<color=#FF9B9B>Manifest lỗi JSON</color>";
                case PackLoadState.UnsupportedVersion: return "<color=#F2D4A7>Phiên bản chưa hỗ trợ</color>";
                case PackLoadState.Invalid: return "<color=#FF9B9B>Manifest không hợp lệ</color>";
            }
            switch (e.Report.Summary)
            {
                case PackSummary.Valid: return "<color=#83E2B1>Hợp lệ · có mục dùng được</color>";
                case PackSummary.MissingMedia: return "<color=#F2D4A7>Thiếu hoặc hỏng media</color>";
                default: return "<color=#F2D4A7>Hợp lệ · 0 mục dùng được cho game</color>";
            }
        }

        static string RowText(Entry e)
        {
            var r = e.Report;
            string counts = r == null ? "—" : $"{r.Total} mục · ready {r.Ready} · EN–VI {r.EligibleEnglish} · JA–VI {r.EligibleJapanese}";
            return $"<b>{Short(e)}</b>{(e.Load.Pack?.TestOnly == true ? "  <size=80%><color=#F2D4A7>test_only</color></size>" : "")}\n<size=78%>{StateLabel(e)} · {counts}</size>\n<size=70%><color=#9FB8C4><noparse>{Where(e)}</noparse></color></size>";
        }

        public void Select(Entry e)
        {
            bool wasListed = rowEntries.Contains(e);
            selected = e;
            if (!wasListed && Cache != null) ShowList(); // a hidden pack opened by path or switch stays visible
            MarkSelected();
            ShowDetail(e);
        }

        void ShowDetail(Entry e)
        {
            bool has = e?.Report != null;
            englishButton.interactable = has && e.Report.EligibleEnglish > 0;
            japaneseButton.interactable = has && e.Report.EligibleJapanese > 0;
            reviewButton.interactable = has;
            SetLabel(englishButton, $"Xem từ English → Tiếng Việt · {(has ? e.Report.EligibleEnglish : 0)} mục");
            UpdatePlay(e);
            SetLabel(japaneseButton, $"Xem từ 日本語 → Tiếng Việt · {(has ? e.Report.EligibleJapanese : 0)} mục");
            if (e == null)
            {
                detailTitle.text = "Chọn một pack";
                detailStatus.text = detailCounts.text = detailMeta.text = "";
                return;
            }
            detailTitle.text = e.Load.Pack != null ? $"<noparse>{e.Load.Pack.PackId}</noparse>" : "Pack không đọc được";
            detailStatus.text = StateLabel(e);
            if (!has)
            {
                var sb = new StringBuilder();
                foreach (var err in e.Load.Errors.GetRange(0, Mathf.Min(6, e.Load.Errors.Count))) sb.AppendLine("• <noparse>" + err + "</noparse>");
                if (e.Load.Errors.Count > 6) sb.AppendLine($"… và {e.Load.Errors.Count - 6} lỗi khác");
                detailCounts.text = sb.ToString();
                detailMeta.text = $"<noparse>{Where(e)}</noparse>";
                return;
            }
            var r = e.Report;
            detailCounts.text =
                $"Tổng mục: <b>{r.Total}</b>\n" +
                $"ready: <b>{r.Ready}</b>   needs_review: <b>{r.NeedsReview}</b>   failed: <b>{r.Failed}</b>\n" +
                $"pending: <b>{r.Pending}</b>   processing: <b>{r.Processing}</b>\n" +
                $"ready nhưng không dùng được: <b>{r.ReadyUnplayable}</b>   tệp media thiếu: <b>{r.MissingMediaFiles}</b>\n" +
                $"Dùng được cho game: EN–VI <b>{r.EligibleEnglish}</b> · JA–VI <b>{r.EligibleJapanese}</b>";
            detailMeta.text = $"contract v{r.Pack.ContractVersion} · pack_version {r.Pack.PackVersion} · test_only {r.Pack.TestOnly} · {(r.Pack.IsDualAudio ? "2 giọng đọc (EN + JA)" : "1 giọng đọc (JA, bản cũ)")}\n" +
                              $"Tải + kiểm tra: {e.LoadMs:F0} ms\n<noparse>{Where(e)}</noparse>";
        }

        /// <summary>Selected pack stays marked independently of keyboard focus.</summary>
        void MarkSelected()
        {
            for (int i = 0; i < rows.Count; i++)
            {
                bool on = rowEntries[i] == selected;
                rows[i].image.color = on ? SelectedRowColor : RowColor;
                var label = rows[i].GetComponentInChildren<TMP_Text>();
                string text = RowText(rowEntries[i]);
                label.text = on ? "<color=#59D8FF>▶ ĐANG CHỌN</color>  " + text : text;
            }
            int sel = rowEntries.IndexOf(selected);
            var scroll = listContent.GetComponentInParent<ScrollRect>();
            if (sel >= 0 && scroll != null && rows.Count > 1)
            {
                Canvas.ForceUpdateCanvases();
                scroll.verticalNormalizedPosition = 1f - sel / (float)(rows.Count - 1); // keep the selected pack visible
            }
        }

        /// <summary>Play needs the start gate's minimum of eligible items and no developer fixture (G-006.1).</summary>
        void UpdatePlay(Entry e)
        {
            int min = new Game.GameConfig().MinEligibleItems;
            bool fixture = e != null && IsFixture(e);
            int en = e?.Report?.EligibleEnglish ?? 0, ja = e?.Report?.EligibleJapanese ?? 0;
            playEnglishButton.interactable = !fixture && en >= min;
            playJapaneseButton.interactable = !fixture && ja >= min;
            SetLabel(playEnglishButton, $"▶ Chơi EN–VI ({en} từ)");
            SetLabel(playJapaneseButton, $"▶ Chơi JA–VI ({ja} từ)");
            playHint.text = e?.Report == null ? "Chọn một pack hợp lệ để chơi."
                : fixture ? "<color=#F2D4A7>Pack kiểm thử của nhà phát triển, không dùng để chơi.</color>"
                : en < min && ja < min ? $"<color=#F2D4A7>Cần ít nhất {min} từ dùng được để chơi.</color>"
                : "Meteor Defense: gõ đúng từ để bắn thiên thạch.";
        }

        void PlayGame(LearningMode mode)
        {
            if (selected?.Report == null || IsFixture(selected)) return;
            LearningSession.Select(selected.Report, mode);
            SceneNav.Load(Game.GameEntry.SetupScene); // G-007: configuration step before the game
        }

        static void SetLabel(Button b, string text) => b.GetComponentInChildren<TMP_Text>().text = text;

        void OpenPreview(LearningMode mode, bool review)
        {
            if (selected?.Report == null) return;
            LearningSession.Select(selected.Report, mode);
            VocabularyPreviewController.ShowReviewItems = review;
            SceneNav.Load("VocabularyPreview");
        }
    }
}
