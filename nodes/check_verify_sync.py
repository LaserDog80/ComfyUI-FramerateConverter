"""
Trope_VerifySync — Verify audio/video sync in output file.

Checks that video and audio stream durations and start times
are within tolerance of each other.
"""

import json
import subprocess

from ._ffmpeg import FFPROBE


class Trope_VerifySync:
    """Verify audio and video streams are synchronized."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "duration_tolerance": ("FLOAT", {"default": 0.05, "min": 0.0, "max": 1.0, "step": 0.01}),
                "start_tolerance": ("FLOAT", {"default": 0.01, "min": 0.0, "max": 1.0, "step": 0.001}),
            },
        }

    RETURN_TYPES = ("BOOLEAN", "STRING",)
    RETURN_NAMES = ("passed", "message",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Verify"

    def execute(self, video_path, duration_tolerance=0.05, start_tolerance=0.01):
        cmd = [
            FFPROBE,
            "-v", "error",
            "-print_format", "json",
            "-show_entries", "stream=duration,start_time,codec_type",
            video_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        except subprocess.TimeoutExpired:
            return (False, "ffprobe timed out",)
        except FileNotFoundError:
            return (False, "ffprobe not found",)

        if result.returncode != 0:
            return (False, f"ffprobe failed: {result.stderr.strip()}",)

        data = json.loads(result.stdout)
        streams = data.get("streams", [])

        video_stream = None
        audio_stream = None
        for s in streams:
            ct = s.get("codec_type")
            if ct == "video" and video_stream is None:
                video_stream = s
            elif ct == "audio" and audio_stream is None:
                audio_stream = s

        if audio_stream is None:
            return (True, "PASS: No audio stream — sync check skipped",)

        if video_stream is None:
            return (False, "FAIL: No video stream found",)

        video_duration = float(video_stream.get("duration", 0))
        audio_duration = float(audio_stream.get("duration", 0))
        duration_diff = abs(video_duration - audio_duration)

        video_start = float(video_stream.get("start_time", 0))
        audio_start = float(audio_stream.get("start_time", 0))
        start_diff = abs(video_start - audio_start)

        messages = []
        passed = True

        if duration_diff > duration_tolerance:
            passed = False
            messages.append(
                f"FAIL: Duration mismatch — video={video_duration:.3f}s, "
                f"audio={audio_duration:.3f}s (diff={duration_diff:.3f}s)"
            )
        else:
            messages.append(
                f"PASS: Durations match — video={video_duration:.3f}s, "
                f"audio={audio_duration:.3f}s (diff={duration_diff:.3f}s)"
            )

        if start_diff > start_tolerance:
            passed = False
            messages.append(
                f"FAIL: Start time mismatch — video={video_start:.3f}s, "
                f"audio={audio_start:.3f}s (diff={start_diff:.3f}s)"
            )

        return (passed, "\n".join(messages),)


if __name__ == "__main__":
    import sys
    node = Trope_VerifySync()
    if len(sys.argv) > 1:
        passed, msg = node.execute(sys.argv[1])
        print(msg)
    else:
        print("Usage: python check_verify_sync.py <video_path>")
