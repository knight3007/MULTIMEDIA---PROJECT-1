using MP1.Content;
using MP1.Game;
using NUnit.Framework;

namespace MP1.Tests
{
    public class TypingCombatTests
    {
        static readonly LearningMode EN = LearningMode.EnglishToVietnamese, JA = LearningMode.JapaneseToVietnamese;

        [Test]
        public void EachCorrectCharacterIsOneHitAndTheLastCompletes()
        {
            var c = TypingCombat.For("pineapple", null, EN);
            Assert.AreEqual(9, c.Required);
            string typed = "";
            foreach (char ch in "pineapple")
            {
                typed += ch;
                var s = c.Update(typed);
                Assert.AreEqual(1, s.NewHits, typed);
                Assert.IsFalse(s.Error);
                Assert.AreEqual(typed == "pineapple", s.Complete);
            }
            Assert.AreEqual(9, c.Hits);
        }

        [Test]
        public void WrongCharacterDealsNoDamageAndReportsOnce()
        {
            var c = TypingCombat.For("cat", null, EN);
            c.Update("c");
            var s = c.Update("cx");
            Assert.AreEqual((0, true, false), (s.NewHits, s.Error, s.Complete));
            Assert.IsFalse(c.Update("cx").Error, "unchanged input: nothing");
            Assert.AreEqual(1, c.Hits);
            Assert.IsTrue(c.Update("cxy").Error, "more wrong text: feedback again");
            Assert.IsFalse(c.Update("cx").Error, "deleting wrong text is not a new error");
        }

        [Test]
        public void UnchangedInputAndBackspaceRetypeNeverDuplicateDamage()
        {
            var c = TypingCombat.For("cat", null, EN);
            Assert.AreEqual(2, c.Update("ca").NewHits);
            Assert.AreEqual(0, c.Update("ca").NewHits);
            Assert.AreEqual(0, c.Update("c").NewHits);
            Assert.AreEqual(0, c.Update("ca").NewHits, "retyping earned progress gives nothing");
            Assert.AreEqual(0, c.Update("").NewHits);
            Assert.AreEqual(2, c.Hits, "damage is never undone or farmed");
            var s = c.Update("cat");
            Assert.AreEqual((1, true), (s.NewHits, s.Complete));
        }

        [Test]
        public void MiddleEditBreaksCompletionUntilFixed()
        {
            var c = TypingCombat.For("cat", null, EN);
            c.Update("ca");
            Assert.IsFalse(c.Update("cbt").Complete);
            Assert.AreEqual(2, c.Hits, "no false progress from the wrong middle unit");
            Assert.IsTrue(c.Update("cat").Complete);
        }

        [Test]
        public void PasteOfTheWholeAnswerCountsAllUnitsAtOnce()
        {
            var c = TypingCombat.For("backpack", null, EN);
            var s = c.Update("BACKPACK");
            Assert.AreEqual((8, true), (s.NewHits, s.Complete), "English ignores case");
        }

        [Test]
        public void SpacesAndPunctuationMustBeTypedButAreNotShots()
        {
            var c = TypingCombat.For("ice-cream cone", null, EN);
            Assert.AreEqual(12, c.Required);
            Assert.AreEqual(3, c.Update("ice").NewHits);
            Assert.AreEqual(0, c.Update("ice-").NewHits);
            Assert.IsFalse(c.Update("icecream").Complete, "separator still required");
            Assert.IsTrue(c.Update("ice-cream cone").Complete);
        }

        [Test]
        public void FillInTheBlankNeedsOnlyTheMissingUnits()
        {
            var p = BlankPuzzle.Create("pineapple", 0.25f, 4);
            var c = TypingCombat.For("pineapple", p, EN);
            Assert.AreEqual(p.HiddenCount, c.Required);
            var s = c.Update(p.Missing());
            Assert.AreEqual((p.HiddenCount, true), (s.NewHits, s.Complete));
            Assert.IsTrue(p.Matches(p.Missing(), "pineapple", EN), "final validator agrees");
        }

        [Test]
        public void RepeatedLettersEachNeedAHit()
        {
            var c = TypingCombat.For("aaa", null, EN);
            Assert.AreEqual(1, c.Update("a").NewHits);
            Assert.AreEqual(1, c.Update("aa").NewHits);
            Assert.IsTrue(c.Update("aaa").Complete);
        }

        [Test]
        public void JapaneseCommittedTextCanAdvanceSeveralUnitsAndMustMatchScript()
        {
            var c = TypingCombat.For("ジャンプする", null, JA);
            Assert.AreEqual(6, c.Required, "small ャ is its own unit");
            Assert.AreEqual(4, c.Update("ジャンプ").NewHits, "one IME commit, four units");
            Assert.IsTrue(c.Update("ジャンプする").Complete);
            var k = TypingCombat.For("学校", null, JA);
            Assert.IsTrue(k.Update("がっこう").Error, "Kana for Kanji is wrong");
            Assert.AreEqual(0, k.Hits);
            Assert.IsTrue(TypingCombat.For("りんご", null, JA).Update("リ").Error, "Katakana for Hiragana is wrong");
        }

        [Test]
        public void NormalisationJoinsDecomposedInput()
        {
            var c = TypingCombat.For("café", null, EN);
            Assert.IsTrue(c.Update("café").Complete);
            Assert.AreEqual(4, c.Hits);
        }
    }
}
