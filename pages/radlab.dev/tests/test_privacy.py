import importlib.util
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("radlab_privacy_builder", ROOT / "build.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class PrivacyTests(unittest.TestCase):
    def setUp(self):
        self.site = builder.Site(builder.load_config(ROOT / "config/site.toml"), fast=True)
        self.site.load()

    def test_footer_and_consent_link_to_local_policy(self):
        for base in ("", "/preview"):
            self.site.cfg.raw["site"]["base_path"] = base
            for lang in self.site.cfg.langs:
                with self.subTest(base=base, lang=lang), patch.object(self.site, "write") as write:
                    self.site.build_home(lang)
                    text = write.call_args.args[1]
                    url = self.site.cfg.href(lang, "privacy")
                    self.assertGreaterEqual(text.count(f'href="{url}"'), 2)
                    self.assertNotIn('href="https://policies.google.com/privacy"', text)

    def test_policy_pages_have_localized_metadata_and_language_switch(self):
        for base in ("", "/preview"):
            self.site.cfg.raw["site"]["base_path"] = base
            for lang in self.site.cfg.langs:
                with self.subTest(base=base, lang=lang), patch.object(self.site, "write") as write:
                    self.site.build_pages(lang)
                    path, text = write.call_args.args
                    other = "en" if lang == "pl" else "pl"
                    prefix = "preview/" if base else ""
                    self.assertEqual(path, prefix + ("en/" if lang == "en" else "") + "privacy/")
                    self.assertIn(f'<html lang="{lang}"', text)
                    self.assertIn(f'href="{self.site.cfg.canonical(lang, "privacy")}"', text)
                    self.assertIn(f'href="{self.site.cfg.href(other, "privacy")}"', text)
                    self.assertIn('hreflang="en-GB"', text)
                    self.assertIn('data-language-auto="false"', text)
                    self.assertIn("Google Analytics", text)
                    for key in ("radlab-analytics-consent", "radlab-language", "radlab-theme", "_ga"):
                        self.assertIn(key, text)
                    self.assertIn("hello@radlab.dev", text)
                    self.assertIn("180", text)
                    self.assertIn(self.site.ui[lang]["consent_settings"], text)
                    self.assertIn("reklam" if lang == "pl" else "advertising", text)

    def test_policies_are_in_sitemap_even_when_analytics_is_disabled(self):
        self.site.cfg.raw["site"]["ga_code"] = ""
        with patch.object(self.site, "write") as write:
            self.site.build_sitemap()
        sitemap = write.call_args.args[1]
        for lang in self.site.cfg.langs:
            self.assertIn(f'<loc>{self.site.cfg.canonical(lang, "privacy")}</loc>', sitemap)
            with patch.object(self.site, "write") as write:
                self.site.build_home(lang)
            text = write.call_args.args[1]
            self.assertIn(f'href="{self.site.cfg.href(lang, "privacy")}"', text)
            self.assertNotIn('id="analytics-consent"', text)


if __name__ == "__main__":
    unittest.main()