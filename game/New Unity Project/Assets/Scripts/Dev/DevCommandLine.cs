using System.Collections;
using System.Collections.Generic;
using MP1.Core;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace MP1.Dev
{
    /// <summary>
    /// PROTOTYPE / VERIFICATION ONLY. Standalone-build switches for G-003.9:
    /// -g003Scene NAME, -g003Capture PNG [-g003Delay SECONDS], -g003Perf SECONDS, -g003NoVsync; quits afterwards.
    /// Does nothing when none of the switches are present.
    /// </summary>
    public class DevCommandLine : MonoBehaviour
    {
        static bool started;
        public static readonly string[] Args = System.Environment.GetCommandLineArgs();

        void Awake()
        {
            if (started) { Destroy(gameObject); return; }
            started = true;
            DontDestroyOnLoad(gameObject);
            if (DevArgs.Has(Args, "-g003NoVsync")) { QualitySettings.vSyncCount = 0; Application.targetFrameRate = -1; } // uncapped perf runs only
            if (DevArgs.Get(Args, "-g006Record") is string recordDir) StartCoroutine(Record(recordDir, DevArgs.GetFloat(Args, "-g006RecordSeconds", 20f), DevArgs.GetFloat(Args, "-g006RecordStart", 3f)));
            string scene = DevArgs.Get(Args, "-g003Scene");
            string capture = DevArgs.Get(Args, "-g003Capture");
            float perf = DevArgs.GetFloat(Args, "-g003Perf", 0f);
            if (scene == null && capture == null && perf <= 0f) return; // recording alone keeps running without quitting
            StartCoroutine(Run(scene, capture, perf, DevArgs.GetFloat(Args, "-g003Delay", 3f)));
        }

        /// <summary>Saves numbered PNG frames (~15 fps, real time) for an owner review video assembled outside Unity.</summary>
        IEnumerator Record(string dir, float seconds, float start)
        {
            System.IO.Directory.CreateDirectory(dir);
            yield return new WaitForSecondsRealtime(start);
            int n = 0;
            float end = Time.realtimeSinceStartup + seconds, next = 0f;
            while (Time.realtimeSinceStartup < end)
            {
                yield return new WaitForEndOfFrame();
                if (Time.realtimeSinceStartup < next) continue;
                next = Time.realtimeSinceStartup + 1f / 15f;
                ScreenCapture.CaptureScreenshot(System.IO.Path.Combine(dir, $"frame_{n++:00000}.png"));
            }
            Debug.Log($"G006_RECORD frames={n} dir={dir}");
        }

        IEnumerator Run(string scene, string capture, float perfSeconds, float delay)
        {
            if (!string.IsNullOrEmpty(scene) && SceneManager.GetActiveScene().name != scene)
                yield return SceneManager.LoadSceneAsync(scene);
            yield return new WaitForSecondsRealtime(delay);
            if (perfSeconds > 0f)
            {
                var frames = new List<float>();
                float end = Time.realtimeSinceStartup + perfSeconds;
                int maxMeteors = 0, spikes33 = 0, spikes50 = 0;
                while (Time.realtimeSinceStartup < end)
                {
                    yield return null;
                    float ms = Time.unscaledDeltaTime * 1000f;
                    frames.Add(ms);
                    if (ms > 50f) spikes50++;
                    if (ms > 33f && ++spikes33 <= 20) Debug.Log($"G003_SPIKE t={Time.realtimeSinceStartup:F2} ms={ms:F1} frame={Time.frameCount}"); // pairs with G006_MEDIA/G006_EVENT timestamps
                    maxMeteors = Mathf.Max(maxMeteors, FindObjectsByType<Game.MeteorView>().Length);
                }
                frames.Sort();
                float sum = 0f;
                foreach (var f in frames) sum += f;
                float avg = sum / Mathf.Max(1, frames.Count);
                float p95 = frames.Count > 0 ? frames[Mathf.Min(frames.Count - 1, (int)(frames.Count * 0.95f))] : 0f;
                float max = frames.Count > 0 ? frames[frames.Count - 1] : 0f;
                int meteors = FindObjectsByType<Sandbox.SandboxMeteor>().Length + FindObjectsByType<Game.MeteorView>().Length;
                Debug.Log($"G003_PERF scene={SceneManager.GetActiveScene().name} res={Screen.width}x{Screen.height} frames={frames.Count} " +
                          $"avgMs={avg:F2} avgFps={1000f / Mathf.Max(avg, 0.001f):F1} p95Ms={p95:F2} maxMs={max:F2} meteors={meteors} maxMeteorViews={maxMeteors} spikes33={spikes33} spikes50={spikes50} " +
                          $"postponed={(FindAnyObjectByType<Game.MeteorDefenseController>() is Game.MeteorDefenseController g ? g.PostponedSpawns : 0)} " +
                          $"monoMB={System.GC.GetTotalMemory(false) / 1048576f:F1} " +
                          $"allocatedMB={UnityEngine.Profiling.Profiler.GetTotalAllocatedMemoryLong() / 1048576f:F1} " +
                          $"reservedMB={UnityEngine.Profiling.Profiler.GetTotalReservedMemoryLong() / 1048576f:F1} " +
                          $"vsync={QualitySettings.vSyncCount} targetFps={Application.targetFrameRate} gpu={SystemInfo.graphicsDeviceName} cpu={SystemInfo.processorType}");
            }
            if (!string.IsNullOrEmpty(capture))
            {
                yield return new WaitForEndOfFrame();
                ScreenCapture.CaptureScreenshot(capture);
                Debug.Log($"G003_CAPTURE {capture} res={Screen.width}x{Screen.height}");
                yield return new WaitForSecondsRealtime(1.5f);
            }
            Application.Quit();
        }
    }
}
