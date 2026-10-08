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
        self.services = self.make_repo("services", ["v0.4.0", "v0.5.0"])
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
            (root / "guides/nested").mkdir(exist_ok=True)
            (root / "guides/nested/index.md").write_text(
                f"# Nested guide\n\nNested {version}\n\n[Overview](../../README.md)\n")
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
            self.assertNotIn("rolling", source)
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

    def test_router_mount_and_incremental_versions(self):
        self.build("--check-links")
        docs = self.output / "docs"
        self.assertTrue((docs / "index.html").is_file())
        self.assertTrue((docs / "router/index.html").is_file())
        for version in ("1.0.0", "1.1.0"):
            archive = docs / "router" / version
            self.assertTrue((archive / "overview.html").is_file())
            self.assertFalse((docs / version).exists())
            guide = (archive / "guides/guide.html").read_text()
            self.assertIn('href="../overview.html"', guide)
            options = Selects(guide).selects["router"]
            for option in options:
                self.assertEqual((archive / "guides" / option["value"]).resolve(),
                                 (docs / "router" / option["data-version"] / "guides/guide.html").resolve())
        self.build("--max-versions", "1", "--check-links")
        versions = json.loads((docs / "versions.json").read_text())["versions"]
        self.assertEqual({v["entry"] for v in versions},
                         {"router/1.0.0/index.html", "router/1.1.0/index.html"})
        self.assertEqual(len(Selects((docs / "index.html").read_text()).selects["router"]), 2)

    def test_latest_nested_links(self):
        config = self.root / "docs.toml"
        config.write_text((TOOLS / "docs.toml").read_text() + '\n[[crosslinks]]\n'
                          'from = "guides/nested/index.md"\n'
                          'link = "../../README.md"\n'
                          'to = "services:README.md"\n')
        self.build("--config", str(config), "--check-links")
        for version in ("", "0.5.0/"):
            page = self.output / f"docs/services/{version}guides/nested/index.html"
            self.assertIn('href="../../index-2.html"', page.read_text())

    def test_collapsible_navigation_and_tag_links(self):
        self.build()
        source = (self.output / "docs/index.html").read_text()
        sidebar = source.split('<aside class="sidebar"', 1)[1].split('</aside>', 1)[0]
        self.assertNotIn('data-switch="router"', source.split('<aside class="sidebar"', 1)[0])
        for repo, name, tag in (("router", "llm-router", "1.1.0"),
                               ("plugins", "llm-router-plugins", "v0.2.0"),
                               ("services", "llm-router-services", "v0.5.0")):
            group = sidebar.split(f'<div data-nav-repo="{repo}">', 1)[1].split('</details>', 1)[0]
            self.assertIn('<details class="nav-group">', group)
            self.assertIn(f'<summary class="nav-repo"><span class="repo-name">{name}</span></summary>', group)
            self.assertLess(group.index('class="repo-name"'), group.index('class="side-head"'))
            self.assertIn(f'data-switch="{repo}"', group)
            self.assertIn(f'<details class="box versions-box" data-versions-repo="{repo}">', source)
            self.assertIn(f'/releases/tag/{tag}', source)
        repositories = source.split('<h2>repositories</h2>', 1)[1].split('</div></div>', 1)[0]
        self.assertNotIn('/commit/', repositories)

    def test_document_sidebar_keeps_all_categories_visible(self):
        self.build()
        for relative in ("router/1.1.0/index.html", "router/1.1.0/guides/guide.html",
                         "plugins/guides/guide.html", "services/guides/guide.html"):
            with self.subTest(relative=relative):
                source = (self.output / "docs" / relative).read_text()
                sidebar = source.split('<nav class="nav-tree"', 1)[1].split('</nav>', 1)[0]
                self.assertIn('<section class="nav-sec open">', sidebar)
                self.assertNotIn('<section class="nav-sec">', sidebar)

    def test_hubs_keep_router_release_and_omit_versions_toc(self):
        self.build("--check-links")
        for relative, router_version in (("index.html", "1.1.0"),
                                         ("router/1.0.0/index.html", "1.0.0"),
                                         ("plugins/index.html", "1.1.0"),
                                         ("plugins/0.1.0/index.html", "1.1.0"),
                                         ("services/index.html", "1.1.0"),
                                         ("services/0.4.0/index.html", "1.1.0")):
            with self.subTest(relative=relative):
                source = (self.output / "docs" / relative).read_text()
                self.assertNotIn('<h2 class="toc-title">versions</h2>', source)
                self.assertNotIn('<details class="nav-group" open>', source)
                panel = source.split('<div class="box" data-router-release>', 1)[1].split('</dl></div>', 1)[0]
                self.assertIn('<h2>Router release</h2>', panel)
                self.assertIn(f'<dt>version</dt><dd class="mono">{router_version}</dd>', panel)
                self.assertIn(f'/releases/tag/{router_version}', panel)
                self.assertIn('<dt>documents</dt><dd class="mono">4</dd>', panel)

    def test_sidebar_versions_and_latest_plugin_status(self):
        self.build("--check-links")
        docs = self.output / "docs"
        for relative in ("index.html", "router/1.1.0/index.html",
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
                                 ("plugins/index.html", "latest")):
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
        self.assertIn('href="../../../router/1.1.0/overview.html"', sidebar)
        self.assertIn('href="guide.html" class="active"', sidebar)
        self.assertEqual(sidebar.count('class="active"'), 1)

    def test_docs_start_page(self):
        self.build("--check-links")
        docs = self.output / "docs"
        source = (docs / "index.html").read_text()
        main = source.split('<main class="main" id="main">', 1)[1]
        self.assertIn('<h2 id="docs-start-title">Choose your documentation</h2>', main)
        self.assertEqual(main.count('class="repo-card"'), 3)
        for repo, target in (("router", "router/1.1.0/index.html"),
                             ("plugins", "plugins/index.html"),
                             ("services", "services/index.html")):
            self.assertIn(f'href="{target}" data-docs-entry="{repo}"', main)
        self.assertIn('<h2 id="docs-quickstart-title">Quick start</h2>', main)
        self.assertIn('href="router/1.1.0/overview.html">Installation & overview</a>', main)
        self.assertLess(main.index('class="docs-start"'), main.index('class="docs-quickstart"'))
        self.assertLess(main.index('class="docs-quickstart"'), main.index('class="hub-side"'))
        self.assertNotIn('class="sec-cards"', main)
        self.assertNotIn('class="vline"', main)
        for relative in ("router/1.0.0/index.html", "router/index.html", "plugins/index.html"):
            archive = (docs / relative).read_text()
            self.assertIn('class="sec-cards" id="sections"', archive)
            self.assertNotIn('class="docs-start"', archive)

    def test_hub_version_panels(self):
        self.build("--check-links")
        docs = self.output / "docs"
        for relative in ("index.html", "router/1.0.0/index.html",
                         "plugins/0.1.0/index.html", "plugins/index.html"):
            source = (docs / relative).read_text()
            router_panel = source.split('data-versions-repo="router">', 1)[1].split('</ul></details>', 1)[0]
            plugins_panel = source.split('data-versions-repo="plugins">', 1)[1].split('</ul></details>', 1)[0]
            self.assertIn('<h2>Router all versions</h2>', router_panel)
            self.assertIn('<h2>Plugins all versions</h2>', plugins_panel)
            self.assertIn('>v1.0.0</a>', router_panel)
            self.assertNotIn('>v0.1.0</a>', router_panel)
            self.assertIn('>v0.1.0</a>', plugins_panel)
            self.assertNotIn('rolling', plugins_panel)
            self.assertRegex(plugins_panel, r'class="vrow[^"]* latest"[^\n]*>v0\.2\.0</a>')
            selected_router = "1.0.0" if relative.startswith("router/1.0.0/") else "1.1.0"
            selected_plugins = "0.1.0" if relative.startswith("plugins/0.1.0/") else "0.2.0"
            self.assertRegex(router_panel, rf'class="vrow current[^\n]*data-version="{selected_router}"')
            self.assertRegex(plugins_panel, rf'class="vrow current[^\n]*data-version="{selected_plugins}"')
        plugin_hub = (docs / "plugins/0.1.0/index.html").read_text()
        self.assertIn('<h2>Router release</h2>', plugin_hub)
        self.assertNotIn('<h2>Plugins release</h2>', plugin_hub)

    def test_latest_tags_and_services_versions(self):
        self.build("--check-links")
        docs = self.output / "docs"
        for repo, newest, older in (("plugins", "0.2.0", "0.1.0"),
                                   ("services", "0.5.0", "0.4.0")):
            latest_page = (docs / repo / "guides/guide.html").read_text()
            self.assertIn(f"Guide v{newest}", latest_page)
            self.assertNotIn("Guide rolling", latest_page)
            for relative in ("index.html", f"{repo}/index.html", f"{repo}/{older}/index.html"):
                source = (docs / relative).read_text()
                options = Selects(source).selects[repo]
                self.assertEqual({o["data-version"] for o in options}, {newest, older})
                self.assertNotIn("rolling", source)
                panel = source.split(f'data-versions-repo="{repo}">', 1)[1].split('</ul></details>', 1)[0]
                self.assertIn(f'<h2>{repo.title()} all versions</h2>', panel)
                self.assertIn(f'>v{older}</a>', panel)
                self.assertRegex(panel, rf'class="vrow[^\"]* latest"[^\n]*>v{re.escape(newest)}</a>')
            archive = (docs / repo / older / "guides/guide.html").read_text()
            self.assertIn(f"Guide v{older}", archive)
            self.assertIn('>archived</span>', archive)

    def test_prereleases_and_no_satellites(self):
        self.build("--include-prerelease")
        self.assertTrue((self.output / "docs/plugins/0.3.0rc1/index.html").is_file())
        prerelease = (self.output / "docs/plugins/0.3.0rc1/index.html").read_text()
        self.assertRegex(prerelease, r'<option [^>]*>v0\.2\.0\s*· latest</option>')
        self.assertNotRegex(prerelease, r'<option [^>]*>v0\.3\.0rc1\s*· latest</option>')
        self.output = self.root / "router-only"
        self.build("--no-satellites", "--check-links")
        source = (self.output / "docs/index.html").read_text()
        self.assertNotIn("plugins", Selects(source).selects)
        self.assertEqual(source.count('class="repo-card"'), 1)
        self.assertNotIn('data-docs-entry="plugins"', source)
        self.assertNotIn('data-docs-entry="services"', source)

    def test_plugins_without_tags(self):
        self.plugins = self.make_repo("untagged-plugins", [])
        self.build("--check-links")
        options = Selects((self.output / "docs/plugins/guides/guide.html").read_text()).selects["plugins"]
        self.assertEqual(len(options), 1)
        self.assertIn("selected", options[0])
        self.assertEqual(options[0]["data-version"], "latest")
        self.assertNotIn("rolling", (self.output / "docs/plugins/index.html").read_text())


    def test_privacy_page_and_consent_gate(self):
        self.build("--check-links")
        docs = self.output / "docs"

        privacy = (self.output / "privacy.html").read_text()
        self.assertIn("Privacy policy", privacy)
        self.assertIn('src="docs/assets/consent.js"', privacy)
        self.assertNotIn("googletagmanager", privacy)

        index = (self.output / "index.html").read_text()
        self.assertIn("docs/assets/consent.js", index)
        self.assertNotIn("googletagmanager", index)

        root_docs = (docs / "index.html").read_text()
        self.assertIn('src="./assets/consent.js"', root_docs)
        self.assertIn('href="../privacy.html"', root_docs)

        page = (docs / "router/1.1.0/guides/guide.html").read_text()
        self.assertIn('src="../../../assets/consent.js"', page)
        self.assertIn('href="../../../../privacy.html"', page)
        self.assertNotIn("googletagmanager", page)

        consent = (docs / "assets/consent.js").read_text()
        self.assertIn("G-9KM7GYM55M", consent)
        self.assertIn("llmRouterConsent", consent)
        self.assertNotIn("var GA_PAYLOAD = @@GA@@;", consent)


if __name__ == "__main__":
    unittest.main()