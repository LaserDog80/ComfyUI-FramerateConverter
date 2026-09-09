"""Real subprocess checks; no media, GPU, network or ComfyUI required."""
import importlib.util
from pathlib import Path
import subprocess
import sys
import time
import unittest
from unittest.mock import patch
from types import SimpleNamespace

spec = importlib.util.spec_from_file_location("ffmpeg_helpers", Path(__file__).parent / "nodes" / "_ffmpeg.py")
helper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(helper)


class ProcessTests(unittest.TestCase):
    def test_capture_and_exit_status(self):
        result = helper.run_cancellable([sys.executable, "-c", "import sys; print('json'); print('diagnostic', file=sys.stderr); sys.exit(3)"])
        self.assertEqual((result.returncode, result.stdout.strip(), result.stderr.strip()), (3, "json", "diagnostic"))

    def test_timeout_reaps_child(self):
        created = []
        original = subprocess.Popen
        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            created.append(child)
            return child
        with patch.object(helper.subprocess, "Popen", side_effect=spawn):
            with self.assertRaises(subprocess.TimeoutExpired):
                helper.run_cancellable([sys.executable, "-c", "import time; time.sleep(30)"], timeout=0.15)
        self.assertIsNotNone(created[0].poll())

    def test_cancel_reaps_child(self):
        created = []
        original = subprocess.Popen
        start = time.monotonic()
        def check():
            if time.monotonic() - start > 0.15:
                raise RuntimeError("cancelled")
        def spawn(*args, **kwargs):
            child = original(*args, **kwargs)
            created.append(child)
            return child
        with patch.object(helper, "model_management", SimpleNamespace(throw_exception_if_processing_interrupted=check)), patch.object(helper.subprocess, "Popen", side_effect=spawn):
            with self.assertRaisesRegex(RuntimeError, "cancelled"):
                helper.run_cancellable([sys.executable, "-c", "import time; time.sleep(30)"])
        self.assertIsNotNone(created[0].poll())
        self.assertLess(time.monotonic() - start, 3)

    def test_verbose_child_cannot_fill_pipe_and_diagnostics_are_bounded(self):
        result = helper.run_cancellable([sys.executable, "-c", "import sys; sys.stderr.write('x' * 2000000 + 'END')"])
        self.assertEqual(len(result.stderr), 1024 * 1024)
        self.assertTrue(result.stderr.endswith("END"))


if __name__ == "__main__":
    unittest.main()
