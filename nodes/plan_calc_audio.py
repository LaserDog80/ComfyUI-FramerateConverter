"""
Trope_CalcAudio — Calculate audio processing parameters.

Computes the audio filter string, pitch shift, and intermediate sample
rate for a given framerate conversion and audio handling mode.
"""

import math


AUDIO_MODES = ["allow_shift", "preserve_pitch", "copy", "no_audio"]


class Trope_CalcAudio:
    """Calculate audio processing parameters for framerate conversion."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source_fps": ("FLOAT", {"default": 24.0, "min": 1.0, "max": 240.0, "step": 0.001}),
                "target_fps": ("FLOAT", {"default": 25.0, "min": 1.0, "max": 240.0, "step": 0.001}),
                "audio_mode": (AUDIO_MODES, {"default": "allow_shift"}),
            },
            "optional": {
                "sample_rate": ("INT", {"default": 48000, "min": 8000, "max": 384000}),
            },
        }

    RETURN_TYPES = ("AUDIO_PARAMS", "STRING",)
    RETURN_NAMES = ("audio_params", "summary",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Configure"

    def execute(self, source_fps, target_fps, audio_mode, sample_rate=48000):
        speed_factor = target_fps / source_fps

        # Pitch shift in semitones (for informational purposes)
        pitch_shift_semitones = 12.0 * math.log2(speed_factor)

        # Build the audio filter string
        if audio_mode == "no_audio":
            filter_string = ""
            description = "Audio will be removed"
            pitch_shift_semitones = 0.0
            intermediate_rate = 0
        elif audio_mode == "copy":
            filter_string = "copy"
            description = "Audio copied unchanged (will desync with speed-changed video)"
            pitch_shift_semitones = 0.0
            intermediate_rate = 0
        elif audio_mode == "preserve_pitch":
            intermediate_rate = int(sample_rate * speed_factor)
            filter_string = f"asetrate={intermediate_rate},aresample={sample_rate}"
            description = "Audio speed-adjusted with pitch correction"
            pitch_shift_semitones = 0.0
        else:  # allow_shift
            filter_string = f"atempo={speed_factor}"
            description = f"Audio speed-adjusted, pitch shifts {pitch_shift_semitones:+.2f} semitones"
            intermediate_rate = 0

        params = {
            "audio_mode": audio_mode,
            "filter_string": filter_string,
            "speed_factor": speed_factor,
            "pitch_shift_semitones": pitch_shift_semitones,
            "sample_rate": sample_rate,
            "intermediate_sample_rate": intermediate_rate,
        }

        lines = [
            f"Audio mode: {audio_mode}",
            description,
        ]
        if audio_mode == "allow_shift":
            lines.append(f"Pitch shift: {pitch_shift_semitones:+.2f} semitones")
        if audio_mode == "preserve_pitch":
            lines.append(f"Intermediate sample rate: {intermediate_rate}Hz -> {sample_rate}Hz")

        return (params, "\n".join(lines),)


if __name__ == "__main__":
    node = Trope_CalcAudio()
    for mode in AUDIO_MODES:
        params, summary = node.execute(24.0, 25.0, mode)
        print(f"--- {mode} ---")
        print(summary)
        print()
