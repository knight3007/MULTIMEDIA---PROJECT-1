using System.Collections.Generic;
using System.IO;
using MP1.Core;
using MP1.Sandbox;
using NUnit.Framework;

namespace MP1.Tests
{
    public class StarFieldTests
    {
        [Test]
        public void PointerIsNormalizedAroundScreenCentre()
        {
            Assert.AreEqual(0f, StarField.NormalizedPointerX(960, 1920), 1e-5);
            Assert.AreEqual(-1f, StarField.NormalizedPointerX(0, 1920), 1e-5);
            Assert.AreEqual(1f, StarField.NormalizedPointerX(1920, 1920), 1e-5);
            Assert.AreEqual(1f, StarField.NormalizedPointerX(5000, 1920), 1e-5, "clamped");
            Assert.AreEqual(0f, StarField.NormalizedPointerX(10, 0), "zero width is safe");
        }

        [Test]
        public void StarFallsAtConstantSpeedAndWrapsToTop()
        {
            var s = new Star { Y = 0f, FallSpeed = 2f };
            StarField.Step(ref s, 0.5f, 0f, 5f, -5f);
            Assert.AreEqual(-1f, s.Y, 1e-5);
            s.Y = -4.9f;
            StarField.Step(ref s, 0.5f, 0f, 5f, -5f);
            Assert.That(s.Y, Is.InRange(-5f, 5f), "wrapped back into the field");
            Assert.AreEqual(4.1f, s.Y, 1e-4);
        }

        [Test]
        public void DeeperStarsMoveFurtherTowardPointerAndSettle()
        {
            var near = new Star { Depth = 1f };
            var far = new Star { Depth = 0.2f };
            for (int i = 0; i < 600; i++)
            {
                StarField.Step(ref near, 0f, 1f, 5f, -5f);
                StarField.Step(ref far, 0f, 1f, 5f, -5f);
            }
            Assert.AreEqual(StarField.MaxParallax, near.X, 1e-3, "near star settles at full parallax");
            Assert.AreEqual(StarField.MaxParallax * 0.2f, far.X, 1e-3, "far star moves less");
        }

        [Test]
        public void TwinkleStaysWithinAmplitude()
        {
            var s = new Star { BaseOpacity = 0.5f, TwinkleSpeed = 1.3f };
            for (float t = 0; t < 10; t += 0.1f)
                Assert.That(StarField.Opacity(s, t), Is.InRange(0.5f - StarField.TwinkleAmplitude - 1e-5f, 0.5f + StarField.TwinkleAmplitude + 1e-5f));
        }
    }

    public class StarLayerTests
    {
        [Test]
        public void PickFollowsSharesAndCoversEveryStar()
        {
            var layers = StarLayers.Defaults();
            var counts = new int[layers.Length];
            for (int i = 0; i < 480; i++) counts[StarLayers.Pick(i, 480, layers)]++;
            Assert.AreEqual(240, counts[0], 1, "far ~50%");
            Assert.AreEqual(154, counts[1], 1, "mid ~32%");
            Assert.AreEqual(86, counts[2], 1, "near ~18%");
            Assert.AreEqual(-1, StarLayers.Pick(0, 10, new StarLayer[0]));
        }

        [Test]
        public void NearerLayersAreLargerBrighterFasterAndDeeper()
        {
            var l = StarLayers.Defaults();
            for (int i = 1; i < l.Length; i++)
            {
                Assert.Greater(l[i].Size.x, l[i - 1].Size.y, $"{l[i].Name} smallest star is bigger than {l[i - 1].Name} largest");
                Assert.Greater(l[i].Opacity.y, l[i - 1].Opacity.y);
                Assert.Greater(l[i].FallSpeed.x, l[i - 1].FallSpeed.x);
                Assert.Greater(l[i].Depth.x, l[i - 1].Depth.y);
            }
            Assert.LessOrEqual(l[0].Opacity.y, 0.4f, "far stars stay subtle");
        }
    }

    public class TargetCycleTests
    {
        [Test]
        public void SkipsResolvedAndWraps()
        {
            Assert.AreEqual(2, TargetCycle.Next(0, new[] { false, true, false }));
            Assert.AreEqual(0, TargetCycle.Next(2, new[] { false, true, false }));
            Assert.AreEqual(1, TargetCycle.Next(1, new[] { true, false, true }), "only one left: stay on it");
            Assert.AreEqual(-1, TargetCycle.Next(0, new[] { true, true }));
            Assert.AreEqual(-1, TargetCycle.Next(0, new bool[0]));
        }
    }

    public class ImeGateTests
    {
        [Test]
        public void ShortcutsBlockedWhileComposing()
        {
            Assert.IsTrue(ImeGate.ShortcutAllowed(""));
            Assert.IsTrue(ImeGate.ShortcutAllowed(null));
            Assert.IsFalse(ImeGate.ShortcutAllowed("りんご"));
        }
    }

    public class MediaPathTests
    {
        [Test]
        public void ResolvesInsidePackAndRejectsEscapes()
        {
            string pack = Path.Combine(Path.GetTempPath(), "mp1_pack");
            Assert.AreEqual(Path.GetFullPath(Path.Combine(pack, "assets", "a.jpg")), MediaPaths.ResolveAsset(pack, "assets/a.jpg"));
            Assert.IsNull(MediaPaths.ResolveAsset(pack, "../outside.jpg"));
            Assert.IsNull(MediaPaths.ResolveAsset(pack, "assets/../../outside.jpg"));
            Assert.IsNull(MediaPaths.ResolveAsset(pack, Path.Combine(Path.GetTempPath(), "x.jpg")), "rooted path");
            Assert.IsNull(MediaPaths.ResolveAsset(pack, ""));
            Assert.IsNull(MediaPaths.ResolveAsset(null, "a.jpg"));
        }

        [Test]
        public void FindsManifestWalkingUp()
        {
            string root = Path.Combine(Path.GetTempPath(), "mp1_root");
            string start = Path.Combine(root, "game", "proj", "Assets");
            string target = Path.GetFullPath(Path.Combine(root, "reports", "pack", "content_pack.json"));
            var existing = new HashSet<string> { target };
            Assert.AreEqual(target, MediaPaths.FindUpwards(start, Path.Combine("reports", "pack", "content_pack.json"), p => existing.Contains(Path.GetFullPath(p))));
            Assert.IsNull(MediaPaths.FindUpwards(start, "missing.json", p => false));
        }
    }

    public class DevArgsTests
    {
        [Test]
        public void ParsesSwitches()
        {
            var args = new[] { "game.exe", "-g003Scene", "GameplaySandbox", "-g003Perf", "10", "-reducedMotion" };
            Assert.AreEqual("GameplaySandbox", DevArgs.Get(args, "-g003Scene"));
            Assert.AreEqual(10f, DevArgs.GetFloat(args, "-g003Perf", 0));
            Assert.AreEqual(3f, DevArgs.GetFloat(args, "-g003Delay", 3));
            Assert.IsTrue(DevArgs.Has(args, "-reducedMotion"));
            Assert.IsNull(DevArgs.Get(args, "-reducedMotion"), "flag at the end has no value");
        }
    }

    public class SandboxAnswerTests
    {
        [Test]
        public void ExactMatchIgnoresCaseOuterSpaceAndNormalization()
        {
            Assert.IsTrue(SandboxAnswer.Matches("  Traffic Light ", "traffic light"));
            Assert.IsTrue(SandboxAnswer.Matches("パイナップル", "パイナップル"));
            Assert.IsTrue(SandboxAnswer.Matches("café", "café"), "NFD input equals NFC expected");
            Assert.IsFalse(SandboxAnswer.Matches("trafficlight", "traffic light"));
            Assert.IsFalse(SandboxAnswer.Matches("", ""));
            Assert.IsFalse(SandboxAnswer.Matches(null, "a"));
        }
    }
}
