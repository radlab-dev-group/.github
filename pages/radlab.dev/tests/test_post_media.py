import importlib.util
import re
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("radlab_media_builder", ROOT / "build.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class PostMediaTests(unittest.TestCase):
    def test_fast_build_is_complete_without_network_or_previous_output(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            site = builder.Site(builder.load_config(ROOT / "site.toml"), fast=True)
            site.dist = Path(directory)
            site.pipeline.dist = site.dist
            site.pipeline.out_dir = site.dist / "assets/img"
            with patch("socket.create_connection", side_effect=AssertionError("network access")):
                site.build()
            self.assertEqual(site.pipeline.missing, [])
            self.assertEqual(builder.check_links(site.dist, site.cfg), [])
            self.assertEqual(builder.check_no_media_token(site.dist), [])

    def test_repository_posts_have_self_contained_media(self):
        cfg = builder.load_config(ROOT / "site.toml")
        self.assertFalse((ROOT / "data/media_map.json").exists())
        self.assertFalse((ROOT / "media").exists())
        for lang in cfg.langs:
            directory = ROOT / lang / "blog/posts"
            self.assertFalse(list(directory.glob("*.md")))
            sources = list(directory.glob("*/index.md"))
            self.assertTrue(sources)
            self.assertEqual(len(builder.load_posts(cfg, lang, include_drafts=True)), len(sources))
            for source in sources:
                text = source.read_text(encoding="utf-8")
                with self.subTest(source=source):
                    self.assertNotIn("@media/", text)
                    self.assertNotRegex(text, r"https?://\S+\.(?:webm|mp4|avif|png|jpe?g)")
                    for reference in re.findall(r"media/[^\s)\"<>]+", text):
                        self.assertTrue((source.parent / reference).is_file(), reference)

    def test_nested_post_loads_local_image_and_video_without_manifest(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            root = Path(directory)
            post_dir = root / "pl/blog/posts/example"
            media = post_dir / "media"
            media.mkdir(parents=True)
            Image.new("RGB", (32, 16)).save(media / "image.png")
            (media / "demo.webm").write_bytes(b"local video")
            (post_dir / "index.md").write_text(
                '---\ntitle: Example\ndate: 2025-10-13\nimage: media/image.png\n---\n'
                '![](media/image.png)\n\n{{< video media/demo.webm >}}', encoding="utf-8")
            cfg = builder.load_config(ROOT / "site.toml")
            cfg.raw["site"]["base_path"] = "/preview"
            with patch.object(builder, "ROOT", root):
                posts = builder.load_posts(cfg, "pl", include_drafts=True)
                self.assertEqual(len(posts), 1)
                post = posts[0]
                self.assertEqual(post.slug, "example")
                self.assertEqual(post.path, "2025-10-13/example")
                for fast in (True, False):
                    with self.subTest(fast=fast):
                        site = builder.Site(cfg, fast=fast)
                        text = site.render_post_html(post)
                        image = str(site.image(post.image))
                        self.assertNotIn("{{<", text)
                        self.assertIn('/preview/pl/blog/posts/example/media/demo.webm', text)
                        self.assertTrue((site.dist / "pl/blog/posts/example/media/demo.webm").exists())
                        self.assertIn("image.png" if fast else "<picture>", image)
                        self.assertEqual(site.pipeline.missing, [])

    def test_missing_media_fails_check(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            site = builder.Site(builder.load_config(ROOT / "site.toml"), fast=True)
            site.dist = Path(directory)
            site.pipeline.dist = site.dist
            site.posts = {}
            with patch.object(builder, "Site", return_value=site), patch.object(site, "build"):
                site.pipeline.missing.append("missing local media")
                self.assertEqual(builder.main(["--check", "--fast"]), 1)


if __name__ == "__main__":
    unittest.main()