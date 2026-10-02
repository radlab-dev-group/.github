import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("radlab_translation_builder", ROOT / "build.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class TranslationTests(unittest.TestCase):
    def setUp(self):
        self.site = builder.Site(builder.load_config(ROOT / "site.toml"), fast=True)
        self.site.load()

    def test_published_english_posts_link_to_originals_in_both_directions(self):
        self.assertTrue(self.site.posts["en"])
        for post in self.site.posts["en"]:
            with self.subTest(slug=post.slug):
                original = self.site.counterpart(post)
                self.assertIsNotNone(original)
                self.assertIs(self.site.counterpart(original), post)
                for article, mate in ((post, original), (original, post)):
                    with patch.object(self.site, "write") as write:
                        self.site.build_post(article)
                    text = write.call_args.args[1]
                    self.assertNotIn(self.site.ui[article.lang]["translation_missing"], text)
                    self.assertIn(f'href="{self.site.cfg.href(mate.lang, mate.path)}"', text)
                    self.assertIn(f'hreflang="{self.site.cfg.site["hreflang"][mate.lang]}"', text)
                    self.assertIn(
                        f'hreflang="x-default" href="{self.site.cfg.canonical(original.lang, original.path)}"',
                        text,
                    )

    def test_untranslated_drafts_keep_the_missing_translation_notice(self):
        self.assertTrue(self.site.drafts["en"])
        for draft in self.site.drafts["en"]:
            with self.subTest(slug=draft.slug):
                original = self.site.originals_of(draft)
                self.assertIsNotNone(original)
                self.assertIsNone(self.site.counterpart(original))
                with patch.object(self.site, "write") as write:
                    self.site.build_post(original)
                self.assertIn(self.site.ui["pl"]["translation_missing"], write.call_args.args[1])

    def test_image_manifest_is_loaded_from_migration_data(self):
        self.assertTrue(self.site.pipeline.manifest)
        token = "@media/czy-mozna-w-prosty-sposob-wprowadzic-baze-wiedzy-dla-genai/01-2025-12-26_22-20-09_5743.avif"
        self.assertEqual(self.site.pipeline.master_for(token), ROOT / token.replace("@media", "media").replace(".avif", ".jpeg"))


if __name__ == "__main__":
    unittest.main()