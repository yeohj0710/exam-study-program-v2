$ErrorActionPreference = "Stop"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$RepoRoot = (Resolve-Path (Join-Path $AppDir "..")).Path
$LauncherDir = Join-Path $AppDir "launcher"
$IconPath = Join-Path $AppDir "public\studyforge.ico"
$CoreExe = Join-Path $LauncherDir "StudyForgeCore.exe"
$BootstrapSource = Join-Path $LauncherDir "StudyForgeBootstrap.cs"
$BootstrapName = -join ((0xC2DC, 0xD5D8, 0x0020, 0xC790, 0xB8CC, 0x0020, 0xC554, 0xAE30, 0x0020, 0xD504, 0xB85C, 0xADF8, 0xB7A8, 0x002E, 0x0065, 0x0078, 0x0065) | ForEach-Object { [char]$_ })
$BootstrapExe = Join-Path $RepoRoot $BootstrapName
$PyInstaller = Join-Path $AppDir ".venv\Scripts\pyinstaller.exe"
$Csc = Join-Path $env:WINDIR "Microsoft.NET\Framework64\v4.0.30319\csc.exe"

if (-not (Test-Path -LiteralPath $PyInstaller)) {
    throw "PyInstaller not found: $PyInstaller"
}
if (-not (Test-Path -LiteralPath $Csc)) {
    throw "C# compiler not found: $Csc"
}

Add-Type -AssemblyName System.Drawing
$bitmap = New-Object System.Drawing.Bitmap 64, 64
$graphics = [System.Drawing.Graphics]::FromImage($bitmap)
$graphics.SmoothingMode = [System.Drawing.Drawing2D.SmoothingMode]::AntiAlias
$graphics.Clear([System.Drawing.Color]::Transparent)
$dark = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::FromArgb(32, 33, 35))
$white = New-Object System.Drawing.SolidBrush ([System.Drawing.Color]::White)
$tealPen = New-Object System.Drawing.Pen ([System.Drawing.Color]::FromArgb(15, 118, 110)), 5
$tealPen.StartCap = [System.Drawing.Drawing2D.LineCap]::Round
$tealPen.EndCap = [System.Drawing.Drawing2D.LineCap]::Round
$tealPen.LineJoin = [System.Drawing.Drawing2D.LineJoin]::Round
$graphics.FillRectangle($dark, 0, 0, 64, 64)
$card = [System.Drawing.PointF[]]@(
    [System.Drawing.PointF]::new(18, 15),
    [System.Drawing.PointF]::new(39, 15),
    [System.Drawing.PointF]::new(47, 23),
    [System.Drawing.PointF]::new(47, 47),
    [System.Drawing.PointF]::new(18, 47)
)
$graphics.FillPolygon($white, $card)
$graphics.DrawLines($tealPen, [System.Drawing.PointF[]]@(
    [System.Drawing.PointF]::new(24, 33),
    [System.Drawing.PointF]::new(30, 39),
    [System.Drawing.PointF]::new(43, 25)
))
$icon = [System.Drawing.Icon]::FromHandle($bitmap.GetHicon())
$stream = [System.IO.File]::Create($IconPath)
try {
    $icon.Save($stream)
}
finally {
    $stream.Dispose()
    $icon.Dispose()
    $graphics.Dispose()
    $bitmap.Dispose()
    $dark.Dispose()
    $white.Dispose()
    $tealPen.Dispose()
}

if (Test-Path -LiteralPath $CoreExe) {
    Remove-Item -LiteralPath $CoreExe -Force
}

& $PyInstaller `
    --clean `
    --noconfirm `
    --onefile `
    --noconsole `
    --name "StudyForgeCore" `
    --distpath $LauncherDir `
    --workpath (Join-Path $AppDir "build\pyinstaller") `
    --specpath (Join-Path $AppDir "build") `
    --paths (Join-Path $AppDir "backend") `
    --icon $IconPath `
    --exclude-module pytest `
    --exclude-module pandas `
    --exclude-module matplotlib `
    --exclude-module pyarrow `
    --exclude-module numpy `
    (Join-Path $LauncherDir "studyforge_launcher.py")
if ($LASTEXITCODE -ne 0) {
    throw "PyInstaller failed"
}

$BootstrapBuildDir = Join-Path ([System.IO.Path]::GetTempPath()) "studyforge-bootstrap-build"
if (Test-Path -LiteralPath $BootstrapBuildDir) {
    Remove-Item -LiteralPath $BootstrapBuildDir -Recurse -Force
}
New-Item -ItemType Directory -Path $BootstrapBuildDir | Out-Null
$TempSource = Join-Path $BootstrapBuildDir "StudyForgeBootstrap.cs"
$TempIcon = Join-Path $BootstrapBuildDir "studyforge.ico"
$TempExe = Join-Path $BootstrapBuildDir "StudyForgeBootstrap.exe"
Copy-Item -LiteralPath $BootstrapSource -Destination $TempSource
Copy-Item -LiteralPath $IconPath -Destination $TempIcon

try {
    & $Csc `
        /nologo `
        /target:winexe `
        /platform:anycpu `
        /optimize+ `
        "/win32icon:$TempIcon" `
        "/out:$TempExe" `
        "/reference:System.Windows.Forms.dll" `
        "/reference:System.Drawing.dll" `
        $TempSource
    if ($LASTEXITCODE -ne 0) {
        throw "C# bootstrap build failed"
    }
    Copy-Item -LiteralPath $TempExe -Destination $BootstrapExe -Force
}
finally {
    Remove-Item -LiteralPath $BootstrapBuildDir -Recurse -Force -ErrorAction SilentlyContinue
}

Write-Host "Built $BootstrapExe"
Write-Host "Built $CoreExe"
