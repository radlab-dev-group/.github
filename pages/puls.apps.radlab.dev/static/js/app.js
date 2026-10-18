/**
 * Puls Informacji by RadLab — Klient JavaScript
 * Obsługa dynamicznego interfejsu, komunikacji z API Flaska i renderowania wyników.
 */

document.addEventListener("DOMContentLoaded", () => {
    // --- Elementy DOM ---
    const queryInput = document.getElementById("query-input");
    const queryError = document.getElementById("query-error");
    const btnSubmit = document.getElementById("btn-submit-creator");
    const btnSubmitSpinner = document.getElementById("btn-submit-spinner");
    const btnSubmitText = document.getElementById("btn-submit-text");
    const btnShuffleSuggestions = document.getElementById("btn-shuffle-suggestions");
    const suggestionsList = document.getElementById("suggestions-list");

    const introHero = document.getElementById("intro-hero");
    const queryPanel = document.getElementById("query-panel");
    const queryBarCompact = document.getElementById("query-bar-compact");
    const compactQueryTitle = document.getElementById("compact-query-title");
    const compactMetaPill = document.getElementById("compact-meta-pill");
    const btnCompactNewTopic = document.getElementById("btn-compact-new-topic");
    const btnCompactRunAgain = document.getElementById("btn-compact-run-again");

    const sourcesLiveBadge = document.getElementById("sources-live-badge");
    const sourcesLiveDot = document.getElementById("sources-live-dot");
    const sourcesLiveText = document.getElementById("sources-live-text");
    const sourcesLoadingMsg = document.getElementById("sources-loading-msg");
    const sourcesErrorMsg = document.getElementById("sources-error-msg");
    const sourcesDetails = document.getElementById("sources-details");
    const sourcesCountLabel = document.getElementById("sources-count-label");
    const sourcesCategoriesContainer = document.getElementById("sources-categories-container");

    const pipelinePanel = document.getElementById("pipeline-panel");
    const pipelineStatusText = document.getElementById("pipeline-status-text");
    const appNotice = document.getElementById("app-notice");

    const articleSection = document.getElementById("article-section");
    const articleHeadline = document.getElementById("article-headline");
    const articleReadingTime = document.getElementById("article-reading-time");
    const articleSourcesLink = document.getElementById("article-sources-link");
    const articleDate = document.getElementById("article-date");
    const articleBodyContent = document.getElementById("article-body-content");
    const techTopic = document.getElementById("tech-topic");
    const techNewsCount = document.getElementById("tech-news-count");
    const techModel = document.getElementById("tech-model");
    const techTime = document.getElementById("tech-time");
    const techWords = document.getElementById("tech-words");
    const techWhen = document.getElementById("tech-when");

    const sourcesResults = document.getElementById("sources-results");
    const sourcesResultsCount = document.getElementById("sources-results-count");
    const polarityTotalCount = document.getElementById("polarity-total-count");
    const polBarPos = document.getElementById("pol-bar-pos");
    const polBarNeg = document.getElementById("pol-bar-neg");
    const polBarAmb = document.getElementById("pol-bar-amb");
    const polPctPos = document.getElementById("pol-pct-pos");
    const polPctNeg = document.getElementById("pol-pct-neg");
    const polPctAmb = document.getElementById("pol-pct-amb");
    const categoryFilterTabs = document.getElementById("category-filter-tabs");
    const sourcesWireScroller = document.getElementById("sources-wire-scroller");
    const sourcesListView = document.getElementById("sources-list-view");
    const sourcesWireView = document.getElementById("sources-wire-view");
    const btnViewWire = document.getElementById("btn-view-wire");
    const btnViewList = document.getElementById("btn-view-list");

    // --- Stan aplikacji ---
    let categoriesData = null;
    let selectedStyle = "simple";
    let selectedDays = 1;
    let currentRawArticleText = "";
    let currentSearchResults = null;
    let currentViewMode = "wire";
    let activeFilterCategory = "__all__";

    const t = (key) => window.I18N?.[key] || key;

    // =========================================================================
    // 1. Inicjalizacja i pobranie kategorii
    // =========================================================================

    async function loadCategories() {
        try {
            const resp = await fetch("/api/categories");
            const data = await resp.json();

            if (data.status && data.body) {
                categoriesData = data.body;
                renderSourcesPanel(categoriesData);

                // Zaktualizuj plakietkę w nagłówku
                if (sourcesLiveBadge) {
                    sourcesLiveBadge.classList.remove("bg-sun-100", "text-sun-700");
                    sourcesLiveBadge.classList.add("bg-accent-50", "text-accent-700");
                    sourcesLiveDot.className = "h-2 w-2 rounded-full bg-accent-600";
                    sourcesLiveText.textContent = t("live_badge");
                }
            } else {
                showSourcesError(data.error || t("categories_error"));
            }
        } catch (err) {
            showSourcesError(err.message || t("categories_error"));
        }
    }

    function showSourcesError(msg) {
        if (sourcesLoadingMsg) sourcesLoadingMsg.classList.add("hidden");
        if (sourcesErrorMsg) {
            sourcesErrorMsg.textContent = msg;
            sourcesErrorMsg.classList.remove("hidden");
        }
    }

    function renderSourcesPanel(categories) {
        if (sourcesLoadingMsg) sourcesLoadingMsg.classList.add("hidden");
        if (!sourcesDetails || !sourcesCategoriesContainer) return;

        const entries = Object.entries(categories);
        const allUrls = new Set();
        entries.forEach(([, info]) => {
            (info.category_pages || []).forEach((p) => {
                if (p.main_url) allUrls.add(p.main_url);
            });
        });

        if (sourcesCountLabel) {
            sourcesCountLabel.textContent = (t("sources_scope_count") || "Przeszukiwane serwisy: {count}")
                .replace("{count}", allUrls.size);
        }

        sourcesCategoriesContainer.innerHTML = "";
        entries.forEach(([catName, info]) => {
            const displayName = info.category_info?.display_name || catName;
            const seen = new Set();
            const uniquePages = (info.category_pages || []).filter((p) => {
                if (!p.main_url || seen.has(p.main_url)) return false;
                seen.add(p.main_url);
                return true;
            });

            const catEl = document.createElement("div");
            catEl.className = "group";
            catEl.innerHTML = `
                <div class="flex items-center justify-between">
                    <span class="font-editorial text-base font-semibold text-ink-950">${escapeHtml(displayName)}</span>
                    <span class="text-xs text-ink-400">${uniquePages.length}</span>
                </div>
                <div class="mt-1.5 flex flex-wrap gap-1.5">
                    ${uniquePages.map((p) => `
                        <span class="inline-flex max-w-full items-center gap-1.5 rounded-full border border-paper-300 bg-paper-100 px-2.5 py-1 text-xs text-ink-700 [overflow-wrap:anywhere]">
                            ${escapeHtml(extractHostname(p.main_url))}
                        </span>
                    `).join("")}
                </div>
            `;
            sourcesCategoriesContainer.appendChild(catEl);
        });

        if (sourcesDetails) sourcesDetails.classList.remove("hidden");
    }

    // =========================================================================
    // 2. Obsługa predefiniowanych pytań i losowania
    // =========================================================================

    if (btnShuffleSuggestions) {
        btnShuffleSuggestions.addEventListener("click", async () => {
            try {
                const resp = await fetch("/api/predefined-queries");
                const data = await resp.json();
                if (data.queries && suggestionsList) {
                    suggestionsList.innerHTML = "";
                    data.queries.forEach((q) => {
                        const btn = document.createElement("button");
                        btn.type = "button";
                        btn.className = "btn-suggestion max-w-full rounded-full border border-paper-300 bg-paper-50 px-4 py-2 text-left text-sm leading-snug text-ink-700 transition hover:border-accent-200 hover:bg-accent-50/60 hover:text-ink-950";
                        btn.dataset.text = q;
                        btn.textContent = q;
                        btn.addEventListener("click", () => setQueryValue(q));
                        suggestionsList.appendChild(btn);
                    });
                }
            } catch (err) {
                console.error("Błąd losowania pytań:", err);
            }
        });
    }

    function setupSuggestionButtons() {
        document.querySelectorAll(".btn-suggestion").forEach((btn) => {
            btn.addEventListener("click", () => {
                const text = btn.dataset.text || btn.textContent.trim();
                setQueryValue(text);
            });
        });
    }

    function setQueryValue(val) {
        if (!queryInput) return;
        queryInput.value = val;
        queryInput.focus();
        if (queryError) queryError.classList.add("hidden");
    }

    // =========================================================================
    // 3. Wybór stylu i zakresu dni
    // =========================================================================

    document.querySelectorAll(".style-card").forEach((card) => {
        card.addEventListener("click", () => {
            document.querySelectorAll(".style-card").forEach((c) => {
                c.classList.remove("border-accent-600", "bg-accent-50", "text-accent-800");
                c.classList.add("border-paper-300", "bg-paper-50", "text-ink-700");
            });
            card.classList.remove("border-paper-300", "bg-paper-50", "text-ink-700");
            card.classList.add("border-accent-600", "bg-accent-50", "text-accent-800");
            selectedStyle = card.dataset.value || "simple";
            const radio = card.querySelector("input[type=radio]");
            if (radio) radio.checked = true;
        });
    });

    document.querySelectorAll(".btn-last-days").forEach((btn) => {
        btn.addEventListener("click", () => {
            document.querySelectorAll(".btn-last-days").forEach((b) => {
                b.classList.remove("bg-paper-50", "font-semibold", "text-accent-800", "shadow-sm");
                b.classList.add("text-ink-500");
                b.setAttribute("aria-pressed", "false");
            });
            btn.classList.remove("text-ink-500");
            btn.classList.add("bg-paper-50", "font-semibold", "text-accent-800", "shadow-sm");
            btn.setAttribute("aria-pressed", "true");
            selectedDays = parseInt(btn.dataset.days || "1", 10);
        });
    });

    // Skrót klawiszowy Ctrl+Enter
    if (queryInput) {
        queryInput.addEventListener("keydown", (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === "Enter") {
                e.preventDefault();
                handleFormSubmit();
            }
        });
    }

    if (btnSubmit) {
        btnSubmit.addEventListener("click", (e) => {
            e.preventDefault();
            handleFormSubmit();
        });
    }

    // =========================================================================
    // 4. Pipeline i proces tworzenia artykułu
    // =========================================================================

    function setPipelinePhase(phase, stepText) {
        if (!pipelinePanel) return;
        pipelinePanel.classList.toggle("hidden", phase === "done");

        const steps = [
            document.getElementById("pipeline-step-1"),
            document.getElementById("pipeline-step-2"),
            document.getElementById("pipeline-step-3"),
            document.getElementById("pipeline-step-4"),
        ];

        let activeIdx = 0;
        if (phase === "searching") activeIdx = 1;
        else if (phase === "generating") activeIdx = 3;
        else if (phase === "done") activeIdx = 4;

        steps.forEach((step, idx) => {
            if (!step) return;
            const numEl = step.querySelector(".step-num");
            const labelEl = step.querySelector(".step-label");

            if (idx <= activeIdx) {
                numEl.className = "step-num flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold bg-accent-700 text-white";
                labelEl.className = "step-label truncate text-sm font-medium text-ink-900";
                if (phase === "done") numEl.textContent = "✓";
                else numEl.textContent = String(idx + 1);
            } else {
                numEl.className = "step-num flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-xs font-semibold bg-paper-300 text-ink-500";
                labelEl.className = "step-label truncate text-sm text-ink-400";
                numEl.textContent = String(idx + 1);
            }
            if (phase === "generating" && idx === activeIdx) {
                numEl.classList.add("motion-safe:animate-pulse");
            }
        });

        if (pipelineStatusText && stepText) {
            pipelineStatusText.textContent = stepText;
        }
    }

    function setBusy(isBusy) {
        if (btnSubmit) btnSubmit.disabled = isBusy;
        if (btnSubmitSpinner) btnSubmitSpinner.classList.toggle("hidden", !isBusy);
        if (btnCompactRunAgain) btnCompactRunAgain.disabled = isBusy;
    }

    async function handleFormSubmit() {
        const query = (queryInput?.value || "").trim();
        if (!query) {
            if (queryError) {
                queryError.textContent = t("no_query_error");
                queryError.classList.remove("hidden");
            }
            queryInput?.focus();
            return;
        }

        if (queryError) queryError.classList.add("hidden");
        if (appNotice) appNotice.classList.add("hidden");
        if (articleSection) articleSection.classList.add("hidden");
        if (sourcesResults) sourcesResults.classList.add("hidden");
        const articleSkeleton = document.getElementById("article-skeleton");
        if (articleSkeleton) articleSkeleton.classList.add("hidden");

        setBusy(true);

        // KROK 1: Wyszukiwanie newsów
        setPipelinePhase("searching", t("progress_search_short"));

        // Wyciągnij listę stron
        const sites = [];
        if (categoriesData) {
            Object.values(categoriesData).forEach((cat) => {
                (cat.category_pages || []).forEach((p) => {
                    if (p.main_url) sites.push(p.main_url);
                });
            });
        }

        try {
            const searchResp = await fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    query: query,
                    last_days: selectedDays,
                    num_of_results: 0,
                    sites: sites,
                }),
            });

            const searchData = await searchResp.json();
            if (!searchData.status || !searchData.body) {
                throw new Error(searchData.error || t("api_error"));
            }

            const searchInCategory = searchData.body.search_result || {};
            const queryResponseId = searchData.body.query_response_id || 0;
            currentSearchResults = searchInCategory;

            // Sprawdź czy cokolwiek znaleziono
            const allItems = [];
            Object.values(searchInCategory).forEach((list) => {
                if (Array.isArray(list)) allItems.push(...list);
            });

            if (allItems.length === 0) {
                setBusy(false);
                setPipelinePhase("idle", "");
                if (appNotice) {
                    appNotice.textContent = t("no_data_found");
                    appNotice.classList.remove("hidden");
                }
                return;
            }

            // KROK 2: Generowanie artykułu
            renderSearchResults(searchInCategory);
            setPipelinePhase("generating", t("progress_gen_short"));
            if (articleSkeleton) articleSkeleton.classList.remove("hidden");

            const newsIds = [];
            allItems.forEach((item) => {
                const id = item.id ?? item.news_id;
                if (typeof id === "number") newsIds.push(id);
            });

            const genResp = await fetch("/api/generate", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    user_query: query,
                    news_ids: newsIds,
                    style: selectedStyle,
                    lang: window.CURRENT_LANG || "pl",
                    sse_query_response_id: queryResponseId,
                }),
            });

            const genData = await genResp.json();
            if (!genData.status || !genData.body) {
                throw new Error(genData.error || t("api_error"));
            }

            const articleObj = genData.body;
            currentRawArticleText = articleObj.article_str || articleObj.article || articleObj.new_article || "";

            // Wyrenderuj artykuł
            renderArticle(query, articleObj, newsIds.length);

            // Zwiń panel formularza do wersji kompaktowej
            collapseToCompact(query);

            setPipelinePhase("done", t("progress_ready"));

            // Płynne przewinięcie do artykułu
            if (articleSection) {
                articleSection.scrollIntoView({ behavior: "smooth", block: "start" });
            }

        } catch (err) {
            console.error("Błąd w procesie generowania:", err);
            if (appNotice) {
                appNotice.textContent = err.message || t("api_error");
                appNotice.classList.remove("hidden");
            }
            setPipelinePhase("error", "");
        } finally {
            if (articleSkeleton) articleSkeleton.classList.add("hidden");
            setBusy(false);
        }
    }

    // =========================================================================
    // 5. Renderowanie artykułu
    // =========================================================================

    function renderArticle(query, articleObj, newsCount) {
        if (!articleSection) return;

        if (articleHeadline) {
            articleHeadline.textContent = articleObj.headline || t("article_title");
        }

        if (articleReadingTime) {
            const minutes = articleObj.reading_minutes || 1;
            articleReadingTime.textContent = (t("reading_time_long") || "Przeczytasz w ok. {minutes} min").replace("{minutes}", minutes);
        }

        if (articleSourcesLink) {
            articleSourcesLink.textContent = `${newsCount} ${t("sources_used")}`;
        }

        if (articleDate) {
            articleDate.textContent = articleObj.formatted_when || articleObj.when_generated || "—";
        }

        if (articleBodyContent) {
            articleBodyContent.innerHTML = articleObj.rendered_html || `<p>${escapeHtml(currentRawArticleText)}</p>`;
        }

        // Szczegóły techniczne
        if (techTopic) techTopic.textContent = query;
        if (techNewsCount) techNewsCount.textContent = newsCount;
        if (techModel) techModel.textContent = articleObj.model_used_to_generate || "—";
        if (techTime) techTime.textContent = articleObj.generation_time ? `${articleObj.generation_time}s` : "—";
        if (techWords) techWords.textContent = articleObj.word_count || "—";
        if (techWhen) techWhen.textContent = articleObj.formatted_when || articleObj.when_generated || "—";

        articleSection.classList.remove("hidden");
    }

    // =========================================================================
    // 6. Renderowanie źródeł i wykresu polaryzacji
    // =========================================================================

    function renderSearchResults(searchInCategory) {
        if (!sourcesResults) return;

        const categories = Object.keys(searchInCategory).filter(
            (c) => searchInCategory[c]?.length > 0
        );

        if (categories.length === 0) {
            sourcesResults.classList.add("hidden");
            return;
        }

        // Zbuduj płaską listę rekordów
        const allRows = [];
        let citation = 1;
        categories.forEach((cat) => {
            (searchInCategory[cat] || []).forEach((item) => {
                allRows.push({
                    citation: citation++,
                    category: cat,
                    item: item,
                });
            });
        });

        // Posortuj od najnowszych
        allRows.sort((a, b) =>
            (b.item.news_sub_page?.when_crawled || "").localeCompare(
                a.item.news_sub_page?.when_crawled || ""
            )
        );

        if (sourcesResultsCount) sourcesResultsCount.textContent = allRows.length;
        if (polarityTotalCount) polarityTotalCount.textContent = allRows.length;

        // Oblicz polaryzację
        let posCount = 0;
        let negCount = 0;
        let ambCount = 0;

        allRows.forEach((row) => {
            const pol = row.item.polarity_3c;
            if (pol === "positive") posCount++;
            else if (pol === "negative") negCount++;
            else ambCount++;
        });

        const total = allRows.length || 1;
        const posPct = Math.round((posCount / total) * 100);
        const negPct = Math.round((negCount / total) * 100);
        const ambPct = Math.round((ambCount / total) * 100);

        if (polBarPos) polBarPos.style.width = `${posPct}%`;
        if (polBarNeg) polBarNeg.style.width = `${negPct}%`;
        if (polBarAmb) polBarAmb.style.width = `${ambPct}%`;

        if (polPctPos) polPctPos.textContent = `${posPct}%`;
        if (polPctNeg) polPctNeg.textContent = `${negPct}%`;
        if (polPctAmb) polPctAmb.textContent = `${ambPct}%`;

        // Renderuj zakładki kategorii
        if (categoryFilterTabs) {
            categoryFilterTabs.innerHTML = `
                <button type="button" class="btn-cat-filter active rounded-full border border-accent-600 bg-accent-50 px-3 py-1.5 text-[13px] text-accent-800 transition" data-category="__all__" aria-pressed="true">
                    ${t("all_categories")}<span class="ml-1.5 text-xs opacity-70">${allRows.length}</span>
                </button>
            `;
            categories.forEach((cat) => {
                const btn = document.createElement("button");
                btn.type = "button";
                btn.className = "btn-cat-filter rounded-full border border-paper-300 bg-paper-50 px-3 py-1.5 text-[13px] text-ink-500 transition hover:border-accent-200 hover:text-accent-800";
                btn.dataset.category = cat;
                btn.setAttribute("aria-pressed", "false");
                btn.innerHTML = `${escapeHtml(cat)}<span class="ml-1.5 text-xs opacity-70">${searchInCategory[cat].length}</span>`;
                categoryFilterTabs.appendChild(btn);
            });

            // Podepnij zdarzenia pod zakładki
            categoryFilterTabs.querySelectorAll(".btn-cat-filter").forEach((btn) => {
                btn.addEventListener("click", () => {
                    categoryFilterTabs.querySelectorAll(".btn-cat-filter").forEach((b) => {
                        b.className = "btn-cat-filter rounded-full border border-paper-300 bg-paper-50 px-3 py-1.5 text-[13px] text-ink-500 transition hover:border-accent-200 hover:text-accent-800";
                        b.setAttribute("aria-pressed", "false");
                    });
                    btn.className = "btn-cat-filter active rounded-full border border-accent-600 bg-accent-50 px-3 py-1.5 text-[13px] text-accent-800 transition";
                    btn.setAttribute("aria-pressed", "true");
                    activeFilterCategory = btn.dataset.category || "__all__";
                    renderFilteredSources(allRows, activeFilterCategory);
                });
            });
        }

        renderFilteredSources(allRows, "__all__");
        sourcesResults.classList.remove("hidden");
    }

    function renderFilteredSources(allRows, selectedCat) {
        const rows = selectedCat === "__all__"
            ? allRows
            : allRows.filter((r) => r.category === selectedCat);

        // Widok Wire (suwak poziomy)
        if (sourcesWireScroller) {
            sourcesWireScroller.innerHTML = "";
            rows.forEach((r) => {
                const item = r.item;
                const polBadge = getPolarityBadge(item.polarity_3c, true);
                const url = item.news_sub_page?.news_url || "#";
                const host = extractHostname(url);
                const crawled = formatCrawled(item.news_sub_page?.when_crawled);

                const card = document.createElement("article");
                card.className = "group flex w-[300px] shrink-0 snap-start flex-col rounded-2xl border border-paper-300 bg-paper-50 p-5 transition hover:-translate-y-0.5 hover:border-accent-200 hover:shadow-md";
                card.innerHTML = `
                    <div class="mb-3 flex items-center gap-2">
                        <span class="inline-flex h-6 w-6 items-center justify-center rounded-full bg-paper-200 text-[11px] font-semibold text-ink-700">${r.citation}</span>
                        <span class="truncate text-xs font-medium text-ink-700">${escapeHtml(host)}</span>
                        <span class="ml-auto text-xs">${polBadge}</span>
                    </div>
                    <p class="line-clamp-5 font-editorial text-[15px] leading-relaxed text-ink-700">${escapeHtml(item.generated_text || "")}</p>
                    <div class="mt-auto flex items-center justify-between gap-2 pt-4">
                        <span class="text-xs text-ink-400">${escapeHtml(crawled)}</span>
                        <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" class="shrink-0 text-xs font-medium text-accent-700 underline-offset-4 transition hover:text-accent-800 hover:underline">
                            ${t("open_source")} ↗
                        </a>
                    </div>
                `;
                sourcesWireScroller.appendChild(card);
            });
        }

        // Widok Listy (pionowy)
        if (sourcesListView) {
            sourcesListView.innerHTML = "";
            rows.forEach((r) => {
                const item = r.item;
                const polBadge = getPolarityBadge(item.polarity_3c);
                const url = item.news_sub_page?.news_url || "#";
                const host = extractHostname(url);
                const crawled = formatCrawled(item.news_sub_page?.when_crawled);

                const row = document.createElement("div");
                row.className = "group flex items-start gap-4 bg-paper-50 px-4 py-4 transition hover:bg-paper-200/60 sm:px-5";
                row.innerHTML = `
                    <span class="mt-0.5 inline-flex h-6 w-6 shrink-0 items-center justify-center rounded-full bg-paper-200 text-[11px] font-semibold text-ink-700">${r.citation}</span>
                    <div class="min-w-0 flex-1">
                        <div class="flex flex-wrap items-center gap-2 text-xs text-ink-400">
                            <span class="font-medium text-ink-700">${escapeHtml(host)}</span>
                            <span>·</span>
                            <span>${escapeHtml(crawled)}</span>
                            <span>·</span>
                            <span>${polBadge}</span>
                        </div>
                        <p class="mt-1.5 line-clamp-2 font-editorial text-[15px] leading-relaxed text-ink-700">
                            ${escapeHtml(item.generated_text || "")}
                        </p>
                    </div>
                    <a href="${escapeHtml(url)}" target="_blank" rel="noopener noreferrer" aria-label="${t("open_source")}: ${escapeHtml(host)}" class="shrink-0 rounded-full border border-paper-300 px-3 py-1.5 text-sm text-accent-700 transition hover:border-accent-200 hover:bg-accent-50 hover:text-accent-800">
                        ↗
                    </a>
                `;
                sourcesListView.appendChild(row);
            });
        }
    }

    // Przełącznik Wire / List
    if (btnViewWire && btnViewList) {
        btnViewWire.addEventListener("click", () => {
            currentViewMode = "wire";
            btnViewWire.className = "rounded-full px-3.5 py-1.5 text-sm font-medium transition bg-paper-50 text-accent-800 shadow-sm";
            btnViewList.className = "rounded-full px-3.5 py-1.5 text-sm transition text-ink-500 hover:text-ink-950";
            if (sourcesWireView) sourcesWireView.classList.remove("hidden");
            if (sourcesListView) sourcesListView.classList.add("hidden");
        });

        btnViewList.addEventListener("click", () => {
            currentViewMode = "list";
            btnViewList.className = "rounded-full px-3.5 py-1.5 text-sm font-medium transition bg-paper-50 text-accent-800 shadow-sm";
            btnViewWire.className = "rounded-full px-3.5 py-1.5 text-sm transition text-ink-500 hover:text-ink-950";
            if (sourcesListView) sourcesListView.classList.remove("hidden");
            if (sourcesWireView) sourcesWireView.classList.add("hidden");
        });
    }

    // =========================================================================
    // 7. Zwijanie i rozwijanie edytora pytań
    // =========================================================================

    function collapseToCompact(query) {
        if (introHero) introHero.classList.add("hidden");
        if (queryPanel) queryPanel.classList.add("hidden");
        if (queryBarCompact) {
            if (compactQueryTitle) compactQueryTitle.textContent = query;
            if (compactMetaPill) {
                const styleName = selectedStyle === "simple" ? t("style_simple") : t("style_formal");
                const daysName = t(`day_${selectedDays}`) || `${selectedDays} dni`;
                compactMetaPill.textContent = `${styleName} · ${daysName}`;
            }
            queryBarCompact.classList.remove("hidden");
        }
    }

    function expandToFull() {
        if (queryBarCompact) queryBarCompact.classList.add("hidden");
        if (queryPanel) queryPanel.classList.remove("hidden");
        queryInput?.focus();
    }

    if (compactQueryTitle) compactQueryTitle.addEventListener("click", expandToFull);
    if (btnCompactNewTopic) btnCompactNewTopic.addEventListener("click", () => {
        currentRawArticleText = "";
        currentSearchResults = null;
        activeFilterCategory = "__all__";
        if (articleSection) articleSection.classList.add("hidden");
        if (sourcesResults) sourcesResults.classList.add("hidden");
        if (pipelinePanel) pipelinePanel.classList.add("hidden");
        if (appNotice) appNotice.classList.add("hidden");
        if (articleHeadline) articleHeadline.textContent = "";
        if (articleBodyContent) articleBodyContent.replaceChildren();
        if (sourcesWireScroller) sourcesWireScroller.replaceChildren();
        if (sourcesListView) sourcesListView.replaceChildren();
        if (categoryFilterTabs) categoryFilterTabs.replaceChildren();
        expandToFull();
        if (queryInput) {
            queryInput.value = "";
            queryInput.focus();
        }
    });
    if (btnCompactRunAgain) btnCompactRunAgain.addEventListener("click", handleFormSubmit);

    // =========================================================================
    // 8. Kopiowanie i pobieranie artykułu
    // =========================================================================

    document.querySelectorAll(".btn-copy-article").forEach((btn) => {
        btn.addEventListener("click", async () => {
            if (!currentRawArticleText) return;
            try {
                await navigator.clipboard.writeText(currentRawArticleText);
                const originalText = btn.textContent;
                btn.textContent = `✓ ${t("copied")}`;
                setTimeout(() => {
                    btn.textContent = originalText;
                }, 2000);
            } catch (err) {
                console.warn("Schowek niedostępny:", err);
            }
        });
    });

    document.querySelectorAll(".btn-download-article").forEach((btn) => {
        btn.addEventListener("click", () => {
            if (!currentRawArticleText) return;
            const blob = new Blob([currentRawArticleText], { type: "text/markdown;charset=utf-8" });
            const url = URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.href = url;
            a.download = `puls-artykul-${Date.now()}.md`;
            a.click();
            URL.revokeObjectURL(url);
        });
    });

    // =========================================================================
    // 9. Pomocniki formatowania i bezpieczeństwa
    // =========================================================================

    function escapeHtml(str) {
        if (!str) return "";
        return String(str)
            .replace(/&/g, "&amp;")
            .replace(/</g, "&lt;")
            .replace(/>/g, "&gt;")
            .replace(/"/g, "&quot;")
            .replace(/'/g, "&#039;");
    }

    function extractHostname(url) {
        if (!url) return "—";
        try {
            return new URL(url).hostname;
        } catch {
            return url;
        }
    }

    function formatCrawled(dateStr) {
        if (!dateStr) return "—";
        return String(dateStr).split(".")[0].replace("T", " ");
    }

    function getPolarityBadge(polarity, dotOnly = false) {
        const meta = {
            positive: { key: "pos", color: "text-emerald-700", dot: "bg-emerald-600" },
            negative: { key: "neg", color: "text-rose-700", dot: "bg-rose-600" },
            ambivalent: { key: "amb", color: "text-ink-500", dot: "bg-paper-400" },
        }[polarity] || { key: "no_polarity", color: "text-ink-400", dot: "bg-ink-400" };
        return dotOnly
            ? `<span class="block h-2 w-2 shrink-0 rounded-full ${meta.dot}" title="${t(meta.key)}" role="img" aria-label="${t(meta.key)}"></span>`
            : `<span class="${meta.color}">${t(meta.key)}</span>`;
    }

    // Inicjalizacja
    setupSuggestionButtons();
    loadCategories();
});
