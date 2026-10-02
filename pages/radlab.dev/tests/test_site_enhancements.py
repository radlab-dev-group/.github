import importlib.util
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("radlab_enhancement_builder", ROOT / "build.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class SiteEnhancementTests(unittest.TestCase):
    def setUp(self):
        self.site = builder.Site(builder.load_config(ROOT / "site.toml"), fast=True)
        self.site.load()

    def home(self, lang):
        with patch.object(self.site, "write") as write:
            self.site.build_home(lang)
        return write.call_args.args[1]

    def test_feed_discovery_and_visible_links_use_file_urls(self):
        for lang in self.site.cfg.langs:
            with self.subTest(lang=lang):
                text = self.home(lang)
                url = self.site.cfg.prefix(lang) + "/feed.xml"
                self.assertIn(f'type="application/atom+xml" title="', text)
                self.assertGreaterEqual(text.count(f'href="{url}"'), 2)
                self.assertNotIn('feed.xml/"', text)

    def test_feed_self_link_matches_generated_file(self):
        with patch.object(self.site, "write") as write:
            self.site.build_feeds()
        for call in write.call_args_list:
            path, text = call.args
            self.assertTrue(path.endswith("feed.xml"))
            self.assertIn(f'href="{self.site.cfg.url}/{path}"', text)
            self.assertNotIn('feed.xml/"', text)

    def test_feed_links_under_a_preview_subpath(self):
        self.site.cfg.raw["site"]["base_path"] = "/preview"
        self.test_feed_discovery_and_visible_links_use_file_urls()
        self.test_feed_self_link_matches_generated_file()

    def test_technology_tags_link_to_localized_products(self):
        for lang in self.site.cfg.langs:
            text = self.home(lang)
            for product in ("playground", "llm-router", "radar", "pii-masker"):
                url = self.site.cfg.href(lang, "products/" + product)
                self.assertRegex(text, rf'<a class="tag-tech" href="{re.escape(url)}">')

    def test_copy_labels_are_localized(self):
        for lang in self.site.cfg.langs:
            text = self.home(lang)
            for name in ("copy_code", "code_copied", "copy_failed"):
                self.assertTrue(self.site.ui[lang].get(name), name)
            self.assertIn('data-copy-code="' + self.site.ui[lang]["copy_code"] + '"', text)


if __name__ == "__main__":
    unittest.main()