$ErrorActionPreference = "Stop"

$AppDir = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$BuildDir = Join-Path ([System.IO.Path]::GetTempPath()) "studyforge-frontend-build"
$DistDir = Join-Path $AppDir "dist"

if (Test-Path -LiteralPath $BuildDir) {
    Remove-Item -LiteralPath $BuildDir -Recurse -Force
}
New-Item -ItemType Directory -Path $BuildDir | Out-Null

foreach ($name in @(
    "src",
    "public",
    "index.html",
    "package.json",
    "package-lock.json",
    "tsconfig.app.json",
    "tsconfig.json",
    "tsconfig.node.json",
    "vite.config.ts"
)) {
    Copy-Item -LiteralPath (Join-Path $AppDir $name) -Destination $BuildDir -Recurse
}

Push-Location $BuildDir
try {
    npm ci
    npx tsc -b
    npx vite build
}
finally {
    Pop-Location
}

if (Test-Path -LiteralPath $DistDir) {
    Remove-Item -LiteralPath $DistDir -Recurse -Force
}
Copy-Item -LiteralPath (Join-Path $BuildDir "dist") -Destination $DistDir -Recurse
Remove-Item -LiteralPath $BuildDir -Recurse -Force
