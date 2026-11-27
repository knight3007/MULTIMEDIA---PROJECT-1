using System.Collections.Generic;
using System.Text;
using MP1.Core;
using TMPro;
using UnityEngine;

namespace MP1.Typography
{
    /// <summary>
    /// G-003.5 input probe. Shows committed text separately from the uncommitted IME composition and logs whether
    /// Tab / Enter / Escape / Backspace / Space would be handled or ignored because a composition is active.
    /// </summary>
    public class InputProbe : MonoBehaviour
    {
        [SerializeField] TMP_InputField field;
        [SerializeField] TMP_Text committedText, compositionText, keyLog, atlasInfo;
        [SerializeField] TMP_FontAsset[] fonts;

        readonly List<string> log = new List<string>();
        static readonly KeyCode[] Watched = { KeyCode.Tab, KeyCode.Return, KeyCode.KeypadEnter, KeyCode.Escape, KeyCode.Backspace, KeyCode.Space };

        void Start()
        {
            Input.imeCompositionMode = IMECompositionMode.On;
            field.onValidateInput += (text, index, c) => c == '\t' ? '\0' : c; // Tab is a game shortcut, never a character
            field.ActivateInputField();
            InvokeRepeating(nameof(RefreshAtlasInfo), 0.5f, 1f);
        }

        void Update()
        {
            string comp = Input.compositionString;
            compositionText.text = string.IsNullOrEmpty(comp)
                ? "IME đang soạn: (không)"
                : $"IME đang soạn (CHƯA xác nhận): <color=#FFD27A><noparse>{comp}</noparse></color>";
            committedText.text = $"Đã xác nhận: “<noparse>{field.text}</noparse>” · {field.text.Length} ký tự";

            foreach (var key in Watched)
            {
                if (!Input.GetKeyDown(key)) continue;
                bool allowed = ImeGate.ShortcutAllowed(comp);
                string what = key == KeyCode.Return || key == KeyCode.KeypadEnter ? (allowed ? $"xác nhận “{field.text}”" : "để IME chốt chữ")
                    : key == KeyCode.Tab ? (allowed ? "đổi mục tiêu (mô phỏng)" : "bỏ qua")
                    : key == KeyCode.Escape ? (allowed ? "về menu" : "bỏ qua, IME tự hủy soạn")
                    : "ký tự/sửa";
                Add($"{key} · {(allowed ? "xử lý" : "IME đang soạn")} → {what}");
                if (allowed && key != KeyCode.Escape) field.ActivateInputField();
            }
        }

        void Add(string line)
        {
            log.Insert(0, $"{Time.realtimeSinceStartup:F1}s  {line}");
            if (log.Count > 8) log.RemoveAt(log.Count - 1);
            var sb = new StringBuilder();
            foreach (var l in log) sb.AppendLine(l);
            keyLog.text = sb.ToString();
        }

        void RefreshAtlasInfo()
        {
            var sb = new StringBuilder();
            foreach (var f in fonts)
            {
                if (f == null) continue;
                var tex = f.atlasTextures != null && f.atlasTextures.Length > 0 ? f.atlasTextures[0] : null;
                sb.AppendLine($"{f.name}: {f.atlasPopulationMode}, {f.atlasTextures?.Length ?? 0} atlas {(tex != null ? tex.width + "×" + tex.height : "-")}, {f.characterTable.Count} ký tự, fallback {f.fallbackFontAssetTable?.Count ?? 0}");
            }
            atlasInfo.text = sb.ToString();
        }
    }
}
