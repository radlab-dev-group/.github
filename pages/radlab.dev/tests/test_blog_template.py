import datetime as dt
import importlib.util
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

from jinja2 import ChoiceLoader, DictLoader, Environment, FileSystemLoader, select_autoescape

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("radlab_site_builder", ROOT / "build.py")
builder = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = builder
SPEC.loader.exec_module(builder)


class BlogTemplateTests(unittest.TestCase):
    def test_mining_article_warning_is_one_paragraph_without_duplicates(self):
        source = (ROOT / "content/pl/blog/posts/zmrozone-kopalnie-kryptowalut/index.md").read_text(encoding="utf-8")
        warning = source.split("{{< callout >}}", 1)[1].split("{{< /callout >}}", 1)[0]
        body = builder.render_markdown("{{< callout >}}" + warning + "{{< /callout >}}", builder.load_config(ROOT / "config/site.toml"))
        self.assertEqual(body.count("<p>"), 2)
        self.assertEqual(body.count("Pomimo dużej kwantyzacji"), 1)
        self.assertIn("Model gpt-oss:120b dostępny za pomocą Ollama", body)
        self.assertNotIn("Modelgpt-oss", body)

    def render(self, body, **overrides):
        post = dict(
            title="Polish QA", description="Model overview", date=dt.date(2024, 4, 15),
            meta={"updated": "2024-08-18"}, reading_minutes=5, tags=["NLP"],
        )
        post.update(overrides)
        env = Environment(
            loader=ChoiceLoader([
                DictLoader({"base.html": "{% block main %}{% endblock %}"}),
                FileSystemLoader(ROOT / "theme/templates"),
            ]),
            autoescape=select_autoescape(["html"]),
        )
        env.filters["datefmt"] = builder.format_date
        return env.get_template("post.html").render(
            post=SimpleNamespace(**post), content=body, outline=builder.article_outline(body),
            counterpart=None, lang="pl", cfg=SimpleNamespace(blog_path="blog/"),
            ui={"blog_title": "Blog", "back_to_blog": "Wszystkie wpisy", "tags": "Tagi",
                "published": "Opublikowano", "updated": "Zaktualizowano",
                "reading_time": "min czytania", "on_this_page": "W tym wpisie",
                "translation_missing": "Brak tłumaczenia"},
            href=lambda path: "/preview/" + path,
        )

    def test_outline_uses_markdown_anchors_and_plain_heading_text(self):
        body = builder.render_markdown(
            "## Model **QA**\n\n### A & B\n\n## Model **QA**\n\n```text\n## Not a heading\n```",
            builder.load_config(ROOT / "config/site.toml"),
        )
        outline = builder.article_outline(body)
        self.assertEqual([entry["text"] for entry in outline], ["Model QA", "A & B", "Model QA"])
        self.assertEqual(len({entry["id"] for entry in outline}), 3)
        text = self.render(body)
        for entry in outline:
            self.assertIn(f'href="#{entry["id"]}"', text)
        self.assertIn("A &amp; B</a>", text)
        self.assertIn('class="outline-h3"', text)

    def test_short_article_has_no_empty_outline_or_optional_fields(self):
        text = self.render('<h2 id="example">Example</h2><p>Text</p>', meta={}, tags=[], description="")
        self.assertNotIn('<aside class="blog-outline">', text)
        self.assertNotIn("blog-post-layout--outline", text)
        self.assertNotIn('class="lede"', text)
        self.assertNotIn('class="tag-row"', text)
        self.assertIn('href="/preview/blog/"', text)
        self.assertIn('<h2 id="example">Example</h2>', text)

    def test_heading_metadata_and_outline_are_escaped(self):
        text = self.render(
            '<h2 id="one">&lt;script&gt;</h2><h2 id="two">Two</h2><h2 id="three">Three</h2>',
            title="<script>alert(1)</script>", tags=["<b>NLP</b>"],
        )
        self.assertNotIn("<script>", text)
        self.assertIn("&lt;b&gt;NLP&lt;/b&gt;", text)
        self.assertIn('href="#one">&lt;script&gt;</a>', text)

    def test_index_handles_missing_images_and_translations(self):
        env = Environment(
            loader=ChoiceLoader([
                DictLoader({"base.html": "{% block main %}{% endblock %}"}),
                FileSystemLoader(ROOT / "theme/templates"),
            ]),
            autoescape=select_autoescape(["html"]),
        )
        env.filters["datefmt"] = builder.format_date
        post = SimpleNamespace(
            title="Polish QA", path="2024-04-15/qa/", date=dt.date(2024, 4, 15),
            image="", reading_minutes=5, description="Overview", tags=[],
        )
        original = SimpleNamespace(path="2024-04-15/polskie-qa/", description="Polski opis")
        text = env.get_template("blog_list.html").render(
            page_posts=[SimpleNamespace(post=post, missing=None), SimpleNamespace(post=post, missing=original)],
            page_count=1, lang="en", default_lang="pl",
            cfg=SimpleNamespace(href=lambda lang, path: f"/{lang}/{path}"),
            href=lambda path: "/en/" + path,
            ui={"blog_title": "Blog", "blog_intro": "Experiments", "reading_time": "min read",
                "read_article": "Read article", "translation_missing": "Not translated", "read_pl": "Read Polish"},
        )
        self.assertNotIn("post-item--media", text)
        self.assertNotIn('class="thumb"', text)
        self.assertEqual(text.count('class="post-read-link"'), 1)
        self.assertIn('href="/en/2024-04-15/qa/"', text)
        self.assertIn('href="/pl/2024-04-15/polskie-qa/"', text)
        self.assertIn("Polski opis", text)


if __name__ == "__main__":
    unittest.main()