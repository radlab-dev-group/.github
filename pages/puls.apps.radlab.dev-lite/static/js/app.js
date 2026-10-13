/**
 * Puls Informacji — Front-end application controller
 * Pure Vanilla JS, zero npm dependencies, fast and lightweight.
 */

(function () {
    "use strict";

    // =========================================================================
    // 1. Translations & Dictionary
    // =========================================================================

    const DICT = {
        app_title: { pl: "Puls Informacji", en: "Puls Informacji" },
        intro_eyebrow: { pl: "Mniej szukania, więcej wiedzy", en: "Less searching, more understanding" },
        intro_title: { pl: "Co chcesz dziś wiedzieć?", en: "What would you like to know today?" },
        intro_description: {
            pl: "Wybierz temat. Zbierz aktualne wiadomości z wielu źródeł w jeden czytelny artykuł. Źródła znajdziesz tuż pod tekstem.",
            en: "Choose a topic. Bring current news from multiple sources together in one easy-to-read article. You’ll find the sources just below the text."
        },
        live_badge: { pl: "Źródła gotowe", en: "Sources ready" },
        live_badge_wait: { pl: "Łączenie ze źródłami…", en: "Connecting to sources…" },
        intro_step_1: { pl: "Wpisz, co Cię interesuje", en: "Tell us what you’re curious about" },
        intro_step_2: { pl: "Przeszukamy aktualne wiadomości z wielu serwisów", en: "We search current news across many outlets" },
        intro_step_3: { pl: "Dostaniesz jeden, spójny artykuł do przeczytania", en: "You get one coherent article to read" },
        index_note: {
            pl: "News ze Strumienia Aktualności trafia do indeksu po ok. 10 minutach.",
            en: "News from the stream lands in the index after ~10 minutes."
        },
        what_is_title: { pl: "Czym jest Puls Informacji?", en: "What is Puls Informacji?" },
        what_is_desc: {
            pl: "<strong>Kreator Aktualności</strong>, to pod spodem system oparty o <strong>RAG</strong>. Działa na zasadach wyszukiwarki, gdzie na zadane przez użytkownika pytanie generowana jest odpowiedź przez model generatywny. Odpowiedź kreowana jest w oparciu o <strong>dostarczone</strong> przez <strong>wyszukiwarkę newsy</strong>, ograniczając przy tym <em>halucynację</em> modeli gen AI. W Kreatorze <strong>nie korzystamy z zewnętrznych API</strong> do przeszukiwania. Bazujemy na <strong>własnym indeksie</strong> przeszukiwaniowemu analizowanych przez nas stron.",
            en: "<strong>News Creator</strong> is a system based on <strong>RAG</strong>. It works like a search engine, where a generative model generates a response to a user's query. The response is created based on <strong>news provided</strong> by the <strong>search engine</strong>, thereby limiting the <em>hallucination</em> of gen AI models. In the Creator, <strong>we do not use external API</strong> for searching. We rely on our <strong>own search index</strong> of the pages we analyze."
        },
        query_label: { pl: "O czym chcesz przeczytać?", en: "What would you like to read about?" },
        query_placeholder: {
            pl: "Na przykład: Co nowego w świecie technologii i sztucznej inteligencji?",
            en: "For example: What’s new in technology and artificial intelligence?"
        },
        style_label: { pl: "Styl generowanego artykułu", en: "Style of the generated article" },
        style_simple: { pl: "Zrozumiała dla każdego", en: "Understandable to everyone" },
        style_simple_desc: { pl: "Prosty język, krótkie zdania", en: "Plain language, short sentences" },
        style_formal: { pl: "Formalny język", en: "Formal language" },
        style_formal_desc: { pl: "Rzeczowy, oficjalny ton", en: "Matter-of-fact, official tone" },
        last_days_label: { pl: "Ostatnie dni", en: "Recent days" },
        btn_run: { pl: "Przygotuj artykuł", en: "Create article" },
        btn_run_again: { pl: "Przygotuj ponownie", en: "Create again" },
        btn_new_topic: { pl: "Nowy temat", en: "New topic" },
        shortcut_hint: { pl: "lub naciśnij Ctrl + Enter", en: "or press Ctrl + Enter" },
        day_1: { pl: "Dziś", en: "Today" },
        day_2: { pl: "2 dni", en: "2 days" },
        day_7: { pl: "Tydzień", en: "Week" },
        suggestions_hint: { pl: "Wybierz jeden z tematów:", en: "Choose one of these topics:" },
        suggestions_refresh: { pl: "Losuj kolejne", en: "Draw again" },
        no_query_error: { pl: "Brak pytania! Należy najpierw wpisać pytanie!", en: "No question! You must enter a question first!" },
        loading_categories: { pl: "Wczytywanie listy kategorii i serwisów…", en: "Loading categories and sources…" },
        sources_scope_count: { pl: "Przeszukiwane serwisy informacyjne: {count}", en: "News sites searched: {count}" },
        sources_show: { pl: "Zobacz źródła", en: "View sources" },
        sources_hide: { pl: "Ukryj źródła", en: "Hide sources" },
        sources_hint: {
            pl: "Kategorie i źródła dostępne w Pulsie Informacji (wszystkie aktywne)",
            en: "Categories and sources available in Puls Informacji (all active)"
        },
        all_sources_active: { pl: "Wszystkie źródła biorą udział w przeszukiwaniu", en: "All sources participate in the search" },
        step_query: { pl: "Pytanie", en: "Query" },
        step_search: { pl: "Przeszukiwanie bazy", en: "Search" },
        step_index: { pl: "Dopasowanie newsów", en: "Matching" },
        step_gen: { pl: "Generowanie artykułu", en: "Generating" },
        progress_search_short: { pl: "Szukamy wiadomości na Twój temat…", en: "Looking for news on your topic…" },
        progress_gen_short: { pl: "Piszemy artykuł. To może potrwać 1–2 minuty — warto chwilę poczekać.", en: "Writing your article. This can take 1–2 minutes — worth the wait." },
        progress_ready: { pl: "Gotowe!", en: "Ready!" },
        notice_title: { pl: "Informacja", en: "Notice" },
        no_data_found: { pl: "Nie odnaleziono nic w bazie!", en: "Nothing found in the database!" },
        api_error: { pl: "Wystąpił błąd połączenia z API. Sprawdź konfigurację i spróbuj ponownie.", en: "Connection error to the API. Check configuration and try again." },
        article_onair: { pl: "Artykuł przygotowany dla Ciebie", en: "An article prepared for you" },
        reading_time_long: { pl: "~{minutes} min czytania", en: "~{minutes} min read" },
        based_on: { pl: "Na podstawie", en: "Based on" },
        sources_used: { pl: "dopasowanych newsów", en: "matched news items" },
        copy: { pl: "Kopiuj", en: "Copy" },
        copied: { pl: "Skopiowano!", en: "Copied!" },
        download: { pl: "Pobierz .md", en: "Download .md" },
        article_actions_hint: { pl: "Podobało się? Zapisz lub skopiuj artykuł.", en: "Enjoyed it? Save or copy the article." },
        tech_details: { pl: "Szczegóły techniczne", en: "Technical details" },
        article_topic: { pl: "Temat", en: "Topic" },
        news_used: { pl: "Wykorzystane newsy", en: "News items used" },
        gen_model: { pl: "Model generujący", en: "Generating model" },
        gen_time: { pl: "Czas generowania (s)", en: "Generation time (s)" },
        word_count: { pl: "Liczba słów", en: "Word count" },
        when_generated: { pl: "Wygenerowano w dniu", en: "Generated on" },
        material_title: { pl: "Źródła do artykułu", en: "Article sources" },
        material_hint: {
            pl: "Wiadomości dopasowane do Twojego tematu i przekazane do przygotowania artykułu — nie lista wszystkich przeszukiwanych serwisów.",
            en: "News matched to your topic and supplied to create the article — not the list of all sites searched."
        },
        view_wire: { pl: "Przegląd", en: "Wire" },
        view_list: { pl: "Lista", en: "List" },
        polarity_title: { pl: "Polaryzacja w dopasowanych newsach", en: "Polarization in matched news" },
        pos: { pl: "pozytywny", en: "positive" },
        neg: { pl: "negatywny", en: "negative" },
        amb: { pl: "ambiwalentny", en: "ambivalent" },
        no_polarity: { pl: "brak klasyfikacji", en: "unclassified" },
        all_categories: { pl: "Wszystkie", en: "All" },
        model_prompt_p1: { pl: "Tworzona przez Ciebie treść musi być napisana", en: "The content you create must be written" },
        model_prompt_formal: { pl: "formalnym/urzędowym tonem.", en: "in a formal/official tone." },
        model_prompt_simple: { pl: "bardzo prostym językiem, aby była zrozumiała dla wszystkich.", en: "in very simple language so that it is understandable to everyone." }
    };

    let currentLang = "pl";

    function t(key, fallback = "") {
        const item = DICT[key];
        if (!item) return fallback || key;
        return item[currentLang] || item.pl || fallback || key;
    }

    function applyTranslations() {
        document.querySelectorAll("[data-i18n]").forEach((el) => {
            const key = el.getAttribute("data-i18n");
            if (key && DICT[key]) {
                el.innerHTML = t(key);
            }
        });
        document.querySelectorAll("[data-i18n-placeholder]").forEach((el) => {
            const key = el.getAttribute("data-i18n-placeholder");
            if (key && DICT[key]) {
                el.setAttribute("placeholder", t(key));
            }
        });
        document.documentElement.lang = currentLang;
    }

    // =========================================================================
    // 2. Application State
    // =========================================================================

    const state = {
        categories: null,
        categoriesLoading: true,
        query: "",
        style: "simple",
        lastDays: 1,
        suggestions: [],
        phase: "idle", // 'idle' | 'searching' | 'generating' | 'done' | 'error'
        searchResult: null,
        queryResponseId: 0,
        article: null,
        numberOfNewsUsed: 0,
        selectedCategory: "__all__",
        viewMode: "wire" // 'wire' | 'list'
    };

    // =========================================================================
    // 3. DOM Elements
    // =========================================================================

    const el = {
        langPl: document.getElementById("langPl"),
        langEn: document.getElementById("langEn"),
        headerStatusBadge: document.getElementById("headerStatusBadge"),
        headerStatusText: document.getElementById("headerStatusText"),
        introSection: document.getElementById("introSection"),

        // Query panel
        queryPanel: document.getElementById("queryPanel"),
        queryCompactBar: document.getElementById("queryCompactBar"),
        compactQueryBtn: document.getElementById("compactQueryBtn"),
        compactBadge: document.getElementById("compactBadge"),
        btnNewTopic: document.getElementById("btnNewTopic"),
        btnRunAgain: document.getElementById("btnRunAgain"),
        queryForm: document.getElementById("queryForm"),
        queryInput: document.getElementById("queryInput"),
        queryError: document.getElementById("queryError"),
        btnShuffleSuggestions: document.getElementById("btnShuffleSuggestions"),
        suggestionsList: document.getElementById("suggestionsList"),
        styleSimpleLabel: document.getElementById("styleSimpleLabel"),
        styleFormalLabel: document.getElementById("styleFormalLabel"),
        dayBtns: document.querySelectorAll(".day-btn"),
        btnRun: document.getElementById("btnRun"),

        // Scope
        sourcesScopeLoading: document.getElementById("sourcesScopeLoading"),
        sourcesScopeError: document.getElementById("sourcesScopeError"),
        sourcesScopeDetails: document.getElementById("sourcesScopeDetails"),
        sourcesScopeCountText: document.getElementById("sourcesScopeCountText"),
        sourcesScopeCategoriesList: document.getElementById("sourcesScopeCategoriesList"),

        // Pipeline
        pipelineStrip: document.getElementById("pipelineStrip"),
        pipeStep1: document.getElementById("pipeStep1"),
        pipeStep2: document.getElementById("pipeStep2"),
        pipeStep3: document.getElementById("pipeStep3"),
        pipeStep4: document.getElementById("pipeStep4"),
        pipelineStatusMsg: document.getElementById("pipelineStatusMsg"),

        // Notices & Errors
        noticeCard: document.getElementById("noticeCard"),
        noticeMsg: document.getElementById("noticeMsg"),
        apiErrorCard: document.getElementById("apiErrorCard"),
        apiErrorMsg: document.getElementById("apiErrorMsg"),

        // Article section
        articleSection: document.getElementById("articleSection"),
        articleHeadline: document.getElementById("articleHeadline"),
        readingTimeText: document.getElementById("readingTimeText"),
        sourcesUsedLink: document.getElementById("sourcesUsedLink"),
        articleDateText: document.getElementById("articleDateText"),
        btnCopyArticle: document.getElementById("btnCopyArticle"),
        btnCopyText: document.getElementById("btnCopyText"),
        btnDownloadArticle: document.getElementById("btnDownloadArticle"),
        articleBodyContent: document.getElementById("articleBodyContent"),
        btnCopyArticleBottom: document.getElementById("btnCopyArticleBottom"),
        btnDownloadArticleBottom: document.getElementById("btnDownloadArticleBottom"),

        // Tech Details
        techTopic: document.getElementById("techTopic"),
        techNewsUsed: document.getElementById("techNewsUsed"),
        techModel: document.getElementById("techModel"),
        techGenTime: document.getElementById("techGenTime"),
        techWordCount: document.getElementById("techWordCount"),
        techWhenGenerated: document.getElementById("techWhenGenerated"),

        // Source material
        sourcesMaterialSection: document.getElementById("sourcesMaterialSection"),
        sourcesCountPill: document.getElementById("sourcesCountPill"),
        viewWireBtn: document.getElementById("viewWireBtn"),
        viewListBtn: document.getElementById("viewListBtn"),
        polarityTotalCount: document.getElementById("polarityTotalCount"),
        polarityBarTrack: document.getElementById("polarityBarTrack"),
        polarityLegend: document.getElementById("polarityLegend"),
        categoryTabsList: document.getElementById("categoryTabsList"),
        sourcesWireContainer: document.getElementById("sourcesWireContainer"),
        sourcesListContainer: document.getElementById("sourcesListContainer")
    };

    // =========================================================================
    // 4. Utility Helpers
    // =========================================================================

    function extractHost(url) {
        try {
            return new URL(url).hostname;
        } catch {
            return url;
        }
    }

    function formatTimestamp(ts) {
        if (!ts) return "—";
        return String(ts).split(".")[0].replace("T", " ");
    }

    function countWords(str) {
        const trimmed = (str || "").trim();
        if (!trimmed) return 0;
        return trimmed.split(/\s+/).length;
    }

    function calculateReadingMinutes(str) {
        return Math.max(1, Math.round(countWords(str) / 180));
    }

    function splitMarkdownHeadline(md) {
        const lines = (md || "").replace(/\r\n/g, "\n").split("\n");
        for (let i = 0; i < Math.min(lines.length, 6); i++) {
            const match = /^#\s+(.+?)\s*$/.exec(lines[i]);
            if (match) {
                const body = lines.slice(0, i).concat("", lines.slice(i + 1)).join("\n");
                return { headline: match[1], body: body };
            }
        }
        return { headline: null, body: md };
    }

    function deriveNumOfResults(lastDays) {
        if (lastDays === 1) return 7;
        if (lastDays < 7) return 9;
        return 12;
    }

    function buildArticlePrompt(lang, style) {
        const p1 = t("model_prompt_p1");
        const styleText = style === "formal" ? t("model_prompt_formal") : t("model_prompt_simple");
        return `${p1} ${styleText}`.trim();
    }

    function extractSitesList(categories) {
        if (!categories) return [];
        const sites = [];
        Object.values(categories).forEach((cat) => {
            (cat.category_pages || []).forEach((p) => {
                if (p.main_url) sites.push(p.main_url);
            });
        });
        return Array.from(new Set(sites));
    }

    function collectNewsIds(searchInCategory) {
        const ids = [];
        if (!searchInCategory) return ids;
        Object.values(searchInCategory).forEach((list) => {
            (list || []).forEach((item) => {
                const id = item.id !== undefined ? item.id : item.news_id;
                if (typeof id === "number") ids.push(id);
            });
        });
        return ids;
    }

    // =========================================================================
    // 5. API Fetchers
    // =========================================================================

    async function fetchCategories() {
        try {
            const resp = await fetch("/api/categories");
            const data = await resp.json();
            if (data && (data.status === true || data.body)) {
                state.categories = data.body || data;
                renderCategoriesScope();
                updateHeaderStatus(true);
            } else {
                showCategoriesError(data.error || "Nie udało się pobrać kategorii");
            }
        } catch (err) {
            showCategoriesError(err.message);
        }
    }

    async function fetchSuggestions() {
        try {
            const resp = await fetch("/api/predefined-queries?count=3");
            if (resp.ok) {
                const list = await resp.json();
                state.suggestions = list;
                renderSuggestions();
            }
        } catch {
            // suggestions are optional
        }
    }

    // =========================================================================
    // 6. UI Renderers
    // =========================================================================

    function updateHeaderStatus(ready) {
        if (ready) {
            el.headerStatusBadge.querySelector(".status-dot").classList.add("ready");
            el.headerStatusText.textContent = t("live_badge");
        } else {
            el.headerStatusBadge.querySelector(".status-dot").classList.remove("ready");
            el.headerStatusText.textContent = t("live_badge_wait");
        }
    }

    function showCategoriesError(msg) {
        el.sourcesScopeLoading.classList.add("hidden");
        el.sourcesScopeError.classList.remove("hidden");
        el.sourcesScopeError.textContent = msg;
    }

    function renderCategoriesScope() {
        if (!state.categories) return;
        el.sourcesScopeLoading.classList.add("hidden");
        el.sourcesScopeDetails.classList.remove("hidden");

        const entries = Object.entries(state.categories);
        const allPages = new Set();
        let catHtml = "";

        entries.forEach(([catName, catInfo]) => {
            const pages = catInfo.category_pages || [];
            const uniqueHosts = new Set();
            pages.forEach((p) => {
                allPages.add(p.main_url);
                uniqueHosts.add(extractHost(p.main_url));
            });

            const displayName = (catInfo.category_info && catInfo.category_info.display_name) || catName;
            const pills = Array.from(uniqueHosts).map((h) => `<span class="scope-page-pill">${h}</span>`).join("");

            catHtml += `
                <div class="scope-category-group">
                    <div class="scope-cat-header">
                        <span class="scope-cat-title">${displayName}</span>
                        <span class="scope-cat-count">${uniqueHosts.size}</span>
                    </div>
                    <div class="scope-pages-pills">${pills}</div>
                </div>
            `;
        });

        el.sourcesScopeCountText.textContent = t("sources_scope_count").replace("{count}", String(allPages.size));
        el.sourcesScopeCategoriesList.innerHTML = catHtml;
    }

    function renderSuggestions() {
        if (!state.suggestions || !state.suggestions.length) {
            el.suggestionsList.innerHTML = "";
            return;
        }
        el.suggestionsList.innerHTML = state.suggestions.map((queryText) => {
            return `<button type="button" class="suggestion-pill" data-query="${encodeURIComponent(queryText)}">${queryText}</button>`;
        }).join("");

        el.suggestionsList.querySelectorAll(".suggestion-pill").forEach((btn) => {
            btn.addEventListener("click", () => {
                const q = decodeURIComponent(btn.getAttribute("data-query"));
                el.queryInput.value = q;
                state.query = q;
                hideQueryError();
            });
        });
    }

    function hideQueryError() {
        el.queryError.classList.add("hidden");
        el.queryError.textContent = "";
    }

    function showQueryError(msg) {
        el.queryError.classList.remove("hidden");
        el.queryError.textContent = msg;
    }

    function setPipelinePhase(phase, stepLabel = "") {
        state.phase = phase;
        if (phase === "idle") {
            el.pipelineStrip.classList.add("hidden");
            el.btnRun.disabled = false;
            return;
        }

        el.pipelineStrip.classList.remove("hidden");
        el.btnRun.disabled = true;

        [el.pipeStep1, el.pipeStep2, el.pipeStep3, el.pipeStep4].forEach((stepEl) => {
            stepEl.classList.remove("active", "done");
        });

        if (phase === "searching") {
            el.pipeStep1.classList.add("done");
            el.pipeStep2.classList.add("active");
            el.pipelineStatusMsg.textContent = stepLabel || t("progress_search_short");
        } else if (phase === "generating") {
            el.pipeStep1.classList.add("done");
            el.pipeStep2.classList.add("done");
            el.pipeStep3.classList.add("done");
            el.pipeStep4.classList.add("active");
            el.pipelineStatusMsg.textContent = stepLabel || t("progress_gen_short");
        } else if (phase === "done") {
            el.pipeStep1.classList.add("done");
            el.pipeStep2.classList.add("done");
            el.pipeStep3.classList.add("done");
            el.pipeStep4.classList.add("done");
            el.pipelineStatusMsg.textContent = t("progress_ready");
            el.btnRun.disabled = false;
        } else if (phase === "error") {
            el.pipelineStrip.classList.add("hidden");
            el.btnRun.disabled = false;
        }
    }

    function hideNotices() {
        el.noticeCard.classList.add("hidden");
        el.apiErrorCard.classList.add("hidden");
    }

    function showNotice(msg) {
        el.noticeCard.classList.remove("hidden");
        el.noticeMsg.textContent = msg;
    }

    function showApiError(msg) {
        el.apiErrorCard.classList.remove("hidden");
        el.apiErrorMsg.textContent = msg || t("api_error");
    }

    // =========================================================================
    // 7. Full Pipeline Execution (Search -> Generate)
    // =========================================================================

    async function runCreatorPipeline() {
        hideNotices();
        hideQueryError();

        const queryText = (el.queryInput.value || "").trim();
        if (!queryText) {
            showQueryError(t("no_query_error"));
            return;
        }
        state.query = queryText;

        if (!state.categories) {
            showApiError("Brak listy kategorii. Odczekaj chwilę na połączenie.");
            return;
        }

        // 1. Search Phase
        setPipelinePhase("searching");

        const sites = extractSitesList(state.categories);
        const numOfResults = deriveNumOfResults(state.lastDays);

        let searchResData = null;
        try {
            const resp = await fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    text_to_search: queryText,
                    num_of_results: numOfResults,
                    number_of_last_days: state.lastDays,
                    sites: sites
                })
            });
            const res = await resp.json();
            if (resp.ok && res.status === true && res.body) {
                searchResData = res.body;
            } else {
                throw new Error(res.error || `HTTP ${resp.status}`);
            }
        } catch (err) {
            setPipelinePhase("error");
            showApiError(err.message);
            return;
        }

        const searchInCategory = searchResData.search_result || {};
        const queryResponseId = searchResData.query_response_id || 0;
        state.searchResult = searchInCategory;
        state.queryResponseId = queryResponseId;

        const totalFound = Object.values(searchInCategory).reduce((sum, list) => sum + (list ? list.length : 0), 0);
        if (totalFound === 0) {
            setPipelinePhase("idle");
            showNotice(t("no_data_found"));
            return;
        }

        // 2. Generation Phase
        setPipelinePhase("generating");

        const newsIds = collectNewsIds(searchInCategory);
        const articleType = buildArticlePrompt(currentLang, state.style);

        let articleData = null;
        try {
            const resp = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_query: queryText,
                    news_ids: newsIds,
                    article_type: articleType,
                    sse_query_response_id: queryResponseId
                })
            });
            const res = await resp.json();
            if (resp.ok && res.status === true && res.body) {
                articleData = res.body;
            } else {
                throw new Error(res.error || `HTTP ${resp.status}`);
            }
        } catch (err) {
            setPipelinePhase("error");
            showApiError(err.message);
            return;
        }

        state.article = articleData;
        state.numberOfNewsUsed = newsIds.length;

        setPipelinePhase("done");
        renderArticle();
        renderSourceMaterial();

        // Collapse query panel into compact bar
        collapseQueryPanel();

        // Scroll to article
        el.articleSection.scrollIntoView({ behavior: "smooth", block: "start" });
    }

    function collapseQueryPanel() {
        el.queryCompactBar.classList.remove("hidden");
        el.queryForm.classList.add("hidden");
        el.compactQueryBtn.textContent = state.query;

        const styleLabel = state.style === "formal" ? t("style_formal") : t("style_simple");
        const dayLabel = state.lastDays === 1 ? t("day_1") : state.lastDays === 2 ? t("day_2") : t("day_7");
        el.compactBadge.textContent = `${styleLabel} · ${dayLabel}`;
    }

    function expandQueryPanel() {
        el.queryCompactBar.classList.add("hidden");
        el.queryForm.classList.remove("hidden");
    }

    // =========================================================================
    // 8. Article Presentation
    // =========================================================================

    function renderArticle() {
        if (!state.article) return;
        el.articleSection.classList.remove("hidden");

        const rawText = state.article.article_str || state.article.article || state.article.new_article || "";
        const parsed = splitMarkdownHeadline(rawText);

        el.articleHeadline.textContent = parsed.headline || state.query;

        const minutes = calculateReadingMinutes(rawText);
        el.readingTimeText.textContent = t("reading_time_long").replace("{minutes}", String(minutes));

        el.sourcesUsedLink.textContent = `${state.numberOfNewsUsed} ${t("sources_used")}`;
        el.articleDateText.textContent = formatTimestamp(state.article.when_generated || new Date().toISOString());

        // Parse markdown body
        if (window.marked && typeof window.marked.parse === "function") {
            el.articleBodyContent.innerHTML = window.marked.parse(parsed.body);
        } else {
            el.articleBodyContent.innerHTML = `<p>${parsed.body}</p>`;
        }

        // Technical details
        el.techTopic.textContent = state.query;
        el.techNewsUsed.textContent = String(state.numberOfNewsUsed);
        el.techModel.textContent = state.article.model_used_to_generate || "—";
        el.techGenTime.textContent = state.article.generation_time !== undefined ? String(state.article.generation_time) : "—";
        el.techWordCount.textContent = String(countWords(rawText));
        el.techWhenGenerated.textContent = formatTimestamp(state.article.when_generated);
    }

    function copyArticleText(btnTextEl) {
        if (!state.article) return;
        const rawText = state.article.article_str || state.article.article || state.article.new_article || "";
        navigator.clipboard.writeText(rawText).then(() => {
            if (btnTextEl) {
                const orig = btnTextEl.textContent;
                btnTextEl.textContent = t("copied");
                setTimeout(() => { btnTextEl.textContent = orig; }, 1800);
            }
        }).catch(() => {});
    }

    function downloadArticleMarkdown() {
        if (!state.article) return;
        const rawText = state.article.article_str || state.article.article || state.article.new_article || "";
        const blob = new Blob([rawText], { type: "text/markdown;charset=utf-8" });
        const url = URL.createObjectURL(blob);
        const a = document.createElement("a");
        a.href = url;
        a.download = `puls-artykul-${Date.now()}.md`;
        a.click();
        URL.revokeObjectURL(url);
    }

    // =========================================================================
    // 9. Source Material (Materiał źródłowy) & Polarity
    // =========================================================================

    function renderSourceMaterial() {
        if (!state.searchResult) return;
        el.sourcesMaterialSection.classList.remove("hidden");

        const searchInCategory = state.searchResult;
        const categories = Object.keys(searchInCategory).filter((cat) => (searchInCategory[cat] || []).length > 0);

        // Build flat ordered rows with sequential citation numbers
        const allRows = [];
        let citation = 1;
        categories.forEach((cat) => {
            (searchInCategory[cat] || []).forEach((item) => {
                allRows.push({
                    citation: citation++,
                    category: cat,
                    item: item
                });
            });
        });

        // Sort by when_crawled desc
        allRows.sort((a, b) => {
            const dateA = (a.item.news_sub_page && a.item.news_sub_page.when_crawled) || "";
            const dateB = (b.item.news_sub_page && b.item.news_sub_page.when_crawled) || "";
            return dateB.localeCompare(dateA);
        });

        el.sourcesCountPill.textContent = String(allRows.length);
        renderPolarityBar(allRows.map((r) => r.item));
        renderCategoryTabs(categories, allRows);
        renderSourceCards(allRows);
    }

    function renderPolarityBar(items) {
        const counts = { positive: 0, negative: 0, ambivalent: 0, unclassified: 0 };
        items.forEach((item) => {
            const pol = item.polarity_3c;
            if (pol && counts[pol] !== undefined) {
                counts[pol]++;
            } else {
                counts.unclassified++;
            }
        });

        const total = items.length;
        el.polarityTotalCount.textContent = String(total);
        if (total === 0) return;

        const segments = [
            { key: "pos", count: counts.positive, label: t("pos") },
            { key: "neg", count: counts.negative, label: t("neg") },
            { key: "amb", count: counts.ambivalent, label: t("amb") },
            { key: "unclass", count: counts.unclassified, label: t("no_polarity") }
        ].filter((s) => s.count > 0);

        // Track bar
        el.polarityBarTrack.innerHTML = segments.map((s) => {
            const pct = (s.count / total) * 100;
            return `<div class="polarity-bar-segment ${s.key}" style="width: ${pct}%" title="${s.label}: ${s.count}"></div>`;
        }).join("");

        // Legend
        el.polarityLegend.innerHTML = segments.map((s) => {
            const pct = Math.round((s.count / total) * 100);
            return `
                <span class="polarity-legend-item">
                    <span class="legend-dot ${s.key}"></span>
                    <span>${s.label}</span>
                    <span class="text-ink-400">${pct}%</span>
                </span>
            `;
        }).join("");
    }

    function renderCategoryTabs(categories, allRows) {
        const tabsHtml = [
            `<button type="button" class="category-tab-btn active" data-category="__all__">${t("all_categories")} (${allRows.length})</button>`
        ];

        categories.forEach((cat) => {
            const count = allRows.filter((r) => r.category === cat).length;
            tabsHtml.push(
                `<button type="button" class="category-tab-btn" data-category="${cat}">${cat} (${count})</button>`
            );
        });

        el.categoryTabsList.innerHTML = tabsHtml.join("");

        el.categoryTabsList.querySelectorAll(".category-tab-btn").forEach((btn) => {
            btn.addEventListener("click", () => {
                el.categoryTabsList.querySelectorAll(".category-tab-btn").forEach((b) => b.classList.remove("active"));
                btn.classList.add("active");
                state.selectedCategory = btn.getAttribute("data-category");
                renderSourceCards(allRows);
            });
        });
    }

    function renderSourceCards(allRows) {
        const filtered = state.selectedCategory === "__all__"
            ? allRows
            : allRows.filter((r) => r.category === state.selectedCategory);

        // Wire View Cards
        el.sourcesWireContainer.innerHTML = filtered.map((row) => {
            const item = row.item;
            const subPage = item.news_sub_page || {};
            const url = subPage.news_url || "";
            const host = extractHost(url);
            const date = formatTimestamp(subPage.when_crawled);
            const pol = item.polarity_3c || "unclassified";
            const polKey = pol === "positive" ? "pos" : pol === "negative" ? "neg" : pol === "ambivalent" ? "amb" : "unclass";
            const polLabel = t(polKey === "unclass" ? "no_polarity" : polKey);

            return `
                <div class="news-wire-card">
                    <div class="card-top">
                        <div class="card-meta">
                            <span class="citation-pill">${row.citation}</span>
                            <span class="card-cat" title="${row.category}">${row.category}</span>
                            <span class="card-date">${date}</span>
                        </div>
                        <p class="card-snippet" title="${item.generated_text || ''}">${item.generated_text || ''}</p>
                    </div>
                    <div class="card-footer">
                        <a href="${url}" target="_blank" rel="noopener" class="card-source-link" title="${url}">
                            <i class="bi bi-box-arrow-up-right me-1"></i>${host}
                        </a>
                        <span class="polarity-tag ${polKey}">● ${polLabel}</span>
                    </div>
                </div>
            `;
        }).join("");

        // List View Items
        el.sourcesListContainer.innerHTML = filtered.map((row) => {
            const item = row.item;
            const subPage = item.news_sub_page || {};
            const url = subPage.news_url || "";
            const host = extractHost(url);
            const date = formatTimestamp(subPage.when_crawled);
            const pol = item.polarity_3c || "unclassified";
            const polKey = pol === "positive" ? "pos" : pol === "negative" ? "neg" : pol === "ambivalent" ? "amb" : "unclass";
            const polLabel = t(polKey === "unclass" ? "no_polarity" : polKey);

            return `
                <div class="news-list-item">
                    <span class="citation-pill">${row.citation}</span>
                    <div class="list-item-content">
                        <div class="list-item-header">
                            <strong class="card-cat">${row.category}</strong>
                            <span class="polarity-tag ${polKey}">● ${polLabel}</span>
                        </div>
                        <p class="list-item-snippet">${item.generated_text || ''}</p>
                        <div class="list-item-footer">
                            <a href="${url}" target="_blank" rel="noopener" class="card-source-link">
                                <i class="bi bi-box-arrow-up-right me-1"></i>${host}
                            </a>
                            <span>${date}</span>
                        </div>
                    </div>
                </div>
            `;
        }).join("");
    }

    // =========================================================================
    // 10. Event Listeners & Initialization
    // =========================================================================

    function initEvents() {
        // Language switcher
        el.langPl.addEventListener("click", () => {
            currentLang = "pl";
            el.langPl.classList.add("active");
            el.langEn.classList.remove("active");
            applyTranslations();
            if (state.article) renderArticle();
            if (state.searchResult) renderSourceMaterial();
        });

        el.langEn.addEventListener("click", () => {
            currentLang = "en";
            el.langEn.classList.add("active");
            el.langPl.classList.remove("active");
            applyTranslations();
            if (state.article) renderArticle();
            if (state.searchResult) renderSourceMaterial();
        });

        // Query input & keyboard shortcut
        el.queryInput.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                runCreatorPipeline();
            }
        });
        el.queryInput.addEventListener("input", hideQueryError);

        // Shuffle predefined questions
        el.btnShuffleSuggestions.addEventListener("click", fetchSuggestions);

        // Style selector
        el.styleSimpleLabel.addEventListener("click", () => {
            state.style = "simple";
            el.styleSimpleLabel.classList.add("active");
            el.styleFormalLabel.classList.remove("active");
        });
        el.styleFormalLabel.addEventListener("click", () => {
            state.style = "formal";
            el.styleFormalLabel.classList.add("active");
            el.styleSimpleLabel.classList.remove("active");
        });

        // Days selector
        el.dayBtns.forEach((btn) => {
            btn.addEventListener("click", () => {
                el.dayBtns.forEach((b) => b.classList.remove("active"));
                btn.classList.add("active");
                state.lastDays = parseInt(btn.getAttribute("data-days"), 10) || 1;
            });
        });

        // Submit buttons
        el.btnRun.addEventListener("click", runCreatorPipeline);
        el.btnRunAgain.addEventListener("click", runCreatorPipeline);
        el.compactQueryBtn.addEventListener("click", expandQueryPanel);
        el.btnNewTopic.addEventListener("click", () => {
            expandQueryPanel();
            el.queryInput.value = "";
            el.queryInput.focus();
        });

        // Article action buttons
        el.btnCopyArticle.addEventListener("click", () => copyArticleText(el.btnCopyText));
        el.btnCopyArticleBottom.addEventListener("click", () => copyArticleText(el.btnCopyArticleBottom.querySelector("span:last-child")));
        el.btnDownloadArticle.addEventListener("click", downloadArticleMarkdown);
        el.btnDownloadArticleBottom.addEventListener("click", downloadArticleMarkdown);

        // View mode buttons (wire / list)
        el.viewWireBtn.addEventListener("click", () => {
            el.viewWireBtn.classList.add("active");
            el.viewListBtn.classList.remove("active");
            el.sourcesWireContainer.classList.remove("hidden");
            el.sourcesListContainer.classList.add("hidden");
        });
        el.viewListBtn.addEventListener("click", () => {
            el.viewListBtn.classList.add("active");
            el.viewWireBtn.classList.remove("active");
            el.sourcesListContainer.classList.remove("hidden");
            el.sourcesWireContainer.classList.add("hidden");
        });
    }

    // Init App
    document.addEventListener("DOMContentLoaded", () => {
        initEvents();
        applyTranslations();
        fetchCategories();
        fetchSuggestions();
    });

})();
