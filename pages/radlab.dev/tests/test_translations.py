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
        self.site = builder.Site(builder.load_config(ROOT / "config/site.toml"), fast=True)
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

    def test_translated_posts_resolve_their_own_local_images(self):
        for lang in self.site.cfg.langs:
            for post in self.site.posts[lang] + self.site.drafts[lang]:
                if not post.image:
                    continue
                with self.subTest(lang=lang, slug=post.slug):
                    source = self.site.pipeline.master_for(post.image)
                    self.assertIsNotNone(source)
                    self.assertEqual(source.parent, post.source_dir / "media")


if __name__ == "__main__":
    unittest.main()