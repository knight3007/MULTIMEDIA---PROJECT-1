using MP1.Core;
using TMPro;
using UnityEngine;

namespace MP1.Sandbox
{
    /// <summary>
    /// PROTOTYPE ONLY (G-003.7). A falling meteor whose sprite rotates while its Vietnamese clue (above) and answer
    /// label (below, Layout A per D-029) stay upright because they are siblings of the rotating sprite, not children.
    /// </summary>
    public class SandboxMeteor : MonoBehaviour
    {
        public Transform SpriteRoot;
        public SpriteRenderer Sprite, Reticle, ClueBg, AnswerBg;
        public TextMeshPro Clue, Answer;
        public float FallSpeed = 0.4f, Spin = 25f, ReticleBase = 2.6f;
        public string Expected;
        public bool Resolved;

        static readonly Color LabelBg = new Color(0.03f, 0.11f, 0.18f, 0.88f);
        static readonly Color LabelBgSelected = new Color(0.05f, 0.2f, 0.3f, 0.95f);

        public void Bind(string clue, string expected)
        {
            Expected = expected;
            Resolved = false;
            Clue.text = clue;
            SetDraft("");
            Fit(Clue, ClueBg);
            gameObject.SetActive(true);
        }

        public void SetSelected(bool selected)
        {
            Reticle.enabled = selected;
            AnswerBg.color = selected ? LabelBgSelected : LabelBg;
            ClueBg.color = LabelBg;
        }

        /// <summary>Shows this meteor's own draft, or a first-character hint when empty.</summary>
        public void SetDraft(string draft)
        {
            Answer.text = string.IsNullOrEmpty(draft) ? (Expected.Length > 0 ? Expected.Substring(0, 1) + " …" : "…") : draft + "▏";
            Fit(Answer, AnswerBg);
        }

        static void Fit(TextMeshPro text, SpriteRenderer bg)
        {
            Vector2 size = text.GetPreferredValues(text.text, 6f, 2f);
            bg.size = new Vector2(Mathf.Max(1.4f, size.x + 0.45f), size.y + 0.22f);
        }

        void Update()
        {
            if (Resolved) return;
            float dt = Time.deltaTime;
            transform.position += Vector3.down * (FallSpeed * dt);
            if (!MotionSettings.Reduced)
            {
                SpriteRoot.Rotate(0f, 0f, Spin * dt);
                if (Reticle.enabled) Reticle.transform.localScale = Vector3.one * (ReticleBase * (1f + Mathf.Sin(Time.time * 4f) * 0.04f));
            }
        }
    }
}
