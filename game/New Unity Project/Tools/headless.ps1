param([ValidateSet('Scenes','EditMode','PlayMode','Build')][string]$Step, [string]$Filter = "", [string]$Output = "Builds/G007_R2_Win64/WordOrbit.exe")
# Headless Unity runs on this project. Only works while the interactive Editor has the project closed.
$u = if ($env:UNITY_EDITOR_EXE) { $env:UNITY_EDITOR_EXE } else { "E:\unity engin\6000.6.10f1\Editor\Unity.exe" } # owner machine default; set UNITY_EDITOR_EXE elsewhere
$p = Split-Path $PSScriptRoot -Parent
$L = Join-Path $p "Logs\headless"; New-Item -ItemType Directory -Force $L | Out-Null
if (Test-Path "$p\Temp\UnityLockfile") { try { [IO.File]::Open("$p\Temp\UnityLockfile", 'Open', 'ReadWrite', 'None').Close() } catch { "Editor has the project open: close it or use 'unity command'."; exit 2 } }
switch ($Step) {
    'Scenes' { $a = @('-batchmode','-quit','-nographics','-projectPath',"`"$p`"",'-executeMethod','MP1.EditorTools.BatchBuild.RebuildScenes','-logFile',"`"$L\scenes.log`"") }
    'Build'  { $a = @('-batchmode','-quit','-projectPath',"`"$p`"",'-executeMethod','MP1.EditorTools.BatchBuild.Windows','-buildOutput',"`"$p\$Output`"",'-logFile',"`"$L\build.log`"") }
    default  { $a = @('-batchmode','-projectPath',"`"$p`"",'-runTests','-testPlatform',$Step,'-testResults',"`"$L\$Step.xml`"",'-logFile',"`"$L\$Step.log`"")
               if ($Step -eq 'EditMode') { $a += '-nographics' }
               if ($Filter) { $a += @('-testFilter', $Filter) }
               Remove-Item "$L\$Step.xml" -ErrorAction SilentlyContinue }
}
$r = Start-Process $u -ArgumentList $a -Wait -PassThru
"$Step exit=$($r.ExitCode)"
switch ($Step) {
    'Scenes' { Select-String "$L\scenes.log" -Pattern "error CS|foundation rebuilt" | Select-Object -First 5 | ForEach-Object Line }
    'Build'  { Select-String "$L\build.log" -Pattern "BATCH_BUILD|error CS" | Select-Object -First 5 | ForEach-Object Line }
    default  {
        if (Test-Path "$L\$Step.xml") {
            $x = [xml](Get-Content "$L\$Step.xml" -Raw); $t = $x.'test-run'
            "total=$($t.total) passed=$($t.passed) failed=$($t.failed) skipped=$($t.skipped)"
            $x.SelectNodes("//test-case[@result='Failed']") | ForEach-Object { $_.fullname; ([string]$_.failure.message.InnerText).Trim(); ([string]$_.failure.'stack-trace'.InnerText).Trim().Split("`n") | Select-Object -First 2 }
        } else { Select-String "$L\$Step.log" -Pattern "error CS" | Select-Object -First 8 | ForEach-Object Line }
    }
}
