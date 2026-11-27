using System;
using System.Collections.Generic;

namespace MP1.Game
{
    /// <summary>A meteor near the spawn row, as far as label spacing is concerned.</summary>
    public struct LaneOccupant
    {
        public float X, Y, LabelWidth;
        public LaneOccupant(float x, float y, float labelWidth) { X = x; Y = y; LabelWidth = labelWidth; }
    }

    /// <summary>
    /// Spec §4 spawn lanes: a lane is usable only if the new labels cannot overlap labels of meteors still near the
    /// spawn row; among usable lanes prefer more free space, with a random tie-break. Returns -1 to postpone.
    /// </summary>
    public static class LaneChooser
    {
        public const float NearRow = 3.2f, Gap = 0.3f, MaxClearance = 6f;

        public static int Choose(IList<float> laneXs, float newLabelWidth, IEnumerable<LaneOccupant> active, float spawnY, Func<float> random01)
        {
            int best = -1;
            float bestScore = float.MinValue;
            var near = new List<LaneOccupant>();
            foreach (var m in active) if (Math.Abs(m.Y - spawnY) <= NearRow) near.Add(m);
            for (int l = 0; l < laneXs.Count; l++)
            {
                float x = laneXs[l], clearance = MaxClearance; // capped so random tie-breaks still matter
                bool fits = true;
                foreach (var m in near)
                {
                    float gap = Math.Abs(m.X - x);
                    if (gap < (newLabelWidth + m.LabelWidth) / 2f + Gap) { fits = false; break; }
                    clearance = Math.Min(clearance, gap);
                }
                if (!fits) continue;
                float score = clearance + random01() * 2f;
                if (score > bestScore) { bestScore = score; best = l; }
            }
            return best;
        }
    }
}
