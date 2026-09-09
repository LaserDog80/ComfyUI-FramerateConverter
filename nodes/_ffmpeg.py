"""
Locate ffmpeg / ffprobe binaries.

When ComfyUI is launched as a macOS .app (or via Finder, Dock, Launchpad),
the GUI process inherits a minimal PATH that does not include /opt/homebrew/bin
or /usr/local/bin, so a bare `subprocess.run(["ffmpeg", ...])` raises
FileNotFoundError. Resolve to absolute paths once at import time and reuse.
"""

import os
import shutil
import subprocess
import tempfile
import time

try:
    import comfy.model_management as model_management
except ImportError:
    model_management = None


def run_cancellable(command, *, capture_output=True, text=True, timeout=60):
    """Run ffmpeg/ffprobe with cancellation and disk-backed log capture.

    Keep stdout intact for ffprobe JSON; retain the last MiB of diagnostics.
    No pipe can fill while waiting. Always reap the child on timeout/cancel.
    """
    def check():
        if model_management is not None:
            model_management.throw_exception_if_processing_interrupted()

    check()
    with tempfile.TemporaryFile() as stdout, tempfile.TemporaryFile() as stderr:
        process = subprocess.Popen(command, stdin=subprocess.DEVNULL, stdout=stdout, stderr=stderr)
        start = time.monotonic()
        try:
            while process.poll() is None:
                check()
                if time.monotonic() - start >= timeout:
                    raise subprocess.TimeoutExpired(command, timeout)
                time.sleep(0.1)
            check()
        except BaseException:
            if process.poll() is None:
                process.terminate()
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait()
            raise
        stdout.seek(0)
        stderr.seek(max(0, stderr.tell() - 1024 * 1024))
        out, err = stdout.read(), stderr.read()
        if text:
            out, err = out.decode("utf-8", errors="replace"), err.decode("utf-8", errors="replace")
        return subprocess.CompletedProcess(command, process.returncode, out, err)


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
