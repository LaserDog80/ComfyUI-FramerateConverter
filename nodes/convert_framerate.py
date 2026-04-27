"""
Trope_ConvertFramerate — One-shot framerate conversion.

Single in/out node: VIDEO in -> VIDEO out. Wraps the whole pipeline
(probe -> calculate -> build -> execute) so it drops naturally into a
Load Video -> Convert Framerate -> Save Video chain.
"""

import hashlib
import io
import os

from .discover_probe_video import Trope_ProbeVideo
from .plan_calc_conversion import Trope_CalcConversion, METHODS
from .plan_calc_audio import Trope_CalcAudio, AUDIO_MODES
from .plan_gen_output_path import Trope_GenOutputPath
from .plan_build_command import Trope_BuildCommand, QUALITY_PRESETS
from .implement_convert import Trope_RunFFmpeg


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


class Trope_ConvertFramerate:
    """One-node framerate conversion: VIDEO in, VIDEO out."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input": ("VIDEO",),
                "target_fps": ("FLOAT", {"default": 25.0, "min": 1.0, "max": 240.0, "step": 0.001}),
            },
            "optional": {
                "method": (METHODS, {"default": "speed_change"}),
                "audio_mode": (AUDIO_MODES, {"default": "allow_shift"}),
                "crf": ("INT", {"default": 18, "min": 0, "max": 51}),
                "minterpolate_quality": (QUALITY_PRESETS, {"default": "high"}),
            },
        }

    RETURN_TYPES = ("VIDEO",)
    RETURN_NAMES = ("output",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter"

    def execute(self, input, target_fps, method="speed_change",
                audio_mode="allow_shift", crf=18,
                minterpolate_quality="high"):
        src_path = self._video_to_path(input)

        media_info, _ = Trope_ProbeVideo().execute(src_path)
        source_fps = media_info["framerate"]
        sample_rate = media_info["audio_sample_rate"] or 48000

        # Sources without audio can't be -map'd to an audio stream.
        effective_audio_mode = "no_audio" if not media_info["has_audio"] else audio_mode

        conv_params, _ = Trope_CalcConversion().execute(
            source_fps, target_fps, method,
            input_duration=media_info["duration"],
            input_frame_count=media_info["frame_count"],
        )
        audio_params, _ = Trope_CalcAudio().execute(
            source_fps, target_fps, effective_audio_mode, sample_rate,
        )
        # Write into ComfyUI's input dir so it's sandbox-safe and can be
        # re-loaded by other nodes if needed.
        output_dir = folder_paths.get_input_directory() if folder_paths else ""
        (out_path,) = Trope_GenOutputPath().execute(
            src_path, target_fps, output_dir,
        )
        _, command_list = Trope_BuildCommand().execute(
            src_path, out_path, conv_params, audio_params,
            crf=crf, minterpolate_quality=minterpolate_quality,
        )
        out_path, ffmpeg_output, success = Trope_RunFFmpeg().execute(command_list)

        if not success:
            raise RuntimeError(
                f"FFmpeg conversion failed:\n{ffmpeg_output.strip()[-500:]}"
            )

        if InputImpl is None:
            raise RuntimeError("ComfyUI VIDEO type unavailable; cannot return result.")

        return (InputImpl.VideoFromFile(out_path),)

    @classmethod
    def IS_CHANGED(cls, input, target_fps, **kwargs):
        return float("NaN")

    @staticmethod
    def _video_to_path(video) -> str:
        """Resolve a ComfyUI VIDEO object to a real file path on disk.

        Handles both VideoFromFile-with-string-source (the common case from
        Load Video) and VideoFromFile-with-BytesIO (e.g. videos synthesized
        in-memory by upstream nodes). For BytesIO sources, dump to a stable
        temp file in ComfyUI's input dir so ffmpeg can read it.
        """
        get_source = getattr(video, "get_stream_source", None)
        if callable(get_source):
            src = get_source()
        else:
            src = video  # last-ditch: assume the object itself is a path/buffer

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
            f"Convert Framerate could not resolve the incoming VIDEO to a "
            f"readable file (got source type: {type(src).__name__})."
        )


if __name__ == "__main__":
    print("Composite node loaded.")
    print(f"Methods: {METHODS}")
    print(f"Audio modes: {AUDIO_MODES}")
    print(f"folder_paths available: {folder_paths is not None}")
    print(f"InputImpl available: {InputImpl is not None}")
