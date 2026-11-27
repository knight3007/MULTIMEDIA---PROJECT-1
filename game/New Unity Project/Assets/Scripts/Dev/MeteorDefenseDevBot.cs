using System.Collections;
using MP1.Core;
using MP1.Game;
using UnityEngine;

namespace MP1.Dev
{
    /// <summary>
    /// VERIFICATION ONLY (G-006 build captures and recordings). Added by <see cref="MeteorDefenseController"/> only when
    /// <c>-g006Bot win|lose</c> is on the command line. "win" types each locked target's answer one text element at a
    /// time (gap <c>-g007TypeGap</c>, default 0.08 s) through the production input path, so every unit fires a laser and
    /// the last one destroys the meteor; with <c>-g006WrongFirst</c> it types one wrong unit first, then deletes it.
    /// "lose" never answers, so meteors breach. Normal players never get this component.
    /// </summary>
    public class MeteorDefenseDevBot : MonoBehaviour
    {
        MeteorDefenseController game;
        string mode;
        bool wrongDone, tabDemoDone;

        public static void AttachIfRequested(MeteorDefenseController controller)
        {
            string m = DevArgs.Get(DevCommandLine.Args, "-g006Bot");
            if (m == null) return;
            var bot = controller.gameObject.AddComponent<MeteorDefenseDevBot>();
            bot.game = controller;
            bot.mode = m.ToLowerInvariant();
            bot.wrongDone = !DevArgs.Has(DevCommandLine.Args, "-g006WrongFirst");
        }

        IEnumerator Start()
        {
            float pauseAt = DevArgs.GetFloat(DevCommandLine.Args, "-g006PauseAt", -1f);
            if (pauseAt > 0f) StartCoroutine(PauseLater(pauseAt));
            if (mode != "win") yield break;
            float delay = DevArgs.GetFloat(DevCommandLine.Args, "-g006BotDelay", 2.5f);
            while (game.Session != null && !game.Session.IsOver)
            {
                yield return new WaitForSeconds(delay);
                if (game.Session.State != SessionState.Playing) continue;
                if (game.Target < 0) { if (game.Config.Targeting == TargetingMode.Manual) game.TabForTests(); continue; }
                var target = game.Active.Find(v => v.Id == game.Target);
                if (target == null) continue;
                // G-007-R2: type one unit at a time through the production input path; the last correct unit destroys
                // the meteor without Enter. -g006WrongFirst first types one wrong unit, then deletes it.
                string answer = target.Puzzle?.Missing() ?? target.Item.SourceText;
                var units = new System.Globalization.StringInfo(answer);
                float gap = DevArgs.GetFloat(DevCommandLine.Args, "-g007TypeGap", 0.08f);
                if (!tabDemoDone && DevArgs.Has(DevCommandLine.Args, "-g007TabDemo") && game.Active.Count >= 2 && units.LengthInTextElements >= 4)
                {
                    // Type half of this answer, Tab away (its damage and draft stay on it), finish the other meteor.
                    tabDemoDone = true;
                    for (int i = 1; i <= units.LengthInTextElements / 2; i++) { game.TypeDraft(units.SubstringByTextElements(0, i)); yield return new WaitForSeconds(gap); }
                    yield return new WaitForSeconds(0.8f);
                    game.TabForTests();
                    yield return new WaitForSeconds(0.5f);
                    continue;
                }
                for (int i = 1; i <= units.LengthInTextElements && target != null && game.Target == target.Id; i++)
                {
                    string prefix = units.SubstringByTextElements(0, i);
                    if (!wrongDone && i == 2)
                    {
                        game.TypeDraft(units.SubstringByTextElements(0, 1) + "#");
                        yield return new WaitForSeconds(0.6f);
                        game.TypeDraft(units.SubstringByTextElements(0, 1));
                        yield return new WaitForSeconds(0.2f);
                        wrongDone = true;
                    }
                    game.TypeDraft(prefix);
                    yield return new WaitForSeconds(gap);
                }
            }
        }

        IEnumerator PauseLater(float seconds)
        {
            yield return new WaitForSecondsRealtime(seconds);
            game.Pause();
        }
    }
}
