"""
Locate ffmpeg / ffprobe binaries.

When ComfyUI is launched as a macOS .app (or via Finder, Dock, Launchpad),
the GUI process inherits a minimal PATH that does not include /opt/homebrew/bin
or /usr/local/bin, so a bare `subprocess.run(["ffmpeg", ...])` raises
FileNotFoundError. Resolve to absolute paths once at import time and reuse.
"""

import os
import shutil


_EXTRA_DIRS = [
    # macOS
    "/opt/homebrew/bin",        # Apple Silicon Homebrew
    "/usr/local/bin",           # Intel Homebrew / common Linux
    # Linux
    "/usr/bin",
    "/snap/bin",
    # Windows — checked relative to common install roots
    r"C:\ffmpeg\bin",
    r"C:\Program Files\ffmpeg\bin",
    r"C:\Program Files (x86)\ffmpeg\bin",
]


def _resolve(name: str) -> str:
    """Return absolute path to a binary, falling back to the bare name."""
    found = shutil.which(name)
    if found:
        return found
    # On Windows, shutil.which finds .exe automatically when the name is
    # passed without extension, so we don't need to special-case it here.
    for d in _EXTRA_DIRS:
        for candidate in (os.path.join(d, name), os.path.join(d, name + ".exe")):
            if os.path.isfile(candidate) and os.access(candidate, os.X_OK):
                return candidate
    return name


FFMPEG = _resolve("ffmpeg")
FFPROBE = _resolve("ffprobe")


def is_available() -> tuple[bool, bool]:
    """Return (ffmpeg_found, ffprobe_found). Both must be True for the pack to work."""
    return (
        os.path.isabs(FFMPEG) and os.access(FFMPEG, os.X_OK),
        os.path.isabs(FFPROBE) and os.access(FFPROBE, os.X_OK),
    )
