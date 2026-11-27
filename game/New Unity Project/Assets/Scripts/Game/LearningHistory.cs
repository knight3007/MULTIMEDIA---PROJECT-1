using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using MP1.Content;
using UnityEngine;

namespace MP1.Game
{
    [Serializable]
    public class ItemStat
    {
        public string item_id;
        public int correct, missed, wrong_enter, typos;
    }

    /// <summary>One finished or abandoned session. Item IDs and counts only: words and meanings stay in the pack.</summary>
    [Serializable]
    public class SessionRecord
    {
        public int schema = 1;
        public string started_utc, ended_utc, outcome, pack_id, mode, difficulty, hint, answer, targeting;
        public long pack_version;
        public double duration_s;
        public int eligible_items, unique_seen, unique_correct, review_items;
        public int seed, score, max_combo, correct, missed, wrong_enter, typos, hit_units, hp_left, hp_start, waves_reached, wave_count;
        public List<ItemStat> items = new List<ItemStat>();
    }

    /// <summary>
    /// D-050 (owner O5): lightweight local learning history, one JSON line per session under persistentDataPath.
    /// No backend, account or cloud. Failures are reported to the caller and never block the results screen.
    /// </summary>
    public static class LearningHistory
    {
        public const int MaxSessions = 500;
        public static string DefaultPath => Path.Combine(Application.persistentDataPath, "LearningHistory", "sessions_v1.jsonl");

        /// <summary>Where a session is written: the override (tests), nowhere for dev-bot runs, else the player's folder.</summary>
        public static string Target(string overridePath, bool devBot) => overridePath ?? (devBot ? null : DefaultPath);

        public static SessionRecord From(MeteorDefenseSession s, LearningMode mode, string packId, long packVersion, int seed, DateTime startedUtc, DateTime endedUtc, int eligibleItems = 0)
        {
            var c = s.Config;
            var r = new SessionRecord
            {
                started_utc = startedUtc.ToString("o"), ended_utc = endedUtc.ToString("o"), duration_s = Math.Round(s.ActiveSeconds, 1),
                outcome = s.State.ToString(), pack_id = packId, pack_version = packVersion, mode = LearningModes.Id(mode),
                difficulty = c.Difficulty.ToString(), hint = c.Hint.ToString(), answer = c.Answer.ToString(), targeting = c.Targeting.ToString(),
                seed = seed, score = s.Score, max_combo = s.MaxCombo, correct = s.Correct, missed = s.Missed, wrong_enter = s.WrongAttempts,
                eligible_items = eligibleItems, unique_seen = s.UniqueSeen, unique_correct = s.UniqueCorrect, review_items = s.ReviewCount,
                typos = s.Typos, hit_units = s.HitUnits, hp_left = s.Hp, hp_start = c.StartingHp, waves_reached = s.WavesStarted, wave_count = s.WaveCount
            };
            foreach (var kv in s.Items.OrderBy(k => k.Key, StringComparer.Ordinal))
                r.items.Add(new ItemStat { item_id = kv.Key, correct = kv.Value.Correct, missed = kv.Value.Missed, wrong_enter = kv.Value.WrongEnter, typos = kv.Value.Typos });
            return r;
        }

        /// <summary>Appends one line, keeping the newest <see cref="MaxSessions"/>. Returns null on success, else the error.</summary>
        public static string Append(SessionRecord record, string path = null)
        {
            path = path ?? DefaultPath;
            try
            {
                Directory.CreateDirectory(Path.GetDirectoryName(path));
                string line = JsonUtility.ToJson(record);
                var lines = File.Exists(path) ? File.ReadAllLines(path).Where(l => l.Length > 0).ToList() : new List<string>();
                if (lines.Count < MaxSessions) { File.AppendAllText(path, line + "\n"); return null; }
                lines = lines.Skip(lines.Count - MaxSessions + 1).ToList();
                lines.Add(line);
                string tmp = path + ".tmp";
                File.WriteAllText(tmp, string.Join("\n", lines) + "\n");
                File.Copy(tmp, path, true); // shortcut: copy-over is not atomic; a crash here leaves the .tmp with the full history
                File.Delete(tmp);
                return null;
            }
            catch (Exception e) { return e.GetType().Name + ": " + e.Message; }
        }

        /// <summary>All readable records, oldest first; corrupt or foreign lines are skipped.</summary>
        public static List<SessionRecord> Read(string path = null)
        {
            path = path ?? DefaultPath;
            var list = new List<SessionRecord>();
            if (!File.Exists(path)) return list;
            foreach (var l in File.ReadAllLines(path))
            {
                if (l.Length == 0) continue;
                try
                {
                    var r = JsonUtility.FromJson<SessionRecord>(l);
                    if (r != null && r.schema == 1 && !string.IsNullOrEmpty(r.pack_id)) list.Add(r);
                }
                catch (Exception) { } // corrupt line: skipped
            }
            return list;
        }
    }
}
