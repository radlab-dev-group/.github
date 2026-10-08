import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from html.parser import HTMLParser


TOOLS = Path(__file__).resolve().parents[1]


class Selects(HTMLParser):
    def __init__(self, source):
        super().__init__()
        self.selects = {}
        self.current = None
        self.feed(source)

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "select":
            self.current = attrs["data-switch"]
            self.selects[self.current] = []
        elif tag == "option" and self.current:
            self.selects[self.current].append(attrs)

    def handle_endtag(self, tag):
        if tag == "select":
            self.current = None


class BuildDocsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(dir=TOOLS / "tests")
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.router = self.make_repo("router", ["1.0.0", "1.1.0"])
        self.plugins = self.make_repo("plugins", ["v0.1.0", "v0.2.0", "v0.3.0rc1"])
        self.services = self.make_repo("services", [])
        self.output = self.root / "site"

    def git(self, root, *args):
        subprocess.run(["git", "-C", str(root), *args], check=True,
                       capture_output=True, text=True)

    def make_repo(self, name, tags):
        root = self.root / name
        root.mkdir()
        self.git(root, "init", "-b", "main")
        self.git(root, "config", "user.name", "Docs Test")
        self.git(root, "config", "user.email", "docs@example.invalid")
        for version in tags + ["rolling"]:
            (root / "README.md").write_text(
                f"# {name}\n\nContent {version}\n\n[Guide](guides/guide.md)\n")
            (root / "guides").mkdir(exist_ok=True)
            (root / "guides/guide.md").write_text(
                f"# Guide\n\nGuide {version}\n\n[Overview](../README.md)\n")
            if version != "v0.1.0":
                (root / "guides/new.md").write_text("# New page\n\nNew content\n")
            self.git(root, "add", ".")
            self.git(root, "commit", "-m", version)
            if version != "rolling":
                self.git(root, "tag", version)
        return root

    def build(self, *extra):
        result = subprocess.run(
            [sys.executable, str(TOOLS / "build_docs.py"),
             "--source", str(self.router), "--plugins", str(self.plugins),
             "--services", str(self.services), "--output", str(self.output),
             "--all-versions", "--search", "all", *extra],
            capture_output=True, text=True,
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
        )
        self.assertEqual(result.returncode, 0, result.stdout + result.stderr)

    def test_independent_archives_and_links(self):
        self.build("--check-links")
        docs = self.output / "docs"
        for version in ("0.1.0", "0.2.0"):
            archive = docs / "plugins" / version
            source = (archive / "index-2.html").read_text()
            self.assertIn(f"Content v{version}", source)
            self.assertNotIn("Content rolling", source)
            self.assertIn('href="guides/guide.html"', source)
            self.assertIn(f"/llm-router-plugins/tree/v{version}", source)
            select = Selects(source).selects
            self.assertIn("router", select)
            selected = [o for o in select["plugins"] if "selected" in o]
            self.assertEqual(len(selected), 1)
            self.assertEqual(selected[0]["value"], "index-2.html")
            self.assertIn("rolling", source)
            self.assertNotIn("0.3.0rc1", source)
            hub_option = Selects((archive / "index.html").read_text()).selects["plugins"][0]
            self.assertEqual((archive / hub_option["value"]).resolve(),
                             (docs / "plugins/0.2.0/index.html").resolve())
            guide = (archive / "guides/guide.html").read_text()
            self.assertIn('data-search="../search.json"', guide)
            index = json.loads((archive / "search.json").read_text())
            self.assertTrue(any("Guide v" in p["b"] for p in index["pages"]))
            for item in index["pages"]:
                self.assertTrue((archive / item["k"]).is_file(), item)
        for path in docs.rglob("*.html"):
            source = path.read_text()
            root = re.search(r'data-docs-root="([^"]+)"', source)
            self.assertEqual((path.parent / root[1]).resolve(), docs.resolve())
            for options in Selects(path.read_text()).selects.values():
                for option in options:
                    if "disabled" in option:
                        self.assertEqual(option["value"], "")
                        continue
                    self.assertTrue((path.parent / option["value"]).is_file(),
                                    (path, option))
                    self.assertTrue((path.parent / option["data-root"]).is_file(),
                                    (path, option))
                    self.assertIn("data-version", option)
                    hub = (path.parent / option["data-root"]).read_text()
                    for repo_id in ("router", "plugins", "services"):
                        self.assertIn(f'data-nav-repo="{repo_id}"', hub)
            search = re.search(r'data-search="([^"]+)"', path.read_text())
            if search:
                index_path = path.parent / search[1]
                self.assertTrue(index_path.is_file(), (path, search[1]))
                for item in json.loads(index_path.read_text())["pages"]:
                    self.assertTrue((index_path.parent / item["k"]).is_file(), item)

    def test_missing_page_falls_back_to_archive_hub(self):
        self.build()
        page = self.output / "docs/plugins/0.2.0/guides/new.html"
        options = Selects(page.read_text()).selects["plugins"]
        self.assertTrue(any(o["value"] == "../../0.1.0/index.html" for o in options))

    def test_sidebar_versions_and_latest_plugin_status(self):
        self.build("--check-links")
        docs = self.output / "docs"
        for relative in ("index.html", "1.1.0/index.html",
                         "plugins/0.2.0/index.html", "plugins/0.2.0/guides/guide.html",
                         "plugins/0.1.0/index.html", "plugins/index.html"):
            source = (docs / relative).read_text()
            sidebar = source.split('<aside class="sidebar"', 1)[1].split('</aside>', 1)[0]
            self.assertIn('data-switch="plugins"', sidebar)
            self.assertIn('llm-router</span>', sidebar)
            self.assertIn('llm-router-plugins</span>', sidebar)
            self.assertIn('llm-router-services</span>', sidebar)
            self.assertRegex(source, r'<option [^>]*>v0\.2\.0\s*· latest</option>')
            self.assertNotIn('data-switch="plugins"', source.split('<aside class="sidebar"', 1)[0])
        for relative, status in (("plugins/0.2.0/index.html", "latest"),
                                 ("plugins/0.2.0/guides/guide.html", "latest"),
                                 ("plugins/0.1.0/index.html", "archived"),
                                 ("plugins/index.html", "rolling")):
            source = (docs / relative).read_text()
            router_context = source.split('<div data-router-context>', 1)[1].split('</a></div>', 1)[0]
            self.assertIn('>v1.1.0</span>', router_context)
            self.assertIn('>latest</span>', router_context)
            self.assertNotIn('>archived</span>', router_context)
            plugin_group = source.split('<div data-nav-repo="plugins">', 1)[1]
            side_head = plugin_group.split('<div class="side-head">', 1)[1].split('</div>', 1)[0]
            self.assertIn(f'>{status}</span>', side_head)
            self.assertIn(f'class="side-tag {"old" if status == "archived" else "live"}"', side_head)
        guide = (docs / "plugins/0.2.0/guides/guide.html").read_text()
        sidebar = guide.split('<aside class="sidebar"', 1)[1].split('</aside>', 1)[0]
        self.assertIn('href="../../../1.1.0/overview.html"', sidebar)
        self.assertIn('href="guide.html" class="active"', sidebar)
        self.assertEqual(sidebar.count('class="active"'), 1)

    def test_prereleases_and_no_satellites(self):
        self.build("--include-prerelease")
        self.assertTrue((self.output / "docs/plugins/0.3.0rc1/index.html").is_file())
        prerelease = (self.output / "docs/plugins/0.3.0rc1/index.html").read_text()
        self.assertRegex(prerelease, r'<option [^>]*>v0\.2\.0\s*· latest</option>')
        self.assertNotRegex(prerelease, r'<option [^>]*>v0\.3\.0rc1\s*· latest</option>')
        self.output = self.root / "router-only"
        self.build("--no-satellites", "--check-links")
        self.assertNotIn("plugins", Selects((self.output / "docs/index.html").read_text()).selects)

    def test_plugins_without_tags(self):
        self.plugins = self.make_repo("untagged-plugins", [])
        self.build("--check-links")
        options = Selects((self.output / "docs/plugins/guides/guide.html").read_text()).selects["plugins"]
        self.assertEqual(len(options), 1)
        self.assertIn("selected", options[0])


if __name__ == "__main__":
    unittest.main()