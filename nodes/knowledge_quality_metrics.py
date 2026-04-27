"""
Trope_QualityMetrics — Measure video quality metrics.

Calculates PSNR and SSIM between an output video and a reference video.
Optionally calculates VMAF (requires FFmpeg compiled with libvmaf).
"""

import re
import subprocess

from ._ffmpeg import FFMPEG


class Trope_QualityMetrics:
    """Calculate PSNR, SSIM, and optionally VMAF quality metrics."""

    @classmethod
    def INPUT_TYPES(cls):
        return {
            "required": {
                "output_path": ("STRING", {"default": "", "multiline": False}),
                "reference_path": ("STRING", {"default": "", "multiline": False}),
            },
            "optional": {
                "include_vmaf": ("BOOLEAN", {"default": False}),
            },
        }

    RETURN_TYPES = ("STRING", "FLOAT", "FLOAT",)
    RETURN_NAMES = ("metrics_report", "psnr", "ssim",)
    FUNCTION = "execute"
    CATEGORY = "Trope Tools/Framerate Converter/Verify"

    def execute(self, output_path, reference_path, include_vmaf=False):
        psnr = self._calc_psnr(output_path, reference_path)
        ssim = self._calc_ssim(output_path, reference_path)

        lines = ["Quality Metrics Report", "=" * 30]

        if psnr is not None:
            rating = _rate_psnr(psnr)
            lines.append(f"PSNR:  {psnr:.2f} dB ({rating})")
        else:
            lines.append("PSNR:  N/A")

        if ssim is not None:
            rating = _rate_ssim(ssim)
            lines.append(f"SSIM:  {ssim:.6f} ({rating})")
        else:
            lines.append("SSIM:  N/A")

        if include_vmaf:
            vmaf = self._calc_vmaf(output_path, reference_path)
            if vmaf is not None:
                rating = _rate_vmaf(vmaf)
                lines.append(f"VMAF:  {vmaf:.2f} ({rating})")
            else:
                lines.append("VMAF:  N/A (requires libvmaf)")

        report = "\n".join(lines)
        return (report, psnr or 0.0, ssim or 0.0,)

    def _calc_psnr(self, output_path, reference_path):
        cmd = [
            FFMPEG,
            "-i", output_path,
            "-i", reference_path,
            "-lavfi", "psnr=stats_file=-",
            "-f", "null", "-",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            match = re.search(r"average:(\d+\.?\d*)", result.stderr)
            if match:
                return float(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def _calc_ssim(self, output_path, reference_path):
        cmd = [
            FFMPEG,
            "-i", output_path,
            "-i", reference_path,
            "-lavfi", "ssim=stats_file=-",
            "-f", "null", "-",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            match = re.search(r"All:(\d+\.?\d*)", result.stderr)
            if match:
                return float(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None

    def _calc_vmaf(self, output_path, reference_path):
        cmd = [
            FFMPEG,
            "-i", output_path,
            "-i", reference_path,
            "-lavfi", "libvmaf",
            "-f", "null", "-",
        ]
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
            if "Unknown filter" in result.stderr or "No such filter" in result.stderr:
                return None
            match = re.search(r"VMAF score:\s*(\d+\.?\d*)", result.stderr)
            if match:
                return float(match.group(1))
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        return None


def _rate_psnr(val):
    if val >= 40: return "excellent"
    if val >= 30: return "good"
    if val >= 20: return "acceptable"
    return "poor"


def _rate_ssim(val):
    if val >= 0.98: return "excellent"
    if val >= 0.95: return "good"
    if val >= 0.90: return "acceptable"
    return "poor"


def _rate_vmaf(val):
    if val >= 93: return "excellent"
    if val >= 80: return "good"
    if val >= 70: return "acceptable"
    return "poor"


if __name__ == "__main__":
    import sys
    node = Trope_QualityMetrics()
    if len(sys.argv) > 2:
        report, psnr, ssim = node.execute(sys.argv[1], sys.argv[2])
        print(report)
    else:
        print("Usage: python knowledge_quality_metrics.py <output_path> <reference_path>")
