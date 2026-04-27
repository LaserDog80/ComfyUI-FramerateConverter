"""
Trope_Remux — Remux a video into a different container format and save it.

Stream-copies all tracks (no re-encoding) into the target container —
no quality loss, just a wrapper change. Pure output node: writes to
ComfyUI's output directory and previews the saved file in-graph. Has
no output port because piping through Save Video would re-save as mp4
and lose the chosen container.
"""

import hashlib
import io
import os
import subprocess

from ._ffmpeg import FFMPEG


# Guarded so the module still loads for standalone smoke tests outside ComfyUI.
try:
    import folder_paths
except ImportError:
    folder_paths = None


FORMATS = ["mov", "mp4", "mkv"]
FORMAT_EXT = {
    "mov": ".mov",
    "mp4": ".mp4",
    "mkv": ".mkv",
}


class Trope_Remux:
    """Change a video's container format without re-encoding, and save it."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("VIDEO",),
                "target_format": (FORMATS, {"default": "mov"}),
                "filename_prefix": ("STRING", {"default": "video/ComfyUI"}),
            },
        }

    RETURN_TYPES = ()
    FUNCTION = "execute"
    OUTPUT_NODE = True
    CATEGORY = "Trope Tools/Framerate Converter"

    def execute(self, input, target_format, filename_prefix):
        if folder_paths is None:
            raise RuntimeError(
                "ComfyUI folder_paths unavailable; cannot save remuxed video."
            )

        src_path = self._video_to_path(input)
        target_ext = FORMAT_EXT[target_format]

        full_output_folder, filename, counter, subfolder, _ = (
            folder_paths.get_save_image_path(
                filename_prefix, folder_paths.get_output_directory()
            )
        )
        os.makedirs(full_output_folder, exist_ok=True)
        new_name = f"{filename}_{counter:05}{target_ext}"
        output_path = os.path.join(full_output_folder, new_name)

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

        # ComfyUI's frontend renders this dict shape as an inline video player —
        # same payload its built-in PreviewVideo / SaveVideo emit.
        return {
            "ui": {
                "images": [
                    {
                        "filename": new_name,
                        "subfolder": subfolder,
                        "type": "output",
                    }
                ],
                "animated": (True,),
            }
        }

    @classmethod
    def IS_CHANGED(cls, input, target_format, filename_prefix):
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
