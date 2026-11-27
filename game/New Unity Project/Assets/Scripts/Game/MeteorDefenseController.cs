using System.Collections;
using System.Collections.Generic;
using MP1.Background;
using MP1.Content;
using MP1.Core;
using MP1.Dev;
using MP1.Library;
using MP1.UI;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace MP1.Game
{
    /// <summary>
    /// G-006 Meteor Defense scene. Vocabulary comes only from <see cref="LearningSession.EligibleItems"/>; rules live in
    /// <see cref="MeteorDefenseSession"/>, scheduling in <see cref="VocabularyDeck"/>, targeting in
    /// <see cref="TargetSelector"/> and answer comparison in <see cref="AnswerChecker"/>. This class only wires them to
    /// sprites, input and UI. Pause uses timeScale 0 plus AudioListener.pause.
    /// </summary>
    public class MeteorDefenseController : MonoBehaviour
    {
        /// <summary>Optional override set before the scene loads (tests, dev switches).</summary>
        public static GameConfig ConfigOverride;

        [Header("Tuning (provisional, G-007 will own this)")]
        [SerializeField] GameConfig config = new GameConfig();

        [Header("Art")]
        [SerializeField] Sprite[] meteorSprites;
        [SerializeField] Sprite shipSprite, flameSprite, shieldSprite, laserSprite, reticleSprite, labelSprite, hpSprite;
        [SerializeField] Material particleMaterial, lineMaterial;
        [SerializeField] TMP_FontAsset font;
        [SerializeField] AudioClip laserClip, hitClip, destroyClip, breachClip, loseClip;

        [Header("Scene")]
        [SerializeField] GalaxyBackground background;
        [SerializeField] TMP_InputField input;
        [SerializeField] TMP_Text scoreText, progressText, headerText, modeText, toastText, endTitle, endStats, errorText, menuLabel, helpText, waveText, comboText, waveBanner;
        [SerializeField] RectTransform hpRow;
        [SerializeField] GameObject pausePanel, endPanel, errorPanel;
        [SerializeField] Button pauseButton, backButton, resumeButton, restartButton, menuButton, endReplay, endLibrary, endMenu, errorLibrary, endReview;

        const float DefenseY = -3.3f, ShipY = -4.25f;

        public MeteorDefenseSession Session { get; private set; }
        public VocabularyDeck Deck { get; private set; }
        public List<MeteorView> Active { get; } = new List<MeteorView>();
        public int Target { get; private set; } = -1;
        public string StartError { get; private set; }
        public LearningMode Mode => LearningSession.Mode;
        public AudioSource Speech => speech;
        public LearningItem LastSpoken { get; private set; }
        public GameConfig Config => config;

        readonly Dictionary<int, string> drafts = new Dictionary<int, string>();
        readonly Dictionary<string, LearningItem> items = new Dictionary<string, LearningItem>();
        int seed;
        readonly List<Image> hpIcons = new List<Image>();
        Transform ship;
        SpriteRenderer shield;
        ParticleSystem burst;
        AudioSource speech, sfx;
        float spawnTimer, toastUntil;
        bool menuConfirm;
        // G-007-R2 combat: bounded laser pool, rate-limited SFX, IME-safe evaluation.
        const int LaserPoolSize = 10, MaxLasersPerInput = 3;
        readonly List<SpriteRenderer> laserPool = new List<SpriteRenderer>();
        readonly List<float> laserUntil = new List<float>();
        float lastLaserSfx;
        bool pendingEval, wasComposing, completedThisFrame;
        /// <summary>Simulated IME composition for tests and dev runs; null = read the real Input.compositionString.</summary>
        public string TestComposition;
        string Composition => TestComposition ?? Input.compositionString;
        public int LasersFired { get; private set; }
        public Transform Ship => ship;
        // G-008: waves (D-046), one-slot pronunciation queue + per-session clip cache (D-048), results/history (D-049/D-050).
        SpeechSlot<LearningItem> speechSlot;
        readonly Dictionary<string, AudioClip> clipCache = new Dictionary<string, AudioClip>();
        bool speechLoading, waveWaiting;
        System.DateTime startedUtc;
        public int SpeechesStarted { get; private set; }
        public int PostponedSpawns { get; private set; }
        public bool SpeechPending => speechSlot != null && speechSlot.HasPending;
        public bool WaveBannerVisible => waveBanner != null && waveBanner.gameObject.activeSelf;
        public string HistoryError { get; private set; }
        public string HistoryPath { get; private set; }
        /// <summary>Dev/test override for the history file (null = persistentDataPath).</summary>
        public static string HistoryPathOverride;

        IEnumerator Start()
        {
            Time.timeScale = 1f;
            AudioListener.pause = false;
            config = (ConfigOverride ?? GameConfig.Selected).Clone();
            WireButtons();
            pausePanel.SetActive(false);
            endPanel.SetActive(false);
            toastText.gameObject.SetActive(false);
            errorPanel.SetActive(false);
            StartError = GameEntry.WhyCannotStart(config);
            if (StartError != null) { ShowError(StartError); yield break; }

            foreach (var it in GameCompatibility.Check(LearningSession.EligibleItems, config, Mode).Usable) items[it.ItemId] = it;
            seed = Mathf.RoundToInt(DevArgs.GetFloat(DevCommandLine.Args, "-g006Seed", System.Environment.TickCount & 0x7fffffff));
            Deck = new VocabularyDeck(items.Keys, seed, config.ItemsPerWave, config.SessionSpawns);
            Session = new MeteorDefenseSession(config);
            sfx = gameObject.AddComponent<AudioSource>(); sfx.playOnAwake = false; sfx.volume = 0.35f;
            speech = gameObject.AddComponent<AudioSource>(); speech.playOnAwake = false; speech.volume = 1f;
            speechSlot = new SpeechSlot<LearningItem>(config.SpeechStaleSeconds);
            foreach (var it in items.Values) StartCoroutine(Preload(it));
            startedUtc = System.DateTime.UtcNow;
            BuildShip();
            BuildDefenseLine();
            burst = BuildBurst();
            BuildHp();
            input.onValidateInput += (t, i, c) => c == '\t' ? '\0' : c;
            input.onValueChanged.AddListener(OnTyped);
            Input.imeCompositionMode = IMECompositionMode.On;
            headerText.text = $"METEOR DEFENSE · {LearningModes.Label(Mode)} · pack v{LearningSession.Pack.PackVersion}\n<size=85%><color=#B8C9D5>{GameLabels.Summary(config)}</color></size>";
            string lang = Mode == LearningMode.EnglishToVietnamese ? "tiếng Anh" : "tiếng Nhật (IME)";
            modeText.text = (config.Answer == AnswerMode.FillInTheBlank ? $"Gõ chữ còn thiếu ({lang}), trái → phải" : $"Gõ cả từ {lang}") + " · mỗi chữ đúng = 1 phát bắn";
            helpText.text = GameLabels.TargetHelp(config.Targeting) + " · Esc tạm dừng · F2 giảm chuyển động";
            SetPlaceholder();
            spawnTimer = config.FirstSpawnDelay;
            Session.Start();
            ShowWaveBanner(1);
            Time.timeScale = DevTimeScale;
            MeteorDefenseDevBot.AttachIfRequested(this);
            input.ActivateInputField();
            RefreshHud();
            Debug.Log($"G006_SESSION start mode={LearningModes.Id(Mode)} pack={LearningSession.Pack.PackId} v{LearningSession.Pack.PackVersion} items={items.Count} seed={seed} spawns={config.SessionSpawns} hp={config.StartingHp} difficulty={config.Difficulty} hint={config.Hint} answer={config.Answer} targeting={config.Targeting}");
        }

        void ShowError(string message)
        {
            errorPanel.SetActive(true);
            errorText.text = message;
            input.gameObject.SetActive(false);
            EventSystem.current.SetSelectedGameObject(errorLibrary.gameObject);
        }

        void SetPlaceholder()
        {
            ((TMP_Text)input.placeholder).text = config.Targeting == TargetingMode.Manual && Target < 0 ? "Nhấn Tab để chọn mục tiêu"
                : Mode == LearningMode.EnglishToVietnamese ? "Gõ từ tiếng Anh…" : "Nhập bằng IME tiếng Nhật…";
        }

        void WireButtons()
        {
            pauseButton.onClick.AddListener(Pause);
            backButton.onClick.AddListener(Back);
            resumeButton.onClick.AddListener(Resume);
            restartButton.onClick.AddListener(Restart);
            menuButton.onClick.AddListener(MenuFromPause);
            endReplay.onClick.AddListener(Restart);
            if (endReview != null) endReview.onClick.AddListener(OpenReview);
            endLibrary.onClick.AddListener(() => Leave("VocabularyLibrary"));
            endMenu.onClick.AddListener(() => Leave(SceneNav.MainMenu));
            errorLibrary.onClick.AddListener(() => Leave("VocabularyLibrary"));
        }

        void Update()
        {
            if (Session == null) return;
            string composition = Composition;
            bool free = ImeGate.ShortcutAllowed(composition);
            bool composedLastFrame = wasComposing;
            wasComposing = !free;
            completedThisFrame = false;
            if (free && Input.GetKeyDown(KeyCode.Escape))
            {
                if (Session.State == SessionState.Playing) Pause();
                else if (Session.State == SessionState.Paused) Resume();
            }
            PumpSpeech();
            if (Session.State != SessionState.Playing) return;

            Session.Tick(Time.unscaledDeltaTime);
            if (Session.AtWaveBoundary && !waveWaiting)
            {
                waveWaiting = true;
                spawnTimer = config.WavePauseSeconds; // scaled time: Pause freezes the transition
                ShowWaveBanner(Session.NextWave + 1);
                Debug.Log($"G008_WAVE cleared={Session.WavesStarted} next={Session.NextWave + 1}");
            }
            spawnTimer -= Time.deltaTime;
            if (spawnTimer <= 0f) TrySpawn();
            CheckBreaches();
            if (Session.State != SessionState.Playing) return;
            UpdateTarget();
            // Text committed while an IME composition was open is evaluated once the composition closes.
            if (pendingEval && free) { pendingEval = false; if (View(Target) is MeteorView pv) Evaluate(pv, input.text); }
            AimShip();
            if (free && Input.GetKeyDown(KeyCode.Tab)) CycleTarget();
            // Enter that confirmed an IME composition, or that follows an automatic kill, never submits again.
            if (free && !composedLastFrame && !completedThisFrame && (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter))) Submit(input.text);
            if (toastText.gameObject.activeSelf && Time.unscaledTime > toastUntil) toastText.gameObject.SetActive(false);
            if (!input.isFocused && free && !pausePanel.activeSelf) input.ActivateInputField();
        }

        // ---------- spawning, movement outcome ----------

        void TrySpawn()
        {
            spawnTimer = 0.5f; // retry soon if postponed
            if (!Session.CanSpawn || Active.Count >= config.MaxConcurrent) return;
            var onScreen = new HashSet<string>();
            foreach (var m in Active) onScreen.Add(m.Item.ItemId);
            string id = Deck.Next(onScreen);
            if (id == null) return;
            var item = items[id];
            // Puzzle seed from session seed + spawn number: stable for this meteor, reproducible from the logged seed.
            var puzzle = config.Answer == AnswerMode.FillInTheBlank ? BlankPuzzle.Create(item.SourceText, config.HiddenRatio, seed * 31 + Session.Spawned) : null;
            var view = CreateView(item, puzzle);
            float spawnY = SpawnLayout.SpawnY(Camera.main.orthographicSize, view.StackTop);
            float x = PickLane(view, spawnY);
            if (float.IsNaN(x)) { Destroy(view.gameObject); Deck.Requeue(id); PostponedSpawns++; Debug.Log($"G007_DEFER item={id} cycle={Deck.LastIssuedCycle} reason=no_lane requeued=true"); return; } // no lane fits: postpone, spec §4
            int wave = Session.NextWave;
            int meteorId = Session.Spawn(id);
            if (waveWaiting || Session.Spawned == 1) { waveWaiting = false; if (waveBanner != null) waveBanner.gameObject.SetActive(false); }
            view.Id = meteorId;
            view.SpawnOrder = meteorId;
            view.name = $"Meteor_{meteorId}_{id}";
            Debug.Log($"G007_SPAWN n={Session.Spawned} meteor={meteorId} item={id} cycle={Deck.LastIssuedCycle} wave={wave + 1} active={Active.Count + 1}");
            view.transform.position = new Vector3(x, spawnY, 0f);
            StartCoroutine(FadeIn(view, 0.25f));
            view.FallSpeed = (spawnY - DefenseY - view.Radius) / config.FallSeconds(view.Item.SourceText, wave);
            Active.Add(view);
            spawnTimer = config.SpawnInterval(wave);
            RefreshHud();
        }

        float PickLane(MeteorView view, float spawnY)
        {
            var cam = Camera.main;
            float halfW = cam.orthographicSize * cam.aspect;
            var lanes = new float[5];
            // Lanes are clamped per meteor so a long label never leaves the screen; overlap is then checked on these xs.
            for (int l = 0; l < lanes.Length; l++)
                lanes[l] = SpawnLayout.ClampX(Mathf.Lerp(-halfW + 2.4f, halfW - 2.4f, l / (float)(lanes.Length - 1)), halfW, view.LabelWidth);
            var occupants = new List<LaneOccupant>(Active.Count);
            foreach (var m in Active) occupants.Add(new LaneOccupant(m.transform.position.x, m.transform.position.y, m.LabelWidth));
            int lane = LaneChooser.Choose(lanes, view.LabelWidth, occupants, spawnY, () => Random.value);
            return lane < 0 ? float.NaN : lanes[lane];
        }

        void CheckBreaches()
        {
            // Spawn order makes concurrent breaches deterministic (spec §4).
            for (int i = 0; i < Active.Count && Session.State == SessionState.Playing; i++)
            {
                var m = Active[i];
                if (m.BottomY > DefenseY) continue;
                if (!Session.RegisterBreach(m.Id)) continue;
                Active.RemoveAt(i--);
                drafts.Remove(m.Id);
                if (m.Id == Target) { Target = -1; input.SetTextWithoutNotify(""); }
                StartCoroutine(FadeOut(m, 0.25f));
                StartCoroutine(FlashShield());
                if (damageRoutine != null) StopCoroutine(damageRoutine);
                damageRoutine = StartCoroutine(DamageFeedback());
                if (breachClip) sfx.PlayOneShot(breachClip, 0.4f);
                Toast($"“{m.Item.Meaning}” chạm phòng tuyến · −1 HP · đáp án: {m.Item.SourceText}", new Color32(240, 180, 106, 255));
                Debug.Log($"G006_EVENT breach meteor={m.Id} item={m.Item.ItemId} hp={Session.Hp}");
                RefreshHud();
            }
            if (Session.IsOver) EndSession();
        }

        // ---------- targeting ----------

        List<TargetCandidate> Candidates()
        {
            var list = new List<TargetCandidate>(Active.Count);
            foreach (var m in Active) list.Add(new TargetCandidate(m.Id, m.SpawnOrder, m.BottomY - DefenseY));
            return list;
        }

        void UpdateTarget()
        {
            bool typing = Target >= 0 && !string.IsNullOrEmpty(DraftOf(Target));
            int next = TargetSelector.Resolve(Target, Candidates(), config.Targeting, typing);
            if (next != Target)
            {
                if (Target >= 0 && Active.Exists(m => m.Id == Target)) drafts[Target] = input.text; // Auto switch keeps any draft
                SetTarget(next);
            }
        }

        void CycleTarget()
        {
            if (!TargetSelector.TabAllowed(config.Targeting)) return;
            if (Target >= 0) drafts[Target] = input.text; // keep the partial answer on its own meteor
            SetTarget(TargetSelector.Cycle(Target, Candidates()));
        }

        void SetTarget(int id)
        {
            Target = id;
            foreach (var m in Active) m.SetSelected(m.Id == id);
            input.SetTextWithoutNotify(id >= 0 && drafts.TryGetValue(id, out var d) ? d : "");
            input.caretPosition = input.text.Length;
            SetPlaceholder();
        }

        void OnTyped(string text)
        {
            if (Target < 0) { if (text.Length > 0) input.SetTextWithoutNotify(""); return; } // Manual with no target: nothing to type into
            drafts[Target] = text;
            var m = View(Target);
            if (m == null) return;
            m.SetDraft(text);
            if (!ImeGate.ShortcutAllowed(Composition)) { pendingEval = true; return; } // unfinished IME text deals no damage
            Evaluate(m, text);
        }

        MeteorView View(int id) => Active.Find(m => m.Id == id);

        // ---------- answers ----------

        /// <summary>
        /// G-007-R2 (D-044): each newly confirmed answer unit fires a laser at this meteor and advances its damage;
        /// a wrong unit flashes without damage; the last correct unit destroys it without Enter, after the
        /// full-answer validator agrees.
        /// </summary>
        void Evaluate(MeteorView m, string text)
        {
            if (Session.State != SessionState.Playing || m.Combat == null) return;
            var step = m.Combat.Update(text);
            if (step.NewHits > 0)
            {
                Session.RegisterHits(m.Id, step.NewHits);
                for (int i = 0; i < Mathf.Min(step.NewHits, MaxLasersPerInput); i++) FireLaser(m, i * 0.12f);
                m.SetProgress(m.Combat.Fraction);
                m.Shake();
                Debug.Log($"G007_COMBAT hit meteor={m.Id} hits={m.Combat.Hits}/{m.Combat.Required}");
            }
            if (step.Error)
            {
                m.FlashWrong(0.35f);
                Session.RegisterTypo(m.Id);
                if (hitClip) sfx.PlayOneShot(hitClip, 0.15f);
                Debug.Log($"G007_COMBAT miss meteor={m.Id}");
            }
            if (step.Complete && Accepts(m, text)) Resolve(m);
        }

        bool Accepts(MeteorView m, string text) =>
            m.Puzzle != null ? m.Puzzle.Matches(text, m.Item.SourceText, Mode) : AnswerChecker.Matches(text, m.Item.SourceText, Mode);

        /// <summary>The single place a meteor is destroyed by an answer: score once, effects, speech, retarget.</summary>
        bool Resolve(MeteorView m)
        {
            if (!Session.ResolveCorrect(m.Id)) return false;
            completedThisFrame = true;
            Active.Remove(m);
            drafts.Remove(m.Id);
            if (Target == m.Id) { Target = -1; input.SetTextWithoutNotify(""); }
            StartCoroutine(Destroyed(m, Session.LastPoints));
            PlaySpeech(m.Item);
            Toast(Session.Combo > 1 ? $"CHÍNH XÁC · +{Session.LastPoints} · COMBO ×{Session.Combo}" : $"CHÍNH XÁC · +{Session.LastPoints}", new Color32(131, 226, 177, 255));
            Debug.Log($"G006_EVENT correct meteor={m.Id} item={m.Item.ItemId} score={Session.Score} points={Session.LastPoints} combo={Session.Combo} t={Time.realtimeSinceStartup:F2}");
            RefreshHud();
            if (Session.IsOver) EndSession();
            else UpdateTarget();
            return true;
        }

        /// <summary>Validates an answer for the locked meteor only (Enter). Public for automated tests.</summary>
        public bool Submit(string text)
        {
            if (Session == null || Session.State != SessionState.Playing || Target < 0) return false;
            var m = View(Target);
            if (m == null) return false;
            if (string.IsNullOrWhiteSpace(text)) { Toast("Gõ đáp án: mỗi chữ đúng là một phát bắn", new Color32(184, 201, 213, 255)); return false; }
            if (Accepts(m, text)) return Resolve(m);
            Session.RegisterWrong(m.Id);
            m.FlashWrong();
            if (hitClip) sfx.PlayOneShot(hitClip, 0.25f);
            Toast($"Chưa đúng với “{m.Item.Meaning}” · sửa chữ sai rồi gõ tiếp", new Color32(255, 155, 155, 255));
            Debug.Log($"G006_EVENT wrong meteor={m.Id} item={m.Item.ItemId}");
            RefreshHud();
            return false;
        }

        Vector3 Nose => ship.position + ship.up * 0.55f;

        /// <summary>Ship turns toward the current target (snaps with reduced motion); straight up when there is none.</summary>
        void AimShip()
        {
            var t = View(Target);
            Vector3 dir = t != null ? (t.SpriteRoot.position - ship.position) : Vector3.up;
            float angle = Mathf.Clamp(Vector2.SignedAngle(Vector2.up, dir), -75f, 75f);
            var want = Quaternion.Euler(0, 0, angle);
            ship.rotation = MotionSettings.Reduced ? want : Quaternion.RotateTowards(ship.rotation, want, 540f * Time.deltaTime);
        }

        /// <summary>
        /// One cosmetic shot from a fixed pool (oldest reused), so rapid typing shows separate beams without unbounded
        /// objects. Damage is already applied by <see cref="TypingCombat"/>; a beam never touches another meteor.
        /// </summary>
        void FireLaser(MeteorView m, float delay)
        {
            LasersFired++;
            int slot = 0;
            for (int i = 1; i < laserPool.Count; i++) if (laserUntil[i] < laserUntil[slot]) slot = i;
            if (laserPool.Count < LaserPoolSize && (laserPool.Count == 0 || laserUntil[slot] > Time.time))
            {
                var sr = NewSprite("Laser", transform, laserSprite, 14);
                sr.enabled = false;
                laserPool.Add(sr); laserUntil.Add(0f);
                slot = laserPool.Count - 1;
            }
            laserUntil[slot] = Time.time + delay + 0.12f;
            StartCoroutine(Beam(laserPool[slot], m, delay, 0.8f, 0.12f));
            if (laserClip && Time.unscaledTime - lastLaserSfx > 0.06f)
            {
                lastLaserSfx = Time.unscaledTime;
                sfx.PlayOneShot(laserClip, speech != null && speech.isPlaying ? 0.06f : 0.18f); // never louder than speech
            }
        }

        IEnumerator Beam(SpriteRenderer laser, MeteorView m, float delay, float width, float life)
        {
            if (delay > 0f) yield return new WaitForSeconds(delay);
            if (m == null || !m.gameObject.activeInHierarchy) { laser.enabled = false; yield break; } // target gone: cosmetic only
            Vector3 from = Nose, to = m.SpriteRoot.position, d = to - from;
            laser.transform.position = from + d / 2f;
            laser.transform.rotation = Quaternion.FromToRotation(Vector3.up, d.normalized);
            laser.transform.localScale = new Vector3(width, d.magnitude / laserSprite.bounds.size.y, 1f);
            laser.enabled = true;
            burst.transform.position = to;
            burst.Emit(MotionSettings.Reduced ? 2 : 5);
            for (float t = 0; t < life; t += Time.deltaTime) { laser.color = new Color(1, 1, 1, 1 - t / life); yield return null; }
            laser.enabled = false;
        }

        IEnumerator Destroyed(MeteorView m, int points)
        {
            Vector3 to = m.SpriteRoot.position;
            m.FallSpeed = 0f;
            var beam = NewSprite("FinalLaser", transform, laserSprite, 14);
            StartCoroutine(Beam(beam, m, 0f, 1.8f, 0.2f)); // stronger final shot
            if (laserClip) sfx.PlayOneShot(laserClip, 0.3f);
            yield return new WaitForSeconds(0.08f);
            if (destroyClip) sfx.PlayOneShot(destroyClip, speech != null && speech.isPlaying ? 0.12f : 0.3f);
            burst.transform.position = to;
            burst.Emit(MotionSettings.Reduced ? 10 : 40);
            StartCoroutine(Popup($"+{points}", to));
            background.Pulse();
            m.gameObject.SetActive(false);
            yield return new WaitForSeconds(0.2f);
            Destroy(beam.gameObject);
            Destroy(m.gameObject);
        }

        /// <summary>
        /// D-048: one pending slot. Idle plays now; while a word plays only the newest waits, and it plays after the
        /// current word only if requested less than SpeechStaleSeconds ago. Clips come from the per-session cache.
        /// </summary>
        void PlaySpeech(LearningItem item)
        {
            var now = speechSlot.Request(item, Time.time, SpeechBusy);
            if (now != null) StartSpeech(now);
        }

        bool SpeechBusy => speechLoading || (speech != null && speech.isPlaying);

        void PumpSpeech()
        {
            if (speechSlot == null || Session.State == SessionState.Paused) return;
            var next = speechSlot.Poll(Time.time, SpeechBusy);
            if (next != null) StartSpeech(next);
        }

        void StartSpeech(LearningItem item)
        {
            if (clipCache.TryGetValue(item.ItemId, out var cached)) { Speak(item, cached, 0d); return; }
            speechLoading = true;
            StartCoroutine(PackMediaLoader.LoadClip(LearningSession.Pack, item.Audio, (clip, err, ms) =>
            {
                speechLoading = false;
                if (clip == null) { Toast($"Không phát được âm thanh: {err}", new Color32(255, 155, 155, 255)); return; }
                if (speech == null) { Destroy(clip); return; }
                if (clipCache.TryGetValue(item.ItemId, out var other)) { Destroy(clip); clip = other; } else clipCache[item.ItemId] = clip;
                Speak(item, clip, ms);
            }));
        }

        void Speak(LearningItem item, AudioClip clip, double ms)
        {
            speech.Stop();
            speech.clip = clip;
            speech.Play();
            LastSpoken = item;
            SpeechesStarted++;
            Debug.Log($"G006_MEDIA speech item={item.ItemId} mode={LearningModes.Id(Mode)} length={clip.length:F2}s ms={ms:F1} t={Time.realtimeSinceStartup:F2}");
        }

        /// <summary>Loads each usable item's selected-language clip once per session, so answers never decode audio.</summary>
        IEnumerator Preload(LearningItem item)
        {
            yield return PackMediaLoader.LoadClip(LearningSession.Pack, item.Audio, (clip, err, ms) =>
            {
                if (clip == null) return; // reported when the word is spoken
                if (this == null || clipCache.ContainsKey(item.ItemId)) { Destroy(clip); return; }
                clipCache[item.ItemId] = clip;
            });
        }

        public bool ClipCached(string itemId) => clipCache.ContainsKey(itemId);

        // ---------- session flow ----------

        public void Pause()
        {
            if (Session?.State != SessionState.Playing) return;
            Session.Pause();
            Time.timeScale = 0f;
            AudioListener.pause = true;
            menuConfirm = false;
            menuLabel.text = "Về Main Menu";
            pausePanel.SetActive(true);
            input.DeactivateInputField();
            EventSystem.current.SetSelectedGameObject(resumeButton.gameObject);
        }

        public void Resume()
        {
            if (Session?.State != SessionState.Paused) return;
            Session.Resume();
            Time.timeScale = DevTimeScale;
            AudioListener.pause = false;
            pausePanel.SetActive(false);
            input.ActivateInputField();
        }

        public void Restart() => Leave("MeteorDefense");

        void MenuFromPause()
        {
            if (!menuConfirm) { menuConfirm = true; menuLabel.text = "Nhấn lần nữa để bỏ ván và về Menu"; return; }
            Session?.Abandon();
            SaveHistory(); // spec §6: abandoned sessions are recorded as abandoned
            Leave(SceneNav.MainMenu);
        }

        /// <summary>Visible Back: during play it pauses instead of ending the session; after the end it returns to the library.</summary>
        void Back()
        {
            if (Session == null || Session.IsOver) { Leave(GameEntry.SetupScene); return; }
            if (Session.State == SessionState.Playing) Pause();
        }

        void Leave(string scene)
        {
            Time.timeScale = 1f;
            AudioListener.pause = false;
            SceneNav.Load(scene);
        }

        void EndSession()
        {
            input.DeactivateInputField();
            input.interactable = false;
            foreach (var m in Active) StartCoroutine(FadeOut(m, 0.4f));
            Active.Clear();
            Target = -1;
            if (waveBanner != null) waveBanner.gameObject.SetActive(false);
            bool win = Session.State == SessionState.Victory;
            if (!win && loseClip) sfx.PlayOneShot(loseClip, 0.5f);
            endTitle.text = win ? "<color=#83E2B1>CHIẾN THẮNG</color>" : "<color=#FF9B9B>PHÒNG TUYẾN THẤT THỦ</color>";
            endStats.text = ResultsText();
            var weak = WeakItemIds();
            if (endReview != null)
            {
                endReview.interactable = weak.Count > 0;
                endReview.GetComponentInChildren<TMP_Text>().text = weak.Count > 0 ? $"Ôn {weak.Count} từ cần ôn" : "Không có từ cần ôn";
            }
            endPanel.SetActive(true);
            EventSystem.current.SetSelectedGameObject(endReplay.gameObject);
            RefreshHud();
            SaveHistory();
            Debug.Log($"G006_SESSION end state={Session.State} score={Session.Score} correct={Session.Correct} wrong={Session.WrongAttempts} missed={Session.Missed} hp={Session.Hp} maxCombo={Session.MaxCombo} typos={Session.Typos} hits={Session.HitUnits} waves={Session.WavesStarted}/{Session.WaveCount} usable={items.Count} seen={Session.UniqueSeen} uniqueCorrect={Session.UniqueCorrect} review={Session.ReviewCount} seconds={Session.ActiveSeconds:F1} speeches={SpeechesStarted} speechReplaced={speechSlot?.Replaced} speechDropped={speechSlot?.Dropped} history={(HistoryError ?? "ok")}");
        }

        static string Percent(double? v) => v.HasValue ? $"{v.Value * 100:0}%" : "—";

        /// <summary>D-049 results: word-level outcomes and character-level typing shown separately; words deduplicated by item.</summary>
        public string ResultsText()
        {
            var s = Session;
            var t = System.TimeSpan.FromSeconds(s.ActiveSeconds);
            string text =
                $"Điểm: <b>{s.Score:N0}</b>   Combo cao nhất: <b>×{s.MaxCombo}</b>\n" +
                $"Từ đúng: <b>{s.Correct}</b>   Bỏ lỡ: <b>{s.Missed}</b>   Enter sai: <b>{s.WrongAttempts}</b>   Gõ sai chữ: <b>{s.Typos}</b>\n" +
                $"Chính xác theo từ: <b>{Percent(s.WordAccuracy)}</b>   Chính xác khi gõ: <b>{Percent(s.TypingAccuracy)}</b>\n" +
                $"Đợt {Mathf.Max(1, s.WavesStarted)} / {s.WaveCount} · đã xử lý {s.Resolved} / {config.SessionSpawns} · HP {s.Hp} / {config.StartingHp} · {(int)t.TotalMinutes:00}:{t.Seconds:00}\n" +
                $"Từ vựng: gặp <b>{s.UniqueSeen} / {items.Count}</b> ({Percent(MeteorDefenseSession.Coverage(s.UniqueSeen, items.Count))}) · trả lời đúng <b>{s.UniqueCorrect}</b> · cần ôn <b>{s.ReviewCount}</b>" +
                (items.Count > config.SessionSpawns ? $" <size=80%>(pack lớn hơn ván {config.SessionSpawns} lượt)</size>\n" : "\n") +
                $"<size=80%><color=#B8C9D5>{LearningModes.Label(Mode)} · {GameLabels.Summary(config)}</color></size>\n";
            var weak = WeakItemIds();
            if (weak.Count == 0) return text + "<size=85%>Không có từ cần ôn.</size>";
            var parts = new List<string>();
            foreach (var id in weak)
            {
                if (parts.Count == 8) break;
                var r = s.Items[id];
                var why = new List<string>();
                if (r.Missed > 0) why.Add($"lỡ ×{r.Missed}");
                if (r.WrongEnter > 0) why.Add($"Enter sai ×{r.WrongEnter}");
                if (r.Typos > 0) why.Add($"gõ sai {r.Typos}");
                parts.Add($"{items[id].SourceText} ({string.Join(", ", why)})");
            }
            string more = weak.Count > parts.Count ? $" +{weak.Count - parts.Count}" : "";
            return text + $"<size=85%>Từ cần ôn ({weak.Count}): <noparse>{string.Join(" · ", parts)}</noparse>{more}</size>";
        }

        /// <summary>Missed, wrong Enter or mistyped items (owner O3), each once, in first-seen order of the session.</summary>
        public List<string> WeakItemIds()
        {
            var list = new List<string>();
            if (Session == null) return list;
            foreach (var kv in Session.Items) if (kv.Value.Weak && items.ContainsKey(kv.Key)) list.Add(kv.Key);
            return list;
        }

        void OpenReview()
        {
            var weak = WeakItemIds();
            if (weak.Count == 0) return;
            VocabularyPreviewController.ReviewItemIds = new HashSet<string>(weak);
            Leave("VocabularyPreview");
        }

        bool historySaved;

        /// <summary>D-050: one local JSON line per finished or abandoned session; a failure is shown, never blocking.</summary>
        void SaveHistory()
        {
            if (historySaved || Session == null || !Session.IsOver) return;
            historySaved = true;
            HistoryPath = LearningHistory.Target(HistoryPathOverride, GetComponent<MeteorDefenseDevBot>() != null);
            if (HistoryPath == null) { HistoryError = "skipped (dev bot)"; return; } // bot runs are not learning
            var rec = LearningHistory.From(Session, Mode, LearningSession.Pack.PackId, LearningSession.Pack.PackVersion, seed, startedUtc, System.DateTime.UtcNow, items.Count);
            HistoryError = LearningHistory.Append(rec, HistoryPath);
            if (HistoryError != null) Toast("Không lưu được lịch sử học (ván vẫn hợp lệ)", new Color32(240, 180, 106, 255));
        }

        void ShowWaveBanner(int wave)
        {
            if (waveBanner == null) return;
            waveBanner.text = $"ĐỢT {wave} / {Session.WaveCount}" + (wave > 1 ? "\n<size=50%>thiên thạch rơi nhanh hơn</size>" : "");
            waveBanner.gameObject.SetActive(true);
        }

        // ---------- HUD and visuals ----------

        void RefreshHud()
        {
            scoreText.text = $"ĐIỂM\n<size=140%>{Session.Score:N0}</size>";
            if (waveText != null) waveText.text = $"ĐỢT {Mathf.Max(1, Session.WavesStarted)} / {Session.WaveCount}";
            if (comboText != null) comboText.text = (Session.Combo > 1 ? $"COMBO ×{Session.Combo}" : "<color=#6E8698>COMBO —</color>") + (Session.MaxCombo > 1 ? $" <size=80%><color=#B8C9D5>· cao nhất ×{Session.MaxCombo}</color></size>" : "");
            progressText.text = $"TIẾN ĐỘ\n<size=140%>{Session.Resolved} / {config.SessionSpawns}</size>";
            for (int i = 0; i < hpIcons.Count; i++) hpIcons[i].color = i < Session.Hp ? Color.white : new Color(1, 1, 1, 0.18f);
        }

        void Toast(string message, Color color)
        {
            toastText.text = $"<noparse>{message}</noparse>";
            toastText.color = color;
            toastText.gameObject.SetActive(true);
            toastUntil = Time.unscaledTime + 2f;
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

        IEnumerator FadeOut(MeteorView m, float seconds)
        {
            if (m == null) yield break;
            m.FallSpeed = 0f;
            var renderers = m.GetComponentsInChildren<SpriteRenderer>();
            var texts = m.GetComponentsInChildren<TextMeshPro>();
            for (float t = 0; t < seconds; t += Time.unscaledDeltaTime)
            {
                float a = 1f - t / seconds;
                foreach (var r in renderers) if (r) { var c = r.color; c.a = Mathf.Min(c.a, a); r.color = c; }
                foreach (var x in texts) if (x) x.alpha = a;
                yield return null;
            }
            if (m) Destroy(m.gameObject);
        }

        // G-008 owner request: red screen flash and a light shake when a meteor hits the defense line.
        Image damageFlash;
        Coroutine damageRoutine;
        Vector3 cameraHome;
        bool cameraHomeSet;
        public float DamageFlashAlpha => damageFlash != null ? damageFlash.color.a : 0f;
        public bool CameraShaken => cameraHomeSet && Camera.main != null && Camera.main.transform.position != cameraHome;

        /// <summary>Red overlay under the HUD (first child of the canvas) fading out, plus a short decaying camera shake; reduced motion: softer flash, no shake.</summary>
        IEnumerator DamageFeedback()
        {
            var cam = Camera.main;
            if (cam != null && !cameraHomeSet) { cameraHome = cam.transform.position; cameraHomeSet = true; }
            if (damageFlash == null)
            {
                var canvas = input.GetComponentInParent<Canvas>().rootCanvas;
                var go = new GameObject("DamageFlash", typeof(RectTransform), typeof(Image));
                var rt = (RectTransform)go.transform;
                rt.SetParent(canvas.transform, false);
                rt.SetAsFirstSibling();
                rt.anchorMin = Vector2.zero; rt.anchorMax = Vector2.one; rt.offsetMin = rt.offsetMax = Vector2.zero;
                damageFlash = go.GetComponent<Image>();
                damageFlash.raycastTarget = false;
            }
            bool reduced = MotionSettings.Reduced;
            float peak = reduced ? 0.14f : 0.26f, life = 0.4f, shakeTime = reduced ? 0f : 0.25f, amp = 0.12f;
            damageFlash.enabled = true;
            for (float t = 0; t < life; t += Time.deltaTime)
            {
                damageFlash.color = new Color(0.9f, 0.08f, 0.06f, peak * (1f - t / life));
                if (cam != null)
                    cam.transform.position = t < shakeTime
                        ? cameraHome + (Vector3)(Random.insideUnitCircle * amp * (1f - t / shakeTime))
                        : cameraHome;
                yield return null;
            }
            damageFlash.color = Color.clear;
            damageFlash.enabled = false;
            if (cam != null) cam.transform.position = cameraHome;
            damageRoutine = null;
        }

        IEnumerator FlashShield()
        {
            shield.enabled = true;
            for (float t = 0; t < 0.45f; t += Time.deltaTime) { shield.color = new Color(1, 1, 1, 0.8f * (1 - t / 0.45f)); yield return null; }
            shield.enabled = false;
        }

        IEnumerator FadeIn(MeteorView m, float seconds)
        {
            var renderers = m.GetComponentsInChildren<SpriteRenderer>();
            var texts = m.GetComponentsInChildren<TextMeshPro>();
            var full = new Color[renderers.Length];
            for (int i = 0; i < renderers.Length; i++) full[i] = renderers[i].color;
            for (float t = 0; t < seconds && m; t += Time.deltaTime)
            {
                float a = MotionSettings.Reduced ? 1f : t / seconds;
                for (int i = 0; i < renderers.Length; i++) if (renderers[i]) { var c = full[i]; c.a *= a; renderers[i].color = c; }
                foreach (var x in texts) if (x) x.alpha = a;
                yield return null;
            }
            if (!m) yield break;
            for (int i = 0; i < renderers.Length; i++) if (renderers[i] && renderers[i] != m.AnswerBg && renderers[i] != m.ClueBg) renderers[i].color = full[i];
            foreach (var x in texts) if (x) x.alpha = 1f;
            m.SetSelected(m.Id == Target); // repaint label backgrounds with their live state colours
            if (m.Combat != null) m.SetProgress(m.Combat.Fraction); // keep damage tint from hits during the fade
        }

        MeteorView CreateView(LearningItem item, BlankPuzzle puzzle)
        {
            var root = new GameObject("Meteor");
            root.transform.SetParent(transform, false);
            var m = root.AddComponent<MeteorView>();
            m.SpriteRoot = new GameObject("SpriteRoot").transform;
            m.SpriteRoot.SetParent(root.transform, false);
            m.Sprite = m.SpriteRoot.gameObject.AddComponent<SpriteRenderer>();
            m.Sprite.sprite = meteorSprites[Random.Range(0, meteorSprites.Length)];
            m.Sprite.sortingOrder = 10;
            m.SpriteRoot.localScale = Vector3.one * 1.15f;
            m.Reticle = NewSprite("Reticle", root.transform, reticleSprite, 9);
            m.Reticle.transform.localScale = Vector3.one * m.ReticleBase;
            m.Reticle.color = new Color(1, 1, 1, 0.75f);
            m.Reticle.enabled = false;
            m.ClueBg = NewLabelBg("ClueBg", root.transform, new Vector3(0, 1.05f, 0));
            m.Clue = NewText("Clue", "", 3f, new Color32(243, 238, 224, 255), 21);
            m.Clue.transform.SetParent(root.transform, false);
            m.Clue.transform.localPosition = new Vector3(0, 1.05f, 0);
            m.AnswerBg = NewLabelBg("AnswerBg", root.transform, new Vector3(0, -1.0f, 0));
            m.Answer = NewText("Answer", "", 3.4f, new Color32(223, 249, 255, 255), 21);
            m.Answer.transform.SetParent(root.transform, false);
            m.Answer.transform.localPosition = new Vector3(0, -1.0f, 0);
            // Damage bar between clue and rock: dark track plus cyan fill (D-044).
            m.BarBg = NewSprite("DamageBarBg", root.transform, labelSprite, 20);
            m.BarBg.color = new Color(0.02f, 0.06f, 0.1f, 0.85f);
            m.BarFill = NewSprite("DamageBarFill", root.transform, labelSprite, 21);
            m.BarFill.color = new Color32(89, 216, 255, 255);
            m.SetBar(m.BarBg, MeteorView.BarWidth, false);
            m.SetProgress(0f);
            m.Combat = TypingCombat.For(item.SourceText, puzzle, Mode);
            m.Spin = Random.Range(-30f, 30f);
            m.Bind(item, config, puzzle, "");
            return m;
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
            line.material = lineMaterial;
            line.startColor = line.endColor = new Color32(89, 216, 255, 150);
            line.sortingOrder = 5;
        }

        void BuildHp()
        {
            for (int i = 0; i < config.StartingHp; i++)
            {
                var go = new GameObject($"HP_{i}", typeof(RectTransform), typeof(Image));
                go.transform.SetParent(hpRow, false);
                var img = go.GetComponent<Image>();
                img.sprite = hpSprite; img.preserveAspect = true; img.raycastTarget = false;
                ((RectTransform)go.transform).sizeDelta = new Vector2(38, 30);
                hpIcons.Add(img);
            }
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
            main.maxParticles = 300;
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
            t.rectTransform.sizeDelta = new Vector2(8f, 1f);
            t.sortingOrder = order;
            return t;
        }

        void OnDestroy()
        {
            Time.timeScale = 1f;
            AudioListener.pause = false;
            foreach (var c in clipCache.Values) if (c != null) Destroy(c);
            clipCache.Clear();
        }

        // ---------- test hooks (automated verification only) ----------

        /// <summary>Spawns immediately, bypassing the timer. Test/dev use only.</summary>
        public void SpawnNow() { spawnTimer = 0f; TrySpawn(); }

        /// <summary>Moves a meteor onto the defense line. Test/dev use only.</summary>
        public void ForceToLine(MeteorView m) => m.transform.position = new Vector3(m.transform.position.x, DefenseY + m.Radius - 0.01f, 0f);

        public void SelectTarget(int id) => SetTarget(id);
        /// <summary>Puts text in the answer field as if typed (fires the per-meteor draft update).</summary>
        public void TypeDraft(string text) => input.text = text;
        public string CurrentInput => input.text;
        /// <summary>Dev switch -g006TimeScale (verification runs only); 1 in normal play.</summary>
        static float DevTimeScale => Mathf.Clamp(DevArgs.GetFloat(DevCommandLine.Args, "-g006TimeScale", 1f), 0.1f, 8f);
        public void TabForTests() => CycleTarget();
        public string DraftOf(int id) => drafts.TryGetValue(id, out var d) ? d : "";
        public bool PausePanelVisible => pausePanel.activeSelf;
        public bool EndPanelVisible => endPanel.activeSelf;
        public bool ErrorPanelVisible => errorPanel.activeSelf;
    }
}
