using System;
using UnityEngine;

namespace MP1.Core
{
    /// <summary>One depth band of the background (background_idea.md §4, §8). Ranges are min/max, picked per star.</summary>
    [Serializable]
    public struct StarLayer
    {
        public string Name;
        [Range(0f, 1f)] public float Share;   // fraction of all stars
        public Vector2 Depth;                 // 0.2 far .. 1 near; scales parallax
        public Vector2 Size;                  // world units (camera shows 10.8 units tall)
        public Vector2 Opacity;
        public Vector2 FallSpeed;             // units per second
        public Vector2 TwinkleSpeed;          // radians per second
    }

    public static class StarLayers
    {
        /// <summary>
        /// G-003-R1 defaults (owner asked for larger objects and more stars). Old G-003 values: 160 stars,
        /// size 0.025-0.075, opacity 0.25-0.7, fall 0.04-0.28, twinkle 0.6-2 for every band.
        /// Far stays small and dim; only the near band gets big and bright.
        /// </summary>
        public static StarLayer[] Defaults() => new[]
        {
            new StarLayer { Name = "Far", Share = 0.50f, Depth = new Vector2(0.15f, 0.35f), Size = new Vector2(0.036f, 0.052f), Opacity = new Vector2(0.22f, 0.40f), FallSpeed = new Vector2(0.03f, 0.07f), TwinkleSpeed = new Vector2(0.4f, 1.1f) },
            new StarLayer { Name = "Mid", Share = 0.32f, Depth = new Vector2(0.45f, 0.70f), Size = new Vector2(0.065f, 0.105f), Opacity = new Vector2(0.38f, 0.66f), FallSpeed = new Vector2(0.09f, 0.16f), TwinkleSpeed = new Vector2(0.7f, 1.6f) },
            new StarLayer { Name = "Near", Share = 0.18f, Depth = new Vector2(0.80f, 1.00f), Size = new Vector2(0.120f, 0.190f), Opacity = new Vector2(0.58f, 0.92f), FallSpeed = new Vector2(0.18f, 0.32f), TwinkleSpeed = new Vector2(1.0f, 2.4f) },
        };

        /// <summary>Layer index for star <paramref name="index"/> of <paramref name="total"/>, proportional to each Share.</summary>
        public static int Pick(int index, int total, StarLayer[] layers)
        {
            if (layers == null || layers.Length == 0) return -1;
            float sum = 0f;
            foreach (var l in layers) sum += Mathf.Max(0f, l.Share);
            if (sum <= 0f || total <= 0) return 0;
            float u = (index + 0.5f) / total, acc = 0f;
            for (int i = 0; i < layers.Length; i++)
            {
                acc += Mathf.Max(0f, layers[i].Share) / sum;
                if (u < acc) return i;
            }
            return layers.Length - 1;
        }
    }
}
