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

$IconGenerator = @'
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import os

icon_path = Path(os.environ["STUDYFORGE_ICON_PATH"])
sizes = [16, 24, 32, 48, 64, 128, 256]

def font(size):
    candidates = [
        r"C:\Windows\Fonts\seguisb.ttf",
        r"C:\Windows\Fonts\segoeuib.ttf",
        r"C:\Windows\Fonts\arialbd.ttf",
    ]
    for candidate in candidates:
        if Path(candidate).exists():
            return ImageFont.truetype(candidate, size)
    return ImageFont.load_default()

images = []
for size in sizes:
    scale = size / 64
    image = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((0, 0, size - 1, size - 1), radius=max(2, round(12 * scale)), fill=(15, 118, 110, 255))
    if size <= 24:
        text = "S"
        text_font = font(max(12, round(34 * scale)))
        box = draw.textbbox((0, 0), text, font=text_font)
        draw.text(((size - (box[2] - box[0])) / 2, (size - (box[3] - box[1])) / 2 - box[1]), text, fill=(255, 255, 255, 255), font=text_font)
    else:
        text = "SF"
        text_font = font(max(20, round(31 * scale)))
        box = draw.textbbox((0, 0), text, font=text_font)
        draw.text(((size - (box[2] - box[0])) / 2, (size - (box[3] - box[1])) / 2 - box[1]), text, fill=(255, 255, 255, 255), font=text_font)
    images.append(image)

images[-1].save(icon_path, sizes=[(s, s) for s in sizes])
'@

$env:STUDYFORGE_ICON_PATH = $IconPath
try {
    $IconGenerator | & (Join-Path $AppDir ".venv\Scripts\python.exe") -
    if ($LASTEXITCODE -ne 0) {
        throw "Icon generation failed"
    }
}
finally {
    Remove-Item Env:\STUDYFORGE_ICON_PATH -ErrorAction SilentlyContinue
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
