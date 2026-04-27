"""
Trope_CalcConversion — Calculate conversion parameters.

Given source and target framerates plus a conversion method, computes
speed factor, PTS factor, duration change, and expected output metrics.
"""

import math


METHODS = ["speed_change", "frame_drop", "frame_blend", "minterpolate"]


class Trope_CalcConversion:
    """Calculate framerate conversion parameters."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "source_fps": ("FLOAT", {"default": 24.0, "min": 1.0, "max": 240.0, "step": 0.001}),
                "target_fps": ("FLOAT", {"default": 25.0, "min": 1.0, "max": 240.0, "step": 0.001}),
                "method": (METHODS, {"default": "speed_change"}),
            },
            "optional": {
                "input_duration": ("FLOAT", {"default": 0.0, "min": 0.0, "max": 86400.0, "step": 0.001}),
                "input_frame_count": ("INT", {"default": 0, "min": 0, "max": 99999999}),
            },
        }

    RETURN_TYPES = ("CONV_PARAMS", "STRING",)
    RETURN_NAMES = ("conversion_params", "summary",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Configure"

    def execute(self, source_fps, target_fps, method,
                input_duration=0.0, input_frame_count=0):
        speed_factor = target_fps / source_fps
        pts_factor = source_fps / target_fps
        is_speed_change = method == "speed_change"

        # Duration change percentage (only meaningful for speed_change)
        duration_change_pct = (1.0 / speed_factor - 1.0) * 100.0 if is_speed_change else 0.0

        # Expected output duration
        if is_speed_change and input_duration > 0:
            output_duration = input_duration * pts_factor
        else:
            output_duration = input_duration

        # Expected output frame count
        if is_speed_change:
            output_frame_count = input_frame_count
        elif input_duration > 0:
            output_frame_count = int(input_duration * target_fps)
        else:
            output_frame_count = 0

        params = {
            "method": method,
            "source_fps": source_fps,
            "target_fps": target_fps,
            "speed_factor": speed_factor,
            "pts_factor": pts_factor,
            "duration_change_pct": duration_change_pct,
            "is_speed_change": is_speed_change,
            "output_duration": output_duration,
            "output_frame_count": output_frame_count,
        }

        lines = [
            f"Method: {method}",
            f"Source FPS: {source_fps:.3f} -> Target FPS: {target_fps:.3f}",
            f"Speed factor: {speed_factor:.6f}x",
            f"PTS factor: {pts_factor:.6f}",
        ]
        if is_speed_change:
            lines.append(f"Duration change: {duration_change_pct:+.2f}%")
        if output_duration > 0:
            lines.append(f"Expected output duration: {output_duration:.2f}s")
        if output_frame_count > 0:
            lines.append(f"Expected output frames: {output_frame_count}")

        return (params, "\n".join(lines),)


if __name__ == "__main__":
    node = Trope_CalcConversion()
    params, summary = node.execute(24.0, 25.0, "speed_change",
                                   input_duration=120.0, input_frame_count=2880)
    print(summary)
