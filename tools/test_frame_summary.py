"""Synthetic tests for tools/frame-summary.py (no game data: every line here is made up).

Run: python -I -B -m unittest discover -s tools -p "test_*.py"     (from the kit's folder)
Copyright (C) 2026 VIBellic contributors. GPL-3.0-or-later: see LICENSE.
"""
import contextlib
import importlib.util
import io
import json
import os
import pathlib
import tempfile
import unittest

HERE = pathlib.Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("frame_summary", HERE / "frame-summary.py")
fs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fs)


def frame_line(t, fps, ms, draws, gpu=0.0, dropped=0, prep=30.0, ansi=False):
    head = f"2026-11-27T12:00:{t:02d}.000000Z  INFO victory_gpu::host: "
    if ansi:
        head = f"\x1b[2m2026-11-27T12:00:{t:02d}.000000Z\x1b[0m \x1b[32m INFO\x1b[0m victory_gpu::host: "
    return (head + f"{fps} fps, {ms} ms/frame ({prep} preparing: copies 10.0 ms 40.0 MB, textures 2.0 ms 20.0 MB; "
            f"{gpu} on the GPU; 5.0 copying back 1.0 MB), {draws} draws/frame, dropped {dropped} without a host "
            f"pipeline (0 being made) and 0 indirect")


SECRET = "B:\\Private\\Folder"
SHADER_LIKE = "hash=0123456789abcdef address=0xdeadbeef00"


class Summary(unittest.TestCase):
    def test_empty_log(self):
        s = fs.summarise_lines([])
        self.assertEqual(s["frame_lines"], 0)
        self.assertEqual(s["world_windows"], 0)
        self.assertNotIn("window_ms_median", s)

    def test_menus_are_not_world(self):
        s = fs.summarise_lines([frame_line(0, 30.0, 33.3, 12), frame_line(5, 30.0, 33.3, 12)])
        self.assertEqual(s["world_windows"], 0)
        self.assertAlmostEqual(s["menu_windows_median_ms"], 33.3)

    def test_world_statistics_and_throughput(self):
        lines = [frame_line(0, 30.0, 33.3, 12),       # menu, gives the first timestamp
                 frame_line(5, 20.0, 50.0, 3000, dropped=300),
                 frame_line(10, 25.0, 40.0, 4000, dropped=400),
                 frame_line(20, 10.0, 100.0, 5000, dropped=500)]   # a 10-second window
        s = fs.summarise_lines(lines)
        self.assertEqual(s["world_windows"], 3)
        self.assertAlmostEqual(s["window_ms_median"], 50.0)
        # (20*5 + 25*5 + 10*10) / 20 s = 16.25: time-weighted, unlike the plain mean 18.33
        self.assertAlmostEqual(s["throughput_fps"], 16.25)
        self.assertAlmostEqual(s["mean_of_window_fps"], 55.0 / 3)
        self.assertAlmostEqual(s["throughput_seconds"], 20.0)
        self.assertAlmostEqual(s["dropped_share"], 0.1)
        self.assertEqual(s["windows_at_30_cap"], 0)

    def test_no_timestamps_means_unknown_throughput(self):
        bare = [frame_line(5, 20.0, 50.0, 3000).split("host: ", 1)[1]] * 3
        s = fs.summarise_lines(bare)
        self.assertEqual(s["world_windows"], 3)
        self.assertIsNone(s["throughput_fps"])
        self.assertIn("unknown", "\n".join(fs.text_report("x", s)))

    def test_gpu_zero_everywhere_is_not_applicable(self):
        s = fs.summarise_lines([frame_line(0, 20.0, 50.0, 3000, gpu=0.0), frame_line(5, 20.0, 50.0, 3000, gpu=0.0)])
        self.assertIsNone(s["gpu_ms"])
        self.assertIn("N/A", "\n".join(fs.text_report("x", s)))

    def test_gpu_measured_is_reported(self):
        s = fs.summarise_lines([frame_line(0, 20.0, 50.0, 3000, gpu=10.0), frame_line(5, 20.0, 50.0, 3000, gpu=20.0)])
        self.assertAlmostEqual(s["gpu_ms"], 15.0)

    def test_ansi_colour_codes_are_stripped(self):
        s = fs.summarise_lines([frame_line(0, 20.0, 50.0, 3000, ansi=True), frame_line(5, 20.0, 50.0, 3000, ansi=True)])
        self.assertEqual(s["world_windows"], 2)
        self.assertAlmostEqual(s["throughput_seconds"], 5.0)

    def test_malformed_lines_are_counted_never_shown(self):
        bad = "2026-11-27T12:00:00Z INFO victory_gpu::host: 20.0 fps, 50.0 ms/frame (garbled " + SHADER_LIKE + " " + SECRET
        s = fs.summarise_lines([bad, frame_line(5, 20.0, 50.0, 3000)])
        self.assertEqual(s["malformed_frame_lines"], 1)
        text = "\n".join(fs.text_report("run", s)) + json.dumps(s)
        self.assertNotIn("garbled", text)
        self.assertNotIn(SECRET, text)
        self.assertNotIn("deadbeef", text)
        self.assertNotIn("0123456789abcdef", text)

    def test_frame_generation_counts_and_unknown_presented_rate(self):
        lines = [frame_line(0, 20.0, 50.0, 3000),
                 "INFO victory_gpu::streamline: DLSS Frame Generation: 26 presents with it on, 0 off, 26 frames shown by it (status 0x0)",
                 "INFO victory_gpu::streamline: DLSS Frame Generation: 20 presents with it on, 4 off, 20 frames shown by it (status 0x0)"]
        s = fs.summarise_lines(lines)
        self.assertEqual(s["frame_generation"], {"status_lines": 2, "presents_on": 46, "presents_off": 4, "generated": 46})
        self.assertIsNone(s["presented_fps"])

    def test_cap_windows_counted(self):
        s = fs.summarise_lines([frame_line(0, 30.0, 33.3, 3000), frame_line(5, 25.0, 40.0, 3000)])
        self.assertEqual(s["windows_at_30_cap"], 1)


class CommandLine(unittest.TestCase):
    def run_main(self, args):
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            code = fs.main(args)
        return code, buf.getvalue()

    def test_missing_file_is_an_error_without_its_path(self):
        missing = os.path.join(tempfile.gettempdir(), "vibellic-no-such-dir", "secret-name.log")
        code, out = self.run_main([missing])
        self.assertEqual(code, 1)
        self.assertIn("not readable", out)
        self.assertNotIn("vibellic-no-such-dir", out)

    def test_old_invocation_and_json_mode_hide_the_path(self):
        with tempfile.TemporaryDirectory(prefix="private-") as d:
            p = os.path.join(d, "run-1.log")
            with open(p, "w", encoding="utf-8") as f:
                f.write("\n".join([frame_line(0, 30.0, 33.3, 12), frame_line(5, 20.0, 50.0, 3000)]))
            code, out = self.run_main([p])
            self.assertEqual(code, 0)
            self.assertIn("== run-1.log", out)
            self.assertNotIn(d, out)
            code, out = self.run_main(["--json", "--label", "A1", p])
            data = json.loads(out)
            self.assertEqual(data[0]["label"], "A1")
            self.assertEqual(data[0]["world_windows"], 1)
            self.assertNotIn(d, out)

    def test_no_arguments_prints_usage(self):
        code, out = self.run_main([])
        self.assertEqual(code, 2)
        self.assertIn("Usage", out)


if __name__ == "__main__":
    unittest.main()
