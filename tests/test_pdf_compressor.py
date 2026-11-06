"""
Automated Unit Tests for PDF Compression Engine
Validates adaptive target size reduction, presets, CLI execution, and edge cases.
"""

import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from PIL import Image, ImageDraw

from pdf_compressor.compressor import (
    compress_to_target_size,
    compress_with_preset,
    format_size,
    get_file_size_kb,
    check_ghostscript,
)


def create_synthetic_pdf(output_path: str, num_pages: int = 4, width: int = 1400, height: int = 1000):
    """Generate a realistic image-heavy multi-page PDF using Pillow."""
    images = []
    for i in range(num_pages):
        # Create patterned image with varied colors to prevent trivial run-length compression
        img = Image.new("RGB", (width, height), color=(i * 50 % 255, 100, 180))
        draw = ImageDraw.Draw(img)

        # Draw diagonal geometric lines & boxes
        for step in range(0, min(width, height), 25):
            draw.rectangle(
                [step, step, step + 20, step + 20],
                fill=((step * 3) % 255, (step * 7) % 255, (step * 11) % 255),
            )
            draw.line([(0, step), (width, height - step)], fill=(255, 255, 255), width=3)

        images.append(img)

    # Save as high-res multi-page PDF
    images[0].save(
        output_path,
        "PDF",
        resolution=300.0,
        save_all=True,
        append_images=images[1:],
    )


class TestPDFCompressor(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.test_dir = tempfile.mkdtemp(prefix="test_pdf_compressor_")
        cls.sample_pdf = os.path.join(cls.test_dir, "sample_heavy.pdf")
        # Generate ~1MB - 2MB synthetic PDF
        create_synthetic_pdf(cls.sample_pdf, num_pages=5, width=1600, height=1200)
        cls.sample_size_bytes = os.path.getsize(cls.sample_pdf)
        cls.sample_size_kb = cls.sample_size_bytes / 1024.0

    @classmethod
    def tearDownClass(cls):
        shutil.rmtree(cls.test_dir, ignore_errors=True)

    def test_ghostscript_present(self):
        """Ensure Ghostscript binary is found and usable."""
        self.assertTrue(check_ghostscript(), "Ghostscript binary must be installed on system")

    def test_format_size_utility(self):
        """Check human-readable size formatting."""
        self.assertEqual(format_size(500), "500 B")
        self.assertEqual(format_size(1024), "1.0 KB")
        self.assertEqual(format_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_size(5 * 1024 * 1024), "5.00 MB")

    def test_passthrough_when_already_under_target(self):
        """If target is larger than original file, passthrough without re-encoding."""
        out_pdf = os.path.join(self.test_dir, "out_passthrough.pdf")
        huge_target_kb = self.sample_size_kb + 1000.0

        res = compress_to_target_size(self.sample_pdf, out_pdf, target_size_kb=huge_target_kb)

        self.assertTrue(res.success)
        self.assertTrue(res.target_met)
        self.assertEqual(res.method, "passthrough")
        self.assertEqual(res.compressed_size_bytes, self.sample_size_bytes)
        self.assertTrue(os.path.exists(out_pdf))

    def test_compress_with_presets(self):
        """Validate preset compression (ebook, screen)."""
        out_screen = os.path.join(self.test_dir, "out_screen.pdf")
        success, size = compress_with_preset(self.sample_pdf, out_screen, preset_name="screen")

        self.assertTrue(success)
        self.assertTrue(os.path.exists(out_screen))
        self.assertLess(size, self.sample_size_bytes, "Screen preset should reduce size")

    def test_adaptive_target_size_compression(self):
        """Compress to exact target size (e.g. 60% of original)."""
        out_target = os.path.join(self.test_dir, "out_target.pdf")
        target_kb = round(self.sample_size_kb * 0.55, 1)

        res = compress_to_target_size(self.sample_pdf, out_target, target_size_kb=target_kb)

        self.assertTrue(res.success)
        self.assertTrue(os.path.exists(out_target))
        self.assertLess(res.compressed_size_bytes, self.sample_size_bytes)
        self.assertGreater(res.reduction_percent, 10.0)

        # Output must be a valid PDF (starts with %PDF)
        with open(out_target, "rb") as f:
            header = f.read(5)
            self.assertEqual(header, b"%PDF-")

    def test_cli_invocation_json(self):
        """Verify CLI tool runs cleanly and emits valid JSON."""
        out_cli = os.path.join(self.test_dir, "out_cli.pdf")
        target_kb = str(int(self.sample_size_kb * 0.6))

        cmd = [
            sys.executable,
            "-m",
            "pdf_compressor.cli",
            self.sample_pdf,
            "-o",
            out_cli,
            "--target-kb",
            target_kb,
            "--json",
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        self.assertEqual(proc.returncode, 0, f"CLI error: {proc.stderr}")
        self.assertIn('"success": true', proc.stdout)
        self.assertTrue(os.path.exists(out_cli))

    def test_cli_target_mb_flag(self):
        """Verify CLI --target-mb flag functions properly."""
        out_cli_mb = os.path.join(self.test_dir, "out_cli_mb.pdf")
        cmd = [
            sys.executable,
            "-m",
            "pdf_compressor.cli",
            self.sample_pdf,
            "-o",
            out_cli_mb,
            "--target-mb",
            "0.5",
            "--json",
        ]
        proc = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        self.assertEqual(proc.returncode, 0)
        self.assertTrue(os.path.exists(out_cli_mb))

    def test_non_existent_file_handling(self):
        """Engine should fail gracefully on non-existent files."""
        res = compress_to_target_size("/tmp/definitely_not_a_real_pdf_12345.pdf", "/tmp/out.pdf", target_size_kb=100)
        self.assertFalse(res.success)
        self.assertIn("File not found", res.message)


if __name__ == "__main__":
    unittest.main()
