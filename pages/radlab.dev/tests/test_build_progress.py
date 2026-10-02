import contextlib
import importlib.util
import io
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("radlab_progress_builder", ROOT / "build.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class BuildProgressTests(unittest.TestCase):
    def build_output(self, verbose=False):
        output = io.StringIO()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory, contextlib.redirect_stdout(output):
            site = builder.Site(builder.load_config(ROOT / "config/site.toml"), fast=True, verbose=verbose)
            site.dist = Path(directory)
            site.pipeline.dist = site.dist
            site.build()
            self.assertTrue((site.dist / "index.html").exists())
            self.assertTrue((site.dist / "sitemap.xml").exists())
        return output.getvalue()

    def test_default_output_is_concise(self):
        output = self.build_output()
        lines = output.splitlines()
        self.assertEqual(len(lines), 5)
        for step, line in enumerate(lines, start=1):
            self.assertTrue(line.startswith(f"[{step}/5] "))
        self.assertIn("image generation disabled", output)
        self.assertNotIn("Wrote:", output)
        self.assertNotIn("Rendering post:", output)

    def test_verbose_output_includes_content_and_files(self):
        output = self.build_output(verbose=True)
        self.assertIn("[1/5] Loading", output)
        self.assertIn("Rendering post: pl/", output)
        self.assertIn("Rendering product:", output)
        self.assertIn("Copied: assets/", output)
        self.assertIn("Wrote: index.html", output)
        self.assertIn("Wrote: robots.txt", output)
        self.assertIn("Wrote: sitemap.xml", output)

    def test_image_progress_reports_generation_reuse_and_failures(self):
        output = io.StringIO()
        with tempfile.TemporaryDirectory(dir=ROOT) as directory, contextlib.redirect_stdout(output):
            root = Path(directory)
            source = root / "example.png"
            Image.new("RGB", (32, 16)).save(source)
            cfg = builder.load_config(ROOT / "config/site.toml")
            progress = builder.BuildProgress(verbose=True)
            pipeline = builder.ImagePipeline(cfg, root / "dist", progress=progress)
            self.assertIsNotNone(pipeline.variants(source))
            first_output = output.getvalue()
            self.assertIn("Processing image:", first_output)
            self.assertIn("Generating WebP:", first_output)
            pipeline.variants(source)
            self.assertEqual(output.getvalue(), first_output)
            cached_pipeline = builder.ImagePipeline(cfg, root / "dist", progress=progress)
            self.assertIsNotNone(cached_pipeline.variants(source))
            self.assertIn("Reusing WebP:", output.getvalue())
            broken = root / "broken.png"
            broken.write_text("not an image", encoding="utf-8")
            self.assertIsNone(pipeline.variants(broken))
            self.assertIn("Image failed:", output.getvalue())
            self.assertEqual(len(pipeline.missing), 1)

    def test_messages_are_flushed_immediately(self):
        progress = builder.BuildProgress(verbose=True)
        with patch("builtins.print") as output:
            progress.stage(1, "Loading content...")
            progress.detail("Processing image: example.png")
        self.assertEqual(output.call_count, 2)
        for call in output.call_args_list:
            self.assertTrue(call.kwargs["flush"])

    def test_cli_accepts_verbose_and_short_alias(self):
        for flag in ("--verbose", "-v"):
            with self.subTest(flag=flag), patch.object(builder, "Site") as site_class:
                site_class.return_value.posts = {}
                site_class.return_value.pipeline.cache = {}
                site_class.return_value.pipeline.missing = []
                with contextlib.redirect_stdout(io.StringIO()):
                    self.assertEqual(builder.main(["--fast", flag]), 0)
                self.assertTrue(site_class.call_args.kwargs["verbose"])
                site_class.return_value.build.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()