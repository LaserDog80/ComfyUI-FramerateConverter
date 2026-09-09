"""
Trope_VerifyFPS — Verify that output video has the expected framerate.

Runs ffprobe on the output file and compares r_frame_rate against
the target fps with a configurable tolerance (default ±0.001).
"""

import json
import subprocess
from ._ffmpeg import run_cancellable

from ._ffmpeg import FFPROBE


class Trope_VerifyFPS:
    """Verify output video framerate matches target."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False}),
                "target_fps": ("FLOAT", {"default": 25.0, "min": 1.0, "max": 240.0, "step": 0.001}),
            },
            "optional": {
                "tolerance": ("FLOAT", {"default": 0.001, "min": 0.0, "max": 1.0, "step": 0.001}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "FLOAT", "STRING",)
    RETURN_NAMES = ("passed", "actual_fps", "message",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Verify"

    def execute(self, video_path, target_fps, tolerance=0.001):
        cmd = [
            FFPROBE,
            "-v", "error",
            "-print_format", "json",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate",
            video_path,
        ]

        try:
            result = run_cancellable(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return (False, 0.0, "ffprobe timed out",)
        except FileNotFoundError:
            return (False, 0.0, "ffprobe not found",)

        if result.returncode != 0:
            return (False, 0.0, f"ffprobe failed: {result.stderr.strip()}",)

        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        if not streams:
            return (False, 0.0, "No video stream found in output",)

        r_frame_rate = streams[0].get("r_frame_rate", "0/1")
        actual_fps = _parse_fraction(r_frame_rate)

        diff = abs(actual_fps - target_fps)
        passed = diff <= tolerance

        if passed:
            message = f"PASS: {actual_fps:.3f}fps matches target {target_fps:.3f}fps (diff={diff:.6f})"
        else:
            message = f"FAIL: {actual_fps:.3f}fps != target {target_fps:.3f}fps (diff={diff:.6f}, tolerance={tolerance})"

        return (passed, actual_fps, message,)


def _parse_fraction(fraction_str):
    if "/" in fraction_str:
        num, den = fraction_str.split("/")
        return float(num) / float(den)
    return float(fraction_str)


if __name__ == "__main__":
    import sys
    node = Trope_VerifyFPS()
    if len(sys.argv) > 2:
        passed, actual, msg = node.execute(sys.argv[1], float(sys.argv[2]))
        print(msg)
    else:
        print("Usage: python check_verify_fps.py <video_path> <target_fps>")
