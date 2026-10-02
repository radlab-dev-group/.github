import importlib.util
import json
import re
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('radlab_seo_builder', ROOT / 'build.py')
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class SeoAnalyticsTests(unittest.TestCase):
    def setUp(self):
        self.site = builder.Site(builder.load_config(ROOT / 'config/site.toml'), fast=True)
        self.site.load()

    def render(self, method, *args):
        with patch.object(self.site, 'write') as write:
            method(*args)
        return [call.args[1] for call in write.call_args_list]

    def test_analytics_on_every_page_type_and_optional(self):
        texts = []
        for lang in self.site.cfg.langs:
            texts += self.render(self.site.build_home, lang)
            texts += self.render(self.site.build_blog_index, lang)
            texts += self.render(self.site.build_product, self.site.products[lang][0])
            texts += self.render(self.site.build_post, self.site.posts[lang][0])
        texts.append(self.site.env.get_template('404.html').render(**self.site.context('pl')))
        for text in texts:
            self.assertIn('gtag/js?id=G-6NPWS2TQEC', text)
            self.assertEqual(text.count("gtag('config',"), 1)
        self.site.cfg.site['ga_code'] = ''
        self.assertNotIn('googletagmanager.com', self.render(self.site.build_home, 'pl')[0])

    def test_localized_seo_and_structured_data(self):
        for lang in self.site.cfg.langs:
            text = self.render(self.site.build_home, lang)[0]
            seo = self.site.cfg.raw['seo'][lang]
            self.assertIn(seo['title'], text)
            self.assertIn(seo['description'], text)
            self.assertIn('name="keywords"', text)
            data = json.loads(re.search(r'<script type="application/ld\+json">(.*?)</script>', text, re.S)[1])
            self.assertEqual(data['@type'], 'WebPage')
            self.assertEqual(data['inLanguage'], lang)
            self.assertEqual(data['url'], self.site.cfg.canonical(lang, ''))

    def test_preferences_only_redirect_homes_and_support_base_path(self):
        self.site.cfg.site['base_path'] = '/preview'
        text = self.render(self.site.build_home, 'pl')[0]
        self.assertIn('data-language-auto="true"', text)
        self.assertIn('data-language-en="/preview/en/"', text)
        self.assertIn('src="/preview/assets/js/preferences.js"', text)
        post = self.render(self.site.build_post, self.site.posts['pl'][0])[0]
        self.assertIn('data-language-auto="false"', post)


if __name__ == '__main__':
    unittest.main()