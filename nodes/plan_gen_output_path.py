"""
Trope_GenOutputPath — Generate an output file path with fps-aware naming.

Creates an output filename following the pattern: stem_TARGETfps.ext
Handles collision avoidance by appending _1, _2, etc.
"""

import os


class Trope_GenOutputPath:
    """Generate an fps-aware output file path."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "input_path": ("STRING", {"default": "", "multiline": False}),
                "target_fps": ("FLOAT", {"default": 25.0, "min": 1.0, "max": 240.0, "step": 0.001}),
            },
            "optional": {
                "output_dir": ("STRING", {"default": "", "multiline": False}),
            },
        }

    RETURN_TYPES = ("STRING",)
    RETURN_NAMES = ("output_path",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Configure"

    def execute(self, input_path, target_fps, output_dir=""):
        base = os.path.basename(input_path)
        stem, ext = os.path.splitext(base)

        # Format fps for filename
        if target_fps == int(target_fps):
            fps_str = str(int(target_fps))
        else:
            fps_str = f"{target_fps:.3f}".rstrip("0").rstrip(".")

        new_name = f"{stem}_{fps_str}fps{ext}"

        if output_dir:
            out = os.path.join(output_dir, new_name)
        else:
            out = os.path.join(os.path.dirname(input_path), new_name)

        # Collision avoidance
        if os.path.exists(out):
            base_stem, base_ext = os.path.splitext(out)
            counter = 1
            while os.path.exists(out):
                out = f"{base_stem}_{counter}{base_ext}"
                counter += 1

        return (out,)


if __name__ == "__main__":
    node = Trope_GenOutputPath()
    result = node.execute("/videos/my_clip.mp4", 25.0)
    print(f"Output path: {result[0]}")

    result2 = node.execute("/videos/my_clip.mp4", 23.976, output_dir="/output")
    print(f"Output path: {result2[0]}")
