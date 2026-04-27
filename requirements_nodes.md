# Community / External Node Dependencies

This document lists all community and external ComfyUI node packs needed
to complete the full framerate conversion workflow alongside the Trope Tools nodes.

## Required System Dependencies

| Dependency | Purpose | Install |
|-----------|---------|---------|
| **FFmpeg** | Video conversion, probing, quality metrics | `apt install ffmpeg` / `brew install ffmpeg` |
| **ffprobe** | Media analysis (bundled with FFmpeg) | Included with FFmpeg |

## Optional Community Node Packs

These are not required for Trope Tools nodes to function, but provide
alternative/complementary capabilities for building richer workflows.

| Pack | Repository | Nodes Used | Purpose |
|------|-----------|------------|---------|
| ComfyUI-VideoHelperSuite | [Kosinkadink/ComfyUI-VideoHelperSuite](https://github.com/Kosinkadink/ComfyUI-VideoHelperSuite) | `VHS_VideoInfo`, `VHS_VideoCombine`, `Load Video (FFmpeg)` | Alternative video loading/saving, metadata extraction |
| ComfyUI-Frame-Interpolation | [Fannovel16/ComfyUI-Frame-Interpolation](https://github.com/Fannovel16/ComfyUI-Frame-Interpolation) | `RIFE VFI` | AI-based frame interpolation (alternative to FFmpeg minterpolate) |

## Trope Tools Nodes — No External Python Dependencies

All Trope Tools nodes use only the Python standard library and shell out to
FFmpeg/ffprobe. No pip packages are required beyond what ComfyUI itself provides.

| Node | Category | Dependencies |
|------|----------|-------------|
| Trope_ConvertFramerate | (top level) | ffmpeg, ffprobe |
| Trope_ProbeVideo | Inspect | ffprobe |
| Trope_DetectVFR | Inspect | ffprobe |
| Trope_ExtractMediaInfo | Inspect | None (pure dict access) |
| Trope_CalcConversion | Configure | None (pure math) |
| Trope_CalcAudio | Configure | None (pure math) |
| Trope_BuildCommand | Configure | None (string building) |
| Trope_GenOutputPath | Configure | None (path manipulation) |
| Trope_RunFFmpeg | Process | ffmpeg |
| Trope_Remux | Process | ffmpeg |
| Trope_VerifyFPS | Verify | ffprobe |
| Trope_VerifySync | Verify | ffprobe |
| Trope_VerifyIntegrity | Verify | ffmpeg |
| Trope_QualityMetrics | Verify | ffmpeg (PSNR/SSIM), libvmaf (optional) |
