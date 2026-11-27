using MP1.Core;
using UnityEngine;

namespace MP1.Background
{
    /// <summary>
    /// Unity adaptation of game/background/background_idea.md: navy/teal gradient (layer 0), three depth layers of
    /// falling stars with spring-damped pointer parallax, subtle twinkle and rare four-point sparkle stars.
    /// Reusable: drop on an empty GameObject in any scene with an orthographic main camera.
    /// </summary>
    public class GalaxyBackground : MonoBehaviour
    {
        [SerializeField] Sprite sparkleSprite;           // Kenney star1.png (§7 four-point star)
        [SerializeField] int starCount = 480;            // G-003-R1: was 160 (owner asked for a denser sky)
        [SerializeField] StarLayer[] layers = StarLayers.Defaults();
        [SerializeField, Range(0f, 0.05f)] float sparkleRatio = 0.02f; // §7: 1-3%
        [SerializeField] Vector2 sparkleSize = new Vector2(0.24f, 0.32f); // was 0.16-0.22
        [SerializeField] float pointerInfluence = 1f;    // lower during gameplay (UX spec: very small effect in play)
        [SerializeField] int sortingOrder = -100;

        static readonly Color Navy = new Color32(6, 19, 34, 255);
        static readonly Color DeepNavy = new Color32(9, 29, 50, 255);
        static readonly Color Teal = new Color32(18, 72, 86, 255);
        static readonly Color NightBlue = new Color32(16, 43, 72, 255);
        static readonly Color StarBlue = new Color32(184, 249, 255, 255);
        static readonly Color StarGold = new Color32(248, 231, 175, 255);

        Camera cam;
        Star[] stars;
        SpriteRenderer[] renderers;
        Color[] baseColors;
        Transform gradient;
        float top, bottom, left, right, pulseUntil;
        int lastW, lastH;
        Sprite dot;

        public int StarCount => stars?.Length ?? 0;
        public StarLayer[] Layers => layers;
        /// <summary>Number of created stars per layer index, for tests and the R1 report.</summary>
        public int[] CountPerLayer()
        {
            var c = new int[layers.Length];
            for (int i = 0; i < (stars?.Length ?? 0); i++) c[Mathf.Max(0, StarLayers.Pick(i, stars.Length, layers))]++;
            return c;
        }

        void Start()
        {
            cam = Camera.main;
            starCount = Mathf.Clamp(Mathf.RoundToInt(DevArgs.GetFloat(Dev.DevCommandLine.Args, "-g003Stars", starCount)), 1, 2000); // perf comparison only
            dot = CreateDotSprite();
            gradient = CreateGradient().transform;
            CreateStars();
            Fit(true);
        }

        /// <summary>§13: brief, gentle brightening after a correct answer. No full-screen flash.</summary>
        public void Pulse(float seconds = 0.6f) => pulseUntil = Time.time + seconds;

        void Update()
        {
            Fit(false);
            bool moving = !MotionSettings.Reduced;
            float pointer = moving ? StarField.NormalizedPointerX(Input.mousePosition.x, Screen.width) * pointerInfluence : 0f;
            float dt = Time.deltaTime, t = Time.time;
            float boost = Time.time < pulseUntil ? 0.25f : 0f;
            for (int i = 0; i < stars.Length; i++)
            {
                if (moving) StarField.Step(ref stars[i], dt, pointer, top, bottom);
                var c = baseColors[i];
                c.a = Mathf.Clamp01((moving ? StarField.Opacity(stars[i], t) : stars[i].BaseOpacity) + (i % 5 == 0 ? boost : 0f));
                renderers[i].color = c;
                renderers[i].transform.localPosition = new Vector3(stars[i].X, stars[i].Y, 0f);
            }
        }

        void Fit(bool force)
        {
            if (cam == null) return;
            if (!force && Screen.width == lastW && Screen.height == lastH) return;
            lastW = Screen.width; lastH = Screen.height;
            float h = cam.orthographicSize * 2f, w = h * cam.aspect;
            Vector3 c = cam.transform.position;
            top = c.y + h / 2f + 0.2f; bottom = c.y - h / 2f - 0.2f; left = c.x - w / 2f; right = c.x + w / 2f;
            transform.position = new Vector3(0f, 0f, 10f);
            gradient.localPosition = new Vector3(c.x, c.y, 1f);
            gradient.localScale = new Vector3(w / 2.56f * 1.02f, h / 1.44f * 1.02f, 1f); // gradient sprite is 256x144 px at 100 ppu
            if (!force) return;
            for (int i = 0; i < stars.Length; i++)
            {
                stars[i].X = stars[i].BaseX = Random.Range(left, right);
                stars[i].Y = Random.Range(bottom, top);
            }
        }

        void CreateStars()
        {
            stars = new Star[starCount];
            renderers = new SpriteRenderer[starCount];
            baseColors = new Color[starCount];
            for (int i = 0; i < starCount; i++)
            {
                // §4: far / mid / near bands with clearly different size, brightness, speed and parallax.
                var layer = layers[Mathf.Max(0, StarLayers.Pick(i, starCount, layers))];
                bool sparkle = sparkleSprite != null && Random.value < sparkleRatio && layer.Depth.x >= 0.45f; // sparkles never in the far band
                stars[i] = new Star
                {
                    Depth = Random.Range(layer.Depth.x, layer.Depth.y),
                    FallSpeed = Random.Range(layer.FallSpeed.x, layer.FallSpeed.y),
                    Size = sparkle ? Random.Range(sparkleSize.x, sparkleSize.y) : Random.Range(layer.Size.x, layer.Size.y),
                    BaseOpacity = sparkle ? 0.8f : Random.Range(layer.Opacity.x, layer.Opacity.y),
                    TwinkleSpeed = sparkle ? Random.Range(0.4f, 0.8f) : Random.Range(layer.TwinkleSpeed.x, layer.TwinkleSpeed.y),
                    TwinkleOffset = Random.Range(0f, Mathf.PI * 2f),
                    IsSparkle = sparkle
                };
                float depth = stars[i].Depth;
                var go = new GameObject(sparkle ? "Sparkle" : "Star");
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = sparkle ? sparkleSprite : dot;
                sr.sortingOrder = sortingOrder + 1 + Mathf.RoundToInt(depth * 3);
                float size = sr.sprite.bounds.size.x;
                go.transform.localScale = Vector3.one * (stars[i].Size / Mathf.Max(size, 0.0001f));
                baseColors[i] = sparkle || Random.value < 0.08f ? StarGold : StarBlue; // §8: a little pale yellow
                renderers[i] = sr;
            }
        }

        GameObject CreateGradient()
        {
            const int w = 256, h = 144;
            var tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { wrapMode = TextureWrapMode.Clamp, filterMode = FilterMode.Bilinear, name = "GalaxyGradient" };
            var px = new Color[w * h];
            for (int y = 0; y < h; y++)
            for (int x = 0; x < w; x++)
            {
                float u = x / (float)(w - 1), v = y / (float)(h - 1);
                Color c = Color.Lerp(Navy, DeepNavy, v * 0.6f + u * 0.2f);
                float teal = Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(0.15f, 0.12f)) / 0.55f);
                float blue = Mathf.Clamp01(1f - Vector2.Distance(new Vector2(u, v), new Vector2(0.85f, 0.85f)) / 0.6f);
                c = Color.Lerp(c, Teal, teal * teal * 0.8f);
                c = Color.Lerp(c, NightBlue, blue * blue * 0.7f);
                px[y * w + x] = c;
            }
            tex.SetPixels(px);
            tex.Apply(false, true);
            var go = new GameObject("Layer0_Gradient");
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(tex, new Rect(0, 0, w, h), new Vector2(0.5f, 0.5f), 100f);
            sr.sortingOrder = sortingOrder;
            return go;
        }

        static Sprite CreateDotSprite()
        {
            const int s = 32;
            var tex = new Texture2D(s, s, TextureFormat.RGBA32, false) { filterMode = FilterMode.Bilinear, name = "StarDot" };
            for (int y = 0; y < s; y++)
            for (int x = 0; x < s; x++)
            {
                float d = Vector2.Distance(new Vector2(x + 0.5f, y + 0.5f), new Vector2(s / 2f, s / 2f)) / (s / 2f);
                float a = Mathf.Clamp01(1f - d);
                tex.SetPixel(x, y, new Color(1, 1, 1, a * a));
            }
            tex.Apply(false, true);
            return Sprite.Create(tex, new Rect(0, 0, s, s), new Vector2(0.5f, 0.5f), 100f);
        }
    }
}
