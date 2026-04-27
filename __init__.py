"""
Trope Tools — Framerate Converter

ComfyUI custom-node pack that converts video framerates using FFmpeg.

Top-level node: Convert Framerate (drag a video onto it, pick a target fps).
The 13 granular nodes underneath let you customise each pipeline stage if
you want to build your own conversion workflow.
"""

import sys

from .nodes._ffmpeg import FFMPEG, FFPROBE, is_available
from .nodes.discover_probe_video import Trope_ProbeVideo
from .nodes.discover_detect_vfr import Trope_DetectVFR
from .nodes.discover_extract_media_info import Trope_ExtractMediaInfo
from .nodes.plan_calc_conversion import Trope_CalcConversion
from .nodes.plan_calc_audio import Trope_CalcAudio
from .nodes.plan_build_command import Trope_BuildCommand
from .nodes.plan_gen_output_path import Trope_GenOutputPath
from .nodes.implement_convert import Trope_RunFFmpeg
from .nodes.implement_remux import Trope_Remux
from .nodes.check_verify_fps import Trope_VerifyFPS
from .nodes.check_verify_sync import Trope_VerifySync
from .nodes.check_verify_integrity import Trope_VerifyIntegrity
from .nodes.knowledge_quality_metrics import Trope_QualityMetrics
from .nodes.convert_framerate import Trope_ConvertFramerate


# Surface a clear console warning if the system ffmpeg/ffprobe binaries are
# missing — otherwise users get a cryptic error on first conversion attempt.
_ffmpeg_ok, _ffprobe_ok = is_available()
if not (_ffmpeg_ok and _ffprobe_ok):
    missing = []
    if not _ffmpeg_ok:
        missing.append("ffmpeg")
    if not _ffprobe_ok:
        missing.append("ffprobe")
    print(
        f"\n[Trope Tools — Framerate Converter] WARNING: {', '.join(missing)} "
        f"not found on PATH or in common install locations.\n"
        f"  macOS:  brew install ffmpeg\n"
        f"  Linux:  apt install ffmpeg  (or distro equivalent)\n"
        f"  Windows: download from https://www.gyan.dev/ffmpeg/builds/ and "
        f"add bin/ to PATH\n"
        f"Conversion nodes will fail until this is resolved.\n",
        file=sys.stderr,
    )


NODE_CLASS_MAPPINGS = {
    # Top-level one-shot
    "trope_ConvertFramerate": Trope_ConvertFramerate,
    # Inspect
    "trope_ProbeVideo": Trope_ProbeVideo,
    "trope_DetectVFR": Trope_DetectVFR,
    "trope_ExtractMediaInfo": Trope_ExtractMediaInfo,
    # Configure
    "trope_CalcConversion": Trope_CalcConversion,
    "trope_CalcAudio": Trope_CalcAudio,
    "trope_BuildCommand": Trope_BuildCommand,
    "trope_GenOutputPath": Trope_GenOutputPath,
    # Process
    "trope_RunFFmpeg": Trope_RunFFmpeg,
    "trope_Remux": Trope_Remux,
    # Verify
    "trope_VerifyFPS": Trope_VerifyFPS,
    "trope_VerifySync": Trope_VerifySync,
    "trope_VerifyIntegrity": Trope_VerifyIntegrity,
    "trope_QualityMetrics": Trope_QualityMetrics,
}

NODE_DISPLAY_NAME_MAPPINGS = {
    "trope_ConvertFramerate": "Convert Framerate",
    "trope_ProbeVideo": "Probe Video",
    "trope_DetectVFR": "Detect VFR",
    "trope_ExtractMediaInfo": "Extract Media Info",
    "trope_CalcConversion": "Calc Conversion",
    "trope_CalcAudio": "Calc Audio",
    "trope_BuildCommand": "Build FFmpeg Command",
    "trope_GenOutputPath": "Generate Output Path",
    "trope_RunFFmpeg": "Run FFmpeg Conversion",
    "trope_Remux": "Remux Container",
    "trope_VerifyFPS": "Verify FPS",
    "trope_VerifySync": "Verify A/V Sync",
    "trope_VerifyIntegrity": "Verify Integrity",
    "trope_QualityMetrics": "Quality Metrics",
}


__all__ = ["NODE_CLASS_MAPPINGS", "NODE_DISPLAY_NAME_MAPPINGS"]
