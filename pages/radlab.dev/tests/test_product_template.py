import unittest
from html.parser import HTMLParser
from pathlib import Path
from types import SimpleNamespace

from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader, select_autoescape


ROOT = Path(__file__).resolve().parents[1]


class Elements(HTMLParser):
    def __init__(self, text):
        super().__init__()
        self.elements = []
        self.feed(text)

    def handle_starttag(self, tag, attrs):
        self.elements.append((tag, dict(attrs)))

    def with_class(self, name):
        return [attrs for _, attrs in self.elements if name in attrs.get("class", "").split()]


class ProductTemplateTests(unittest.TestCase):
    def render(self, **overrides):
        product = dict(
            title="PII Masker", subtitle="Privacy protection", icon="shield",
            meta={"status": "Open Source", "version": "v1.1"}, tags=["NER", "FastMasker"],
            actions=[
                {"label": "Try online", "href": "https://example.org/demo", "style": "primary"},
                {"label": "Repository", "href": "https://example.org/code", "style": "quiet"},
                {"label": "Documentation", "href": "/docs/", "style": "quiet"},
            ],
        )
        product.update(overrides)
        env = Environment(
            loader=ChoiceLoader([
                DictLoader({"base.html": "{% block main %}{% endblock %}"}),
                FileSystemLoader(ROOT / "templates"),
            ]),
            autoescape=select_autoescape(["html"]),
        )
        return env.get_template("product.html").render(
            product=SimpleNamespace(**product), counterpart=None,
            ui={"all_products": "Our solutions", "tags": "Tags", "translation_missing": "Not translated"},
            href=lambda path: "/" + path, content="<h2>Architecture</h2>",
        )

    def test_action_hierarchy_and_external_link_safety(self):
        text = self.render()
        elements = Elements(text)
        self.assertEqual(len(elements.with_class("btn-primary")), 1)
        self.assertEqual(len(elements.with_class("product-resource-link")), 2)
        self.assertFalse(elements.with_class("btn-quiet"))
        for tag, attrs in elements.elements:
            if tag == "a" and attrs.get("href", "").startswith("https://"):
                self.assertEqual(attrs["target"], "_blank")
                self.assertIn("noopener", attrs["rel"])
        self.assertLess(text.index("product-actions"), text.index("product-tags"))
        self.assertNotIn("product-cta", text)
        self.assertNotIn("badge-accent", text)

    def test_optional_header_fields(self):
        text = self.render(meta={}, tags=[], actions=[], icon="", subtitle="")
        elements = Elements(text)
        for name in ("product-meta", "product-tags", "product-actions", "product-icon-badge", "lede"):
            self.assertFalse(elements.with_class(name), name)
        self.assertIn("<h1>PII Masker</h1>", text)
        self.assertIn("<h2>Architecture</h2>", text)

    def test_metadata_is_escaped(self):
        text = self.render(title="<script>alert(1)</script>", tags=["<b>NER</b>"])
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;script&gt;", text)
        self.assertIn("&lt;b&gt;NER&lt;/b&gt;", text)


if __name__ == "__main__":
    unittest.main()