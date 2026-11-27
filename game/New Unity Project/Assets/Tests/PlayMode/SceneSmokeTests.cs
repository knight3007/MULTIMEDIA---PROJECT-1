using System.Collections;
using System.Linq;
using MP1.Background;
using MP1.Sandbox;
using NUnit.Framework;
using TMPro;
using UnityEngine;
using UnityEngine.SceneManagement;
using UnityEngine.TestTools;
using UnityEngine.UI;

namespace MP1.Tests
{
    public class SceneSmokeTests
    {
        [UnityTest]
        public IEnumerator EachSceneLoadsWithBackgroundAndNoMissingReferences([Values("MainMenu", "VocabularyLibrary", "VocabularyPreview", "GameSetup", "MeteorDefense", "TypographyInput", "GameplaySandbox", "MediaProbe")] string scene)
        {
            yield return SceneManager.LoadSceneAsync(scene);
            yield return null; yield return null;
            var bg = Object.FindFirstObjectByType<GalaxyBackground>();
            Assert.IsNotNull(bg, "background present");
            Assert.Greater(bg.StarCount, 50, "stars created");
            foreach (var t in Object.FindObjectsByType<TMP_Text>())
                Assert.IsNotNull(t.font, $"{t.name} has a font");
            foreach (var img in Object.FindObjectsByType<Image>())
                Assert.IsNotNull(img.sprite, $"{img.name} has a sprite");
        }

        [UnityTest]
        public IEnumerator SecondaryScreensHaveVisibleBackButtonThatReturnsToMenu([Values("TypographyInput", "GameplaySandbox", "MediaProbe", "VocabularyLibrary")] string scene)
        {
            yield return SceneManager.LoadSceneAsync(scene);
            yield return null;
            var back = Object.FindObjectsByType<Button>().SingleOrDefault(b => b.name == "BackButton");
            Assert.IsNotNull(back, "Back button present");
            Assert.IsTrue(back.interactable && back.gameObject.activeInHierarchy, "clickable");
            StringAssert.Contains("Quay lại", back.GetComponentInChildren<TMP_Text>().text);
            Assert.Greater(back.onClick.GetPersistentEventCount(), 0, "wired in the scene, not only at runtime");
            var rect = (RectTransform)back.transform;
            foreach (var other in Object.FindObjectsByType<Selectable>())
            {
                if (other == back) continue;
                var r = WorldRect((RectTransform)other.transform);
                var mask = other.GetComponentInParent<RectMask2D>();
                if (mask != null) r = Clip(r, WorldRect(mask.rectTransform)); // scrolled-away rows are clipped, not visible
                if (r.width <= 0 || r.height <= 0) continue;
                Assert.IsFalse(WorldRect(rect).Overlaps(r), $"Back overlaps {other.name}");
            }
            back.onClick.Invoke();
            yield return null; yield return null;
            Assert.AreEqual("MainMenu", SceneManager.GetActiveScene().name);
        }

        static Rect Clip(Rect a, Rect b) => Rect.MinMaxRect(Mathf.Max(a.xMin, b.xMin), Mathf.Max(a.yMin, b.yMin), Mathf.Min(a.xMax, b.xMax), Mathf.Min(a.yMax, b.yMax));

        static Rect WorldRect(RectTransform rt)
        {
            var c = new Vector3[4];
            rt.GetWorldCorners(c);
            return new Rect(c[0].x, c[0].y, c[2].x - c[0].x, c[2].y - c[0].y);
        }

        [UnityTest]
        public IEnumerator BackgroundIsDenserWithThreeDistinctLayers()
        {
            yield return SceneManager.LoadSceneAsync("MainMenu");
            yield return null;
            var bg = Object.FindFirstObjectByType<GalaxyBackground>();
            Assert.GreaterOrEqual(bg.StarCount, 320, "R1: at least 2x the old 160 stars");
            var counts = bg.CountPerLayer();
            Assert.AreEqual(3, counts.Length);
            Assert.Greater(counts[0], counts[1]);
            Assert.Greater(counts[1], counts[2], "few large near stars, many small far ones");
        }

        [UnityTest]
        public IEnumerator MainMenuOnlyEnablesImplementedEntries()
        {
            yield return SceneManager.LoadSceneAsync("MainMenu");
            yield return null;
            var buttons = Object.FindObjectsByType<Button>();
            Assert.IsFalse(buttons.Any(b => b.name == "Flashcard"), "G-005 cancelled: Flashcard merged into the Vocabulary Library");
            foreach (var name in new[] { "Settings" })
                Assert.IsFalse(buttons.Single(b => b.name == name).interactable, $"{name} must be visibly unavailable");
            foreach (var name in new[] { "PlayGame", "Library", "Exit", "TypographyInput", "GameplaySandbox", "MediaProbe" })
                Assert.IsTrue(buttons.Single(b => b.name == name).interactable, $"{name} works");
        }

        [UnityTest]
        public IEnumerator SandboxLabelsStayUprightWhileSpritesRotate()
        {
            yield return SceneManager.LoadSceneAsync("GameplaySandbox");
            yield return new WaitForSeconds(1f);
            var meteors = Object.FindObjectsByType<SandboxMeteor>();
            Assert.GreaterOrEqual(meteors.Length, 3);
            bool anyRotated = false;
            foreach (var m in meteors)
            {
                anyRotated |= Mathf.Abs(Mathf.DeltaAngle(0, m.SpriteRoot.eulerAngles.z)) > 1f;
                Assert.AreEqual(0f, Mathf.DeltaAngle(0, m.Clue.transform.eulerAngles.z), 0.01f, "clue upright");
                Assert.AreEqual(0f, Mathf.DeltaAngle(0, m.Answer.transform.eulerAngles.z), 0.01f, "answer upright");
            }
            Assert.IsTrue(anyRotated, "at least one sprite actually rotated");
        }

        [UnityTest]
        public IEnumerator CorrectAnswerResolvesTargetAndScores()
        {
            yield return SceneManager.LoadSceneAsync("GameplaySandbox");
            yield return null;
            var ctrl = Object.FindFirstObjectByType<SandboxController>();
            var target = ctrl.Meteors[ctrl.Target];
            var input = Object.FindFirstObjectByType<TMP_InputField>();
            input.text = target.Expected;
            ctrl.SendMessage("Submit");
            yield return new WaitForSeconds(0.2f);
            Assert.IsTrue(target.Resolved, "meteor destroyed");
            Assert.IsFalse(target.gameObject.activeSelf, "hidden after the hit");
            StringAssert.Contains("100", Object.FindObjectsByType<TMP_Text>().First(t => t.name == "Score").text);
        }
    }
}
