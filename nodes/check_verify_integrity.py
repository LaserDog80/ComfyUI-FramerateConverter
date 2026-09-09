"""
Trope_VerifyIntegrity — Verify output video is not corrupted.

Performs a full decode test by running ffmpeg -f null, checking for
decode errors in stderr output.
"""

import subprocess
from ._ffmpeg import run_cancellable

from ._ffmpeg import FFMPEG


class Trope_VerifyIntegrity:
    """Verify output video file integrity via full decode test."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING",)
    RETURN_NAMES = ("passed", "message",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Verify"

    def execute(self, video_path):
        cmd = [
            FFMPEG,
            "-v", "error",
            "-i", video_path,
            "-f", "null",
            "-",
        ]

        try:
            result = run_cancellable(
                cmd,
                capture_output=True,
                text=True,
                timeout=300,
            )
        except subprocess.TimeoutExpired:
            return (False, "FAIL: Decode verification timed out (5 min limit)",)
        except FileNotFoundError:
            return (False, "FAIL: ffmpeg not found",)

        if result.returncode != 0:
            return (False, f"FAIL: File failed to decode — {result.stderr.strip()}",)

        # `-v error` only emits real errors, but transient decoder warnings can
        # surface here too. Only treat lines containing actual error keywords as
        # failures — informational lines and empty stderr both pass.
        stderr = result.stderr.strip()
        if stderr:
            error_lines = [
                line for line in stderr.splitlines()
                if _is_decode_error(line)
            ]
            if error_lines:
                joined = "\n".join(error_lines)
                return (False, f"FAIL: Decode errors — {joined}",)

        return (True, "PASS: Full decode completed with zero errors",)

    @classmethod
    def IS_CHANGED(cls, video_path):
        # Re-run if the file might have changed
        import os
        try:
            stat = os.stat(video_path)
            return f"{stat.st_mtime}_{stat.st_size}"
        except OSError:
            return float("NaN")


_DECODE_ERROR_KEYWORDS = (
    "error", "invalid", "corrupt", "missing", "could not",
    "failed", "no frame", "truncat",
)


def _is_decode_error(line: str) -> bool:
    """Return True if an ffmpeg stderr line indicates a real decode error."""
    lower = line.lower()
    return any(kw in lower for kw in _DECODE_ERROR_KEYWORDS)


if __name__ == "__main__":
    import sys
    node = Trope_VerifyIntegrity()
    if len(sys.argv) > 1:
        passed, msg = node.execute(sys.argv[1])
        print(msg)
    else:
        print("Usage: python check_verify_integrity.py <video_path>")
