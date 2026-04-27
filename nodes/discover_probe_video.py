"""
Trope_ProbeVideo — Probe a video file and extract metadata.

Runs ffprobe to extract framerate, duration, frame count, resolution,
codec info, and audio properties from a video file.
"""

import json
import subprocess

from ._ffmpeg import FFPROBE


class Trope_ProbeVideo:
    """Probe a video file and return structured metadata."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("MEDIA_INFO", "STRING",)
    RETURN_NAMES = ("media_info", "summary",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Inspect"

    def execute(self, video_path):
        cmd = [
            FFPROBE,
            "-v", "error",
            "-print_format", "json",
            "-show_entries",
            "format=duration:stream=r_frame_rate,avg_frame_rate,nb_frames,"
            "width,height,codec_name,codec_type,sample_rate,channels",
            video_path,
        ]

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        if result.returncode != 0:
            raise RuntimeError(f"ffprobe failed: {result.stderr.strip()}")

        data = json.loads(result.stdout)
        fmt = data.get("format", {})
        streams = data.get("streams", [])

        video_stream = None
        audio_stream = None
        for s in streams:
            ct = s.get("codec_type")
            if ct == "video" and video_stream is None:
                video_stream = s
            elif ct == "audio" and audio_stream is None:
                audio_stream = s

        if video_stream is None:
            raise RuntimeError("No video stream found in file")

        r_frame_rate = video_stream.get("r_frame_rate", "0/1")
        fps = _parse_fraction(r_frame_rate)
        duration = float(fmt.get("duration", 0))

        # nb_frames is often the literal string "N/A" on MOV/some MKV containers,
        # so we can't rely on key presence — try to parse, fall back to duration*fps.
        frame_count = 0
        nb_frames_raw = video_stream.get("nb_frames")
        try:
            frame_count = int(nb_frames_raw)
        except (TypeError, ValueError):
            if duration > 0 and fps > 0:
                frame_count = int(duration * fps)

        width = int(video_stream.get("width", 0))
        height = int(video_stream.get("height", 0))
        video_codec = video_stream.get("codec_name", "unknown")

        has_audio = audio_stream is not None
        audio_sample_rate = int(audio_stream.get("sample_rate", 0)) if has_audio else 0
        audio_channels = int(audio_stream.get("channels", 0)) if has_audio else 0
        audio_codec = audio_stream.get("codec_name", "") if has_audio else ""

        media_info = {
            "path": video_path,
            "framerate": fps,
            "framerate_fraction": r_frame_rate,
            "duration": duration,
            "frame_count": frame_count,
            "width": width,
            "height": height,
            "video_codec": video_codec,
            "has_audio": has_audio,
            "audio_sample_rate": audio_sample_rate,
            "audio_channels": audio_channels,
            "audio_codec": audio_codec,
        }

        summary_lines = [
            f"File: {video_path}",
            f"FPS: {fps:.3f} ({r_frame_rate})",
            f"Duration: {duration:.2f}s",
            f"Frames: {frame_count}",
            f"Resolution: {width}x{height}",
            f"Video codec: {video_codec}",
        ]
        if has_audio:
            summary_lines.append(f"Audio: {audio_codec} {audio_sample_rate}Hz {audio_channels}ch")
        else:
            summary_lines.append("Audio: none")

        summary = "\n".join(summary_lines)
        return (media_info, summary,)


def _parse_fraction(fraction_str):
    """Parse a framerate fraction string like '24000/1001' to float."""
    if "/" in fraction_str:
        num, den = fraction_str.split("/")
        return float(num) / float(den)
    return float(fraction_str)


if __name__ == "__main__":
    import sys
    node = Trope_ProbeVideo()
    if len(sys.argv) > 1:
        info, summary = node.execute(sys.argv[1])
        print(summary)
        print("\nRaw media_info:")
        print(json.dumps(info, indent=2))
    else:
        print("Usage: python discover_probe_video.py <video_path>")
