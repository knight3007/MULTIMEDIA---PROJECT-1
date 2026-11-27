using MP1.Content;
using MP1.Core;
using TMPro;
using UnityEngine;

namespace MP1.Game
{
    /// <summary>
    /// One production meteor (G-006/G-007). Its sprite rotates; the Vietnamese clue (with optional first-unit hint) above
    /// and the answer label below (Layout A / D-029) are siblings of the sprite, so text stays upright. Movement uses
    /// scaled time, so pausing (timeScale 0) freezes it. Outcome logic lives in <see cref="MeteorDefenseSession"/>.
    /// </summary>
    public class MeteorView : MonoBehaviour
    {
        public Transform SpriteRoot;
        public SpriteRenderer Sprite, Reticle, ClueBg, AnswerBg, BarBg, BarFill;
        [System.NonSerialized] public TypingCombat Combat; // G-007-R2 damage progress, owned by this meteor
        public TextMeshPro Clue, Answer;
        public int Id, SpawnOrder;
        [System.NonSerialized] public LearningItem Item; // runtime data from LearningSession, never saved in the scene
        [System.NonSerialized] public BlankPuzzle Puzzle; // Fill-in-the-Blank only; fixed for the meteor's lifetime
        [System.NonSerialized] public GameConfig Config;
        public float FallSpeed, Spin, ReticleBase = 2.6f, Radius = 0.55f;

        public const float ClueY = 1.05f;
        static readonly Color LabelBg = new Color(0.03f, 0.11f, 0.18f, 0.9f);
        static readonly Color LabelBgSelected = new Color(0.05f, 0.24f, 0.33f, 0.97f);
        static readonly Color WrongBg = new Color(0.36f, 0.09f, 0.12f, 0.97f);
        float wrongUntil;
        bool selected;

        public float BottomY => transform.position.y - Radius;
        public float LabelWidth => Mathf.Max(ClueBg.size.x, AnswerBg.size.x);

        /// <summary>Height of the clue label's top above the meteor centre, for the safe spawn area.</summary>
        public float StackTop => ClueY + ClueBg.size.y / 2f;

        public void Bind(LearningItem item, GameConfig config, BlankPuzzle puzzle, string draft)
        {
            Item = item; Config = config; Puzzle = puzzle;
            string first = config.ShowsFirstUnit ? System.Globalization.StringInfo.GetNextTextElement(item.SourceText ?? "", 0) : null;
            Clue.text = "<noparse>" + item.Meaning + "</noparse>" + (first != null ? $"<color=#59D8FF>  ·  <noparse>{first}</noparse>…</color>" : "");
            Fit(Clue, ClueBg);
            SetDraft(draft);
        }

        /// <summary>Shows this meteor's own draft: full word as typed, or the puzzle with typed units in its blanks.</summary>
        public void SetDraft(string draft)
        {
            if (Puzzle != null) Answer.text = "<noparse>" + Puzzle.Display(draft) + "</noparse>";
            else Answer.text = string.IsNullOrEmpty(draft) ? "…" : "<noparse>" + draft + "</noparse>▏";
            Fit(Answer, AnswerBg);
            Paint();
        }

        public const float BarWidth = 1.3f, BarHeight = 0.1f, BarY = 0.68f;
        float shakeUntil;

        /// <summary>Places a plain (non-sliced) bar sprite of this width; a left-anchored bar grows from the track's left edge.</summary>
        public void SetBar(SpriteRenderer bar, float width, bool leftAnchored)
        {
            var s = bar.sprite.bounds.size;
            bar.transform.localScale = new Vector3(Mathf.Max(0.001f, width) / s.x, BarHeight / s.y, 1f);
            bar.transform.localPosition = new Vector3(leftAnchored ? -BarWidth / 2f + width / 2f : 0f, BarY, 0);
        }

        /// <summary>Damage bar (left to right) plus a light reddening of the rock as hits land; no new sprites needed.</summary>
        public void SetProgress(float fraction)
        {
            if (BarFill) SetBar(BarFill, BarWidth * Mathf.Clamp01(fraction), true);
            if (Sprite) Sprite.color = Color.Lerp(Color.white, new Color(1f, 0.55f, 0.45f), Mathf.Clamp01(fraction) * 0.8f);
        }

        public void Shake(float seconds = 0.12f)
        {
            if (!MotionSettings.Reduced) shakeUntil = Time.time + seconds;
        }

        public void SetSelected(bool on)
        {
            selected = on;
            Reticle.enabled = on;
            Answer.fontStyle = on ? FontStyles.Bold : FontStyles.Normal; // target change readable without colour
            Paint();
        }

        public void FlashWrong(float seconds = 0.6f)
        {
            wrongUntil = Time.unscaledTime + seconds;
            Paint();
        }

        void Paint()
        {
            AnswerBg.color = Time.unscaledTime < wrongUntil ? WrongBg : selected ? LabelBgSelected : LabelBg;
            ClueBg.color = LabelBg;
        }

        static void Fit(TextMeshPro text, SpriteRenderer bg)
        {
            Vector2 size = text.GetPreferredValues(text.text, 8f, 2f);
            bg.size = new Vector2(Mathf.Max(1.4f, size.x + 0.45f), size.y + 0.22f);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            transform.position += Vector3.down * (FallSpeed * dt);
            if (wrongUntil > 0 && Time.unscaledTime >= wrongUntil) { wrongUntil = 0; Paint(); }
            if (MotionSettings.Reduced) return;
            SpriteRoot.localPosition = Time.time < shakeUntil ? (Vector3)(Random.insideUnitCircle * 0.06f) : Vector3.zero;
            SpriteRoot.Rotate(0f, 0f, Spin * dt);
            if (Reticle.enabled) Reticle.transform.localScale = Vector3.one * (ReticleBase * (1f + Mathf.Sin(Time.time * 4f) * 0.04f));
        }
    }
}
