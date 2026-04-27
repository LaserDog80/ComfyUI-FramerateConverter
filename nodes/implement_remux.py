"""
Trope_Remux — Remux a video into a different container format.

Stream-copies all tracks (no re-encoding) into the target container —
no quality loss, just a wrapper change. VIDEO in -> VIDEO out so it
chains naturally with Convert Framerate and ComfyUI's built-in
Load Video / Save Video.
"""

import hashlib
import io
import os
import subprocess

from ._ffmpeg import FFMPEG


# These imports only succeed inside a running ComfyUI process. Guard them so
# the module still loads for unit tests / standalone smoke tests.
try:
    import folder_paths
except ImportError:
    folder_paths = None

try:
    from comfy_api.latest import InputImpl
except ImportError:
    InputImpl = None


FORMATS = ["mov", "mp4", "mkv"]
FORMAT_EXT = {
    "mov": ".mov",
    "mp4": ".mp4",
    "mkv": ".mkv",
}


class Trope_Remux:
    """Change a video's container format without re-encoding."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("VIDEO",),
                "target_format": (FORMATS, {"default": "mov"}),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("output",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter"

    def execute(self, input, target_format):
        src_path = self._video_to_path(input)
        target_ext = FORMAT_EXT[target_format]
        basename = os.path.basename(src_path)
        stem, current_ext = os.path.splitext(basename)

        # Already in the target container — skip the round-trip.
        if current_ext.lower() == target_ext.lower():
            if InputImpl is None:
                raise RuntimeError("ComfyUI VIDEO type unavailable; cannot return result.")
            return (InputImpl.VideoFromFile(src_path),)

        output_dir = folder_paths.get_input_directory() if folder_paths else os.path.dirname(src_path)
        new_name = f"{stem}_remux{target_ext}"
        output_path = os.path.join(output_dir, new_name)

        if os.path.exists(output_path):
            base, ext = os.path.splitext(output_path)
            counter = 1
            while os.path.exists(output_path):
                output_path = f"{base}_{counter}{ext}"
                counter += 1

        cmd = [
            FFMPEG, "-y",
            "-i", src_path,
            "-c", "copy",
            output_path,
        ]

        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            raise RuntimeError("Remux timed out (10 minute limit)")
        except FileNotFoundError:
            raise RuntimeError("ffmpeg not found. Is FFmpeg installed?")

        if result.returncode != 0:
            raise RuntimeError(
                f"FFmpeg remux failed:\n{result.stderr.strip()[-500:]}"
            )

        if InputImpl is None:
            raise RuntimeError("ComfyUI VIDEO type unavailable; cannot return result.")

        return (InputImpl.VideoFromFile(output_path),)

    @classmethod
    def IS_CHANGED(cls, input, target_format):
        return float("NaN")

    @staticmethod
    def _video_to_path(video) -> str:
        """Resolve a ComfyUI VIDEO object to a real file path on disk."""
        get_source = getattr(video, "get_stream_source", None)
        if callable(get_source):
            src = get_source()
        else:
            src = video

        if isinstance(src, str) and os.path.isfile(src):
            return src

        if isinstance(src, io.BytesIO):
            src.seek(0)
            data = src.read()
            digest = hashlib.sha1(data).hexdigest()[:16]
            temp_dir = (
                folder_paths.get_input_directory() if folder_paths else "/tmp"
            )
            temp_path = os.path.join(temp_dir, f"trope_video_{digest}.mp4")
            if not os.path.isfile(temp_path):
                with open(temp_path, "wb") as f:
                    f.write(data)
            return temp_path

        raise RuntimeError(
            f"Remux Container could not resolve the incoming VIDEO to a "
            f"readable file (got source type: {type(src).__name__})."
        )


if __name__ == "__main__":
    print("Remux node loaded.")
    print(f"Supported formats: {FORMATS}")
    print(f"folder_paths available: {folder_paths is not None}")
    print(f"InputImpl available: {InputImpl is not None}")
