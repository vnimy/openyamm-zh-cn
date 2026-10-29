# 一键构建简体中文补丁的 mods 部分（可选：连 exe 一起打包）。
#
# 用法：
#   scripts\build.ps1                                     # 用自动探测到的源码树
#   scripts\build.ps1 -OpenYamm D:\src\openyamm-1.17
#   scripts\build.ps1 -Exe D:\src\openyamm-1.17\build-mingw\game\openyamm.exe   # 顺带打包 zip
#
# 需要：Python 3.10+；编 exe 另需 CMake 与编译器（见 docs/build.md）。

param(
    [string]$OpenYamm = "",
    [string]$Exe = "",
    [string]$OutDir = "build/mods",
    [string]$Dist = "",
    [switch]$SkipFonts
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent $PSScriptRoot
Set-Location $Root

function Invoke-Step {
    param([string]$Title, [string[]]$Arguments)

    Write-Host ""
    Write-Host "== $Title" -ForegroundColor Cyan
    & python @Arguments
    if ($LASTEXITCODE -ne 0) {
        Write-Host "失败：$Title" -ForegroundColor Red
        exit $LASTEXITCODE
    }
}

Invoke-Step "合成覆盖表" @("tools/make_ui_text.py")
Invoke-Step "体检覆盖表" @("tools/check_tables.py")

$patchArgs = @("tools/build_patch.py", "--out", $OutDir)
if ($OpenYamm) { $patchArgs += @("--openyamm", $OpenYamm) }
Invoke-Step "生成译文数据表" $patchArgs

if (-not $SkipFonts) {
    $fontDir = Join-Path $OutDir "engine/fonts/truetype"

    $subsetArgs = @("tools/font_subset.py", "--patch", $OutDir, "--out", $fontDir)
    if ($OpenYamm) { $subsetArgs += @("--openyamm", $OpenYamm) }
    Invoke-Step "收集字形子集" $subsetArgs

    Invoke-Step "烘焙字体描述" @(
        "tools/build_fonts.py",
        "--font", "assets/fonts/NotoSansSC.ttf",
        "--license", "assets/fonts/OFL.txt",
        "--out", $OutDir
    )
}

Write-Host ""
Write-Host "mods 已生成：$OutDir" -ForegroundColor Green

if ($Exe) {
    if (-not $Dist) { $Dist = "dist/OpenYAMM-117-zh_cn.zip" }
    Invoke-Step "打包" @("tools/package.py", "--mod", $OutDir, "--exe", $Exe, "--out", $Dist)
    Write-Host "已打包：$Dist" -ForegroundColor Green
} else {
    Write-Host "未指定 -Exe，跳过打包。需要 zip 时传 -Exe <openyamm.exe 路径>。" -ForegroundColor Yellow
}
