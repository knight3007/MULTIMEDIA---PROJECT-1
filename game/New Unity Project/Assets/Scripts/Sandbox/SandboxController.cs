using System.Collections;
using System.Collections.Generic;
using MP1.Background;
using MP1.Core;
using MP1.Dev;
using TMPro;
using UnityEngine;

namespace MP1.Sandbox
{
    /// <summary>
    /// PROTOTYPE ONLY (G-003.7): technical sandbox for sprites, upright labels, target lock, Tab switching, typing,
    /// laser, particles and score popup. No waves, difficulty, hints, persistence or production validation.
    /// </summary>
    public class SandboxController : MonoBehaviour
    {
        [Header("Art (provisional, see ASSET_SOURCES.md)")]
        [SerializeField] Sprite[] meteorSprites;
        [SerializeField] Sprite shipSprite, flameSprite, shieldSprite, laserSprite, reticleSprite, labelSprite;
        [SerializeField] Material particleMaterial, lineMaterial;
        [SerializeField] TMP_FontAsset font;
        [SerializeField] AudioClip laserClip, hitClip;

        [Header("Scene")]
        [SerializeField] GalaxyBackground background;
        [SerializeField] TMP_InputField input;
        [SerializeField] TMP_Text scoreText, comboText, statsText, toastText, langText;
        [SerializeField] int meteorCount = 3;

        const float DefenseY = -3.3f, ShipY = -4.25f;

        // EN-VI and JA-VI sample words (Japanese spans Hiragana, Katakana and Kanji). Not a vocabulary scheduler.
        static readonly string[,] Words =
        {
            { "Quả dứa", "Pineapple", "パイナップル" },
            { "Đèn giao thông", "Traffic light", "信号機" },
            { "Thường xuyên", "Frequently", "よく" },
            { "Quả táo", "Apple", "りんご" },
            { "Ăn", "Eat", "食べる" },
            { "Tiếng Nhật", "Japanese", "日本語" },
        };

        readonly List<SandboxMeteor> meteors = new List<SandboxMeteor>();
        readonly List<string> drafts = new List<string>();
        Transform ship;
        SpriteRenderer shield;
        ParticleSystem burst;
        AudioSource audioSource;
        bool japanese;
        int target, score, combo, wordCursor, breaches;
        float toastUntil, statsTimer, frameAcc;
        int frameCount;

        public IReadOnlyList<SandboxMeteor> Meteors => meteors;
        public int Target => target;

        void Start()
        {
            meteorCount = Mathf.Clamp(Mathf.RoundToInt(DevArgs.GetFloat(DevCommandLine.Args, "-g003Meteors", meteorCount)), 1, 60);
            japanese = string.Equals(DevArgs.Get(DevCommandLine.Args, "-g003Lang"), "JA", System.StringComparison.OrdinalIgnoreCase);
            audioSource = gameObject.AddComponent<AudioSource>();
            audioSource.playOnAwake = false;
            audioSource.volume = 0.4f;
            BuildShip();
            BuildDefenseLine();
            burst = BuildBurst();
            for (int i = 0; i < meteorCount; i++) AddMeteor();
            Select(0);
            input.onValidateInput += (t, i, c) => c == '\t' ? '\0' : c;
            input.onValueChanged.AddListener(v => { if (target >= 0) { drafts[target] = v; meteors[target].SetDraft(v); } });
            input.ActivateInputField();
            Input.imeCompositionMode = IMECompositionMode.On;
            RefreshHud();
        }

        void Update()
        {
            bool free = ImeGate.ShortcutAllowed(Input.compositionString);
            if (free && Input.GetKeyDown(KeyCode.Tab)) Select(TargetCycle.Next(target, ResolvedFlags()));
            if (free && (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))) Submit();
            if (Input.GetKeyDown(KeyCode.F1)) { japanese = !japanese; for (int i = 0; i < meteors.Count; i++) Rebind(i); Select(target); RefreshHud(); }
            if (Input.GetKeyDown(KeyCode.F3)) { for (int i = 0; i < 5 && meteors.Count < 60; i++) AddMeteor(); RefreshHud(); }
            if (Input.GetKeyDown(KeyCode.F4)) { RemoveMeteors(5); RefreshHud(); }

            for (int i = 0; i < meteors.Count; i++)
                if (!meteors[i].Resolved && meteors[i].transform.position.y < DefenseY + 0.4f) Breach(i);

            if (toastText.gameObject.activeSelf && Time.unscaledTime > toastUntil) toastText.gameObject.SetActive(false);
            frameAcc += Time.unscaledDeltaTime; frameCount++; statsTimer += Time.unscaledDeltaTime;
            if (statsTimer >= 0.5f)
            {
                float ms = frameAcc / frameCount * 1000f;
                statsText.text = $"{ms:F1} ms · {1000f / ms:F0} FPS · {meteors.Count} thiên thạch";
                statsTimer = frameAcc = 0f; frameCount = 0;
            }
            if (!input.isFocused && free) input.ActivateInputField();
        }

        bool[] ResolvedFlags()
        {
            var r = new bool[meteors.Count];
            for (int i = 0; i < r.Length; i++) r[i] = meteors[i].Resolved;
            return r;
        }

        void Select(int index)
        {
            if (index < 0) return;
            target = index;
            for (int i = 0; i < meteors.Count; i++) meteors[i].SetSelected(i == target);
            input.SetTextWithoutNotify(drafts[target]);
            input.caretPosition = drafts[target].Length;
        }

        void Submit()
        {
            if (target < 0) return;
            var m = meteors[target];
            if (SandboxAnswer.Matches(input.text, m.Expected))
            {
                score += 100; combo++;
                StartCoroutine(Fire(target));
                int next = TargetCycle.Next(target, ResolvedFlags());
                if (next >= 0) Select(next);
                Toast("CHÍNH XÁC · +100", new Color32(131, 226, 177, 255));
            }
            else
            {
                combo = 0;
                Toast($"Chưa đúng với “{m.Clue.text}” · sửa rồi nhấn Enter", new Color32(255, 155, 155, 255));
            }
            RefreshHud();
        }

        IEnumerator Fire(int index)
        {
            var m = meteors[index];
            m.Resolved = true;
            drafts[index] = "";
            Vector3 from = ship.position + Vector3.up * 0.55f, to = m.SpriteRoot.position;
            var laser = new GameObject("Laser").AddComponent<SpriteRenderer>();
            laser.sprite = laserSprite; laser.sortingOrder = 14;
            Vector3 d = to - from;
            laser.transform.position = from + d / 2f;
            laser.transform.rotation = Quaternion.FromToRotation(Vector3.up, d.normalized);
            laser.transform.localScale = new Vector3(1.2f, d.magnitude / laserSprite.bounds.size.y, 1f);
            if (laserClip) audioSource.PlayOneShot(laserClip);
            yield return new WaitForSeconds(0.08f);
            burst.transform.position = to;
            burst.Emit(MotionSettings.Reduced ? 8 : 28);
            if (hitClip) audioSource.PlayOneShot(hitClip, 0.6f);
            StartCoroutine(Popup("+100", to));
            background.Pulse();
            m.gameObject.SetActive(false);
            for (float t = 0; t < 0.15f; t += Time.deltaTime) { laser.color = new Color(1, 1, 1, 1 - t / 0.15f); yield return null; }
            Destroy(laser.gameObject);
            yield return new WaitForSeconds(0.9f);
            Respawn(index, false);
            if (target < 0 || meteors[target].Resolved) Select(index);
        }

        IEnumerator Popup(string text, Vector3 at)
        {
            var t = NewText("ScorePopup", text, 4f, new Color32(248, 223, 158, 255), 40);
            t.transform.position = at + Vector3.up * 0.4f;
            float life = MotionSettings.Reduced ? 0.35f : 0.8f;
            for (float e = 0; e < life; e += Time.deltaTime)
            {
                if (!MotionSettings.Reduced) t.transform.position += Vector3.up * (1.2f * Time.deltaTime);
                t.alpha = 1f - e / life;
                yield return null;
            }
            Destroy(t.gameObject);
        }

        void Breach(int index)
        {
            breaches++;
            combo = 0;
            StartCoroutine(FlashShield());
            Toast($"“{meteors[index].Clue.text}” chạm phòng tuyến (sandbox, không trừ HP)", new Color32(240, 180, 106, 255));
            drafts[index] = "";
            Respawn(index, false);
            if (index == target) Select(index);
            RefreshHud();
        }

        IEnumerator FlashShield()
        {
            shield.enabled = true;
            for (float t = 0; t < 0.45f; t += Time.deltaTime) { shield.color = new Color(1, 1, 1, 0.8f * (1 - t / 0.45f)); yield return null; }
            shield.enabled = false;
        }

        void AddMeteor()
        {
            var root = new GameObject($"Meteor_{meteors.Count}");
            root.transform.SetParent(transform, false);
            var m = root.AddComponent<SandboxMeteor>();
            m.SpriteRoot = new GameObject("SpriteRoot").transform;
            m.SpriteRoot.SetParent(root.transform, false);
            m.Sprite = m.SpriteRoot.gameObject.AddComponent<SpriteRenderer>();
            m.Sprite.sprite = meteorSprites[meteors.Count % meteorSprites.Length];
            m.Sprite.sortingOrder = 10;
            m.SpriteRoot.localScale = Vector3.one * 1.15f;
            m.Reticle = NewSprite("Reticle", root.transform, reticleSprite, 9);
            m.Reticle.transform.localScale = Vector3.one * m.ReticleBase;
            m.Reticle.color = new Color(1, 1, 1, 0.75f);
            m.ClueBg = NewLabelBg("ClueBg", root.transform, new Vector3(0, 1.05f, 0));
            m.Clue = NewText("Clue", "", 3f, new Color32(243, 238, 224, 255), 21);
            m.Clue.transform.SetParent(root.transform, false);
            m.Clue.transform.localPosition = new Vector3(0, 1.05f, 0);
            m.AnswerBg = NewLabelBg("AnswerBg", root.transform, new Vector3(0, -1.0f, 0));
            m.Answer = NewText("Answer", "", 3.4f, new Color32(223, 249, 255, 255), 21);
            m.Answer.transform.SetParent(root.transform, false);
            m.Answer.transform.localPosition = new Vector3(0, -1.0f, 0);
            m.Spin = Random.Range(-35f, 35f);
            meteors.Add(m);
            drafts.Add("");
            Respawn(meteors.Count - 1, true);
        }

        void RemoveMeteors(int n)
        {
            for (int k = 0; k < n && meteors.Count > 1; k++)
            {
                int last = meteors.Count - 1;
                Destroy(meteors[last].gameObject);
                meteors.RemoveAt(last); drafts.RemoveAt(last);
            }
            if (target >= meteors.Count) Select(0);
        }

        /// <summary>Initial spawns are staggered inside the view; later respawns enter from above the top edge.</summary>
        void Respawn(int index, bool initial)
        {
            var cam = Camera.main;
            float halfW = cam.orthographicSize * cam.aspect;
            int lanes = Mathf.Max(3, Mathf.FloorToInt((halfW * 2f - 3f) / 3.2f));
            int lane = (index * 3) % lanes; // 3 is coprime with typical lane counts, so neighbours land far apart
            float x = Mathf.Lerp(-halfW + 2.2f, halfW - 2.2f, lane / (float)(lanes - 1));
            float y = initial ? cam.orthographicSize - 2.4f - (index % 3) * 1.9f - (index / lanes) * 0.9f : cam.orthographicSize + 1.4f;
            meteors[index].transform.position = new Vector3(x, y, 0f);
            meteors[index].FallSpeed = Random.Range(0.35f, 0.5f);
            Rebind(index);
        }

        void Rebind(int index)
        {
            int w = (wordCursor++) % Words.GetLength(0);
            meteors[index].Bind(Words[w, 0], Words[w, japanese ? 2 : 1]);
            meteors[index].SetDraft(drafts[index]);
        }

        void RefreshHud()
        {
            scoreText.text = $"ĐIỂM · SANDBOX\n<size=140%>{score:N0}</size>";
            comboText.text = $"COMBO\n<size=140%>× {combo}</size>";
            langText.text = japanese ? "JA → VI · gõ bằng IME tiếng Nhật" : "EN → VI · gõ từ tiếng Anh";
            input.placeholder.GetComponent<TMP_Text>().text = japanese ? "Nhập bằng IME tiếng Nhật…" : "Gõ từ tiếng Anh…";
        }

        void Toast(string message, Color color)
        {
            toastText.text = message;
            toastText.color = color;
            toastText.gameObject.SetActive(true);
            toastUntil = Time.unscaledTime + 1.6f;
        }

        void BuildShip()
        {
            ship = NewSprite("Ship", transform, shipSprite, 15).transform;
            ship.position = new Vector3(0, ShipY, 0);
            ship.localScale = Vector3.one * 0.9f;
            var flame = NewSprite("Flame", ship, flameSprite, 14);
            flame.transform.localPosition = new Vector3(0, -0.62f, 0);
            flame.transform.localRotation = Quaternion.Euler(0, 0, 180);
            shield = NewSprite("Shield", ship, shieldSprite, 16);
            shield.enabled = false;
        }

        void BuildDefenseLine()
        {
            var line = new GameObject("DefenseLine").AddComponent<LineRenderer>();
            line.transform.SetParent(transform, false);
            line.positionCount = 2;
            float halfW = Camera.main.orthographicSize * Camera.main.aspect;
            line.SetPositions(new[] { new Vector3(-halfW, DefenseY, 0), new Vector3(halfW, DefenseY, 0) });
            line.widthMultiplier = 0.03f;
            line.material = lineMaterial != null ? lineMaterial : particleMaterial;
            line.startColor = line.endColor = new Color32(89, 216, 255, 140);
            line.sortingOrder = 5;
        }

        ParticleSystem BuildBurst()
        {
            var go = new GameObject("DestroyBurst");
            go.transform.SetParent(transform, false);
            var ps = go.AddComponent<ParticleSystem>();
            ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
            var main = ps.main;
            main.loop = false; main.playOnAwake = false;
            main.startLifetime = new ParticleSystem.MinMaxCurve(0.4f, 0.8f);
            main.startSpeed = new ParticleSystem.MinMaxCurve(1.5f, 4f);
            main.startSize = new ParticleSystem.MinMaxCurve(0.08f, 0.22f);
            main.startColor = new ParticleSystem.MinMaxGradient(new Color32(184, 249, 255, 255), new Color32(248, 223, 158, 255));
            main.simulationSpace = ParticleSystemSimulationSpace.World;
            main.maxParticles = 400;
            var emission = ps.emission; emission.rateOverTime = 0;
            var shape = ps.shape; shape.shapeType = ParticleSystemShapeType.Circle; shape.radius = 0.3f;
            var col = ps.colorOverLifetime; col.enabled = true;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(Color.white, 0), new GradientColorKey(Color.white, 1) }, new[] { new GradientAlphaKey(1, 0), new GradientAlphaKey(0, 1) });
            col.color = g;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.material = particleMaterial;
            r.sortingOrder = 30;
            return ps;
        }

        SpriteRenderer NewSprite(string name, Transform parent, Sprite sprite, int order)
        {
            var sr = new GameObject(name).AddComponent<SpriteRenderer>();
            sr.transform.SetParent(parent, false);
            sr.sprite = sprite; sr.sortingOrder = order;
            return sr;
        }

        SpriteRenderer NewLabelBg(string name, Transform parent, Vector3 pos)
        {
            var sr = NewSprite(name, parent, labelSprite, 20);
            sr.drawMode = SpriteDrawMode.Sliced;
            sr.transform.localPosition = pos;
            return sr;
        }

        TextMeshPro NewText(string name, string text, float size, Color color, int order)
        {
            var t = new GameObject(name).AddComponent<TextMeshPro>();
            t.font = font;
            t.text = text;
            t.fontSize = size;
            t.color = color;
            t.alignment = TextAlignmentOptions.Center;
            t.textWrappingMode = TextWrappingModes.NoWrap;
            t.rectTransform.sizeDelta = new Vector2(6f, 1f);
            t.sortingOrder = order;
            return t;
        }
    }
}
