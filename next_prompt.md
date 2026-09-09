# Resume: FramerateConverter

9 Sep 2026: branch `fix/cancellable-ffmpeg`, version 1.0.2. All eight modules
calling ffmpeg/ffprobe now use nodes/_ffmpeg.py's cancellable runner. Child
processes are reaped on Cancel/timeout, capture goes to temporary files and
returned stderr is capped to its last MiB. Unused per-frame quality logs removed.

Verified: four real subprocess tests (`python -m unittest -v test_ffmpeg_process`)
cover success/nonzero exit, Cancel, timeout and large output. Real FFmpeg clip
generation, ffprobe 24fps and quality SSIM 1.0 passed. No server restart or merge.
Next: restart ComfyUI and verify Cancel on a representative conversion.

Full four-pack audit is in ../ComfyUI-TropeTools/docs/performance-audit-2026-09-09.md.
