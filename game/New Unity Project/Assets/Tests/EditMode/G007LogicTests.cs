using System.Collections.Generic;
using System.Linq;
using MP1.Content;
using MP1.Game;
using NUnit.Framework;

namespace MP1.Tests
{
    public class DifficultyPresetTests
    {
        [TestCase(Difficulty.Easy, 5, 18f, 7f, 2, 0.25f)]
        [TestCase(Difficulty.Normal, 4, 15f, 6f, 3, 0.5f)]
        [TestCase(Difficulty.Hard, 3, 12f, 5f, 4, 0.75f)]
        [TestCase(Difficulty.Expert, 2, 10f, 4f, 5, 0.9f)]
        public void PresetsFollowSpecTable(Difficulty d, int hp, float fall, float spawn, int max, float ratio)
        {
            var c = new GameConfig { Hint = HintMode.NoHint, Answer = AnswerMode.FillInTheBlank }.WithDifficulty(d);
            Assert.AreEqual((hp, fall, spawn, max, ratio), (c.StartingHp, c.BaseFallSeconds, c.MinSpawnInterval, c.MaxConcurrent, c.HiddenRatio));
            Assert.AreEqual((HintMode.NoHint, AnswerMode.FillInTheBlank), (c.Hint, c.Answer), "player modes kept");
            Assert.AreEqual(30, c.SessionSpawns, "finite 30-meteor session");
            Assert.AreEqual(fall + 0.6f * 4, c.FallSeconds("abcdefghijkl"), 1e-4, "long-word allowance kept");
        }

        [Test]
        public void NormalPresetEqualsG006Baseline()
        {
            var g006 = new GameConfig();
            var n = g006.WithDifficulty(Difficulty.Normal);
            Assert.AreEqual((g006.StartingHp, g006.BaseFallSeconds, g006.MinSpawnInterval, g006.MaxConcurrent, g006.PointsPerCorrect),
                (n.StartingHp, n.BaseFallSeconds, n.MinSpawnInterval, n.MaxConcurrent, n.PointsPerCorrect));
        }
    }

    public class BlankPuzzleTests
    {
        static readonly LearningMode EN = LearningMode.EnglishToVietnamese, JA = LearningMode.JapaneseToVietnamese;

        [Test]
        public void HidesRatioOfLettersAndValidatesMissingUnitsInOrder()
        {
            var p = BlankPuzzle.Create("pineapple", 0.5f, 3);
            Assert.AreEqual(5, p.HiddenCount, "round(0.5 x 9) = 5 (away from zero)");
            string missing = p.Missing();
            Assert.IsTrue(p.Matches(missing, "pineapple", EN));
            Assert.IsTrue(p.Matches(missing.ToUpperInvariant(), "pineapple", EN), "English ignores case");
            Assert.IsFalse(p.Matches(missing + "x", "pineapple", EN), "wrong count");
            Assert.IsFalse(p.Matches("", "pineapple", EN));
            Assert.AreEqual(p.Units.Length, BlankPuzzle.Split(p.Display().Replace(BlankPuzzle.Gap.ToString(), "")).Length, "display keeps every position");
        }

        [Test]
        public void SameSeedSamePuzzleSoItIsStableAndReproducible()
        {
            var a = BlankPuzzle.Create("strawberry", 0.75f, 11);
            var b = BlankPuzzle.Create("strawberry", 0.75f, 11);
            CollectionAssert.AreEqual(a.Hidden, b.Hidden);
            Assert.AreEqual(a.Display(), b.Display());
        }

        [Test]
        public void RepeatedCharactersNeedOneEntryPerHiddenPosition()
        {
            var p = BlankPuzzle.Create("aaa", 0.9f, 1);
            Assert.AreEqual(2, p.HiddenCount, "clamped to keep one visible");
            Assert.IsTrue(p.Matches("aa", "aaa", EN));
            Assert.IsFalse(p.Matches("a", "aaa", EN));
        }

        [Test]
        public void ShortWordsAreUnsupportedAndRatioIsClamped()
        {
            Assert.IsNull(BlankPuzzle.Create("a", 0.5f, 1));
            Assert.IsFalse(BlankPuzzle.Supports("I."));
            Assert.AreEqual(1, BlankPuzzle.Create("ox", 0.25f, 1).HiddenCount, "at least one hidden");
            Assert.AreEqual(1, BlankPuzzle.Create("ox", 0.9f, 1).HiddenCount, "at least one visible");
        }

        [Test]
        public void SpacesAndPunctuationAreNeverBlankedInMultiwordTerms()
        {
            for (int seed = 0; seed < 20; seed++)
            {
                var p = BlankPuzzle.Create("ice-cream cone", 0.9f, seed);
                for (int i = 0; i < p.Units.Length; i++)
                    if (p.Units[i] == " " || p.Units[i] == "-") Assert.IsFalse(p.Hidden[i]);
                Assert.IsTrue(p.Matches(p.Missing(), "ice-cream cone", EN));
            }
        }

        [Test]
        public void JapaneseKanaKanjiAndLongVowelStayWholeAndExact()
        {
            var p = BlankPuzzle.Create("りんご", 0.25f, 5);
            Assert.AreEqual(1, p.HiddenCount);
            Assert.IsTrue(p.Matches(p.Missing(), "りんご", JA));
            var k = BlankPuzzle.Create("コーヒー", 0.5f, 2);
            Assert.AreEqual(4, k.Units.Length, "ー is its own unit");
            Assert.IsTrue(k.Matches(k.Missing(), "コーヒー", JA));
            var kanji = BlankPuzzle.Create("学校", 0.5f, 2);
            Assert.IsTrue(kanji.Matches(kanji.Missing(), "学校", JA));
            string wrongScript = kanji.Missing() == "学" ? "がく" : "こう";
            Assert.IsFalse(kanji.Matches(wrongScript, "学校", JA), "no Kana for Kanji");
        }

        [Test]
        public void CombiningMarksStayWithTheirBaseAfterNfc()
        {
            string decomposed = "café"; // NFC becomes café, 4 units
            Assert.AreEqual(4, BlankPuzzle.Split(decomposed).Length);
            var p = BlankPuzzle.Create(decomposed, 0.9f, 1);
            Assert.IsTrue(p.Matches(p.Missing(), "café", EN));
        }
    }

    public class GameCompatibilityTests
    {
        static LearningItem It(string id, string src, string vi, string imgSha) => new LearningItem
        {
            ItemId = id, SourceText = src, Meaning = vi,
            Image = imgSha == null ? null : new MediaAsset { Sha256 = imgSha }, GameplayEligible = true
        };

        static List<LearningItem> Pool(int n) => Enumerable.Range(0, n).Select(i => It($"i{i}", $"word{i}", $"nghĩa {i}", $"sha{i}")).ToList();

        [Test]
        public void G006DefaultAcceptsTenDistinctItems()
        {
            var r = GameCompatibility.Check(Pool(10), new GameConfig(), LearningMode.EnglishToVietnamese);
            Assert.IsTrue(r.CanStart);
            Assert.AreEqual(10, r.Usable.Count);
        }

        [Test]
        public void MissingImagesDoNotAffectGameplayEligibility()
        {
            var pool = Pool(10);
            pool[0].Image = null; // images are not used in gameplay (D-043)
            var r = GameCompatibility.Check(pool, new GameConfig(), LearningMode.EnglishToVietnamese);
            Assert.AreEqual(10, r.Usable.Count);
            Assert.IsTrue(r.CanStart);
        }

        [Test]
        public void SameMeaningIsAmbiguousWithoutAFirstLetterHint()
        {
            var pool = Pool(11);
            pool[1].Meaning = pool[0].Meaning; // word0 / word1 share the clue and the first letter
            pool[2].Meaning = pool[3].Meaning; pool[2].SourceText = "xylophone";
            var noHint = GameCompatibility.Check(pool, new GameConfig { Hint = HintMode.NoHint }, LearningMode.EnglishToVietnamese);
            Assert.AreEqual(7, noHint.Usable.Count);
            var textOnly = GameCompatibility.Check(pool, new GameConfig { Hint = HintMode.TextOnly }, LearningMode.EnglishToVietnamese);
            Assert.AreEqual(9, textOnly.Usable.Count, "first letter separates xylophone from word3");
        }

        [Test]
        public void FillInTheBlankExcludesTooShortTermsWithoutChangingModes()
        {
            var pool = Pool(10);
            pool[0].SourceText = "I";
            var cfg = new GameConfig { Answer = AnswerMode.FillInTheBlank };
            var r = GameCompatibility.Check(pool, cfg, LearningMode.EnglishToVietnamese);
            Assert.AreEqual(9, r.Usable.Count);
            Assert.IsFalse(r.CanStart);
            Assert.AreEqual(AnswerMode.FillInTheBlank, cfg.Answer, "never silently switched");
        }
    }

    public class TargetingModeTests
    {
        static List<TargetCandidate> Two => new List<TargetCandidate> { new TargetCandidate(1, 1, 5f), new TargetCandidate(2, 2, 1f) };

        [Test]
        public void HybridKeepsTargetAndAcquiresWhenNone()
        {
            Assert.AreEqual(1, TargetSelector.Resolve(1, Two, TargetingMode.Hybrid, false));
            Assert.AreEqual(2, TargetSelector.Resolve(-1, Two, TargetingMode.Hybrid, false));
            Assert.IsTrue(TargetSelector.TabAllowed(TargetingMode.Hybrid));
        }

        [Test]
        public void AutoFollowsMostUrgentUnlessTyping()
        {
            Assert.AreEqual(2, TargetSelector.Resolve(1, Two, TargetingMode.Auto, false));
            Assert.AreEqual(1, TargetSelector.Resolve(1, Two, TargetingMode.Auto, true), "stable while typing");
            Assert.IsFalse(TargetSelector.TabAllowed(TargetingMode.Auto));
        }

        [Test]
        public void ManualNeverAcquiresByItself()
        {
            Assert.AreEqual(-1, TargetSelector.Resolve(-1, Two, TargetingMode.Manual, false));
            Assert.AreEqual(1, TargetSelector.Resolve(1, Two, TargetingMode.Manual, false));
            Assert.AreEqual(-1, TargetSelector.Resolve(7, Two, TargetingMode.Manual, true), "removed target released");
            Assert.AreEqual(2, TargetSelector.Cycle(-1, Two), "Tab acquires the most urgent first");
        }
    }

    public class SpawnLayoutTests
    {
        [TestCase(7.2f, 1.4f, 7.2f)]   // short label: edge lane unchanged
        [TestCase(7.2f, 6.0f, 6.35f)]  // long Fill pattern: pulled in so its right edge stays on screen
        [TestCase(-7.2f, 6.0f, -6.35f)]
        [TestCase(3f, 30f, 0f)]        // wider than the screen: centred
        public void LongLabelsStayInsideTheScreen(float lane, float width, float expected)
        {
            float x = SpawnLayout.ClampX(lane, 9.6f, width);
            Assert.AreEqual(expected, x, 1e-4);
            if (width < 19f) Assert.LessOrEqual(System.Math.Abs(x) + width / 2f, 9.6f - SpawnLayout.SideMargin + 1e-4);
        }

        [TestCase(1.4f)]
        [TestCase(2.6f)]
        public void StackTopStaysBelowHud(float stackTop)
        {
            float y = SpawnLayout.SpawnY(5.4f, stackTop);
            Assert.LessOrEqual(y + stackTop, SpawnLayout.SafeTop(5.4f));
            Assert.Greater(SpawnLayout.SafeTop(5.4f), 4.2f, "HUD band is about 112 of 1080 px");
            Assert.Less(SpawnLayout.SafeTop(5.4f), 5.4f - 1.0f);
        }
    }
}
