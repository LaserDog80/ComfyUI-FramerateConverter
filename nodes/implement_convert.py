"""
Trope_RunFFmpeg — Execute an FFmpeg framerate conversion.

Runs the FFmpeg command built by Trope_BuildCommand and returns
the result status, output path, and FFmpeg stderr output.
"""

import re
import subprocess


class Trope_RunFFmpeg:
    """Execute an FFmpeg conversion command."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "command_list": ("CMD_LIST",),
            },
            "optional": {
                "expected_duration": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 86400.0}),
            },
        }

    RETURN_TYPES = ("STRING", "STRING", "BOOLEAN",)
    RETURN_NAMES = ("output_path", "ffmpeg_output", "success",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Process"
    OUTPUT_NODE = True

    def execute(self, command_list, expected_duration=0.0):
        # The output path is always the last argument in our commands
        output_path = command_list[-1]

        try:
            result = subprocess.run(
                command_list,
                capture_output=True,
                text=True,
                timeout=3600,
            )

            if result.returncode != 0:
                return (output_path, result.stderr, False,)

            return (output_path, result.stderr, True,)

        except subprocess.TimeoutExpired:
            return (output_path, "ERROR: Conversion timed out (1 hour limit)", False,)
        except FileNotFoundError:
            return (output_path, "ERROR: ffmpeg not found. Is FFmpeg installed?", False,)

    @classmethod
    def IS_CHANGED(cls, command_list, expected_duration=0.0):
        # Always re-execute — conversion is a side effect
        return float("NaN")


if __name__ == "__main__":
    node = Trope_RunFFmpeg()
    # Minimal test: just print what would run
    test_cmd = ["echo", "ffmpeg", "-y", "-i", "input.mp4", "output.mp4"]
    out_path, output, success = node.execute(test_cmd)
    print(f"Output path: {out_path}")
    print(f"Success: {success}")
    print(f"Output: {output}")
