using System;
using System.Collections.Generic;
using System.Text;
using MP1.Content;
using MP1.Core;
using MP1.Dev;
using MP1.UI;
using TMPro;
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.UI;

namespace MP1.Game
{
    /// <summary>
    /// G-007.1 Game Configuration screen: Library (pack + language) → here → Meteor Defense. Reads only
    /// <see cref="LearningSession"/> (no second pack reader), checks the choice with <see cref="GameCompatibility"/>,
    /// previews a real eligible question and stores the choice in <see cref="GameConfig.Selected"/> for play and Replay.
    /// </summary>
    public class GameSetupController : MonoBehaviour
    {
        [SerializeField] TMP_Text packText, countText, explainText, statusText, previewClue, previewAnswer, previewCaption;
        [SerializeField] Button[] difficultyButtons, hintButtons, answerButtons, targetButtons;
        [SerializeField] Button startButton, nextSampleButton;

        public GameConfig Config { get; private set; }
        public GameCompatibility.Result Compat { get; private set; }
        public LearningItem Sample { get; private set; }
        public Button StartButton => startButton;

        static readonly Color On = Color.white, Off = new Color(0.52f, 0.62f, 0.7f, 1f);
        int sampleIndex;

        void Start()
        {
            Config = GameConfig.Selected.Clone();
            ApplyDevArgs();
            for (int i = 0; i < difficultyButtons.Length; i++) { var d = (Difficulty)i; difficultyButtons[i].onClick.AddListener(() => SetDifficulty(d)); }
            for (int i = 0; i < hintButtons.Length; i++) { var h = (HintMode)i; hintButtons[i].onClick.AddListener(() => SetHint(h)); }
            for (int i = 0; i < answerButtons.Length; i++) { var a = (AnswerMode)i; answerButtons[i].onClick.AddListener(() => SetAnswer(a)); }
            for (int i = 0; i < targetButtons.Length; i++) { var t = (TargetingMode)i; targetButtons[i].onClick.AddListener(() => SetTargeting(t)); }
            startButton.onClick.AddListener(StartGame);
            nextSampleButton.onClick.AddListener(() => { sampleIndex++; Refresh(); });
            Refresh();
            EventSystem.current.SetSelectedGameObject(startButton.interactable ? startButton.gameObject : difficultyButtons[(int)Config.Difficulty].gameObject);
            // Verification runs (-g006Play) go straight on unless -g007Hold keeps this screen for a capture.
            if (DevArgs.Get(DevCommandLine.Args, "-g006Play") != null && !DevArgs.Has(DevCommandLine.Args, "-g007Hold") && startButton.interactable)
                Invoke(nameof(StartGame), 0.3f);
        }

        void ApplyDevArgs()
        {
            if (Parse<Difficulty>("-g007Difficulty") is Difficulty d) Config = Config.WithDifficulty(d);
            if (Parse<HintMode>("-g007Hint") is HintMode h) Config.Hint = h;
            if (Parse<AnswerMode>("-g007Answer") is AnswerMode a) Config.Answer = a;
            if (Parse<TargetingMode>("-g007Target") is TargetingMode t) Config.Targeting = t;
        }

        static T? Parse<T>(string flag) where T : struct =>
            DevArgs.Get(DevCommandLine.Args, flag) is string s && Enum.TryParse<T>(s, true, out var v) ? v : (T?)null;

        public void SetDifficulty(Difficulty d) { Config = Config.WithDifficulty(d); Refresh(); }
        public void SetHint(HintMode h) { Config.Hint = h; Refresh(); }
        public void SetAnswer(AnswerMode a) { Config.Answer = a; Refresh(); }
        public void SetTargeting(TargetingMode t) { Config.Targeting = t; Refresh(); }

        void Refresh()
        {
            Mark(difficultyButtons, (int)Config.Difficulty);
            Mark(hintButtons, (int)Config.Hint);
            Mark(answerButtons, (int)Config.Answer);
            Mark(targetButtons, (int)Config.Targeting);
            explainText.text = GameLabels.Explain(Config);

            if (!LearningSession.HasSelection)
            {
                packText.text = "Chưa chọn Content Pack";
                countText.text = "";
                Block("Quay lại Thư viện để chọn pack và ngôn ngữ.");
                return;
            }
            var pack = LearningSession.Pack;
            packText.text = $"<noparse>{pack.PackId}</noparse> · v{pack.PackVersion}  ·  {LearningModes.Label(LearningSession.Mode)}";
            Compat = GameCompatibility.Check(LearningSession.EligibleItems, Config, LearningSession.Mode);
            var sb = new StringBuilder($"Từ dùng được với cấu hình này: <b>{Compat.Usable.Count}</b> / {LearningSession.EligibleItems.Count}");
            if (Compat.Excluded.Count > 0)
            {
                sb.Append($"  ·  loại {Compat.Excluded.Count}: ");
                for (int i = 0; i < Compat.Excluded.Count && i < 4; i++)
                    sb.Append(i > 0 ? "; " : "").Append("<noparse>").Append(Compat.Excluded[i].Key.SourceText).Append("</noparse> (").Append(Compat.Excluded[i].Value).Append(')');
                if (Compat.Excluded.Count > 4) sb.Append("; …");
            }
            countText.text = sb.ToString();
            string why = GameEntry.WhyCannotStart(Config);
            if (why != null) Block(why);
            else
            {
                startButton.interactable = true;
                statusText.text = "<color=#83E2B1>Sẵn sàng.</color> Nhấn Bắt đầu.";
            }
            ShowSample();
        }

        void Block(string why)
        {
            startButton.interactable = false;
            statusText.text = $"<color=#F2D4A7>Chưa thể bắt đầu:</color> {why}";
            if (!LearningSession.HasSelection) { Sample = null; previewClue.text = previewAnswer.text = ""; }
            else ShowSample();
        }

        void Mark(Button[] group, int selected)
        {
            for (int i = 0; i < group.Length; i++)
            {
                group[i].image.color = i == selected ? On : Off;
                var label = group[i].GetComponentInChildren<TMP_Text>();
                label.fontStyle = i == selected ? FontStyles.Bold | FontStyles.Underline : FontStyles.Normal; // not colour alone
            }
        }

        /// <summary>One real question as it will look in play; updates whenever an option changes.</summary>
        void ShowSample()
        {
            var pool = Compat != null && Compat.Usable.Count > 0 ? Compat.Usable : LearningSession.EligibleItems;
            if (pool.Count == 0) { Sample = null; previewClue.text = "Không có từ nào để xem trước."; previewAnswer.text = ""; return; }
            Sample = pool[sampleIndex % pool.Count];
            string first = Config.ShowsFirstUnit ? System.Globalization.StringInfo.GetNextTextElement(Sample.SourceText, 0) : null;
            previewClue.text = "<noparse>" + Sample.Meaning + "</noparse>" + (first != null ? $"<color=#59D8FF>  ·  <noparse>{first}</noparse>…</color>" : "");
            var puzzle = Config.Answer == AnswerMode.FillInTheBlank ? BlankPuzzle.Create(Sample.SourceText, Config.HiddenRatio, sampleIndex + 1) : null;
            previewAnswer.text = puzzle != null ? "<noparse>" + puzzle.Display() + "</noparse>" : Config.Answer == AnswerMode.FillInTheBlank ? "(từ quá ngắn)" : "…";
            previewCaption.text = puzzle != null ? $"Cần gõ: <noparse>{puzzle.Missing()}</noparse>  ·  đáp án đủ: <noparse>{Sample.SourceText}</noparse>" : $"Đáp án: <noparse>{Sample.SourceText}</noparse>";
        }

        public void StartGame()
        {
            if (!startButton.interactable) return;
            GameConfig.Selected = Config.Clone();
            SceneNav.Load(GameEntry.SceneName);
        }
    }
}
