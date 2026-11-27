using System.IO;
using MP1.Content;
using MP1.Game;
using NUnit.Framework;

namespace MP1.Tests
{
    /// <summary>D-048 one-slot pronunciation queue.</summary>
    public class SpeechSlotTests
    {
        [Test]
        public void IdlePlaysNowAndBusyKeepsOnlyTheNewest()
        {
            var q = new SpeechSlot<string>(1.5f);
            Assert.AreEqual("a", q.Request("a", 0f, busy: false));
            Assert.IsNull(q.Request("b", 0.1f, busy: true));
            Assert.IsNull(q.Request("c", 0.2f, busy: true));
            Assert.IsNull(q.Request("d", 0.3f, busy: true));
            Assert.AreEqual(2, q.Replaced, "backlog never exceeds one word");
            Assert.IsNull(q.Poll(0.5f, busy: true), "waits for the current word");
            Assert.AreEqual("d", q.Poll(0.9f, busy: false));
            Assert.IsFalse(q.HasPending);
        }

        [Test]
        public void StaleRequestIsDroppedAndScaledTimeFreezesWhilePaused()
        {
            var q = new SpeechSlot<string>(1.5f);
            q.Request("a", 0f, busy: true);
            Assert.IsNull(q.Poll(1.6f, busy: false), "older than 1.5 s: dropped");
            Assert.AreEqual(1, q.Dropped);
            q.Request("b", 10f, busy: true);
            // Pause freezes Time.time, so the caller's clock does not advance during a pause.
            Assert.AreEqual("b", q.Poll(11f, busy: false));
        }
    }

    /// <summary>D-050 local learning history: JSON lines, item IDs and counts only.</summary>
    public class LearningHistoryTests
    {
        string dir;

        [SetUp] public void MakeDir() { dir = Path.Combine(Path.GetTempPath(), "mp1_history_" + System.Guid.NewGuid().ToString("N")); }
        [TearDown] public void RemoveDir() { if (Directory.Exists(dir)) Directory.Delete(dir, true); }

        static SessionRecord Sample(int score)
        {
            var c = new GameConfig().WithDifficulty(Difficulty.Hard);
            var s = new MeteorDefenseSession(c);
            s.Start();
            int a = s.Spawn("item-a"); s.RegisterTypo(a); s.ResolveCorrect(a);
            int b = s.Spawn("item-b"); s.RegisterBreach(b);
            var r = LearningHistory.From(s, LearningMode.JapaneseToVietnamese, "pack-1", 47, 7, System.DateTime.UtcNow, System.DateTime.UtcNow);
            r.score = score;
            return r;
        }

        [Test]
        public void RoundTripKeepsIdsAndCountsButNoWords()
        {
            string path = Path.Combine(dir, "h.jsonl");
            Assert.IsNull(LearningHistory.Append(Sample(200), path));
            var all = LearningHistory.Read(path);
            Assert.AreEqual(1, all.Count);
            var r = all[0];
            Assert.AreEqual(("pack-1", 47L, "Hard", 1, 1, 1), (r.pack_id, r.pack_version, r.difficulty, r.correct, r.missed, r.typos));
            Assert.AreEqual(2, r.items.Count);
            Assert.AreEqual(("item-a", 1, 1), (r.items[0].item_id, r.items[0].correct, r.items[0].typos));
            StringAssert.DoesNotContain("SourceText", File.ReadAllText(path));
        }

        [Test]
        public void CorruptLinesAreSkippedAndTheFileIsCapped()
        {
            string path = Path.Combine(dir, "h.jsonl");
            Directory.CreateDirectory(dir);
            File.WriteAllText(path, "{not json\n\n{\"schema\":9}\n");
            for (int i = 0; i < LearningHistory.MaxSessions + 3; i++) Assert.IsNull(LearningHistory.Append(Sample(i), path));
            var all = LearningHistory.Read(path);
            Assert.AreEqual(LearningHistory.MaxSessions, File.ReadAllLines(path).Length, "newest MaxSessions lines kept");
            Assert.AreEqual(LearningHistory.MaxSessions + 2, all[all.Count - 1].score, "newest last");
        }

        [Test]
        public void WriteFailureIsReportedNotThrown()
        {
            Directory.CreateDirectory(dir);
            string blocked = Path.Combine(dir, "is_a_directory");
            Directory.CreateDirectory(blocked);
            Assert.IsNotNull(LearningHistory.Append(Sample(1), blocked));
        }
    }
}
