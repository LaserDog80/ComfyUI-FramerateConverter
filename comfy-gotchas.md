# ComfyUI Gotchas

Reference notes for building ComfyUI custom nodes. Each entry captures a
non-obvious trap that bites silently — the workflow runs to completion,
the file is saved, but something downstream is wrong. Skim this end to
end before writing or modifying node code.

---

## Section A — ComfyUI node API

### Endpoint nodes need the `OUTPUT_NODE` pattern

A node that writes a final artifact to disk should set
`OUTPUT_NODE = True`, leave `RETURN_TYPES = ()`, and return a
`{"ui": {...}}` dict. Don't return a data type that downstream nodes
might re-process — the built-in `Save*` nodes will silently re-encode or
re-wrap whatever you pipe into them, undoing the work your node just did.

```python
class MyNode:
    RETURN_TYPES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "MyCategory"

    def execute(self, ...):
        # write file to disk
        return {"ui": {"images": [{"filename": ..., "subfolder": ..., "type": "output"}]}}
```

### Inline media preview uses a specific UI dict shape

To render a saved video inline (matching `PreviewVideo` / `SaveVideo`),
return exactly this shape — the `animated: (True,)` tuple is the flag
that flips the renderer from still image to video player:

```python
return {
    "ui": {
        "images": [
            {"filename": new_name, "subfolder": subfolder, "type": "output"}
        ],
        "animated": (True,),
    }
}
```

Image previews use the same shape without `animated`. Note that the key
is `"images"` even for video — that's not a typo, it's how the frontend
discriminator works.

### `INPUT_TYPES` shape

Classmethod returning a dict with `"required"`, optionally `"optional"`
and `"hidden"`. Type tuples are:

```python
@classmethod
def INPUT_TYPES(cls):
    return {
        "required": {
            "text":   ("STRING", {"default": "", "multiline": False}),
            "count":  ("INT",    {"default": 1, "min": 1, "max": 100}),
            "ratio":  ("FLOAT",  {"default": 1.0, "min": 0.0, "max": 10.0, "step": 0.01}),
            "mode":   (["a", "b", "c"], {"default": "a"}),   # dropdown
            "image":  ("IMAGE",),
            "video":  ("VIDEO",),
        },
    }
```

Default values are mandatory for primitives. Dropdowns are a list of
strings as the type slot.

### `IS_CHANGED` returning `float("NaN")` disables result caching

Use this for nodes whose output isn't fully determined by their declared
inputs — anything that reads from disk, calls an external process, or has
time-dependent behavior. Without it, ComfyUI may serve a stale cached
result on a re-run.

```python
@classmethod
def IS_CHANGED(cls, *args, **kwargs):
    return float("NaN")
```

The signature must match `execute`'s parameters (or accept `*args,
**kwargs`).

### Node registration

Two top-level dicts in the package `__init__.py`:

```python
NODE_CLASS_MAPPINGS = {
    "my_node_id": MyNode,
}
NODE_DISPLAY_NAME_MAPPINGS = {
    "my_node_id": "My Node",
}
```

The internal id (`my_node_id`) is what gets serialized into workflow
JSON — changing it breaks every saved workflow that uses the node. The
display name is safe to rename freely.

### Use `folder_paths` for any output path

Don't roll your own filename collision logic. Call:

```python
import folder_paths
full_folder, filename, counter, subfolder, _ = folder_paths.get_save_image_path(
    filename_prefix, folder_paths.get_output_directory()
)
out_path = os.path.join(full_folder, f"{filename}_{counter:05}.ext")
```

It handles `subfolder/name` splitting inside `filename_prefix` and gives
you the zero-padded counter the frontend expects. The same `subfolder`
value is what you put in the `{"ui": ...}` preview dict.

### Guard ComfyUI imports for testability

The `folder_paths`, `comfy_api`, and `comfy.*` modules only exist inside
a running ComfyUI process. Wrap the imports so the module still loads
under unit tests, CLI smoke runs, and IDE language servers:

```python
try:
    import folder_paths
except ImportError:
    folder_paths = None

try:
    from comfy_api.latest import InputImpl
except ImportError:
    InputImpl = None
```

Then check at the top of `execute()` and raise a clear error if you hit
`None`. The standalone `if __name__ == "__main__":` smoke block in each
node module is a useful pattern.

### The `VIDEO` type isn't always a path

It may be a path string *or* a `BytesIO`. Resolve before passing
anything to `subprocess`:

```python
def _video_to_path(video) -> str:
    get_source = getattr(video, "get_stream_source", None)
    src = get_source() if callable(get_source) else video

    if isinstance(src, str) and os.path.isfile(src):
        return src

    if isinstance(src, io.BytesIO):
        src.seek(0)
        data = src.read()
        digest = hashlib.sha1(data).hexdigest()[:16]
        temp_dir = folder_paths.get_input_directory() if folder_paths else "/tmp"
        temp_path = os.path.join(temp_dir, f"video_{digest}.mp4")
        if not os.path.isfile(temp_path):
            with open(temp_path, "wb") as f:
                f.write(data)
        return temp_path

    raise RuntimeError(f"Could not resolve VIDEO (got {type(src).__name__})")
```

Keying the temp file by content hash means re-runs reuse it instead of
piling up duplicates.

### Surface missing system binaries early

If your nodes shell out to external tools (ffmpeg, ffprobe, ImageMagick,
etc.), probe for them at module import in `__init__.py` and print a
stderr warning with per-OS install hints if missing:

```python
import shutil, sys
if not shutil.which("ffmpeg"):
    print(
        "[MyPack] WARNING: ffmpeg not found on PATH.\n"
        "  macOS:  brew install ffmpeg\n"
        "  Linux:  apt install ffmpeg\n"
        "  Windows: gyan.dev/ffmpeg/builds + add bin/ to PATH",
        file=sys.stderr,
    )
```

Otherwise users hit a cryptic `FileNotFoundError` deep inside an execute
call, often hours into a workflow.

### Comfy Registry publish triggers on `pyproject.toml` changes only

The standard `.github/workflows/publish.yml` runs the
`Comfy-Org/publish-node-action` on pushes to `main` whose path filter
matches `pyproject.toml`:

```yaml
on:
  push:
    branches: [main]
    paths: ["pyproject.toml"]
```

Code-only fixes don't ship to users on the Manager stable channel until
you bump the version. End any user-visible fix with a version bump in
`pyproject.toml` — that's the publish trigger, not the merge to main.

---

## Section B — FFmpeg / ffprobe (commonly hit from custom nodes)

### `atempo` per-stage range is `[0.5, 2.0]`

Speed factors outside that range silently distort the audio. Chain
stages of `0.5` or `2.0` until the remainder fits, then append the
remainder:

```python
def chain_atempo(speed_factor: float) -> str:
    parts = []
    remaining = speed_factor
    while remaining < 0.5:
        parts.append("atempo=0.5")
        remaining /= 0.5
    while remaining > 2.0:
        parts.append("atempo=2.0")
        remaining /= 2.0
    parts.append(f"atempo={remaining}")
    return ",".join(parts)

# 5x speed -> "atempo=2.0,atempo=2.0,atempo=1.25"
```

### Prefer `avg_frame_rate` over `r_frame_rate`

`r_frame_rate` is the LCM of stream timestamps and is unreliable on VFR
or AI-generated sources — some exporters declare `r_frame_rate=60/1` for
footage that actually plays at ~24 fps. Use `avg_frame_rate`
(`total_frames / duration`) and fall back to `r_frame_rate` only when
avg is missing or zero:

```python
avg = video_stream.get("avg_frame_rate", "0/0")
r   = video_stream.get("r_frame_rate", "0/1")
fps = parse_fraction(avg)
if fps <= 0:
    fps = parse_fraction(r)
```

### Harden fraction parsers against `"0/0"` and `"N/A"`

ffprobe returns these literally for unknown fields. A naive `num/den`
parser throws `ZeroDivisionError` or `ValueError`. Return `0.0` on
malformed input so the caller's fallback path triggers instead of
crashing the whole node:

```python
def parse_fraction(s):
    try:
        if "/" in s:
            num, den = s.split("/")
            den_f = float(den)
            return float(num) / den_f if den_f else 0.0
        return float(s)
    except (ValueError, AttributeError, TypeError):
        return 0.0
```

### `nb_frames` is often the literal string `"N/A"`

Common on MOV and some MKV containers. Wrap the parse and fall back to
`duration * fps`:

```python
try:
    frame_count = int(stream.get("nb_frames"))
except (TypeError, ValueError):
    frame_count = int(duration * fps) if duration > 0 and fps > 0 else 0
```

### Stream-copy with `-c copy` for container changes

Wrapping a video in a different container (mp4 ↔ mov ↔ mkv) doesn't need
re-encoding — `ffmpeg -y -i in.mp4 -c copy out.mov` is lossless and
near-instant. Reach for this before any pipeline that decodes and
re-encodes.
