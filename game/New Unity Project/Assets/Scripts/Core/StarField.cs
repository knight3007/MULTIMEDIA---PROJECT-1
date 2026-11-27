using UnityEngine;

namespace MP1.Core
{
    /// <summary>One background star. Fields follow game/background/background_idea.md §9.</summary>
    public struct Star
    {
        public float X, Y, BaseX, Vx;
        public float Depth, FallSpeed, Size;
        public float BaseOpacity, TwinkleSpeed, TwinkleOffset;
        public bool IsSparkle;
    }

    /// <summary>Pure star-field maths so the behaviour is testable without a scene.</summary>
    public static class StarField
    {
        public const float MaxParallax = 0.6f;   // world units at depth 1
        public const float SpringForce = 0.02f;  // background_idea.md §3 (spring + damping)
        public const float Damping = 0.88f;
        public const float TwinkleAmplitude = 0.15f; // §6

        /// <summary>§5: pointer X mapped to [-1, 1] around the screen centre.</summary>
        public static float NormalizedPointerX(float pointerX, float screenWidth)
        {
            if (screenWidth <= 0f) return 0f;
            return Mathf.Clamp((pointerX / screenWidth - 0.5f) * 2f, -1f, 1f);
        }

        /// <summary>§2 constant fall with wrap, §3 spring/damping toward baseX + depth-scaled pointer offset.</summary>
        // shortcut: spring runs per frame like the reference formula, so feel varies slightly with frame rate; switch to fixed sub-steps if it matters.
        public static void Step(ref Star s, float dt, float pointerNorm, float top, float bottom)
        {
            s.Y -= s.FallSpeed * dt;
            float height = top - bottom;
            if (height > 0f)
                while (s.Y < bottom) s.Y += height;

            float targetX = s.BaseX + pointerNorm * MaxParallax * s.Depth;
            s.Vx += (targetX - s.X) * SpringForce;
            s.Vx *= Damping;
            s.X += s.Vx;
        }

        /// <summary>§6 subtle twinkle; sparkle stars (§7) twinkle slower via their TwinkleSpeed.</summary>
        public static float Opacity(in Star s, float time)
        {
            return Mathf.Clamp01(s.BaseOpacity + Mathf.Sin(time * s.TwinkleSpeed + s.TwinkleOffset) * TwinkleAmplitude);
        }
    }
}
