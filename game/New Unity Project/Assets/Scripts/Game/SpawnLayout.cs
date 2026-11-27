namespace MP1.Game
{
    /// <summary>
    /// G-007.7 safe spawn area: a new meteor appears with its whole label stack (image, clue, sprite, answer) below the
    /// top HUD, so no clue is hidden behind foreground UI. Fall speed is computed from this point to the defense line
    /// over the configured fall time, so starting lower never shortens the time a player has.
    /// </summary>
    public static class SpawnLayout
    {
        /// <summary>Top HUD band in reference pixels (Back/HP/score/pause end at ~96 px) plus a margin, of a 1080 px canvas.</summary>
        public const float HudBandPixels = 112f, ReferenceHeight = 1080f, Margin = 0.1f;

        /// <summary>World Y of the HUD's lower edge for an orthographic camera of this size.</summary>
        public static float SafeTop(float orthoSize) => orthoSize - 2f * orthoSize * HudBandPixels / ReferenceHeight;

        public const float SideMargin = 0.25f;

        /// <summary>
        /// Keeps a meteor's widest label (long Fill-in-the-Blank patterns) fully on screen: an edge lane is pulled
        /// inwards by half the label width. Labels wider than the screen are centred.
        /// </summary>
        public static float ClampX(float x, float halfWidth, float labelWidth)
        {
            float limit = halfWidth - labelWidth / 2f - SideMargin;
            return limit <= 0f ? 0f : System.Math.Max(-limit, System.Math.Min(limit, x));
        }

        /// <summary>Meteor centre Y so that its stack top (world units above the centre) sits just below the HUD.</summary>
        public static float SpawnY(float orthoSize, float stackTop) => SafeTop(orthoSize) - Margin - stackTop;
    }
}
