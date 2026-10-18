"""
Puls Informacji — Słownik wielojęzyczny (PL / EN).
Przeniesiony 1:1 ze specyfikacji Next.js / ui_lang_def.xlsx.
"""

LANGS = [
    {"code": "pl", "label": "Polski", "flag": "🇵🇱"},
    {"code": "en", "label": "English", "flag": "🇬🇧"},
]

DICT = {
    "app_title": {"pl": "Puls Informacji", "en": "Puls Informacji"},
    "app_tagline": {"pl": "Co słychać teraz?", "en": "What’s happening now?"},
    "intro_eyebrow": {"pl": "Mniej szukania, więcej wiedzy", "en": "Less searching, more understanding"},
    "intro_title": {"pl": "Co chcesz dziś wiedzieć?", "en": "What would you like to know today?"},
    "intro_description": {
        "pl": "Wybierz temat. Zbierz aktualne wiadomości z wielu źródeł w jeden czytelny artykuł. Źródła znajdziesz tuż pod tekstem.",
        "en": "Choose a topic. Bring current news from multiple sources together in one easy-to-read article. You’ll find the sources just below the text.",
    },
    "live_badge": {"pl": "Źródła gotowe", "en": "Sources ready"},
    "live_badge_wait": {"pl": "Łączenie ze źródłami…", "en": "Connecting to sources…"},
    "intro_step_1": {
        "pl": "Wpisz, co Cię interesuje",
        "en": "Tell us what you’re curious about",
    },
    "intro_step_2": {
        "pl": "Przeszukamy aktualne wiadomości z wielu serwisów",
        "en": "We search current news across many outlets",
    },
    "intro_step_3": {
        "pl": "Dostaniesz jeden, spójny artykuł do przeczytania",
        "en": "You get one coherent article to read",
    },
    "index_note": {
        "pl": "News ze Strumienia Aktualności trafia do indeksu po ok. 10 minutach",
        "en": "News from the stream lands in the index after ~10 minutes",
    },
    "what_is_title": {
        "pl": "Czym jest Puls Informacji?",
        "en": "What is Puls Informacji?",
    },
    "what_is_desc": {
        "pl": "**Kreator Aktualności**, to pod spodem system oparty o **RAG**. Działa na zasadach wyszukiwarki, gdzie na zadane przez użytkownika pytanie generowana jest odpowiedź przez model generatywny. Odpowiedź kreowana jest w oparciu o **dostarczone** przez **wyszukiwarkę newsy**, ograniczając przy tym _halucynację_ modeli gen AI. W Kreatorze **nie korzystamy z zewnętrznych API** do przeszukiwania. Bazujemy na **własnym indeksie** przeszukiwaniowemu analizowanych przez nas stron.",
        "en": "**News Creator** is a system based on **RAG**. It works like a search engine, where a generative model generates a response to a user's query. The response is created based on **news provided** by the **search engine**, thereby limiting the _hallucination_ of gen AI models. In the Creator, **we do not use external API** for searching. We rely on our **own search index** of the pages we analyze.",
    },
    "query_label": {
        "pl": "O czym chcesz przeczytać?",
        "en": "What would you like to read about?",
    },
    "query_placeholder": {
        "pl": "Na przykład: Co nowego w świecie technologii i sztucznej inteligencji?",
        "en": "For example: What’s new in technology and artificial intelligence?",
    },
    "style_label": {
        "pl": "Styl generowanego artykułu",
        "en": "Style of the generated article",
    },
    "style_simple": {
        "pl": "Zrozumiała dla każdego",
        "en": "Understandable to everyone",
    },
    "style_formal": {
        "pl": "Formalny język",
        "en": "Formal language",
    },
    "last_days_label": {"pl": "Ostatnie dni", "en": "Recent days"},
    "btn_run": {"pl": "Przygotuj artykuł", "en": "Create article"},
    "btn_edit_query": {"pl": "Edytuj zapytanie", "en": "Edit query"},
    "btn_close_editor": {"pl": "Zwiń", "en": "Collapse"},
    "btn_run_again": {"pl": "Przygotuj ponownie", "en": "Create again"},
    "btn_new_topic": {"pl": "Nowy temat", "en": "New topic"},
    "shortcut_hint": {
        "pl": "lub naciśnij Ctrl + Enter",
        "en": "or press Ctrl + Enter",
    },
    "style_simple_desc": {
        "pl": "Prosty język, krótkie zdania",
        "en": "Plain language, short sentences",
    },
    "style_formal_desc": {
        "pl": "Rzeczowy, oficjalny ton",
        "en": "Matter-of-fact, official tone",
    },
    "day_1": {"pl": "Dziś", "en": "Today"},
    "day_2": {"pl": "2 dni", "en": "2 days"},
    "day_7": {"pl": "Tydzień", "en": "Week"},
    "days_suffix": {"pl": "dni", "en": "days"},
    "suggestions_title": {
        "pl": "Szukasz inspiracji?",
        "en": "Need some inspiration?",
    },
    "suggestions_hint": {
        "pl": "Wybierz jeden z tematów",
        "en": "Choose one of these topics",
    },
    "suggestions_refresh": {"pl": "Losuj kolejne", "en": "Draw again"},
    "no_query_error": {
        "pl": "Brak pytania! Należy najpierw wpisać pytanie!",
        "en": "No question! You must enter a question first!",
    },
    "model_prompt_p1": {
        "pl": "Tworzona przez Ciebie treść musi być napisana",
        "en": "The content you create must be written",
    },
    "model_prompt_formal": {
        "pl": "formalnym/urzędowym tonem.",
        "en": "in a formal/official tone.",
    },
    "model_prompt_simple": {
        "pl": "bardzo prostym językiem, aby była zrozumiała dla wszystkich.",
        "en": "in very simple language so that it is understandable to everyone.",
    },
    "progress_search": {
        "pl": "Trwa wyszukiwanie newsów związanych z zapytaniem...",
        "en": "Searching for news related to your query...",
    },
    "progress_gen": {
        "pl": "Trwa kreowanie aktualności... na naszym sprzęcie może to chwilę potrwać (nawet 1-2 min)... :)",
        "en": "Creating the article... on our hardware this may take a while (even 1-2 min)... :)",
    },
    "progress_ready": {"pl": "Gotowe!", "en": "Ready!"},
    "progress_search_short": {
        "pl": "Szukamy wiadomości na Twój temat…",
        "en": "Looking for news on your topic…",
    },
    "progress_gen_short": {
        "pl": "Piszemy artykuł. To może potrwać 1–2 minuty — warto chwilę poczekać.",
        "en": "Writing your article. This can take 1–2 minutes — worth the wait.",
    },
    "notice_title": {"pl": "Informacja", "en": "Notice"},
    "no_data_found": {
        "pl": "Nie odnaleziono nic w bazie!",
        "en": "Nothing found in the database!",
    },
    "api_error": {
        "pl": "Wystąpił błąd połączenia z API. Sprawdź konfigurację i spróbuj ponownie.",
        "en": "Connection error to the API. Check configuration and try again.",
    },
    "found_news_title": {
        "pl": "Wykaz znalezionych newsów",
        "en": "List of found news",
    },
    "sources_title": {
        "pl": "Zasięg wyszukiwania",
        "en": "Search scope",
    },
    "sources_scope_count": {
        "pl": "Przeszukiwane serwisy informacyjne: {count}",
        "en": "News sites searched: {count}",
    },
    "sources_show": {"pl": "Zobacz źródła", "en": "View sources"},
    "sources_hide": {"pl": "Ukryj źródła", "en": "Hide sources"},
    "sources_hint": {
        "pl": "Kategorie i źródła dostępne w Pulsie Informacji (wszystkie aktywne)",
        "en": "Categories and sources available in Puls Informacji (all active)",
    },
    "pages": {"pl": "stron", "en": "sites"},
    "polarity_title": {
        "pl": "Polaryzacja w dopasowanych newsach",
        "en": "Polarization in matched news",
    },
    "polarity_subtitle": {
        "pl": "Polaryzacja 3c w dopasowanych newsach [procent]",
        "en": "Polarization 3c in matched news [percent]",
    },
    "pos": {"pl": "pozytywny", "en": "positive"},
    "neg": {"pl": "negatywny", "en": "negative"},
    "amb": {"pl": "ambiwalentny", "en": "ambivalent"},
    "article_title": {"pl": "Twój artykuł", "en": "Your article"},
    "article_onair": {"pl": "Artykuł przygotowany dla Ciebie", "en": "An article prepared for you"},
    "article_topic": {"pl": "Temat", "en": "Topic"},
    "article_actions_hint": {
        "pl": "Podobało się? Zapisz lub skopiuj artykuł.",
        "en": "Enjoyed it? Save or copy the article.",
    },
    "tech_details": {"pl": "Szczegóły techniczne", "en": "Technical details"},
    "back_to_top": {"pl": "Wróć na górę", "en": "Back to top"},
    "article_empty": {
        "pl": "Model nie zwrócił treści spróbuje ponownie za chwilę.",
        "en": "The model returned no content — please try again in a moment.",
    },
    "based_on": {"pl": "Na podstawie", "en": "Based on"},
    "sources_used": {"pl": "dopasowanych newsów", "en": "matched news items"},
    "material_title": {"pl": "Źródła do artykułu", "en": "Article sources"},
    "material_hint": {
        "pl": "Wiadomości dopasowane do Twojego tematu i przekazane do przygotowania artykułu — nie lista wszystkich przeszukiwanych serwisów.",
        "en": "News matched to your topic and supplied to create the article — not the list of all sites searched.",
    },
    "view_wire": {"pl": "Przegląd", "en": "Wire"},
    "view_list": {"pl": "Lista", "en": "List"},
    "no_polarity": {"pl": "brak klasyfikacji", "en": "unclassified"},
    "all_categories": {"pl": "Wszystkie", "en": "All"},
    "when_generated": {
        "pl": "Wygenerowano w dniu",
        "en": "Generated on",
    },
    "gen_time": {
        "pl": "Czas generowania (s)",
        "en": "Generation time (s)",
    },
    "gen_model": {"pl": "Model generujący", "en": "Generating model"},
    "news_used": {
        "pl": "Liczba dopasowanych newsów",
        "en": "Number of matching news items",
    },
    "word_count": {"pl": "słów", "en": "words"},
    "reading_time": {"pl": "min czytania", "en": "min read"},
    "reading_time_long": {
        "pl": "Przeczytasz w ok. {minutes} min",
        "en": "About {minutes} min read",
    },
    "copy": {"pl": "Kopiuj", "en": "Copy"},
    "copied": {"pl": "Skopiowano!", "en": "Copied!"},
    "download": {"pl": "Pobierz .md", "en": "Download .md"},
    "open_source": {"pl": "Otwórz źródło", "en": "Open source"},
    "step_query": {"pl": "Zapytanie", "en": "Query"},
    "step_search": {"pl": "Wyszukiwanie", "en": "Search"},
    "step_index": {"pl": "Dopasowanie", "en": "Matching"},
    "step_gen": {"pl": "Generowanie", "en": "Generation"},
    "footer_note": {
        "pl": "Puls Informacji by RadLab — aktualne wiadomości na Twój temat",
        "en": "Puls Informacji by RadLab — current news on your topic",
    },
    "footer_disclaimer": {
        "pl": "Artykuły powstają automatycznie na podstawie zebranych wiadomości. Zawsze możesz zajrzeć do źródeł pod tekstem.",
        "en": "Articles are generated automatically from collected news. You can always check the sources below the text.",
    },
    "loading_categories": {
        "pl": "Ładowanie indeksu źródeł...",
        "en": "Loading source index...",
    },
    "categories_error": {
        "pl": "Nie udało się pobrać kategorii źródeł.",
        "en": "Failed to load source categories.",
    },
    "all_sources_active": {
        "pl": "wszystkie źródła aktywne",
        "en": "all sources active",
    },
}


def t(key: str, lang: str = "pl") -> str:
    """Tłumaczenie klucza na wybrany język."""
    entry = DICT.get(key)
    if not entry:
        return key
    return entry.get(lang, entry.get("pl", key))


def build_article_prompt(lang: str = "pl", style: str = "simple") -> str:
    """Buduje prefix promptu dla modelu generatora."""
    p1 = t("model_prompt_p1", lang)
    if style == "formal":
        p2 = t("model_prompt_formal", lang)
    else:
        p2 = t("model_prompt_simple", lang)
    return f"{p1} {p2}"
