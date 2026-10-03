import importlib.util
import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path
from types import ModuleType
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("radlab_admin_core", ROOT / "admin_core.py")
core = importlib.util.module_from_spec(SPEC)
sys.modules[SPEC.name] = core
SPEC.loader.exec_module(core)


def make_fake_repo(directory: Path) -> Path:
    """Minimal content tree + translations.json under a temp root."""
    for lang in ("pl", "en"):
        (directory / "content" / lang / "blog" / "posts").mkdir(parents=True)
    (directory / "config").mkdir(parents=True)
    return directory


def write_post(store: core.ContentStore, lang: str, slug: str, body: str, **extra) -> None:
    meta = {
        "title": f"Tytuł {slug}",
        "date": date(2026, 1, 5),
        "updated": date(2026, 1, 6),
        "slug": slug,
        "description": "Opis",
        "tags": ["ai", "nlp"],
        "categories": ["GenAI"],
        "lang": lang,
    }
    meta.update(extra)
    store.save_post(lang, slug, meta, body)


class SlugifyTests(unittest.TestCase):
    def test_polish_diacritics_are_dropped(self):
        self.assertEqual(core.slugify("Przeglądarka informacji"), "przegladarka-informacji")

    def test_punctuation_becomes_hyphens(self):
        self.assertEqual(core.slugify("QA: uczenie GPU i CPU!"), "qa-uczenie-gpu-i-cpu")

    def test_empty_falls_back(self):
        self.assertEqual(core.slugify("///"), "wpis")

    def test_unique_slug_avoids_collisions(self):
        with tempfile.TemporaryDirectory(dir=ROOT) as tmp:
            store = core.ContentStore(make_fake_repo(Path(tmp)))
            write_post(store, "pl", "abc", "x")
            write_post(store, "pl", "abc-2", "x")
            self.assertEqual(core.unique_slug(store, "pl", "abc"), "abc-3")
            self.assertEqual(core.unique_slug(store, "pl", "wolny"), "wolny")


class FrontMatterTests(unittest.TestCase):
    def test_round_trip_preserves_values(self):
        meta = {
            "title": 'Cytat "polski" i \\ backslash',
            "date": date(2026, 3, 1),
            "slug": "x-y",
            "tags": ["a", 'b"c'],
            "draft": True,
            "wp_id": 42,
        }
        rendered = core.meta_to_front_matter(meta)
        parsed, body = core.parse_front_matter(rendered + "treść")
        self.assertEqual(parsed["title"], meta["title"])
        self.assertEqual(parsed["date"], date(2026, 3, 1))
        self.assertEqual(parsed["tags"], meta["tags"])
        self.assertIs(parsed["draft"], True)
        self.assertEqual(parsed["wp_id"], 42)
        self.assertEqual(body, "treść")

    def test_scalar_style_matches_existing_posts(self):
        meta = {"title": "Tytuł", "slug": "llm-router", "image": "media/a.png",
                "lang": "pl", "wp_id": 42, "draft": "yes"}
        rendered = core.meta_to_front_matter(meta)
        self.assertIn("slug: llm-router", rendered)
        self.assertIn("image: media/a.png", rendered)
        self.assertIn('title: "Tytuł"', rendered)
        self.assertIn("wp_id: 42", rendered)
        self.assertIn('draft: "yes"', rendered)  # reserved word must be quoted
        parsed, _ = core.parse_front_matter(rendered)
        self.assertEqual(parsed["draft"], "yes")

    def test_key_order_follows_existing_posts(self):
        meta = {"wp_id": 1, "title": "t", "slug": "s", "draft": False, "lang": "pl"}
        rendered = core.meta_to_front_matter(meta)
        self.assertLess(rendered.index("title:"), rendered.index("slug:"))
        self.assertLess(rendered.index("slug:"), rendered.index("lang:"))
        self.assertGreater(rendered.index("wp_id:"), rendered.index("lang:"))

    def test_no_front_matter_returns_empty_meta(self):
        meta, body = core.parse_front_matter("po prostu tekst")
        self.assertEqual(meta, {})
        self.assertEqual(body, "po prostu tekst")


class TranslationsFileTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self._tmp.name)
        make_fake_repo(self.root)
        self.store = core.ContentStore(self.root)
        self.store.write_translations({"stary-wpis": {"en": "old", "verified": True}})

    def tearDown(self):
        self._tmp.cleanup()

    def test_write_uses_exact_repo_format(self):
        self.store.write_translations({"b": {"en": "x"}, "a": {"en": "y", "verified": True}})
        raw = self.store.translations_path.read_text(encoding="utf-8")
        self.assertEqual(raw, json.dumps(
            {"a": {"en": "y", "verified": True}, "b": {"en": "x"}},
            indent=1, ensure_ascii=False, sort_keys=True))
        self.assertFalse(raw.endswith("\n"))

    def test_link_translation_new_entry(self):
        self.store.link_translation("pl-slug", "en-slug", verified=False)
        data = self.store.read_translations()
        self.assertEqual(data["pl-slug"], {"en": "en-slug", "verified": False})

    def test_link_translation_relink_resets_verified_keeps_extras(self):
        self.store.write_translations(
            {"pl": {"en": "old-en", "verified": True, "shared_images": 3}})
        self.store.link_translation("pl", "new-en", verified=False)
        entry = self.store.read_translations()["pl"]
        self.assertEqual(entry, {"en": "new-en", "verified": False, "shared_images": 3})

    def test_delete_post_unlinks_both_directions(self):
        write_post(self.store, "pl", "pl-a", "x")
        write_post(self.store, "en", "en-a", "x")
        self.store.link_translation("pl-a", "en-a", verified=True)
        self.store.delete_post("pl", "pl-a")
        self.assertNotIn("pl-a", self.store.read_translations())
        self.store.link_translation("pl-b", "en-a", verified=True)
        self.store.delete_post("en", "en-a")
        self.assertNotIn("pl-b", self.store.read_translations())

    def test_plain_string_shape_is_tolerated_on_read(self):
        self.store.translations_path.write_text('{"pl-x": "en-x"}', encoding="utf-8")
        data = self.store.read_translations()
        self.assertEqual(data["pl-x"], {"en": "en-x", "verified": True})


class ContentStoreTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self._tmp.name)
        make_fake_repo(self.root)
        self.store = core.ContentStore(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def test_save_and_load_round_trip(self):
        path = self.store.save_post("pl", "mój-wpis", {
            "title": "Tytuł", "date": date(2026, 5, 1), "slug": "mój-wpis",
            "tags": ["a"], "lang": "pl", "draft": True,
        }, "treść wpisu")
        self.assertTrue(path.is_file())
        post = self.store.load_post("pl", "mój-wpis")
        self.assertEqual(post.meta["title"], "Tytuł")
        self.assertEqual(post.meta["date"], date(2026, 5, 1))
        self.assertTrue(post.meta["draft"])
        self.assertEqual(post.body, "treść wpisu")

    def test_list_posts_sorted_and_counterparts(self):
        write_post(self.store, "pl", "starszy", "x", date=date(2025, 1, 1))
        write_post(self.store, "pl", "nowszy", "x", date=date(2026, 1, 1))
        write_post(self.store, "en", "nowszy-en", "x", date=date(2026, 1, 1))
        self.store.link_translation("nowszy", "nowszy-en", verified=True)
        posts = self.store.list_posts()
        self.assertEqual([p.slug for p in posts], ["nowszy-en", "nowszy", "starszy"])
        by_id = {(p.lang, p.slug): p for p in posts}
        self.assertEqual(by_id[("pl", "nowszy")].counterpart, "nowszy-en")
        self.assertEqual(by_id[("en", "nowszy-en")].counterpart, "nowszy")
        self.assertIsNone(by_id[("pl", "starszy")].counterpart)

    def test_load_missing_post_raises(self):
        with self.assertRaises(core.PostNotFound):
            self.store.load_post("pl", "nie-ma")

    def test_delete_missing_post_raises(self):
        with self.assertRaises(core.PostNotFound):
            self.store.delete_post("pl", "nie-ma")

    def test_rename_moves_dir_media_and_relinks(self):
        write_post(self.store, "pl", "stary", "treść")
        write_post(self.store, "en", "stary-en", "x")
        self.store.link_translation("stary", "stary-en", verified=True)
        media = self.store.post_dir("pl", "stary") / "media"
        media.mkdir()
        (media / "a.png").write_bytes(b"png")
        # EN counterpart declares translation_of in its front matter
        en_file = self.store.post_dir("en", "stary-en") / "index.md"
        en_file.write_text(en_file.read_text(encoding="utf-8")
                           + "\ntranslation_of: stary\n", encoding="utf-8")

        self.store.rename_post("pl", "stary", "nowy")

        self.assertTrue(self.store.post_exists("pl", "nowy"))
        self.assertFalse(self.store.post_exists("pl", "stary"))
        self.assertTrue((self.store.post_dir("pl", "nowy") / "media" / "a.png").is_file())
        data = self.store.read_translations()
        self.assertEqual(data["nowy"]["en"], "stary-en")
        self.assertIs(data["nowy"]["verified"], False)
        self.assertNotIn("stary", data)
        self.assertIn("translation_of: nowy",
                      (self.store.post_dir("en", "stary-en") / "index.md").read_text(encoding="utf-8"))

    def test_rename_to_existing_slug_raises(self):
        write_post(self.store, "pl", "a", "x")
        write_post(self.store, "pl", "b", "x")
        with self.assertRaises(core.PostExists):
            self.store.rename_post("pl", "a", "b")


class FakeTranslator:
    """Stands in for Translator inside translate_post; no network."""

    def __init__(self, prefix="[EN] "):
        self.prefix = prefix
        self.calls = []

    def translate_texts(self, target_lang, texts, model=None,
                        max_new_tokens=None, progress=None):
        self.calls.append((target_lang, list(texts), model, max_new_tokens))
        return [f"{self.prefix}{text}" for text in texts]


class TranslatePostTests(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(dir=ROOT)
        self.root = Path(self._tmp.name)
        make_fake_repo(self.root)
        self.store = core.ContentStore(self.root)

    def tearDown(self):
        self._tmp.cleanup()

    def _source_post(self):
        write_post(
            self.store, "pl", "pol-slug",
            "## Nagłówek\n\nAkapit z **pogrubieniem**.\n",
            image="media/zdj.png",
        )
        media = self.store.post_dir("pl", "pol-slug") / "media"
        media.mkdir()
        (media / "zdj.png").write_bytes(b"png-bytes")

    def test_pl_to_en_creates_linked_draft(self):
        self._source_post()
        translator = FakeTranslator()
        loaded = core.translate_post(self.store, "pl", "pol-slug", "en", translator,
                                     model="m", make_draft=True)
        self.assertEqual(loaded.lang, "en")
        self.assertEqual(loaded.meta["title"], "[EN] Tytuł pol-slug")
        self.assertEqual(loaded.meta["lang"], "en")
        self.assertEqual(loaded.meta["translation_of"], "pol-slug")
        self.assertIs(loaded.meta["draft"], True)
        self.assertEqual(loaded.meta["image"], "media/zdj.png")
        self.assertIn("[EN] ## Nagłówek", loaded.body)
        self.assertTrue((loaded.path.parent / "media" / "zdj.png").is_file())
        data = self.store.read_translations()
        self.assertEqual(data["pol-slug"], {"en": loaded.slug, "verified": False})
        self.assertEqual(translator.calls[0][2], "m")

    def test_slug_comes_from_translated_title(self):
        write_post(self.store, "pl", "pol-slug", "treść")
        translator = FakeTranslator(prefix="")
        # title "Tytuł pol-slug" -> "[EN]" empty prefix leaves slug from original title
        loaded = core.translate_post(self.store, "pl", "pol-slug", "en", translator)
        self.assertEqual(loaded.slug, "tytul-pol-slug")

    def test_en_to_pl_links_under_pl_slug(self):
        write_post(self.store, "en", "en-slug", "body", title="English title")
        translator = FakeTranslator(prefix="[PL] ")
        loaded = core.translate_post(self.store, "en", "en-slug", "pl", translator)
        self.assertEqual(loaded.lang, "pl")
        self.assertNotIn("translation_of", loaded.meta)
        self.assertEqual(loaded.meta["title"], "[PL] English title")
        data = self.store.read_translations()
        self.assertEqual(data[loaded.slug], {"en": "en-slug", "verified": False})

    def test_existing_counterpart_requires_overwrite(self):
        self._source_post()
        write_post(self.store, "en", "existing-en", "x")
        self.store.link_translation("pol-slug", "existing-en", verified=True)
        with self.assertRaises(core.PostExists):
            core.translate_post(self.store, "pl", "pol-slug", "en", FakeTranslator())
        loaded = core.translate_post(self.store, "pl", "pol-slug", "en",
                                     FakeTranslator(), overwrite=True)
        self.assertEqual(loaded.slug, "existing-en")
        self.assertTrue(self.store.post_exists("en", "existing-en"))

    def test_progress_reports_every_field(self):
        self._source_post()
        events = []
        core.translate_post(self.store, "pl", "pol-slug", "en", FakeTranslator(),
                            progress=lambda d, t, label: events.append((d, t, label)))
        self.assertEqual(len(events), 5)
        self.assertEqual(events[-1][:2], (5, 5))
        self.assertEqual([e[2] for e in events],
                         ["tytuł", "opis", "tagi", "kategorie", "treść"])

    def test_same_language_rejected(self):
        self._source_post()
        with self.assertRaises(core.PostError):
            core.translate_post(self.store, "pl", "pol-slug", "pl", FakeTranslator())


class TranslatorDispatchTests(unittest.TestCase):
    """Translator routes through the right LLMRouterClient methods."""

    def setUp(self):
        self._saved_modules = {
            name: sys.modules.get(name)
            for name in ("llm_router_lib", "llm_router_lib.client")
        }
        self._saved_path = list(sys.path)
        self.calls = []

        fake_pkg = ModuleType("llm_router_lib")
        fake_client = ModuleType("llm_router_lib.client")
        calls = self.calls

        class FakeClient:
            default_model = None

            def __init__(self, api=None, token=None, timeout=None,
                         retries=None, default_model=None):
                self.default_model = default_model
                self.kwargs = dict(api=api, token=token, timeout=timeout,
                                   retries=retries, default_model=default_model)

            def ping(self):
                calls.append(("ping",))
                return SimpleNamespace(status=True, body="pong")

            def models(self):
                calls.append(("models",))
                return SimpleNamespace(ids=["model-a", "model-b"])

            def translate(self, *, texts, model, max_new_tokens):
                calls.append(("translate", tuple(texts), model, max_new_tokens))
                items = [SimpleNamespace(original=t, translated=f"PL:{t}")
                         for t in texts]
                return SimpleNamespace(response=items)

            def extended_conversation_with_model(self, *, system_prompt,
                                                 user_last_statement, model,
                                                 max_new_tokens):
                calls.append(("extended", user_last_statement, model,
                              max_new_tokens, system_prompt))
                return SimpleNamespace(response=f"EN:{user_last_statement}")

            def close(self):
                calls.append(("close",))

        fake_client.LLMRouterClient = FakeClient
        fake_pkg.client = fake_client
        sys.modules["llm_router_lib"] = fake_pkg
        sys.modules["llm_router_lib.client"] = fake_client

    def tearDown(self):
        for name, module in self._saved_modules.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module
        sys.path[:] = self._saved_path

    def _translator(self):
        return core.Translator(api="http://router.test", model="model-a")

    def test_client_gets_env_api_and_model(self):
        import os
        os.environ.pop("LLM_ROUTER_API", None)
        translator = self._translator()
        self.assertEqual(translator.client.kwargs["api"], "http://router.test")
        self.assertEqual(translator.client.default_model, "model-a")

    def test_to_polish_uses_translate_method_in_one_call(self):
        translator = self._translator()
        result = translator.translate_texts("pl", ["Hello", "World"], model="model-a")
        self.assertEqual(result, ["PL:Hello", "PL:World"])
        self.assertEqual(self.calls[-1][0], "translate")
        self.assertEqual(self.calls[-1][1], ("Hello", "World"))
        self.assertEqual(len([c for c in self.calls if c[0] == "translate"]), 1)

    def test_to_english_uses_extended_conversation_per_text(self):
        translator = self._translator()
        result = translator.translate_texts(
            "en", ["Witaj", "Świat"], model="model-a",
            progress=lambda d, t, text: None)
        self.assertEqual(result, ["EN:Witaj", "EN:Świat"])
        extended = [c for c in self.calls if c[0] == "extended"]
        self.assertEqual(len(extended), 2)
        self.assertIn("English", extended[0][4])
        self.assertNotIn("Polish", extended[0][4].split("translate to is English")[0]
                         .rsplit("Task:", 1)[-1])

    def test_missing_model_raises(self):
        translator = self._translator()
        translator.client.default_model = None
        with self.assertRaises(core.PostError):
            translator.translate_texts("pl", ["x"])


if __name__ == "__main__":
    unittest.main()
