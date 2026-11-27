using System;
using System.Collections.Generic;
using System.IO;
using System.Text.RegularExpressions;

namespace MP1.Content
{
    /// <summary>
    /// Reads and structurally validates a Content Pack v1 manifest (docs/contracts/content_pack_v1.md).
    /// Structure problems (unknown core field, wrong type, bad ID, unsafe path, duplicate item) reject the pack;
    /// readiness and media are judged separately by <see cref="PackEligibility"/>.
    /// </summary>
    public static class ContentPackReader
    {
        public const long SupportedContractVersion = 1;
        const long MaxSafeInt = 9007199254740991;
        const int MaxReportedErrors = 25;

        static readonly HashSet<string> PackKeys = new HashSet<string> { "contract_version", "pack_id", "pack_version", "import_id", "test_only", "items", "extensions" };
        static readonly HashSet<string> ItemKeys = new HashSet<string> { "item_id", "source_row", "english", "japanese", "vietnamese", "target_sense", "status", "review_status", "quality", "technical_integrity", "distribution", "image", "audio", "errors", "extensions", "audio_english", "audio_japanese" };
        static readonly string[] ItemRequired = { "item_id", "source_row", "english", "japanese", "vietnamese", "target_sense", "status", "review_status", "quality", "technical_integrity", "distribution", "image", "audio", "errors" };
        static readonly HashSet<string> AssetKeys = new HashSet<string> { "path", "mime_type", "sha256", "size_bytes", "source" };
        static readonly HashSet<string> Statuses = new HashSet<string> { "pending", "processing", "needs_review", "ready", "failed" };
        static readonly HashSet<string> Reviews = new HashSet<string> { "pending", "approved", "rejected" };
        static readonly HashSet<string> Tri = new HashSet<string> { "unknown", "pass", "fail" };
        static readonly HashSet<string> Distribution = new HashSet<string> { "unknown", "permitted", "restricted" };
        static readonly HashSet<string> Mimes = new HashSet<string> { "image/png", "image/jpeg", "audio/mpeg", "audio/wav" };
        static readonly string[] QualityDims = { "semantic_correctness", "image_relevance", "image_visual_quality", "audio_pronunciation" };
        static readonly Regex Uuid4 = new Regex("^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$");
        static readonly Regex Sha = new Regex("^[0-9a-f]{64}$");

        public static PackLoadResult Load(string manifestPath)
        {
            var r = new PackLoadResult { ManifestPath = manifestPath };
            if (string.IsNullOrEmpty(manifestPath) || !File.Exists(manifestPath))
            {
                r.State = PackLoadState.MissingManifest;
                r.Errors.Add("Không tìm thấy tệp manifest.");
                return r;
            }
            string text;
            try { text = File.ReadAllText(manifestPath, System.Text.Encoding.UTF8); }
            catch (Exception e) { r.State = PackLoadState.MissingManifest; r.Errors.Add("Không đọc được manifest: " + e.Message); return r; }
            return Parse(text, manifestPath);
        }

        public static PackLoadResult Parse(string json, string manifestPath)
        {
            var r = new PackLoadResult { ManifestPath = manifestPath };
            object root;
            try { root = StrictJson.Parse(json); }
            catch (StrictJson.JsonException e) { r.State = PackLoadState.Malformed; r.Errors.Add("JSON lỗi: " + e.Message); return r; }
            if (!(root is Dictionary<string, object> obj)) { r.State = PackLoadState.Malformed; r.Errors.Add("Gốc JSON phải là object."); return r; }

            // Version first: an unsupported pack is reported as such, not as a pile of field errors.
            if (!obj.TryGetValue("contract_version", out var cv) || !(cv is long v)) { r.State = PackLoadState.Invalid; r.Errors.Add("Thiếu contract_version (số nguyên)."); return r; }
            if (v != SupportedContractVersion) { r.State = PackLoadState.UnsupportedVersion; r.Errors.Add($"contract_version {v} chưa được hỗ trợ (chỉ hỗ trợ {SupportedContractVersion})."); return r; }

            var errs = new List<string>();
            var pack = new ContentPack
            {
                ContractVersion = v,
                ManifestPath = manifestPath,
                RootDir = string.IsNullOrEmpty(manifestPath) ? null : Path.GetDirectoryName(Path.GetFullPath(manifestPath))
            };
            foreach (var k in obj.Keys) if (!PackKeys.Contains(k)) errs.Add($"Trường lạ ở pack: '{k}'.");
            foreach (var k in new[] { "pack_id", "import_id", "test_only", "items" }) if (!obj.ContainsKey(k)) errs.Add($"Pack thiếu trường bắt buộc '{k}'.");
            pack.PackId = Str(obj, "pack_id", "pack", errs);
            if (pack.PackId != null && !(pack.PackId.StartsWith("pack-") && Uuid4.IsMatch(pack.PackId.Substring(5)))) errs.Add("pack_id phải có dạng pack-UUIDv4.");
            pack.PackVersion = PosInt(obj, "pack_version", "pack", errs, 1);
            pack.ImportId = Str(obj, "import_id", "pack", errs);
            if (pack.ImportId != null && !(pack.ImportId.StartsWith("imp-") && Uuid4.IsMatch(pack.ImportId.Substring(4)))) errs.Add("import_id phải có dạng imp-UUIDv4.");
            if (!obj.TryGetValue("test_only", out var to) || !(to is bool tb)) errs.Add("test_only phải là boolean."); else pack.TestOnly = tb;
            if (obj.TryGetValue("extensions", out var ext))
            {
                if (!(ext is Dictionary<string, object> eobj)) errs.Add("extensions phải là object.");
                else if (eobj.TryGetValue("language_modes", out var lm)) { pack.HasLanguageModes = true; CheckLanguageModes(lm, errs); }
            }

            if (!obj.TryGetValue("items", out var itemsRaw) || !(itemsRaw is List<object> items)) errs.Add("items phải là mảng.");
            else if (items.Count == 0) errs.Add("Pack rỗng không hợp lệ (items trống).");
            else
            {
                var ids = new HashSet<string>(StringComparer.Ordinal);
                for (int i = 0; i < items.Count && errs.Count < MaxReportedErrors; i++)
                {
                    var item = ReadItem(items[i], i, errs);
                    if (item == null) continue;
                    if (item.ItemId != null && !ids.Add(item.ItemId)) errs.Add($"item_id trùng: {item.ItemId}.");
                    pack.Items.Add(item);
                }
            }

            if (errs.Count > 0) { r.State = PackLoadState.Invalid; r.Errors.AddRange(errs); return r; }
            r.State = PackLoadState.Valid;
            r.Pack = pack;
            return r;
        }

        static void CheckLanguageModes(object lm, List<string> errs)
        {
            if (!(lm is Dictionary<string, object> modes)) { errs.Add("extensions.language_modes phải là object."); return; }
            foreach (var mode in LearningModes.All)
            {
                string id = LearningModes.Id(mode);
                var (src, tr, audio) = LearningModes.Fields(mode);
                if (!modes.TryGetValue(id, out var m) || !(m is Dictionary<string, object> mm)) { errs.Add($"language_modes thiếu {id}."); continue; }
                if (!(Get(mm, "source") == src && Get(mm, "translation") == tr && Get(mm, "audio") == audio))
                    errs.Add($"language_modes.{id} phải là {src} + {tr} + {audio}.");
            }
        }

        static string Get(Dictionary<string, object> o, string k) => o.TryGetValue(k, out var v) ? v as string : null;

        static PackItem ReadItem(object raw, int index, List<string> errs)
        {
            string at = $"items[{index}]";
            if (!(raw is Dictionary<string, object> o)) { errs.Add($"{at} phải là object."); return null; }
            foreach (var k in o.Keys) if (!ItemKeys.Contains(k)) errs.Add($"{at}: trường lạ '{k}'.");
            foreach (var k in ItemRequired) if (!o.ContainsKey(k)) errs.Add($"{at}: thiếu trường bắt buộc '{k}'.");
            var it = new PackItem
            {
                ItemId = Str(o, "item_id", at, errs),
                SourceRow = PosInt(o, "source_row", at, errs, 2),
                English = Str(o, "english", at, errs),
                Japanese = Str(o, "japanese", at, errs),
                Vietnamese = Str(o, "vietnamese", at, errs),
                TargetSense = NullableStr(o, "target_sense", at, errs),
                Status = Enum(o, "status", Statuses, at, errs),
                ReviewStatus = Enum(o, "review_status", Reviews, at, errs),
                TechnicalIntegrity = Enum(o, "technical_integrity", Tri, at, errs),
                HasDualAudioFields = o.ContainsKey("audio_english") || o.ContainsKey("audio_japanese"),
            };
            if (it.ItemId != null && !(it.ItemId.StartsWith("item-") && Uuid4.IsMatch(it.ItemId.Substring(5)))) errs.Add($"{at}: item_id phải có dạng item-UUIDv4.");

            if (o.TryGetValue("quality", out var q) && q is Dictionary<string, object> qo)
            {
                it.SemanticCorrectness = Enum(qo, QualityDims[0], Tri, at + ".quality", errs);
                it.ImageRelevance = Enum(qo, QualityDims[1], Tri, at + ".quality", errs);
                it.ImageVisualQuality = Enum(qo, QualityDims[2], Tri, at + ".quality", errs);
                it.AudioPronunciation = Enum(qo, QualityDims[3], Tri, at + ".quality", errs);
                if (qo.TryGetValue("evidence", out var ev) && ev is List<object> evl)
                {
                    foreach (var e in evl)
                        if (e is Dictionary<string, object> eo)
                            it.Evidence.Add(new QualityEvidence { Dimension = Get(eo, "dimension"), Reviewer = Get(eo, "reviewer"), AssetSha256 = Get(eo, "asset_sha256") });
                        else errs.Add($"{at}.quality.evidence phải chứa object.");
                }
                else errs.Add($"{at}.quality.evidence phải là mảng.");
            }
            else if (o.ContainsKey("quality")) errs.Add($"{at}.quality phải là object.");

            if (o.TryGetValue("distribution", out var d) && d is Dictionary<string, object> dobj) it.DistributionStatus = Enum(dobj, "status", Distribution, at + ".distribution", errs);
            else if (o.ContainsKey("distribution")) errs.Add($"{at}.distribution phải là object.");

            if (o.TryGetValue("errors", out var er)) { if (er is List<object> el) it.ErrorCount = el.Count; else errs.Add($"{at}.errors phải là mảng."); }

            it.Image = Asset(o, "image", at, errs, "image/");
            it.Audio = Asset(o, "audio", at, errs, "audio/");
            it.AudioEnglish = Asset(o, "audio_english", at, errs, "audio/");
            it.AudioJapanese = Asset(o, "audio_japanese", at, errs, "audio/");
            if (it.Audio != null && it.AudioJapanese != null && (it.Audio.Sha256 != it.AudioJapanese.Sha256 || it.Audio.Path != it.AudioJapanese.Path))
                errs.Add($"{at}: audio phải trùng khớp audio_japanese (alias).");
            return it;
        }

        static MediaAsset Asset(Dictionary<string, object> o, string key, string at, List<string> errs, string mimePrefix)
        {
            if (!o.TryGetValue(key, out var raw) || raw == null) return null;
            string where = $"{at}.{key}";
            if (!(raw is Dictionary<string, object> a)) { errs.Add($"{where} phải là object hoặc null."); return null; }
            foreach (var k in a.Keys) if (!AssetKeys.Contains(k)) errs.Add($"{where}: trường lạ '{k}'.");
            foreach (var k in new[] { "path", "mime_type", "sha256", "source" }) if (!a.ContainsKey(k)) errs.Add($"{where}: thiếu '{k}'.");
            var asset = new MediaAsset { Path = Str(a, "path", where, errs), MimeType = Str(a, "mime_type", where, errs), Sha256 = Str(a, "sha256", where, errs), SizeBytes = PosInt(a, "size_bytes", where, errs, 1) };
            if (asset.MimeType != null && (!Mimes.Contains(asset.MimeType) || !asset.MimeType.StartsWith(mimePrefix))) errs.Add($"{where}: mime_type '{asset.MimeType}' không hợp lệ.");
            if (asset.Sha256 != null && !Sha.IsMatch(asset.Sha256)) errs.Add($"{where}: sha256 phải là 64 ký tự hex thường.");
            string pathErr = MediaSafety.CheckDeclared(asset);
            if (pathErr != null) errs.Add($"{where}: {pathErr}");
            return asset;
        }

        static string Str(Dictionary<string, object> o, string k, string at, List<string> errs)
        {
            if (!o.TryGetValue(k, out var v)) return null; // missing keys are reported once by the required-key check
            if (v is string s) return s;
            errs.Add($"{at}.{k} phải là chuỗi.");
            return null;
        }

        static string NullableStr(Dictionary<string, object> o, string k, string at, List<string> errs)
        {
            if (!o.TryGetValue(k, out var v) || v == null) return null;
            if (v is string s) return s;
            errs.Add($"{at}.{k} phải là chuỗi hoặc null.");
            return null;
        }

        static string Enum(Dictionary<string, object> o, string k, HashSet<string> allowed, string at, List<string> errs)
        {
            if (!o.TryGetValue(k, out var v)) { if (at.Contains(".")) errs.Add($"{at}: thiếu '{k}'."); return null; }
            if (v is string s && allowed.Contains(s)) return s;
            errs.Add($"{at}.{k} = '{v}' không thuộc giá trị cho phép.");
            return null;
        }

        static long PosInt(Dictionary<string, object> o, string k, string at, List<string> errs, long min)
        {
            if (!o.TryGetValue(k, out var v)) { if (at == "pack" || at.Contains(".")) errs.Add($"{at}: thiếu '{k}'."); return 0; }
            if (v is long l && l >= min && l <= MaxSafeInt) return l;
            errs.Add($"{at}.{k} phải là số nguyên ≥ {min}.");
            return 0;
        }
    }
}
