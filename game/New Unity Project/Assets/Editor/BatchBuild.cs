using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace MP1.EditorTools
{
    /// <summary>
    /// Headless entry points for -batchmode runs (no Editor window needed).
    /// Unity.exe -batchmode -quit -projectPath . -executeMethod MP1.EditorTools.BatchBuild.Windows -buildOutput Builds/X/WordOrbit.exe
    /// </summary>
    public static class BatchBuild
    {
        public static void RebuildScenes() => Debug.Log(G003Builder.BuildAll());

        public static void Windows()
        {
            var args = System.Environment.GetCommandLineArgs();
            int i = System.Array.IndexOf(args, "-buildOutput");
            string output = i >= 0 && i + 1 < args.Length ? args[i + 1] : "Builds/G007_Win64/WordOrbit.exe";
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
                locationPathName = output,
                target = BuildTarget.StandaloneWindows64,
                options = BuildOptions.Development,
            });
            var s = report.summary;
            Debug.Log($"BATCH_BUILD result={s.result} size={s.totalSize} warnings={s.totalWarnings} errors={s.totalErrors} out={output}");
            EditorApplication.Exit(s.result == BuildResult.Succeeded ? 0 : 1);
        }
    }
}
