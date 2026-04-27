# Framerate Converter

*Part of the Trope Tools suite — by [TropeMedia](https://github.com/LaserDog80).*

Two simple ComfyUI nodes for working with video files:

- **Convert Framerate** — change a video's frame rate (24 → 25, 30 → 25, anything to anything).
- **Remux Container** — change a video's container (`.mov` ↔ `.mp4` ↔ `.mkv`) without re-encoding, so no quality loss.

Both nodes use ComfyUI's standard `VIDEO` type, so you can chain them together or wire them into the built-in **Load Video** / **Save Video** nodes.

## What they do

### Convert Framerate
Converts videos between any common framerates — 24, 25, 30, 60 fps and anything in between. Useful for:

- **Film → PAL** (24 → 25 fps)
- **NTSC film → PAL** (23.976 → 25 fps)
- **PAL → film** (25 → 24 fps)
- **NTSC → PAL** (30 / 29.97 → 25 fps)
- Slowing 60 fps footage to 30 fps
- Anything else FFmpeg can do

Audio stays in sync. Quality stays high. You don't need to know any FFmpeg.

### Remux Container
Swaps the container format around the same video and audio streams — no re-encoding, no quality loss, runs in seconds even on long files. Useful for:

- Putting an `.mp4` inside a `.mov` so it imports cleanly into Final Cut / Resolve
- Moving footage out of `.mkv` for editors that don't read it
- Standardising deliverables to a single container

## Install (the easy way)

### Option 1 — ComfyUI Manager (recommended)

1. Open ComfyUI Manager.
2. Search for **Trope Tools — Framerate Converter**.
3. Click **Install**.
4. Restart ComfyUI.

### Option 2 — Manual

1. Find your ComfyUI `custom_nodes/` folder.
2. Drop this folder inside it.
3. Restart ComfyUI.

### One thing you need separately: FFmpeg

This node uses FFmpeg under the hood — it's a free tool you install once and forget about.

| Your computer | What to type / do |
|---|---|
| **Mac** | Open Terminal, paste `brew install ffmpeg`, hit enter. (Don't have Homebrew? Get it at [brew.sh](https://brew.sh).) |
| **Windows** | Download the build from [gyan.dev/ffmpeg/builds](https://www.gyan.dev/ffmpeg/builds/), unzip it, and add the `bin/` folder to your PATH. ([Step-by-step guide](https://phoenixnap.com/kb/ffmpeg-windows).) |
| **Linux** | `sudo apt install ffmpeg` (or your distro's equivalent). |

If FFmpeg isn't installed, the ComfyUI console shows a clear warning when it starts up — so you'll know.

**No `pip install` needed.** This pack uses only Python's standard library.

## How to use it

The simplest possible workflow:

```
[Load Video]  →  [Convert Framerate]  →  [Save Video]
```

1. Right-click the canvas → **Add Node → Trope Tools → Framerate Converter → Convert Framerate**.
2. Connect a **Load Video** node (any source) into the `input` slot.
3. Set `target_fps` (default is 25.0 — change it to whatever you need).
4. Connect `output` to a **Save Video** node.
5. Hit **Queue Prompt**.

That's it. The converted video saves to `~/comfyui/output/`.

You can also skip Save Video — Convert Framerate already drops a converted file into `~/comfyui/input/` named `<original>_<targetfps>fps.mp4`.

### Chaining the two nodes together

Because both nodes use the `VIDEO` type, you can wire them directly:

```
[Load Video]  →  [Convert Framerate]  →  [Remux Container]
```

This lets you change the framerate **and** the container in a single pass — for example, "take this 24 fps `.mp4` and give me a 25 fps `.mov`."

> **Don't pipe `Remux Container` into `Save Video`.** The built-in Save Video node ignores the input's container and re-saves as `.mp4`, which would undo the remux. `Remux Container` writes its output straight to `~/comfyui/output/` itself — set `filename_prefix` on the node to control the name.

## The settings (only if you want to tweak)

The defaults work for most jobs. If you want to fine-tune:

### `method` — how the conversion is done

| Method | What it does | When to use it |
|---|---|---|
| **speed_change** *(default)* | Adjusts playback speed slightly, keeps every frame | Small fps changes like 24 ↔ 25 — gives the cleanest result |
| **frame_drop** | Drops or duplicates frames | Big jumps like 60 → 30 fps |
| **frame_blend** | Blends adjacent frames together | Smoother than frame_drop, slight ghosting |
| **minterpolate** | AI-style motion interpolation | Highest quality up-conversion, but slow |

### `audio_mode` — how the audio is handled (only matters with `speed_change`)

| Mode | What happens |
|---|---|
| **allow_shift** *(default)* | Audio plays at the new speed; pitch shifts a tiny bit (~0.7 semitones for 24→25). Most people can't hear it. |
| **preserve_pitch** | Audio is re-pitched so it sounds the same as the original. |
| **copy** | Original audio is kept untouched (will go out of sync — only useful for tests). |
| **no_audio** | Strips audio entirely. |

### `crf` — quality dial

Number from 0 (huge file, perfect quality) to 51 (tiny file, awful quality). Default is **18**, which looks essentially identical to source. Lower = better.

## Mac users — about Full Disk Access

The ComfyUI desktop app on Mac is sandboxed. By default it can only read/write inside `~/comfyui/`. If you want to convert a video sitting somewhere else on your computer:

**System Settings → Privacy & Security → Full Disk Access → +** → add **ComfyUI.app** → restart it.

If you're happy dragging files into the Load Video node (the normal way), you don't need to do this at all.

## Help, something's wrong

**"ffmpeg not found" warning when ComfyUI starts**
You haven't installed FFmpeg yet — see the install section above.

**"No such file or directory"**
The video file path probably has weird characters in it, or it's outside ComfyUI's sandbox. Use the upload widget on Load Video instead of typing a path.

**Audio is out of sync after conversion**
Try setting `audio_mode` to `preserve_pitch`. If it's still off, your source video might have a variable framerate (some phone recordings do this) — you'd need to convert it to a constant framerate first.

**Output looks lower-quality than the source**
Lower the `crf` number. 14 is near-source quality, 0 is fully lossless (much bigger files).

## More than two nodes?

This pack is built around two simple nodes — **Convert Framerate** and **Remux Container** — which is what 99% of people need. Underneath, there are 12 smaller building-block nodes (Probe Video, Calc Conversion, Run FFmpeg, Verify FPS, etc.) you can use to build custom workflows if you want fine-grained control. They're tucked away under the **Trope Tools / Framerate Converter / Inspect, Configure, Process, Verify** menus. **Most users will never need them.**

## Credits

- Built around [FFmpeg](https://ffmpeg.org/) — the open-source video toolkit.
- Published by **TropeMedia**.

## License

MIT — see [LICENSE](LICENSE).
