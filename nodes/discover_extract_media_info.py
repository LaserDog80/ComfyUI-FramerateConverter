"""
Trope_ExtractMediaInfo — Pull scalar fields out of a MEDIA_INFO dict.

Lets ProbeVideo's output flow as scalars into CalcConversion / CalcAudio /
GenOutputPath without retyping source_fps, duration, etc.
"""


class Trope_ExtractMediaInfo:
    """Unpack a MEDIA_INFO dict into typed scalar outputs."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "media_info": ("MEDIA_INFO",),
            },
        }

    RETURN_TYPES = (
        "FLOAT", "FLOAT", "INT", "INT", "INT",
        "BOOLEAN", "INT", "STRING",
    )
    RETURN_NAMES = (
        "source_fps", "duration", "frame_count", "width", "height",
        "has_audio", "audio_sample_rate", "video_path",
    )
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Inspect"

    def execute(self, media_info):
        return (
            float(media_info.get("framerate", 0.0)),
            float(media_info.get("duration", 0.0)),
            int(media_info.get("frame_count", 0)),
            int(media_info.get("width", 0)),
            int(media_info.get("height", 0)),
            bool(media_info.get("has_audio", False)),
            int(media_info.get("audio_sample_rate", 0)),
            str(media_info.get("path", "")),
        )


if __name__ == "__main__":
    sample = {
        "path": "/videos/clip.mp4", "framerate": 23.976, "duration": 120.0,
        "frame_count": 2877, "width": 1920, "height": 1080,
        "has_audio": True, "audio_sample_rate": 48000,
    }
    out = Trope_ExtractMediaInfo().execute(sample)
    print(out)
