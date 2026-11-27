using System.Collections.Generic;
using System.IO;
using MP1.Background;
using MP1.Dev;
using MP1.Library;
using MP1.Media;
using MP1.Sandbox;
using MP1.Typography;
using MP1.UI;
using TMPro;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.SceneManagement;
using UnityEngine.TextCore.LowLevel;
using UnityEngine.UI;

namespace MP1.EditorTools
{
    /// <summary>
    /// Regenerates the G-003 foundation from code: sprite import settings, TMP font assets, particle material and
    /// the four scenes. Scenes are OVERWRITTEN on each run; edit this builder, not the scenes, while G-003 lasts.
    /// Menu: Tools/MP1/Rebuild G-003 Foundation. CLI: unity command script eval "MP1.EditorTools.G003Builder.BuildAll()".
    /// </summary>
    public static class G003Builder
    {
        const string Art = "Assets/Art/Sprites/";
        const string Fonts = "Assets/Fonts/";
        public static readonly string[] Scenes = { "MainMenu", "VocabularyLibrary", "VocabularyPreview", "GameSetup", "MeteorDefense", "TypographyInput", "GameplaySandbox", "MediaProbe" };

        static readonly Color Panel = new Color32(13, 36, 54, 235);
        static readonly Color Text = new Color32(243, 247, 255, 255);
        static readonly Color Muted = new Color32(184, 201, 213, 255);
        static readonly Color Accent = new Color32(89, 216, 255, 255);
        static readonly Color Warn = new Color32(242, 212, 167, 255);
        static readonly Color ButtonText = new Color32(6, 36, 58, 255);

        static TMP_FontAsset medium, regular, sans;

        [MenuItem("Tools/MP1/Rebuild G-003 Foundation")]
        public static string BuildAll()
        {
            ConfigureImports();
            BuildFonts();
            var particleMat = BuildParticleMaterial();
            BuildMainMenu();
            BuildTypography();
            BuildSandbox(particleMat);
            BuildMediaProbe();
            BuildLibrary();
            BuildPreview();
            BuildGameSetup();
            BuildMeteorDefense(particleMat);
            ConfigureProject();
            AssetDatabase.SaveAssets();
            return "G-003 foundation rebuilt: " + string.Join(", ", Scenes);
        }

        // ---------- assets ----------

        static void ConfigureImports()
        {
            var borders = new Dictionary<string, Vector4>
            {
                { "UI/buttonBlue.png", new Vector4(10, 10, 10, 10) },
                { "UI/panel_rectangle.png", new Vector4(16, 16, 16, 16) },
            };
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { "Assets/Art/Sprites" }))
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                var ti = (TextureImporter)AssetImporter.GetAtPath(path);
                ti.textureType = TextureImporterType.Sprite;
                ti.spriteImportMode = SpriteImportMode.Single;
                ti.spritePixelsPerUnit = 100;           // 1 px = 1/100 unit; camera ortho size 5.4 shows 1080 px tall
                ti.filterMode = FilterMode.Bilinear;     // smooth vector-style Kenney art, not pixel art
                ti.textureCompression = TextureImporterCompression.Uncompressed; // tiny sprites, keep edges crisp
                ti.alphaIsTransparency = true;
                ti.mipmapEnabled = false;
                ti.wrapMode = TextureWrapMode.Clamp;
                var s = new TextureImporterSettings();
                ti.ReadTextureSettings(s);
                s.spriteMeshType = SpriteMeshType.FullRect;
                s.spriteAlignment = (int)SpriteAlignment.Center;
                ti.SetTextureSettings(s);
                string key = path.Substring(Art.Length);
                ti.spriteBorder = borders.TryGetValue(key, out var b) ? b : Vector4.zero;
                ti.SaveAndReimport();
            }
        }

        static void BuildFonts()
        {
            regular = FontAsset("NotoSansJP-Regular", null);
            medium = FontAsset("NotoSansJP-Medium", null);
            sans = FontAsset("NotoSans-Regular", regular); // EN/VI face with Japanese fallback
        }

        /// <summary>Dynamic SDF font asset: glyphs are added on demand, so imported vocabulary never needs a pre-baked CJK atlas.</summary>
        static TMP_FontAsset FontAsset(string file, TMP_FontAsset fallback)
        {
            string path = Fonts + file + " SDF.asset";
            var fa = AssetDatabase.LoadAssetAtPath<TMP_FontAsset>(path);
            if (fa == null)
            {
                var font = AssetDatabase.LoadAssetAtPath<Font>(Fonts + file + ".ttf");
                fa = TMP_FontAsset.CreateFontAsset(font, 72, 7, GlyphRenderMode.SDFAA, 1024, 1024, AtlasPopulationMode.Dynamic, true);
                fa.name = file + " SDF";
                AssetDatabase.CreateAsset(fa, path);
                fa.atlasTextures[0].name = file + " Atlas";
                AssetDatabase.AddObjectToAsset(fa.atlasTextures[0], fa);
                fa.material.name = file + " Material";
                AssetDatabase.AddObjectToAsset(fa.material, fa);
            }
            var so = new SerializedObject(fa);
            var clear = so.FindProperty("m_ClearDynamicDataOnBuild");
            if (clear != null) { clear.boolValue = true; so.ApplyModifiedPropertiesWithoutUndo(); }
            fa.fallbackFontAssetTable = fallback != null ? new List<TMP_FontAsset> { fallback } : new List<TMP_FontAsset>();
            EditorUtility.SetDirty(fa);
            return fa;
        }

        static Material BuildParticleMaterial()
        {
            const string path = "Assets/Materials/Particle_Star.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Sprites/Default")); AssetDatabase.CreateAsset(mat, path); }
            mat.mainTexture = AssetDatabase.LoadAssetAtPath<Texture2D>(Art + "VFX/star1.png");
            EditorUtility.SetDirty(mat);
            return mat;
        }

        static Material BuildLineMaterial()
        {
            const string path = "Assets/Materials/Line_Plain.mat";
            var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (mat == null) { mat = new Material(Shader.Find("Sprites/Default")); AssetDatabase.CreateAsset(mat, path); }
            return mat;
        }

        static Sprite S(string rel) => AssetDatabase.LoadAssetAtPath<Sprite>(Art + rel);

        static void ConfigureProject()
        {
            var list = new List<EditorBuildSettingsScene>();
            foreach (var s in Scenes) list.Add(new EditorBuildSettingsScene($"Assets/Scenes/{s}.unity", true));
            EditorBuildSettings.scenes = list.ToArray();
            PlayerSettings.productName = "Word Orbit G-003 Prototype";
            PlayerSettings.companyName = "MultimediaProject1";
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1600;
            PlayerSettings.defaultScreenHeight = 900;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.runInBackground = true;
            EditorSettings.defaultBehaviorMode = EditorBehaviorMode.Mode2D;
        }

        // ---------- scene scaffolding ----------

        static Scene NewScene(string name, bool escapeToMenu, float pointerInfluence)
        {
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var cam = new GameObject("Main Camera", typeof(Camera), typeof(AudioListener)).GetComponent<Camera>();
            cam.tag = "MainCamera";
            cam.orthographic = true;
            cam.orthographicSize = 5.4f;
            cam.transform.position = new Vector3(0, 0, -10);
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color32(6, 19, 34, 255);

            var bg = new GameObject("GalaxyBackground").AddComponent<GalaxyBackground>();
            Set(bg, "sparkleSprite", S("VFX/star1.png"));
            Set(bg, "pointerInfluence", pointerInfluence);

            var nav = new GameObject("SceneNav").AddComponent<SceneNav>();
            Set(nav, "escapeToMenu", escapeToMenu);
            new GameObject("EventSystem", typeof(EventSystem), typeof(StandaloneInputModule));
            return scene;
        }

        static void Save(Scene scene, string name)
        {
            Directory.CreateDirectory("Assets/Scenes");
            EditorSceneManager.SaveScene(scene, $"Assets/Scenes/{name}.unity");
        }

        static RectTransform Canvas()
        {
            var go = new GameObject("Canvas", typeof(Canvas), typeof(CanvasScaler), typeof(GraphicRaycaster));
            go.GetComponent<Canvas>().renderMode = RenderMode.ScreenSpaceOverlay;
            var scaler = go.GetComponent<CanvasScaler>();
            scaler.uiScaleMode = CanvasScaler.ScaleMode.ScaleWithScreenSize;
            scaler.referenceResolution = new Vector2(1920, 1080);
            scaler.screenMatchMode = CanvasScaler.ScreenMatchMode.MatchWidthOrHeight;
            scaler.matchWidthOrHeight = 0.5f;
            return (RectTransform)go.transform;
        }

        static RectTransform Rect(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, Vector2? pivot = null)
        {
            var rt = (RectTransform)new GameObject(name, typeof(RectTransform)).transform;
            rt.SetParent(parent, false);
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = pivot ?? anchor;
            rt.anchoredPosition = pos;
            rt.sizeDelta = size;
            return rt;
        }

        static Image PanelImage(string name, Transform parent, Vector2 anchor, Vector2 pos, Vector2 size)
        {
            var img = Rect(name, parent, anchor, pos, size).gameObject.AddComponent<Image>();
            img.sprite = S("UI/panel_rectangle.png");
            img.type = Image.Type.Sliced;
            img.color = Panel;
            return img;
        }

        static TextMeshProUGUI Label(string name, Transform parent, string text, float size, Color color, TMP_FontAsset font = null,
            TextAlignmentOptions align = TextAlignmentOptions.TopLeft)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var t = go.AddComponent<TextMeshProUGUI>();
            t.font = font ?? medium;
            t.text = text; t.fontSize = size; t.color = color; t.alignment = align;
            t.textWrappingMode = TextWrappingModes.Normal;
            t.raycastTarget = false;
            return t;
        }

        static Button MakeButton(string name, Transform parent, string label, bool interactable, float height = 64)
        {
            var go = new GameObject(name, typeof(RectTransform), typeof(Image), typeof(Button), typeof(LayoutElement));
            go.transform.SetParent(parent, false);
            go.GetComponent<LayoutElement>().minHeight = height;
            var img = go.GetComponent<Image>();
            img.sprite = S("UI/buttonBlue.png");
            img.type = Image.Type.Sliced;
            var btn = go.GetComponent<Button>();
            btn.interactable = interactable;
            var cb = btn.colors;
            cb.normalColor = Color.white;
            cb.highlightedColor = new Color32(214, 245, 255, 255);
            cb.selectedColor = new Color32(150, 228, 255, 255);   // keyboard focus is clearly visible
            cb.pressedColor = new Color32(120, 205, 236, 255);
            cb.disabledColor = new Color32(120, 136, 150, 150);
            cb.fadeDuration = 0.08f;
            btn.colors = cb;
            var t = Label("Label", go.transform, label, 26, interactable ? ButtonText : new Color32(30, 50, 66, 255), medium, TextAlignmentOptions.Center);
            var rt = t.rectTransform; rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = new Vector2(16, 0); rt.offsetMax = new Vector2(-16, 0);
            return btn;
        }

        static VerticalLayoutGroup Column(Transform parent, float spacing)
        {
            var v = parent.gameObject.AddComponent<VerticalLayoutGroup>();
            v.spacing = spacing; v.padding = new RectOffset(28, 28, 28, 28);
            v.childControlHeight = true; v.childControlWidth = true; v.childForceExpandHeight = false; v.childForceExpandWidth = true;
            return v;
        }

        static TMP_InputField InputField(Transform parent, Vector2 anchor, Vector2 pos, Vector2 size, string placeholder)
        {
            var go = TMP_DefaultControls.CreateInputField(new TMP_DefaultControls.Resources());
            go.name = "AnswerInput";
            var rt = (RectTransform)go.transform;
            rt.SetParent(parent, false);
            rt.anchorMin = rt.anchorMax = rt.pivot = anchor; rt.anchoredPosition = pos; rt.sizeDelta = size;
            var bgImg = go.GetComponent<Image>(); bgImg.sprite = S("UI/panel_rectangle.png"); bgImg.type = Image.Type.Sliced; bgImg.color = new Color32(22, 57, 80, 255);
            var field = go.GetComponent<TMP_InputField>();
            field.fontAsset = medium;
            field.pointSize = 30;
            field.textComponent.color = Text;
            field.caretColor = Accent;
            field.customCaretColor = true;
            field.selectionColor = new Color32(89, 216, 255, 90);
            var ph = (TMP_Text)field.placeholder;
            ph.text = placeholder; ph.font = medium; ph.fontSize = 30; ph.color = new Color32(180, 205, 214, 255); // >= 4.5:1 on the field
            field.textComponent.font = medium;
            return field;
        }

        static void Set(Object target, string field, object value)
        {
            var so = new SerializedObject(target);
            var p = so.FindProperty(field);
            switch (value)
            {
                case Object o: p.objectReferenceValue = o; break;
                case bool b: p.boolValue = b; break;
                case float f: p.floatValue = f; break;
                case int i: p.intValue = i; break;
                case string str: p.stringValue = str; break;
                case Object[] arr:
                    p.arraySize = arr.Length;
                    for (int k = 0; k < arr.Length; k++) p.GetArrayElementAtIndex(k).objectReferenceValue = arr[k];
                    break;
            }
            so.ApplyModifiedPropertiesWithoutUndo();
        }

        /// <summary>
        /// G-003-R1 owner requirement: every secondary screen shows a visible Back button (arrow + text) at the same
        /// top-left spot. It calls SceneNav.GoBack, the same target as Esc.
        /// </summary>
        static Button BackButton(Transform canvas)
        {
            var nav = Object.FindFirstObjectByType<SceneNav>();
            var btn = MakeButton("BackButton", canvas, "←  Quay lại", true, 56);
            var rt = (RectTransform)btn.transform;
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = new Vector2(28, -16);
            rt.sizeDelta = new Vector2(220, 56);
            UnityEditor.Events.UnityEventTools.AddPersistentListener(btn.onClick, nav.GoBack);
            return btn;
        }

        static void Tag(Transform canvas, string text)
        {
            var t = Label("PrototypeTag", canvas, text, 20, Warn, medium, TextAlignmentOptions.Center);
            var rt = t.rectTransform; rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0.5f, 1f); rt.anchoredPosition = new Vector2(0, -14); rt.sizeDelta = new Vector2(1100, 34);
        }

        // ---------- scenes ----------

        static void BuildMainMenu()
        {
            var scene = NewScene("MainMenu", false, 1f);
            new GameObject("DevCommandLine").AddComponent<DevCommandLine>();
            var canvas = Canvas();
            Tag(canvas, "BẢN DỰNG KỸ THUẬT G-003 · giao diện tạm, chưa được duyệt");

            var title = Label("Title", canvas, "WORD <color=#84DCE3>ORBIT</color>", 112, Text, medium);
            var trt = title.rectTransform; trt.anchorMin = trt.anchorMax = trt.pivot = new Vector2(0, 1); trt.anchoredPosition = new Vector2(150, -150); trt.sizeDelta = new Vector2(900, 140);
            title.characterSpacing = 6;
            var sub = Label("Subtitle", canvas, "Tên tạm · Học từ vựng English / 日本語 → Tiếng Việt giữa dải ngân hà.", 28, Muted, regular);
            var srt = sub.rectTransform; srt.anchorMin = srt.anchorMax = srt.pivot = new Vector2(0, 1); srt.anchoredPosition = new Vector2(154, -300); srt.sizeDelta = new Vector2(900, 80);

            var menu = PanelImage("ProductMenu", canvas, new Vector2(0, 0.5f), new Vector2(150, -120), new Vector2(560, 470));
            menu.rectTransform.pivot = new Vector2(0, 0.5f);
            Column(menu.transform, 14);
            var play = MakeButton("PlayGame", menu.transform, "Chơi Meteor Defense", true);
            var library = MakeButton("Library", menu.transform, "Thư viện từ vựng", true);
            MakeButton("Settings", menu.transform, "Cài đặt · chưa có", false);
            var exit = MakeButton("Exit", menu.transform, "Thoát", true);
            var note = Label("Unavailable", menu.transform, "Các mục “chưa có” thuộc giai đoạn sau (G-006+).", 20, Muted, regular);
            note.gameObject.AddComponent<LayoutElement>().minHeight = 30;

            var dev = PanelImage("TechTests", canvas, new Vector2(1, 0.5f), new Vector2(-150, -40), new Vector2(620, 460));
            dev.rectTransform.pivot = new Vector2(1, 0.5f);
            Column(dev.transform, 14);
            var head = Label("Heading", dev.transform, "Kiểm thử kỹ thuật G-003", 34, Text, medium);
            head.gameObject.AddComponent<LayoutElement>().minHeight = 46;
            var typo = MakeButton("TypographyInput", dev.transform, "Chữ đa ngôn ngữ & nhập liệu", true);
            var sandbox = MakeButton("GameplaySandbox", dev.transform, "Sandbox gameplay (không phải game thật)", true);
            var media = MakeButton("MediaProbe", dev.transform, "Ảnh & âm thanh từ Content Pack thử", true);
            var help = Label("Help", dev.transform, "↑ ↓ / Tab chọn · Enter bấm · Esc quay về menu · F2 giảm chuyển động", 20, Muted, regular);
            help.gameObject.AddComponent<LayoutElement>().minHeight = 56;

            var ctrl = new GameObject("MainMenuController").AddComponent<MainMenuController>();
            Set(ctrl, "playButton", play); Set(ctrl, "libraryButton", library); Set(ctrl, "typographyButton", typo); Set(ctrl, "sandboxButton", sandbox); Set(ctrl, "mediaButton", media); Set(ctrl, "exitButton", exit);
            Save(scene, "MainMenu");
        }

        const string Samples =
            "Pineapple · Traffic light · Frequently\n" +
            "Quả dứa · Đèn giao thông · Tiếng Việt · Thường xuyên\n" +
            "ă â đ ê ô ơ ư  Ă Â Đ Ê Ô Ơ Ư\n" +
            "ắ ằ ẳ ẵ ặ ế ễ ệ ớ ờ ở ỡ ợ\n" +
            "りんご · パイナップル · 信号機 · 日本語 · 食べる\n" +
            "Score · Điểm · スコア\n" +
            "<size=80%>Dài: traffic light at a very busy intersection — đèn giao thông ở ngã tư đông đúc — 交差点の信号機と横断歩道</size>\n" +
            "<size=80%>Thiếu glyph (cố ý): 𠮷 😀</size>";

        static void BuildTypography()
        {
            var scene = NewScene("TypographyInput", true, 0.4f);
            var canvas = Canvas();
            Tag(canvas, "G-003.5 · Chữ đa ngôn ngữ & nhập liệu");
            BackButton(canvas);
            var fonts = new[] { (regular, "Noto Sans JP Regular"), (medium, "Noto Sans JP Medium"), (sans, "Noto Sans + fallback Noto Sans JP") };
            for (int i = 0; i < 3; i++)
            {
                var p = PanelImage($"Font_{i}", canvas, new Vector2(0.5f, 1), new Vector2(-610 + i * 610, -90), new Vector2(580, 536));
                p.rectTransform.pivot = new Vector2(0.5f, 1);
                var h = Label("FontName", p.transform, fonts[i].Item2, 24, Accent, medium);
                Stretch(h.rectTransform, 24, 18, 24, 486);
                var body = Label("Samples", p.transform, Samples, 23, Text, fonts[i].Item1);
                body.lineSpacing = 4;
                body.overflowMode = TextOverflowModes.Ellipsis; // never spill into the input panel
                Stretch(body.rectTransform, 24, 62, 24, 18);
            }

            var ip = PanelImage("InputPanel", canvas, new Vector2(0.5f, 0), new Vector2(0, 24), new Vector2(1820, 400));
            ip.rectTransform.pivot = new Vector2(0.5f, 0);
            var field = InputField(ip.transform, new Vector2(0, 1), new Vector2(30, -30), new Vector2(880, 64), "Gõ English hoặc bật IME tiếng Nhật…");
            ((RectTransform)field.transform).pivot = new Vector2(0, 1);
            var committed = Label("Committed", ip.transform, "", 26, Text, medium); Place(committed.rectTransform, 30, -110, 880, 40);
            var comp = Label("Composition", ip.transform, "", 26, Warn, medium); Place(comp.rectTransform, 30, -152, 880, 40);
            var log = Label("KeyLog", ip.transform, "", 20, Muted, regular); Place(log.rectTransform, 30, -200, 880, 190);
            var steps = Label("ManualSteps", ip.transform,
                "<b>Kiểm tra IME thủ công (Windows):</b>\n1. Thêm bàn phím Microsoft IME tiếng Nhật, bấm vào ô nhập.\n2. Alt+` hoặc phím 半角/全角 để bật chế độ あ.\n3. Gõ <i>ringo</i> → thấy りんご ở dòng “IME đang soạn”, ô “Đã xác nhận” chưa đổi.\n4. Space để đổi sang リンゴ / 林檎; trong lúc soạn bấm Tab và Esc → log ghi “IME đang soạn”, không đổi mục tiêu, không thoát.\n5. Enter để chốt → chữ chuyển sang “Đã xác nhận”. Enter lần nữa → log “xác nhận”.\n6. Thử thêm: shingouki → 信号機, taberu → 食べる, painappuru → パイナップル.",
                20, Text, regular);
            Place(steps.rectTransform, 950, -22, 840, 280);
            var atlas = Label("AtlasInfo", ip.transform, "", 18, Muted, regular); Place(atlas.rectTransform, 950, -300, 840, 90);

            var probe = new GameObject("InputProbe").AddComponent<InputProbe>();
            Set(probe, "field", field); Set(probe, "committedText", committed); Set(probe, "compositionText", comp);
            Set(probe, "keyLog", log); Set(probe, "atlasInfo", atlas);
            Set(probe, "fonts", new Object[] { regular, medium, sans });
            Save(scene, "TypographyInput");
        }

        static void BuildSandbox(Material particleMat)
        {
            var scene = NewScene("GameplaySandbox", true, 0.25f);
            var canvas = Canvas();
            Tag(canvas, "SANDBOX KỸ THUẬT G-003 · không phải Meteor Defense chính thức");
            BackButton(canvas);

            var hud = Rect("HUD", canvas, new Vector2(0.5f, 1), new Vector2(0, 0), new Vector2(1920, 120), new Vector2(0.5f, 1));
            var hpLabel = Label("HPLabel", hud, "HP / PHÒNG TUYẾN", 18, Muted, medium); Place(hpLabel.rectTransform, 290, -24, 260, 26);
            for (int i = 0; i < 4; i++)
            {
                var icon = Rect($"HP_{i}", hud, new Vector2(0, 1), new Vector2(292 + i * 46, -56), new Vector2(38, 30), new Vector2(0, 1)).gameObject.AddComponent<Image>();
                icon.sprite = S("UI/playerLife2_blue.png"); icon.preserveAspect = true; icon.raycastTarget = false;
            }
            var score = Label("Score", hud, "", 20, Text, medium, TextAlignmentOptions.TopRight); PlaceRight(score.rectTransform, -330, -36, 260, 80);
            var combo = Label("Combo", hud, "", 20, Text, medium, TextAlignmentOptions.TopRight); PlaceRight(combo.rectTransform, -150, -36, 160, 80);
            var stats = Label("Stats", hud, "", 18, Muted, regular, TextAlignmentOptions.TopRight); PlaceRight(stats.rectTransform, -50, -110, 520, 30);

            var console = PanelImage("AnswerConsole", canvas, new Vector2(0, 0), new Vector2(40, 30), new Vector2(760, 150));
            console.rectTransform.pivot = Vector2.zero;
            var lang = Label("Lang", console.transform, "", 20, Accent, medium); Place(lang.rectTransform, 26, -16, 700, 30);
            var field = InputField(console.transform, new Vector2(0, 0), new Vector2(24, 24), new Vector2(712, 64), "Gõ từ tiếng Anh…");
            ((RectTransform)field.transform).pivot = Vector2.zero;
            var help = Label("Help", canvas, "Tab đổi mục tiêu · Enter bắn · F1 đổi EN/JA · F2 giảm chuyển động · F3/F4 ± 5 thiên thạch · Esc về menu", 20, Muted, regular, TextAlignmentOptions.BottomRight);
            var hrt = help.rectTransform; hrt.anchorMin = hrt.anchorMax = hrt.pivot = new Vector2(1, 0); hrt.anchoredPosition = new Vector2(-40, 34); hrt.sizeDelta = new Vector2(700, 60);
            var toast = Label("Toast", canvas, "", 28, Text, medium, TextAlignmentOptions.Center);
            var tr = toast.rectTransform; tr.anchorMin = tr.anchorMax = tr.pivot = new Vector2(0.5f, 0); tr.anchoredPosition = new Vector2(0, 260); tr.sizeDelta = new Vector2(1100, 44);
            toast.gameObject.SetActive(false);

            var ctrl = new GameObject("SandboxController").AddComponent<SandboxController>();
            Set(ctrl, "meteorSprites", new Object[] { S("Meteors/meteorGrey_big1.png"), S("Meteors/meteorBrown_big1.png"), S("Meteors/meteorGrey_big2.png") });
            Set(ctrl, "shipSprite", S("Ship/playerShip2_blue.png")); Set(ctrl, "flameSprite", S("VFX/fire00.png"));
            Set(ctrl, "shieldSprite", S("VFX/shield1.png")); Set(ctrl, "laserSprite", S("VFX/laserBlue01.png"));
            Set(ctrl, "reticleSprite", S("UI/crosshair_color_a_double.png")); Set(ctrl, "labelSprite", S("UI/panel_rectangle.png"));
            Set(ctrl, "particleMaterial", particleMat); Set(ctrl, "lineMaterial", BuildLineMaterial()); Set(ctrl, "font", medium);
            Set(ctrl, "laserClip", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/SFX/sfx_laser1.ogg"));
            Set(ctrl, "hitClip", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/SFX/sfx_zap.ogg"));
            Set(ctrl, "background", Object.FindFirstObjectByType<GalaxyBackground>());
            Set(ctrl, "input", field); Set(ctrl, "scoreText", score); Set(ctrl, "comboText", combo);
            Set(ctrl, "statsText", stats); Set(ctrl, "toastText", toast); Set(ctrl, "langText", lang);
            Save(scene, "GameplaySandbox");
        }

        static void BuildMediaProbe()
        {
            var scene = NewScene("MediaProbe", true, 0.4f);
            var canvas = Canvas();
            Tag(canvas, "G-003.8 · Media từ Content Pack thử nghiệm (needs_review, test_only)");
            BackButton(canvas);
            var frame = PanelImage("ImageFrame", canvas, new Vector2(0, 0.5f), new Vector2(120, 0), new Vector2(760, 760));
            frame.rectTransform.pivot = new Vector2(0, 0.5f);
            frame.color = new Color32(233, 239, 237, 255);
            var raw = Rect("Image", frame.transform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(720, 720)).gameObject.AddComponent<RawImage>();
            var fit = raw.gameObject.AddComponent<AspectRatioFitter>();
            fit.aspectMode = AspectRatioFitter.AspectMode.FitInParent;
            var right = PanelImage("Controls", canvas, new Vector2(1, 0.5f), new Vector2(-120, 0), new Vector2(860, 760));
            right.rectTransform.pivot = new Vector2(1, 0.5f);
            Column(right.transform, 16);
            var info = Label("ItemInfo", right.transform, "", 30, Text, medium); info.gameObject.AddComponent<LayoutElement>().minHeight = 200;
            var en = MakeButton("PlayEnglish", right.transform, "Phát âm English", true);
            var ja = MakeButton("PlayJapanese", right.transform, "Phát âm 日本語", true);
            var missing = MakeButton("MissingFile", right.transform, "Thử: tệp ảnh không tồn tại", true);
            var invalid = MakeButton("InvalidPath", right.transform, "Thử: đường dẫn ra ngoài pack", true);
            var status = Label("Status", right.transform, "", 24, Muted, regular); status.gameObject.AddComponent<LayoutElement>().minHeight = 90;
            var note = Label("Note", right.transform, "Đọc trực tiếp từ reports/EXCEL_15_SMOKE/…/content_pack_v46. Không sao chép vào Assets, không đổi trạng thái needs_review. Không phải Content Pack runtime (G-004).", 18, Muted, regular);
            note.gameObject.AddComponent<LayoutElement>().minHeight = 70;
            var probe = new GameObject("MediaProbe").AddComponent<MediaProbe>();
            Set(probe, "image", raw); Set(probe, "itemInfo", info); Set(probe, "status", status);
            Set(probe, "playEnglish", en); Set(probe, "playJapanese", ja); Set(probe, "missingFile", missing); Set(probe, "invalidPath", invalid);
            Save(scene, "MediaProbe");
        }

        static void BuildLibrary()
        {
            var scene = NewScene("VocabularyLibrary", true, 0.4f);
            var canvas = Canvas();
            Tag(canvas, "G-004 · Thư viện từ vựng · dữ liệu thật từ Content Pack");
            BackButton(canvas);
            var title = Label("Title", canvas, "Thư viện từ vựng", 44, Text, medium);
            Place(title.rectTransform, 280, -14, 900, 60);

            // Left: discovered packs
            var left = PanelImage("PackList", canvas, new Vector2(0, 1), new Vector2(40, -96), new Vector2(980, 950));
            left.rectTransform.pivot = new Vector2(0, 1);
            var state = Label("ListState", left.transform, "", 22, Muted, regular); Place(state.rectTransform, 26, -18, 930, 60);
            var viewport = Rect("Viewport", left.transform, new Vector2(0, 1), new Vector2(20, -84), new Vector2(940, 640), new Vector2(0, 1));
            viewport.gameObject.AddComponent<RectMask2D>();
            var content = Rect("Content", viewport, new Vector2(0, 1), Vector2.zero, new Vector2(940, 0), new Vector2(0, 1));
            content.anchorMin = new Vector2(0, 1); content.anchorMax = new Vector2(1, 1);
            var vlg = content.gameObject.AddComponent<VerticalLayoutGroup>();
            vlg.spacing = 10; vlg.childControlHeight = true; vlg.childControlWidth = true; vlg.childForceExpandHeight = false; vlg.childForceExpandWidth = true;
            content.gameObject.AddComponent<ContentSizeFitter>().verticalFit = ContentSizeFitter.FitMode.PreferredSize;
            var scroll = viewport.gameObject.AddComponent<ScrollRect>();
            scroll.content = content; scroll.horizontal = false; scroll.viewport = viewport; scroll.scrollSensitivity = 40; scroll.movementType = ScrollRect.MovementType.Clamped;
            var row = MakeButton("RowTemplate", content, "", true, 96);
            row.image.color = VocabularyLibraryController.RowColor;  // dark rows so status colours stay readable
            var rowColors = row.colors; rowColors.highlightedColor = new Color32(205, 235, 255, 255); rowColors.selectedColor = new Color32(185, 230, 255, 255); row.colors = rowColors;
            var rowLabel = row.GetComponentInChildren<TextMeshProUGUI>();
            rowLabel.color = Text;
            rowLabel.alignment = TextAlignmentOptions.Left; rowLabel.fontSize = 22; rowLabel.textWrappingMode = TextWrappingModes.NoWrap; rowLabel.overflowMode = TextOverflowModes.Ellipsis;
            rowLabel.rectTransform.offsetMin = new Vector2(20, 4); rowLabel.rectTransform.offsetMax = new Vector2(-20, -4);
            var path = InputField(left.transform, new Vector2(0, 1), new Vector2(26, -742), new Vector2(620, 60), "Đường dẫn thư mục hoặc tệp content_pack*.json…");
            ((RectTransform)path.transform).pivot = new Vector2(0, 1);
            path.pointSize = 22; ((TMP_Text)path.placeholder).fontSize = 22;
            var open = MakeButton("OpenPath", left.transform, "Mở pack", true, 60);
            Place((RectTransform)open.transform, 662, -742, 140, 60);
            var rescan = MakeButton("Rescan", left.transform, "Quét lại", true, 60);
            Place((RectTransform)rescan.transform, 814, -742, 140, 60);
            var drop = Label("DropHint", left.transform, "", 18, Muted, regular); Place(drop.rectTransform, 26, -816, 930, 60);
            var import = MakeButton("ImportExcel", left.transform, "Import Excel · dự kiến", false, 52);
            Place((RectTransform)import.transform, 26, -880, 440, 52);
            var showAll = MakeButton("ShowAllPacks", left.transform, "Hiện cả pack lỗi", true, 52);
            Place((RectTransform)showAll.transform, 480, -880, 474, 52);
            showAll.GetComponentInChildren<TextMeshProUGUI>().fontSize = 22;

            // Right: selected pack
            var right = PanelImage("PackDetail", canvas, new Vector2(1, 1), new Vector2(-40, -96), new Vector2(820, 950));
            right.rectTransform.pivot = new Vector2(1, 1);
            var dTitle = Label("DetailTitle", right.transform, "", 26, Accent, medium); Place(dTitle.rectTransform, 28, -22, 770, 40);
            var dStatus = Label("DetailStatus", right.transform, "", 28, Text, medium); Place(dStatus.rectTransform, 28, -70, 770, 44);
            var dCounts = Label("DetailCounts", right.transform, "", 24, Text, regular); dCounts.lineSpacing = 10; Place(dCounts.rectTransform, 28, -126, 770, 270);
            var dMeta = Label("DetailMeta", right.transform, "", 18, Muted, regular); Place(dMeta.rectTransform, 28, -404, 770, 110);
            var modes = Label("ModesHeading", right.transform, "Xem từ vựng (chỉ mục ready, media đã kiểm tra):", 22, Muted, medium); Place(modes.rectTransform, 28, -500, 770, 34);
            var en = MakeButton("ModeEnglish", right.transform, "English → Tiếng Việt", false, 56); Place((RectTransform)en.transform, 28, -536, 764, 56);
            var ja = MakeButton("ModeJapanese", right.transform, "日本語 → Tiếng Việt", false, 56); Place((RectTransform)ja.transform, 28, -600, 764, 56);
            var playHead = Label("PlayHeading", right.transform, "Chơi Meteor Defense:", 22, Muted, medium); Place(playHead.rectTransform, 28, -668, 770, 34);
            var playEn = MakeButton("PlayEnglish", right.transform, "▶ Chơi EN–VI", false, 60); Place((RectTransform)playEn.transform, 28, -704, 374, 60);
            var playJa = MakeButton("PlayJapanese", right.transform, "▶ Chơi JA–VI", false, 60); Place((RectTransform)playJa.transform, 418, -704, 374, 60);
            var playHint = Label("PlayHint", right.transform, "", 18, Muted, regular); Place(playHint.rectTransform, 28, -770, 764, 34);
            var review = MakeButton("ReviewPreview", right.transform, "Xem cả mục chưa sẵn sàng (chỉ kiểm tra, không vào game)", false, 52); Place((RectTransform)review.transform, 28, -816, 764, 52);
            var reviewNote = Label("ReviewNote", right.transform, "Mục needs_review / failed chỉ hiển thị để chủ dự án kiểm tra nội dung; trạng thái không bị thay đổi.", 18, Muted, regular); Place(reviewNote.rectTransform, 28, -874, 764, 50);

            var ctrl = new GameObject("VocabularyLibrary").AddComponent<VocabularyLibraryController>();
            Set(ctrl, "listContent", content); Set(ctrl, "rowTemplate", row); Set(ctrl, "listState", state);
            Set(ctrl, "detailTitle", dTitle); Set(ctrl, "detailStatus", dStatus); Set(ctrl, "detailCounts", dCounts); Set(ctrl, "detailMeta", dMeta); Set(ctrl, "dropHint", drop);
            Set(ctrl, "englishButton", en); Set(ctrl, "japaneseButton", ja); Set(ctrl, "reviewButton", review); Set(ctrl, "openButton", open); Set(ctrl, "rescanButton", rescan); Set(ctrl, "showAllButton", showAll); Set(ctrl, "playEnglishButton", playEn); Set(ctrl, "playJapaneseButton", playJa); Set(ctrl, "playHint", playHint);
            Set(ctrl, "pathInput", path);
            Save(scene, "VocabularyLibrary");
        }

        static void BuildPreview()
        {
            var scene = NewScene("VocabularyPreview", true, 0.4f);
            Set(Object.FindFirstObjectByType<SceneNav>(), "backScene", "VocabularyLibrary");
            var canvas = Canvas();
            Tag(canvas, "Thư viện từ vựng · xem từ, hình ảnh và phát âm");
            BackButton(canvas);
            var frame = PanelImage("ImageFrame", canvas, new Vector2(0, 0.5f), new Vector2(80, -20), new Vector2(760, 760));
            frame.rectTransform.pivot = new Vector2(0, 0.5f);
            frame.color = new Color32(233, 239, 237, 255);
            var raw = Rect("Image", frame.transform, new Vector2(0.5f, 0.5f), Vector2.zero, new Vector2(720, 720)).gameObject.AddComponent<RawImage>();
            raw.gameObject.AddComponent<AspectRatioFitter>().aspectMode = AspectRatioFitter.AspectMode.FitInParent;
            var right = PanelImage("Details", canvas, new Vector2(1, 0.5f), new Vector2(-80, -20), new Vector2(940, 860));
            right.rectTransform.pivot = new Vector2(1, 0.5f);
            var tag = Label("ItemTag", right.transform, "", 22, Text, medium); Place(tag.rectTransform, 30, -26, 880, 34);
            var src = Label("SourceText", right.transform, "", 72, Text, medium); src.overflowMode = TextOverflowModes.Ellipsis; Place(src.rectTransform, 30, -74, 880, 190);
            var meaning = Label("Meaning", right.transform, "", 44, new Color32(169, 227, 220, 255), medium); Place(meaning.rectTransform, 30, -270, 880, 120);
            var info = Label("Info", right.transform, "", 18, Muted, regular); Place(info.rectTransform, 30, -400, 880, 60);
            var counter = Label("Counter", right.transform, "", 22, Muted, medium); Place(counter.rectTransform, 30, -470, 880, 34);
            var play = MakeButton("PlayAudio", right.transform, "Phát âm", true, 64); Place((RectTransform)play.transform, 30, -520, 260, 64);
            var prev = MakeButton("Prev", right.transform, "← Trước", true, 64); Place((RectTransform)prev.transform, 310, -520, 200, 64);
            var next = MakeButton("Next", right.transform, "Tiếp →", true, 64); Place((RectTransform)next.transform, 530, -520, 200, 64);
            var media = Label("MediaStatus", right.transform, "", 20, Muted, regular); Place(media.rectTransform, 30, -600, 880, 60);
            var modeHead = Label("ModeHeading", right.transform, "Đổi chế độ:", 20, Muted, medium); Place(modeHead.rectTransform, 30, -672, 880, 30);
            var en = MakeButton("ModeEnglish", right.transform, "English → Tiếng Việt", true, 60); Place((RectTransform)en.transform, 30, -710, 420, 60);
            var ja = MakeButton("ModeJapanese", right.transform, "日本語 → Tiếng Việt", true, 60); Place((RectTransform)ja.transform, 470, -710, 420, 60);
            var empty = Label("Empty", right.transform, "", 30, Warn, medium, TextAlignmentOptions.Center); Place(empty.rectTransform, 30, -200, 880, 120);
            var ctrl = new GameObject("VocabularyPreview").AddComponent<VocabularyPreviewController>();
            Set(ctrl, "image", raw); Set(ctrl, "sourceText", src); Set(ctrl, "meaningText", meaning); Set(ctrl, "info", info); Set(ctrl, "counter", counter);
            Set(ctrl, "itemTag", tag); Set(ctrl, "mediaStatus", media); Set(ctrl, "emptyText", empty);
            Set(ctrl, "prevButton", prev); Set(ctrl, "nextButton", next); Set(ctrl, "playButton", play); Set(ctrl, "englishButton", en); Set(ctrl, "japaneseButton", ja);
            Save(scene, "VocabularyPreview");
        }

        static GameObject Overlay(string name, Transform canvas, Vector2 size, out RectTransform panel)
        {
            var dim = Rect(name, canvas, new Vector2(0.5f, 0.5f), Vector2.zero, Vector2.zero).gameObject.AddComponent<Image>();
            dim.rectTransform.anchorMin = Vector2.zero; dim.rectTransform.anchorMax = Vector2.one; dim.rectTransform.sizeDelta = Vector2.zero;
            dim.sprite = S("UI/panel_rectangle.png"); dim.type = Image.Type.Sliced; dim.color = new Color(0.01f, 0.04f, 0.07f, 0.72f);
            var box = PanelImage("Panel", dim.transform, new Vector2(0.5f, 0.5f), Vector2.zero, size);
            box.color = new Color32(13, 36, 54, 250);
            panel = box.rectTransform;
            return dim.gameObject;
        }

        /// <summary>G-007.1 configuration step: Library → GameSetup → MeteorDefense. Options are segmented button rows.</summary>
        static void BuildGameSetup()
        {
            var scene = NewScene("GameSetup", true, 0.6f);
            Set(Object.FindFirstObjectByType<SceneNav>(), "backScene", "VocabularyLibrary");
            var canvas = Canvas();
            BackButton(canvas);
            var title = Label("Title", canvas, "CẤU HÌNH VÁN CHƠI · METEOR DEFENSE", 30, Warn, medium, TextAlignmentOptions.Center);
            var trt = title.rectTransform; trt.anchorMin = trt.anchorMax = trt.pivot = new Vector2(0.5f, 1f); trt.anchoredPosition = new Vector2(0, -24); trt.sizeDelta = new Vector2(1200, 44);

            var left = PanelImage("Options", canvas, new Vector2(0, 1), new Vector2(40, -96), new Vector2(1080, 950));
            left.rectTransform.pivot = new Vector2(0, 1);
            var pack = Label("Pack", left.transform, "", 24, Text, medium); Place(pack.rectTransform, 30, -22, 1020, 34);
            var count = Label("Count", left.transform, "", 19, Muted, regular); Place(count.rectTransform, 30, -60, 1020, 56);
            float y = -128;
            Button[] Group(string heading, string[] names)
            {
                var h = Label(heading, left.transform, heading, 20, Accent, medium); Place(h.rectTransform, 30, y, 1020, 28);
                var row = Rect(heading + "Row", left.transform, new Vector2(0, 1), new Vector2(30, y - 32), new Vector2(1020, 58), new Vector2(0, 1));
                var hl = row.gameObject.AddComponent<HorizontalLayoutGroup>(); hl.spacing = 12; hl.childControlWidth = hl.childControlHeight = true; hl.childForceExpandWidth = hl.childForceExpandHeight = true;
                var list = new List<Button>();
                foreach (var n in names)
                {
                    var b = MakeButton(heading + "_" + n, row, n, true, 58);
                    var t = b.GetComponentInChildren<TMP_Text>();
                    t.enableAutoSizing = true; t.fontSizeMin = 16; t.fontSizeMax = 22; t.textWrappingMode = TextWrappingModes.NoWrap; // long labels shrink, never wrap
                    list.Add(b);
                }
                y -= 112;
                return list.ToArray();
            }
            var diff = Group("Độ khó", new[] { "Dễ", "Thường", "Khó", "Chuyên gia" });
            var hint = Group("Gợi ý", new[] { "Chỉ nghĩa", "Nghĩa + chữ đầu" }); // no image hints in gameplay (D-043)
            var ans = Group("Kiểu trả lời", new[] { "Gõ cả từ", "Điền chỗ trống" });
            var tgt = Group("Nhắm mục tiêu", new[] { "Tự động + Tab", "Tự động", "Thủ công (Tab)" });
            var explain = Label("Explain", left.transform, "", 20, Text, regular); explain.lineSpacing = 8; Place(explain.rectTransform, 30, y - 6, 1020, 250);
            var status = Label("Status", left.transform, "", 22, Text, medium); Place(status.rectTransform, 30, -872, 1020, 64);

            var right = PanelImage("Preview", canvas, new Vector2(1, 1), new Vector2(-40, -96), new Vector2(720, 950));
            right.rectTransform.pivot = new Vector2(1, 1);
            var ph = Label("PreviewHeading", right.transform, "XEM TRƯỚC CÂU HỎI (dữ liệu thật của pack)", 20, Accent, medium); Place(ph.rectTransform, 30, -22, 660, 30);
            var clueBg = PanelImage("ClueBg", right.transform, new Vector2(0.5f, 1), new Vector2(0, -110), new Vector2(620, 64)); clueBg.rectTransform.pivot = new Vector2(0.5f, 1); clueBg.color = new Color(0.03f, 0.11f, 0.18f, 0.95f);
            var clue = Label("Clue", clueBg.transform, "", 30, new Color32(243, 238, 224, 255), medium, TextAlignmentOptions.Center); Stretch(clue.rectTransform, 10, 6, 10, 6);
            var meteor = Rect("Meteor", right.transform, new Vector2(0.5f, 1), new Vector2(0, -188), new Vector2(120, 110), new Vector2(0.5f, 1)).gameObject.AddComponent<Image>();
            meteor.sprite = S("Meteors/meteorGrey_big1.png"); meteor.preserveAspect = true; meteor.raycastTarget = false;
            var ansBg = PanelImage("AnswerBg", right.transform, new Vector2(0.5f, 1), new Vector2(0, -314), new Vector2(620, 70)); ansBg.rectTransform.pivot = new Vector2(0.5f, 1); ansBg.color = new Color(0.05f, 0.24f, 0.33f, 0.97f);
            var answer = Label("Answer", ansBg.transform, "", 34, new Color32(223, 249, 255, 255), medium, TextAlignmentOptions.Center); Stretch(answer.rectTransform, 10, 6, 10, 6);
            var caption = Label("Caption", right.transform, "", 19, Muted, regular, TextAlignmentOptions.Top); Place(caption.rectTransform, 30, -400, 660, 80);
            var nextSample = MakeButton("NextSample", right.transform, "Ví dụ khác", true, 56); Place((RectTransform)nextSample.transform, 30, -490, 240, 56);
            var start = MakeButton("StartGame", right.transform, "▶  Bắt đầu", true, 84); Place((RectTransform)start.transform, 30, -836, 660, 84);
            start.GetComponentInChildren<TMP_Text>().fontSize = 34;

            var ctrl = new GameObject("GameSetup").AddComponent<Game.GameSetupController>();
            Set(ctrl, "packText", pack); Set(ctrl, "countText", count); Set(ctrl, "explainText", explain); Set(ctrl, "statusText", status);
            Set(ctrl, "previewClue", clue); Set(ctrl, "previewAnswer", answer); Set(ctrl, "previewCaption", caption);
            Set(ctrl, "difficultyButtons", diff); Set(ctrl, "hintButtons", hint); Set(ctrl, "answerButtons", ans); Set(ctrl, "targetButtons", tgt);
            Set(ctrl, "startButton", start); Set(ctrl, "nextSampleButton", nextSample);
            Save(scene, "GameSetup");
        }

        /// <summary>G-006 production Meteor Defense scene. Vocabulary only from LearningSession; tuning in the controller's GameConfig.</summary>
        static void BuildMeteorDefense(Material particleMat)
        {
            var scene = NewScene("MeteorDefense", false, 0.25f);
            Set(Object.FindFirstObjectByType<SceneNav>(), "backScene", "GameSetup");
            var canvas = Canvas();

            var back = MakeButton("BackButton", canvas, "←  Quay lại", true, 56);
            Place((RectTransform)back.transform, 28, -16, 220, 56);
            var header = Label("Header", canvas, "METEOR DEFENSE", 20, Warn, medium, TextAlignmentOptions.Center);
            var hr = header.rectTransform; hr.anchorMin = hr.anchorMax = hr.pivot = new Vector2(0.5f, 1f); hr.anchoredPosition = new Vector2(0, -12); hr.sizeDelta = new Vector2(900, 62);
            var hpLabel = Label("HPLabel", canvas, "HP / PHÒNG TUYẾN", 18, Muted, medium); Place(hpLabel.rectTransform, 290, -20, 260, 26);
            var hpRow = Rect("HPRow", canvas, new Vector2(0, 1), new Vector2(290, -50), new Vector2(260, 32), new Vector2(0, 1));
            var hl = hpRow.gameObject.AddComponent<HorizontalLayoutGroup>(); hl.spacing = 8; hl.childControlWidth = hl.childControlHeight = false; hl.childForceExpandWidth = hl.childForceExpandHeight = false;
            var score = Label("Score", canvas, "", 20, Text, medium, TextAlignmentOptions.TopRight); PlaceRight(score.rectTransform, -470, -14, 200, 80);
            var progress = Label("Progress", canvas, "", 20, Text, medium, TextAlignmentOptions.TopRight); PlaceRight(progress.rectTransform, -258, -14, 200, 80);
            var pause = MakeButton("PauseButton", canvas, "Tạm dừng", true, 56); PlaceRight((RectTransform)pause.transform, -28, -16, 210, 56);
            // G-008 HUD row under the header, inside the 112 px HUD band: wave progress and current combo.
            var wave = Label("Wave", canvas, "", 20, Accent, medium, TextAlignmentOptions.Right);
            var wr = wave.rectTransform; wr.anchorMin = wr.anchorMax = new Vector2(0.5f, 1f); wr.pivot = new Vector2(1f, 1f); wr.anchoredPosition = new Vector2(-16, -76); wr.sizeDelta = new Vector2(260, 30);
            var combo = Label("Combo", canvas, "", 20, Warn, medium, TextAlignmentOptions.Left);
            var cr = combo.rectTransform; cr.anchorMin = cr.anchorMax = new Vector2(0.5f, 1f); cr.pivot = new Vector2(0f, 1f); cr.anchoredPosition = new Vector2(16, -76); cr.sizeDelta = new Vector2(260, 30);
            var banner = Label("WaveBanner", canvas, "", 64, Text, medium, TextAlignmentOptions.Center);
            var br = banner.rectTransform; br.anchorMin = br.anchorMax = br.pivot = new Vector2(0.5f, 0.5f); br.anchoredPosition = new Vector2(0, 90); br.sizeDelta = new Vector2(1000, 160);
            banner.raycastTarget = false;

            var console = PanelImage("AnswerConsole", canvas, new Vector2(0, 0), new Vector2(40, 30), new Vector2(760, 150));
            console.rectTransform.pivot = Vector2.zero;
            var mode = Label("Mode", console.transform, "", 20, Accent, medium); Place(mode.rectTransform, 26, -16, 700, 30); mode.enableAutoSizing = true; mode.fontSizeMin = 13; mode.fontSizeMax = 20; mode.textWrappingMode = TextWrappingModes.NoWrap; // one line; long JA/Fill text shrinks
            var field = InputField(console.transform, new Vector2(0, 0), new Vector2(24, 24), new Vector2(712, 64), "Gõ đáp án…");
            ((RectTransform)field.transform).pivot = Vector2.zero;
            var help = Label("Help", canvas, "Tab đổi mục tiêu · Enter trả lời · Esc tạm dừng · F2 giảm chuyển động", 20, Muted, regular, TextAlignmentOptions.BottomRight);
            var hrt = help.rectTransform; hrt.anchorMin = hrt.anchorMax = hrt.pivot = new Vector2(1, 0); hrt.anchoredPosition = new Vector2(-40, 34); hrt.sizeDelta = new Vector2(760, 60);
            var toast = Label("Toast", canvas, "", 28, Text, medium, TextAlignmentOptions.Center);
            var tr = toast.rectTransform; tr.anchorMin = tr.anchorMax = tr.pivot = new Vector2(0.5f, 0); tr.anchoredPosition = new Vector2(0, 262); tr.sizeDelta = new Vector2(1300, 44);

            var pausePanel = Overlay("PausePanel", canvas, new Vector2(560, 430), out var pp);
            Column(pp, 16);
            var pTitle = Label("PauseTitle", pp, "TẠM DỪNG", 44, Text, medium, TextAlignmentOptions.Center); pTitle.gameObject.AddComponent<LayoutElement>().minHeight = 70;
            var resume = MakeButton("Resume", pp, "Tiếp tục", true);
            var restart = MakeButton("Restart", pp, "Chơi lại từ đầu", true);
            var menu = MakeButton("MenuFromPause", pp, "Về Main Menu", true);

            var endPanel = Overlay("EndPanel", canvas, new Vector2(1160, 860), out var ep);
            Column(ep, 18);
            var endTitle = Label("EndTitle", ep, "", 52, Text, medium, TextAlignmentOptions.Center); endTitle.gameObject.AddComponent<LayoutElement>().minHeight = 80;
            var endStats = Label("EndStats", ep, "", 24, Text, regular, TextAlignmentOptions.Center); endStats.lineSpacing = 10; endStats.gameObject.AddComponent<LayoutElement>().minHeight = 330;
            endStats.enableAutoSizing = true; endStats.fontSizeMin = 16; endStats.fontSizeMax = 24; // long review lists shrink instead of overflowing
            var replay = MakeButton("Replay", ep, "Chơi lại", true);
            var review = MakeButton("EndReview", ep, "Ôn từ cần ôn", true);
            var toLibrary = MakeButton("EndLibrary", ep, "Thư viện từ vựng", true);
            var toMenu = MakeButton("EndMenu", ep, "Main Menu", true);

            var errorPanel = Overlay("ErrorPanel", canvas, new Vector2(960, 380), out var xp);
            Column(xp, 18);
            var errTitle = Label("ErrorTitle", xp, "Chưa thể bắt đầu Meteor Defense", 36, Warn, medium, TextAlignmentOptions.Center); errTitle.gameObject.AddComponent<LayoutElement>().minHeight = 60;
            var errText = Label("ErrorText", xp, "", 26, Text, regular, TextAlignmentOptions.Center); errText.gameObject.AddComponent<LayoutElement>().minHeight = 120;
            var errLib = MakeButton("ErrorLibrary", xp, "Về Thư viện từ vựng", true);

            var ctrl = new GameObject("MeteorDefense").AddComponent<Game.MeteorDefenseController>();
            Set(ctrl, "meteorSprites", new Object[] { S("Meteors/meteorGrey_big1.png"), S("Meteors/meteorBrown_big1.png"), S("Meteors/meteorGrey_big2.png") });
            Set(ctrl, "shipSprite", S("Ship/playerShip2_blue.png")); Set(ctrl, "flameSprite", S("VFX/fire00.png"));
            Set(ctrl, "shieldSprite", S("VFX/shield1.png")); Set(ctrl, "laserSprite", S("VFX/laserBlue01.png"));
            Set(ctrl, "reticleSprite", S("UI/crosshair_color_a_double.png")); Set(ctrl, "labelSprite", S("UI/panel_rectangle.png"));
            Set(ctrl, "hpSprite", S("UI/playerLife2_blue.png"));
            Set(ctrl, "particleMaterial", particleMat); Set(ctrl, "lineMaterial", BuildLineMaterial()); Set(ctrl, "font", medium);
            Set(ctrl, "laserClip", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/SFX/sfx_laser1.ogg"));
            Set(ctrl, "hitClip", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/SFX/sfx_zap.ogg"));
            Set(ctrl, "destroyClip", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/SFX/sfx_twoTone.ogg"));
            Set(ctrl, "breachClip", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/SFX/sfx_shieldDown.ogg"));
            Set(ctrl, "loseClip", AssetDatabase.LoadAssetAtPath<AudioClip>("Assets/Audio/SFX/sfx_lose.ogg"));
            Set(ctrl, "background", Object.FindFirstObjectByType<GalaxyBackground>());
            Set(ctrl, "input", field); Set(ctrl, "scoreText", score); Set(ctrl, "progressText", progress); Set(ctrl, "headerText", header);
            Set(ctrl, "waveText", wave); Set(ctrl, "comboText", combo); Set(ctrl, "waveBanner", banner); Set(ctrl, "endReview", review);
            Set(ctrl, "helpText", help);
            Set(ctrl, "modeText", mode); Set(ctrl, "toastText", toast); Set(ctrl, "endTitle", endTitle); Set(ctrl, "endStats", endStats);
            Set(ctrl, "errorText", errText); Set(ctrl, "menuLabel", menu.GetComponentInChildren<TextMeshProUGUI>()); Set(ctrl, "hpRow", hpRow);
            Set(ctrl, "pausePanel", pausePanel); Set(ctrl, "endPanel", endPanel); Set(ctrl, "errorPanel", errorPanel);
            Set(ctrl, "pauseButton", pause); Set(ctrl, "backButton", back); Set(ctrl, "resumeButton", resume); Set(ctrl, "restartButton", restart);
            Set(ctrl, "menuButton", menu); Set(ctrl, "endReplay", replay); Set(ctrl, "endLibrary", toLibrary); Set(ctrl, "endMenu", toMenu); Set(ctrl, "errorLibrary", errLib);
            Save(scene, "MeteorDefense");
        }

        static void Stretch(RectTransform rt, float left, float top, float right, float bottom)
        {
            rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.pivot = new Vector2(0, 1);
            rt.offsetMin = new Vector2(left, bottom); rt.offsetMax = new Vector2(-right, -top);
        }

        static void Place(RectTransform rt, float x, float y, float w, float h)
        {
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(0, 1);
            rt.anchoredPosition = new Vector2(x, y); rt.sizeDelta = new Vector2(w, h);
        }

        static void PlaceRight(RectTransform rt, float x, float y, float w, float h)
        {
            rt.anchorMin = rt.anchorMax = rt.pivot = new Vector2(1, 1);
            rt.anchoredPosition = new Vector2(x, y); rt.sizeDelta = new Vector2(w, h);
        }
    }
}
