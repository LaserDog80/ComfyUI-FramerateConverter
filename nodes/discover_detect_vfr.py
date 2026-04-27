"""
Trope_DetectVFR — Detect if a video has variable framerate.

Compares r_frame_rate and avg_frame_rate from ffprobe.
A divergence > 0.5 fps indicates variable framerate.
"""

import json
import subprocess

from ._ffmpeg import FFPROBE


class Trope_DetectVFR:
    """Detect whether a video file has variable framerate."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING",)
    RETURN_NAMES = ("is_vfr", "message",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Inspect"

    def execute(self, video_path):
        cmd = [
            FFPROBE,
            "-v", "error",
            "-print_format", "json",
            "-select_streams", "v:0",
            "-show_entries", "stream=r_frame_rate,avg_frame_rate",
            video_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

        data = json.loads(result.stdout)
        streams = data.get("streams", [])
        if not streams:
            return (False, "No video stream found",)

        stream = streams[0]
        r_fps = _parse_fraction(stream.get("r_frame_rate", "0/1"))
        avg_fps = _parse_fraction(stream.get("avg_frame_rate", "0/1"))

        is_vfr = abs(r_fps - avg_fps) > 0.5

        if is_vfr:
            message = (
                f"Variable framerate detected: base={r_fps:.3f}fps, "
                f"avg={avg_fps:.3f}fps. Consider converting to CFR first."
            )
        else:
            message = f"Constant framerate: {r_fps:.3f}fps"

        return (is_vfr, message,)


def _parse_fraction(fraction_str):
    if "/" in fraction_str:
        num, den = fraction_str.split("/")
        return float(num) / float(den)
    return float(fraction_str)


if __name__ == "__main__":
    import sys
    node = Trope_DetectVFR()
    if len(sys.argv) > 1:
        is_vfr, msg = node.execute(sys.argv[1])
        print(f"VFR: {is_vfr}")
        print(msg)
    else:
        print("Usage: python discover_detect_vfr.py <video_path>")
