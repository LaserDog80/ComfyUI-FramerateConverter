"""
Trope_BuildCommand — Build the FFmpeg command for framerate conversion.

Takes conversion parameters, audio parameters, and file paths to produce
the complete FFmpeg command. Supports all four conversion methods.
"""

from fractions import Fraction

from ._ffmpeg import FFMPEG


# Minterpolate quality presets
_MINTERPOLATE_PRESETS = {
    "fast": {"mi_mode": "dup", "mc_mode": "obmc", "me_mode": "bidir", "vsbmc": 0},
    "medium": {"mi_mode": "blend", "mc_mode": "obmc", "me_mode": "bidir", "vsbmc": 0},
    "high": {"mi_mode": "mci", "mc_mode": "obmc", "me_mode": "bidir", "vsbmc": 0},
    "best": {"mi_mode": "mci", "mc_mode": "aobmc", "me_mode": "bidir", "vsbmc": 1},
}

QUALITY_PRESETS = ["fast", "medium", "high", "best"]


class Trope_BuildCommand:
    """Build the FFmpeg command for a framerate conversion."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "video_path": ("STRING", {"default": "", "multiline": False}),
                "output_path": ("STRING", {"default": "", "multiline": False}),
                "conversion_params": ("CONV_PARAMS",),
            },
            "optional": {
                "audio_params": ("AUDIO_PARAMS",),
                "video_codec": ("STRING", {"default": "libx264"}),
                "crf": ("INT", {"default": 18, "min": 0, "max": 51}),
                "preset": ("STRING", {"default": "medium"}),
                "audio_codec": ("STRING", {"default": "aac"}),
                "audio_bitrate": ("STRING", {"default": "192k"}),
                "minterpolate_quality": (QUALITY_PRESETS, {"default": "high"}),
            },
        }

    RETURN_TYPES = ("STRING", "CMD_LIST",)
    RETURN_NAMES = ("ffmpeg_command", "command_list",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Configure"

    def execute(self, video_path, output_path, conversion_params,
                audio_params=None, video_codec="libx264", crf=18,
                preset="medium", audio_codec="aac", audio_bitrate="192k",
                minterpolate_quality="high"):

        method = conversion_params["method"]
        source_fps = conversion_params["source_fps"]
        target_fps = conversion_params["target_fps"]

        audio_mode = audio_params["audio_mode"] if audio_params else "allow_shift"
        audio_filter = audio_params["filter_string"] if audio_params else f"atempo={target_fps / source_fps}"

        if method == "speed_change":
            cmd = self._build_speed_change(
                video_path, output_path, source_fps, target_fps,
                audio_mode, audio_filter, video_codec, crf, preset,
                audio_codec, audio_bitrate,
            )
        elif method == "frame_drop":
            cmd = self._build_fps_filter(
                video_path, output_path, target_fps,
                video_codec, crf, preset,
            )
        elif method == "frame_blend":
            cmd = self._build_framerate_blend(
                video_path, output_path, target_fps,
                video_codec, crf, preset,
            )
        elif method == "minterpolate":
            cmd = self._build_minterpolate(
                video_path, output_path, target_fps,
                minterpolate_quality, video_codec, crf, preset,
            )
        else:
            raise ValueError(f"Unknown method: {method}")

        cmd_string = _command_to_string(cmd)
        return (cmd_string, cmd,)

    def _build_speed_change(self, inp, out, src_fps, tgt_fps,
                            audio_mode, audio_filter,
                            vcodec, crf, preset, acodec, abitrate):
        src = Fraction(src_fps).limit_denominator(10001)
        tgt = Fraction(tgt_fps).limit_denominator(10001)
        pts = src / tgt

        if audio_mode == "no_audio":
            return [
                FFMPEG, "-y", "-i", inp,
                "-filter_complex", f"[0:v]setpts={pts}*PTS[v]",
                "-map", "[v]", "-an",
                "-r", str(tgt_fps),
                "-c:v", vcodec, "-crf", str(crf), "-preset", preset,
                out,
            ]
        elif audio_mode == "copy":
            return [
                FFMPEG, "-y", "-i", inp,
                "-filter_complex", f"[0:v]setpts={pts}*PTS[v]",
                "-map", "[v]", "-map", "0:a",
                "-r", str(tgt_fps),
                "-c:v", vcodec, "-crf", str(crf), "-preset", preset,
                "-c:a", "copy",
                out,
            ]
        else:  # preserve_pitch and allow_shift use the same shape;
               # the audio_filter string from CalcAudio differs between them.
            filter_complex = f"[0:v]setpts={pts}*PTS[v];[0:a]{audio_filter}[a]"
            return [
                FFMPEG, "-y", "-i", inp,
                "-filter_complex", filter_complex,
                "-map", "[v]", "-map", "[a]",
                "-r", str(tgt_fps),
                "-c:v", vcodec, "-crf", str(crf), "-preset", preset,
                "-c:a", acodec, "-b:a", abitrate,
                out,
            ]

    def _build_fps_filter(self, inp, out, tgt_fps, vcodec, crf, preset):
        return [
            FFMPEG, "-y", "-i", inp,
            "-vf", f"fps={tgt_fps}",
            "-c:a", "copy",
            "-c:v", vcodec, "-crf", str(crf), "-preset", preset,
            out,
        ]

    def _build_framerate_blend(self, inp, out, tgt_fps, vcodec, crf, preset):
        filt = f"framerate=fps={tgt_fps}:interp_start=0:interp_end=255:scene=100"
        return [
            FFMPEG, "-y", "-i", inp,
            "-vf", filt,
            "-c:a", "copy",
            "-c:v", vcodec, "-crf", str(crf), "-preset", preset,
            out,
        ]

    def _build_minterpolate(self, inp, out, tgt_fps, quality, vcodec, crf, preset):
        mi = _MINTERPOLATE_PRESETS[quality]
        filt = (
            f"minterpolate=fps={tgt_fps}:"
            f"mi_mode={mi['mi_mode']}:"
            f"mc_mode={mi['mc_mode']}:"
            f"me_mode={mi['me_mode']}:"
            f"vsbmc={mi['vsbmc']}:"
            f"scd=fdiff"
        )
        return [
            FFMPEG, "-y", "-i", inp,
            "-vf", filt,
            "-c:a", "copy",
            "-c:v", vcodec, "-crf", str(crf), "-preset", preset,
            out,
        ]


def _command_to_string(cmd):
    """Convert command list to a shell-safe display string."""
    def quote(arg):
        if " " in arg or ";" in arg or "[" in arg:
            return f'"{arg}"'
        return arg
    return " ".join(quote(a) for a in cmd)


if __name__ == "__main__":
    node = Trope_BuildCommand()
    conv_params = {
        "method": "speed_change",
        "source_fps": 24.0,
        "target_fps": 25.0,
        "speed_factor": 25.0 / 24.0,
        "pts_factor": 24.0 / 25.0,
    }
    audio_params = {
        "audio_mode": "allow_shift",
        "filter_string": "atempo=1.0416666666666667",
    }
    cmd_str, cmd_list = node.execute(
        "input.mp4", "output.mp4", conv_params, audio_params,
    )
    print(cmd_str)
