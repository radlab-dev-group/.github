/**
 * Radar Informacji — Reader Edition
 * Front-end: pobieranie podsumowań i renderowanie w czytelnym, jednokolumnowym układzie.
 */

const API = {
    base: window.location.origin,
    async summary(dateStr) {
        const r = await fetch(`${this.base}/api/summary?date=${encodeURIComponent(dateStr)}`);
        if (!r.ok) { const b = await r.json().catch(() => ({})); throw new Error(b.error || `HTTP ${r.status}`); }
        return r.json();
    },
    async dates() {
        const r = await fetch(`${this.base}/api/dates`);
        if (!r.ok) return [];
        const b = await r.json(); return b.dates || [];
    },
    async status() {
        try { const r = await fetch(`${this.base}/api/status`); if (!r.ok) return null; return r.json(); } catch { return null; }
    },
};

/* ====== Helpers ====== */
function escapeHtml(s) {
    if (!s) return '';
    const d = document.createElement('div'); d.textContent = s; return d.innerHTML;
}

const PL_MONTHS = ['stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia'];
const PL_WEEKDAYS = ['niedziela','poniedziałek','wtorek','środa','czwartek','piątek','sobota'];

function parseDate(ds) {
    const d = new Date(ds + 'T00:00:00');
    return isNaN(d) ? null : d;
}
function formatDatePl(ds) {
    const d = parseDate(ds);
    if (!d) return ds;
    return `${d.getDate()} ${PL_MONTHS[d.getMonth()]} ${d.getFullYear()}`;
}
function formatWeekdayPl(ds) {
    const d = parseDate(ds);
    if (!d) return '';
    const w = PL_WEEKDAYS[d.getDay()];
    return w.charAt(0).toUpperCase() + w.slice(1);
}
function todayIso() {
    const t = new Date();
    return `${t.getFullYear()}-${String(t.getMonth() + 1).padStart(2, '0')}-${String(t.getDate()).padStart(2, '0')}`;
}
function addDays(ds, n) {
    const parts = ds.split('-').map(Number);
    const d = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + n));
    return d.toISOString().split('T')[0];
}
/** Ostatni dzień, dla którego istnieje wydanie — radar podsumowuje dni poprzedzające. */
function latestIso() {
    return addDays(todayIso(), -1);
}
/** Względna etykieta dnia: „Wczoraj”, „Przedwczoraj” lub nazwa dnia tygodnia. */
function relativeDayLabel(ds) {
    const today = todayIso();
    if (ds === addDays(today, -1)) return 'Wczoraj';
    if (ds === addDays(today, -2)) return 'Przedwczoraj';
    const d = parseDate(ds);
    return d ? `${formatWeekdayPl(ds)} ${d.getDate()}.${String(d.getMonth() + 1).padStart(2, '0')}` : ds;
}

/** Polska odmiana rzeczownika po liczebniku: plural(3, 'artykuł', 'artykuły', 'artykułów') */
function plural(n, one, few, many) {
    n = Math.abs(n);
    if (n === 1) return `${n} ${one}`;
    const m10 = n % 10, m100 = n % 100;
    if (m10 >= 2 && m10 <= 4 && !(m100 >= 12 && m100 <= 14)) return `${n} ${few}`;
    return `${n} ${many}`;
}

function getDominantPolarity(p3c) {
    if (!p3c) return 'ambivalent';
    let mx = -1, k = 'ambivalent';
    for (const [k2, v] of Object.entries(p3c)) { if (v > mx) { mx = v; k = k2; } }
    return k;
}
const MOOD_LABEL = { positive: 'Dobre wieści', negative: 'Trudny temat', ambivalent: 'Neutralnie' };
const MOOD_COLOR = { positive: 'var(--positive)', negative: 'var(--negative)', ambivalent: 'var(--ambivalent)' };

function renderMarkdown(md) {
    if (!md) return '';
    marked.setOptions({ breaks: true, gfm: true });
    return marked.parse(md);
}

function hostnameOf(u) {
    try { return new URL(u).hostname.replace(/^www\./, ''); } catch { return ''; }
}

/* ====== Bookmarks (localStorage) ====== */
function getBookmarks() { try { return JSON.parse(localStorage.getItem('iv_bookmarks') || '[]'); } catch { return []; } }
function saveBookmarks(b) { localStorage.setItem('iv_bookmarks', JSON.stringify(b)); }
function isBookmarked(key) { return getBookmarks().some(b => b.key === key); }
function toggleBookmark(key, data) {
    let b = getBookmarks();
    const idx = b.findIndex(x => x.key === key);
    if (idx >= 0) { b.splice(idx, 1); } else { b.push({ key, ...data, saved: new Date().toISOString() }); }
    saveBookmarks(b);
}

let allClusters = [];
let currentDate = null;

/* ====== Próg „tematu dnia” — górny kwartyl liczby źródeł ====== */
function computeHotThreshold(clusters) {
    const counts = clusters.map(c => (c.news_urls || []).length).sort((a, b) => a - b);
    if (counts.length < 4) return Infinity;
    const qIdx = Math.ceil(counts.length * 0.75) - 1;
    return Math.max(counts[qIdx], 2);
}

/* ====== Nagłówek wydania: data, zdanie-podsumowanie, nastrój ====== */
function renderEditionHeader(dateStr, stats, clustersCount) {
    const elDate = document.getElementById('editionDate');
    const elWeek = document.getElementById('editionWeekday');
    const elIntro = document.getElementById('editionIntro');
    if (elDate) elDate.textContent = formatDatePl(dateStr);
    if (elWeek) elWeek.textContent = formatWeekdayPl(dateStr);

    if (!stats) {
        if (elIntro) elIntro.textContent = 'Na ten dzień nie mamy jeszcze podsumowania. Spróbuj wybrać inny dzień.';
        renderMood(null);
        return;
    }
    const total = stats.total_articles || 0;
    const topics = stats.total_clusters || clustersCount || 0;
    const domains = stats.unique_domains || 0;
    const pol = stats.polarity || {};
    const pos = pol.positive || 0, neg = pol.negative || 0, amb = pol.ambivalent || 0;
    const sum = pos + neg + amb;

    let moodSentence = '';
    if (sum > 0) {
        const posShare = pos / sum, negShare = neg / sum;
        if (negShare > 0.5) moodSentence = 'Tego dnia w mediach przeważały trudne wiadomości.';
        else if (posShare > 0.5) moodSentence = 'Tego dnia w mediach przeważały dobre wiadomości.';
        else if (negShare > posShare + 0.1) moodSentence = 'Ton doniesień był raczej poważny.';
        else if (posShare > negShare + 0.1) moodSentence = 'Ton doniesień był raczej optymistyczny.';
        else moodSentence = 'Nastroje w mediach były wyważone.';
    }

    if (elIntro) {
        elIntro.innerHTML =
            `Przeczytaliśmy <strong>${plural(total, 'artykuł', 'artykuły', 'artykułów')}</strong>` +
            (domains ? ` z <strong>${plural(domains, 'serwisu', 'serwisów', 'serwisów')}</strong>` : '') +
            ` i zebraliśmy je w <strong>${plural(topics, 'temat', 'tematy', 'tematów')}</strong>. ${moodSentence}`;
    }
    renderMood(sum > 0 ? { pos, neg, amb, sum } : null);
}

function renderMood(m) {
    const sec = document.getElementById('moodSection');
    const track = document.getElementById('moodTrack');
    const legend = document.getElementById('moodLegend');
    if (!sec || !track || !legend) return;
    if (!m) { sec.style.display = 'none'; return; }
    const pct = v => (v / m.sum * 100).toFixed(1);
    track.innerHTML = `
        <span class="m-pos" style="width:${pct(m.pos)}%" title="Pozytywne: ${m.pos}"></span>
        <span class="m-amb" style="width:${pct(m.amb)}%" title="Neutralne: ${m.amb}"></span>
        <span class="m-neg" style="width:${pct(m.neg)}%" title="Negatywne: ${m.neg}"></span>`;
    legend.innerHTML = `
        <span class="pos"><b>${Math.round(m.pos / m.sum * 100)}%</b> dobrych wieści</span>
        <span class="amb"><b>${Math.round(m.amb / m.sum * 100)}%</b> neutralnych</span>
        <span class="neg"><b>${Math.round(m.neg / m.sum * 100)}%</b> trudnych tematów</span>`;
    sec.style.display = '';
}

/* ====== Spis tematów ====== */
function renderToc(clusters) {
    const sec = document.getElementById('tocSection');
    const list = document.getElementById('tocList');
    const count = document.getElementById('tocCount');
    if (!sec || !list) return;
    if (!clusters.length) { sec.style.display = 'none'; return; }

    // Klastry są posortowane malejąco po liczbie źródeł — na górze „tematy dnia”.
    // Kilka najważniejszych pokazujemy jako czytelną listę, resztę jako zwarte „pigułki”.
    const hotCount = clusters.filter(c => c._hot).length;
    const leadCount = Math.min(clusters.length, Math.max(3, Math.min(hotCount || 0, 6)));

    const lead = clusters.slice(0, leadCount).map((c, i) => {
        const dominant = getDominantPolarity(c.stats?.polarity_3c || {});
        const n = c.stats?.num_of_texts || (c.news_urls || []).length;
        const domains = new Set((c.news_urls || []).map(hostnameOf).filter(Boolean)).size;
        const meta = [plural(n, 'artykuł', 'artykuły', 'artykułów'),
                      domains ? plural(domains, 'serwis', 'serwisy', 'serwisów') : null].filter(Boolean).join(' · ');
        return `<li><a href="#temat-${i}" data-target="${i}">
            <span class="toc-lead-num">${i + 1}</span>
            <span class="toc-lead-body">
                <span class="toc-lead-title">${escapeHtml(c.label_str || `Temat ${i + 1}`)}</span>
                <span class="toc-lead-meta"><span class="toc-dot" style="background:${MOOD_COLOR[dominant]}"></span>${meta}</span>
            </span>
        </a></li>`;
    }).join('');

    const rest = clusters.slice(leadCount).map((c, j) => {
        const i = j + leadCount;
        const dominant = getDominantPolarity(c.stats?.polarity_3c || {});
        const n = c.stats?.num_of_texts || (c.news_urls || []).length;
        const label = c.label_str || `Temat ${i + 1}`;
        return `<a class="toc-chip" href="#temat-${i}" data-target="${i}" title="${escapeHtml(label)}">
            <span class="toc-dot" style="background:${MOOD_COLOR[dominant]}"></span>
            <span class="toc-chip-label">${escapeHtml(label)}</span>
            <span class="toc-chip-count">${n}</span>
        </a>`;
    }).join('');

    list.innerHTML = `
        <div class="toc-lead">
            <div class="toc-section-label"><i class="bi bi-star-fill"></i> Najważniejsze tematy</div>
            <ol class="toc-lead-list">${lead}</ol>
        </div>
        ${rest ? `
        <div class="toc-rest">
            <div class="toc-section-label">Pozostałe tematy <small>${clusters.length - leadCount}</small></div>
            <div class="toc-chips" id="tocChips" data-collapsed="true">${rest}</div>
            <button type="button" class="toc-more" id="tocMore" style="display:none;">
                <i class="bi bi-chevron-down"></i> <span>Pokaż wszystkie tematy</span>
            </button>
        </div>` : ''}`;

    if (count) count.textContent = plural(clusters.length, 'temat', 'tematy', 'tematów');
    sec.style.display = '';
    requestAnimationFrame(updateTocMore);
}

function updateTocMore() {
    const chips = document.getElementById('tocChips');
    const btn = document.getElementById('tocMore');
    if (!chips || !btn) return;
    const collapsed = chips.dataset.collapsed === 'true';
    const overflowing = collapsed && chips.scrollHeight > chips.clientHeight + 4;
    const hiddenCount = collapsed
        ? [...chips.querySelectorAll('.toc-chip')].filter(a => a.style.display !== 'none' && a.offsetTop + a.offsetHeight > chips.clientHeight).length
        : 0;
    btn.style.display = overflowing || !collapsed ? '' : 'none';
    btn.querySelector('span').textContent = collapsed
        ? `Pokaż wszystkie tematy${hiddenCount ? ` (+${hiddenCount})` : ''}`
        : 'Zwiń listę';
    btn.querySelector('i').className = collapsed ? 'bi bi-chevron-down' : 'bi bi-chevron-up';
}

/* ====== Pojedynczy temat (artykuł) ====== */
function renderStory(cluster, idx, dateStr, opts = {}) {
    const compact = !!opts.compact;
    const p3c = cluster.stats?.polarity_3c || {};
    const dominant = getDominantPolarity(p3c);
    const headline = cluster.label_str || 'Bez tytułu';
    const sources = cluster.news_urls || [];
    const articleCount = cluster.stats?.num_of_texts || sources.length;

    // Grupowanie źródeł po serwisie
    const groups = {};
    sources.forEach(u => { const h = hostnameOf(u) || 'inne'; (groups[h] = groups[h] || []).push(u); });
    const groupEntries = Object.entries(groups).sort((a, b) => b[1].length - a[1].length);
    const topDomains = groupEntries.slice(0, 3).map(([h]) => h);
    const moreDomains = groupEntries.length - topDomains.length;

    const bookKey = `iv_bk_${dateStr.replace(/-/g, '')}_${idx}`;
    const saved = isBookmarked(bookKey);

    const kicker = `
        <div class="story-kicker">
            <span class="story-num">${compact ? escapeHtml(dateStr) : `Temat ${idx + 1}`}</span>
            ${cluster._hot ? '<span class="sep"></span><span class="hot-badge">Temat dnia</span>' : ''}
            <span class="sep"></span>
            <span class="mood-badge ${dominant}">${MOOD_LABEL[dominant]}</span>
        </div>`;

    const meta = `
        <div class="story-meta">
            <span><i class="bi bi-journal-text"></i>${plural(articleCount, 'artykuł', 'artykuły', 'artykułów')}</span>
            ${groupEntries.length ? `<span><i class="bi bi-globe2"></i>${plural(groupEntries.length, 'serwis', 'serwisy', 'serwisów')}</span>` : ''}
            ${topDomains.length ? `<span class="domains">m.in. ${topDomains.map(escapeHtml).join(', ')}${moreDomains > 0 ? ` i ${moreDomains} innych` : ''}</span>` : ''}
            ${compact ? '' : `<button class="bookmark-btn${saved ? ' saved' : ''}" data-bookkey="${bookKey}" data-keywords="${escapeHtml(headline)}" title="${saved ? 'Usuń z zapisanych' : 'Zapisz temat'}" aria-label="Zapisz temat">
                <i class="bi ${saved ? 'bi-bookmark-fill' : 'bi-bookmark'}"></i>
            </button>`}
        </div>`;

    let sourcesHtml = '';
    if (groupEntries.length) {
        const items = groupEntries.map(([host, urls]) => `
            <li>
                <div class="source-group-name">${escapeHtml(host)} <small>· ${plural(urls.length, 'artykuł', 'artykuły', 'artykułów')}</small></div>
                <ul class="source-links">${urls.map(u => `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener" title="${escapeHtml(u)}">${escapeHtml(u.replace(/^https?:\/\/(www\.)?/, ''))}</a></li>`).join('')}</ul>
            </li>`).join('');
        sourcesHtml = `
            <details>
                <summary><i class="bi bi-link-45deg"></i>Źródła: ${plural(sources.length, 'artykuł', 'artykuły', 'artykułów')} z ${plural(groupEntries.length, 'serwisu', 'serwisów', 'serwisów')}</summary>
                <div class="details-body"><ul class="source-groups">${items}</ul></div>
            </details>`;
    }

    let simHtml = '';
    const similarities = cluster.similarity || {};
    const simDates = Object.keys(similarities).sort();
    if (!compact && simDates.length) {
        simHtml = `
            <details>
                <summary><i class="bi bi-clock-history"></i>Ten temat pojawiał się też w innych dniach (${simDates.length})</summary>
                <div class="details-body similar-days">
                    ${simDates.map(d => `<button class="similar-day-btn similarity-date-btn" data-date="${escapeHtml(d)}" data-cluster-idx="${idx}">${formatDatePl(d)}</button>`).join('')}
                </div>
            </details>`;
    }

    let techHtml = '';
    if (!compact) {
        const rows = [];
        const pos = p3c.positive || 0, neg = p3c.negative || 0, amb = p3c.ambivalent || 0;
        if (pos + neg + amb > 0) rows.push(['Wydźwięk artykułów', `${pos} pozytywnych · ${amb} neutralnych · ${neg} negatywnych`]);
        const pli = cluster.stats?.pli_value;
        if (pli !== undefined) rows.push(['Wskaźnik polaryzacji (PLI)', pli.toFixed(3)]);
        const langs = cluster.stats?.language || {};
        if (Object.keys(langs).length) rows.push(['Języki źródeł', Object.entries(langs).map(([l, n]) => `${l.toUpperCase()} (${n})`).join(', ')]);
        if (rows.length) {
            techHtml = `
                <details>
                    <summary><i class="bi bi-info-circle"></i>Szczegóły techniczne</summary>
                    <div class="details-body"><dl class="tech-grid">${rows.map(([k, v]) => `<div><dt>${k}</dt><dd>${escapeHtml(v)}</dd></div>`).join('')}</dl></div>
                </details>`;
        }
    }

    const classes = ['story', 'fade-in'];
    if (idx === 0 && !compact) classes.push('story-lead');
    if (cluster._hot) classes.push('is-hot');

    return `
    <article class="${classes.join(' ')}" id="${compact ? '' : `temat-${idx}`}" data-idx="${idx}" data-date="${escapeHtml(dateStr)}" style="animation-delay:${Math.min(idx * 0.05, 0.6)}s">
        ${kicker}
        <h2 class="story-headline">${escapeHtml(headline)}</h2>
        ${meta}
        <div class="story-body">${renderMarkdown(cluster.article_text || '')}</div>
        ${(sourcesHtml || simHtml || techHtml) ? `<div class="story-footer">${sourcesHtml}${simHtml}${techHtml}</div>` : ''}
    </article>`;
}

function show(id) { const e = document.getElementById(id); if (e) e.style.display = ''; }
function hide(id) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }

/* ====== Wspólne: przygotowanie klastrów (sortowanie, temat dnia) ====== */
function prepareClusters(clusters) {
    const hotThreshold = computeHotThreshold(clusters);
    const enriched = clusters.map(c => ({ ...c, _hot: (c.news_urls || []).length >= hotThreshold }));
    return enriched.sort((a, b) => (b.news_urls || []).length - (a.news_urls || []).length);
}

function renderStories(grid, clusters, dateStr) {
    if (!grid) return;
    grid.innerHTML = clusters.map((c, i) => renderStory(c, i, dateStr)).join('');
    if (window.MathJax?.typesetPromise) window.MathJax.typesetPromise([grid]).catch(() => {});
}

/* ====== Modal: podobne dni ====== */
function showSimilarityModal(dateStr, similarities) {
    const mid = 'simModal';
    document.getElementById(mid)?.remove();

    const simDates = Object.keys(similarities).sort();
    if (!simDates.length) return;
    let currentIndex = 0;

    function renderBody() {
        const day = simDates[currentIndex];
        const list = similarities[day] || [];
        const stories = list.map((item, i) => renderStory(item.target || {}, i, day, { compact: true })).join('');
        return `
            <div class="d-flex justify-content-between align-items-center flex-wrap gap-2 mb-3">
                <small class="text-muted">Wybierz dzień:</small>
                <div class="sim-dates-list">${simDates.map((d, i) =>
                    `<button class="sim-date-pill${i === currentIndex ? ' active' : ''}" data-idx="${i}">${formatDatePl(d)}</button>`
                ).join('')}</div>
            </div>
            <div class="stories">${stories || '<p class="text-muted">Brak podobnych tematów.</p>'}</div>`;
    }

    document.body.insertAdjacentHTML('beforeend', `
    <div class="modal fade sim-modal" id="${mid}" tabindex="-1"><div class="modal-dialog modal-lg modal-dialog-scrollable"><div class="modal-content">
        <div class="modal-header"><h5 class="modal-title"><i class="bi bi-clock-history me-2"></i>Ten temat w innych dniach</h5><button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Zamknij"></button></div>
        <div class="modal-body">${renderBody()}</div>
    </div></div></div>`);

    const modalEl = document.getElementById(mid);
    modalEl.addEventListener('click', (e) => {
        const pill = e.target.closest('.sim-date-pill');
        if (!pill) return;
        const idx = parseInt(pill.dataset.idx);
        if (idx !== currentIndex) { currentIndex = idx; modalEl.querySelector('.modal-body').innerHTML = renderBody(); }
    });
    modalEl.addEventListener('hidden.bs.modal', () => modalEl.remove(), { once: true });
    new bootstrap.Modal(modalEl).show();
}

/* ====== Panel zapisanych ====== */
function renderBookmarkPanel() {
    const bms = getBookmarks();
    const list = document.getElementById('bookmarksFullList');
    if (!list) return;
    if (!bms.length) {
        list.innerHTML = '<p class="text-muted py-3">Nie masz jeszcze zapisanych tematów. Kliknij <i class="bi bi-bookmark"></i> obok tytułu, aby wrócić do niego później.</p>';
        return;
    }
    list.innerHTML = bms.slice().reverse().map(b => `
        <div class="bookmark-item" data-key="${escapeHtml(b.key)}">
            <div>
                <div class="bk-title">${escapeHtml(b.keywords)}</div>
                <div class="bk-date">${formatDatePl(b.date)}</div>
            </div>
            <div class="d-flex gap-2 flex-shrink-0">
                <button class="btn btn-link link-btn">Otwórz</button>
                <button class="btn btn-link bookmark-remove" data-key="${escapeHtml(b.key)}" title="Usuń"><i class="bi bi-trash3"></i></button>
            </div>
        </div>`).join('');
}

/* ====== Filtry ====== */
let currentSentiment = 'all';
let currentSearch = '';

function applyFilters() {
    const cards = document.querySelectorAll('.story[data-idx]');
    let visible = 0;
    cards.forEach(card => {
        const cluster = allClusters[parseInt(card.dataset.idx)];
        if (!cluster) return;
        const sentiment = getDominantPolarity(cluster.stats?.polarity_3c || {});
        const hay = `${cluster.label_str || ''} ${cluster.article_text || ''}`.toLowerCase();
        const okSent = currentSentiment === 'all' || sentiment === currentSentiment;
        const okSearch = !currentSearch || hay.includes(currentSearch.toLowerCase());
        card.style.display = okSent && okSearch ? '' : 'none';
        if (okSent && okSearch) visible++;
    });
    const vc = document.getElementById('visibleCount');
    if (vc) vc.textContent = visible === cards.length ? '' : `Pokazano ${visible} z ${cards.length}`;
    document.querySelectorAll('.toc a[data-target]').forEach(a => {
        const card = document.querySelector(`.story[data-idx="${a.dataset.target}"]`);
        const el = a.closest('li') || a;
        el.style.display = card && card.style.display === 'none' ? 'none' : '';
    });
    updateTocMore();
}

/* ====== Ładowanie: strona główna ====== */
async function loadSummary(dateStr) {
    currentDate = dateStr;
    const grid = document.getElementById('newspaperGrid');
    if (grid) grid.innerHTML = '';
    hide('errorBox'); hide('emptySection'); hide('mainGrid'); hide('moodSection');
    show('loadingSection');
    markActiveQuickDate(dateStr);
    updateNextButton(dateStr);

    document.getElementById('editionDate').textContent = formatDatePl(dateStr);
    document.getElementById('editionWeekday').textContent = formatWeekdayPl(dateStr);

    try {
        const data = await API.summary(dateStr);
        hide('loadingSection');
        const clusters = data.summaries?.[0]?.clusters || [];

        if (clusters.length) {
            allClusters = prepareClusters(clusters);
            renderEditionHeader(data.date, data.stats, clusters.length);
            renderToc(allClusters);
            renderStories(grid, allClusters, data.date);
            show('mainGrid');
            applyFilters();
        } else {
            allClusters = [];
            renderEditionHeader(dateStr, null, 0);
            document.getElementById('emptyMsg').textContent = data.message || 'Na ten dzień nie mamy jeszcze podsumowania.';
            show('emptySection');
        }
    } catch (err) {
        hide('loadingSection');
        const box = document.getElementById('errorBox');
        if (box) { box.textContent = `Nie udało się pobrać wydania: ${err.message}`; show('errorBox'); }
    }
}

/* ====== Ładowanie: strona daty ====== */
async function loadDateSummary(dateStr, gridId) {
    currentDate = dateStr;
    const grid = document.getElementById(gridId);
    if (grid) grid.innerHTML = '';
    hide('dateEmptySection'); hide('tocSection');
    show('dateLoading');

    try {
        const data = await API.summary(dateStr);
        hide('dateLoading');
        const clusters = data.summaries?.[0]?.clusters || [];
        if (clusters.length) {
            allClusters = prepareClusters(clusters);
            renderEditionHeader(data.date, data.stats, clusters.length);
            renderToc(allClusters);
            renderStories(grid, allClusters, data.date);
        } else {
            renderEditionHeader(dateStr, null, 0);
            show('dateEmptySection');
        }
    } catch (err) {
        const l = document.getElementById('dateLoading');
        if (l) l.innerHTML = `<p class="mt-3" style="color:var(--negative)">Nie udało się pobrać wydania: ${escapeHtml(err.message)}</p>`;
    }
}

/* ====== Zdarzenia ====== */
function scrollToStory(idx) {
    const card = document.querySelector(`.story[data-idx="${idx}"]`);
    if (!card) return false;
    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
    card.classList.remove('highlight'); void card.offsetWidth; card.classList.add('highlight');
    setTimeout(() => card.classList.remove('highlight'), 2500);
    return true;
}

function initToc() {
    document.addEventListener('click', (e) => {
        const more = e.target.closest('#tocMore');
        if (more) {
            const chips = document.getElementById('tocChips');
            if (chips) chips.dataset.collapsed = chips.dataset.collapsed === 'true' ? 'false' : 'true';
            updateTocMore();
            return;
        }
        const a = e.target.closest('.toc a[data-target]');
        if (!a) return;
        e.preventDefault();
        scrollToStory(a.dataset.target);
    });
    window.addEventListener('resize', () => updateTocMore());
}

function initBookmarks() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.bookmark-btn');
        if (btn) {
            const key = btn.dataset.bookkey;
            const card = btn.closest('.story');
            toggleBookmark(key, { keywords: btn.dataset.keywords, date: card?.dataset.date || '', idx: parseInt(card?.dataset.idx || 0) });
            const isBk = isBookmarked(key);
            btn.classList.toggle('saved', isBk);
            btn.title = isBk ? 'Usuń z zapisanych' : 'Zapisz temat';
            btn.innerHTML = `<i class="bi ${isBk ? 'bi-bookmark-fill' : 'bi-bookmark'}"></i>`;
            renderBookmarkPanel();
            return;
        }
        const rmBtn = e.target.closest('.bookmark-remove');
        if (rmBtn) {
            toggleBookmark(rmBtn.dataset.key, {});
            renderBookmarkPanel();
            document.querySelectorAll(`.bookmark-btn[data-bookkey="${rmBtn.dataset.key}"]`).forEach(b => {
                b.classList.remove('saved'); b.innerHTML = '<i class="bi bi-bookmark"></i>';
            });
            return;
        }
        const okBtn = e.target.closest('.link-btn');
        if (okBtn) {
            const item = okBtn.closest('.bookmark-item');
            const bm = getBookmarks().find(b => b.key === item?.dataset.key);
            if (!bm) return;
            if (bm.date && bm.date === currentDate && scrollToStory(bm.idx)) { hide('bookmarksOverlay'); return; }
            window.open(`/date/${bm.date}?topic=${bm.idx || 0}`, '_blank');
        }
    });
}

function initSentimentFilter() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.chip[data-sentiment]');
        if (!btn) return;
        document.querySelectorAll('.chip[data-sentiment]').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        currentSentiment = btn.dataset.sentiment;
        applyFilters();
    });
}

function initSearch() {
    const input = document.getElementById('searchInput');
    if (!input) return;
    input.addEventListener('input', (e) => { currentSearch = e.target.value.trim(); applyFilters(); });
}

function markActiveQuickDate(ds) {
    document.querySelectorAll('.quick-date-btn[data-date]').forEach(b => b.classList.toggle('active', b.dataset.date === ds));
}
function updateNextButton(ds) {
    const next = document.getElementById('nextDay');
    if (next) next.disabled = ds >= latestIso();
}

function initDateNav() {
    const picker = document.getElementById('datePicker');
    const prevBtn = document.getElementById('prevDay');
    const nextBtn = document.getElementById('nextDay');
    if (!picker) return;

    const go = (ds) => { picker.value = ds; loadSummary(ds); };
    if (prevBtn) prevBtn.addEventListener('click', () => picker.value && go(addDays(picker.value, -1)));
    if (nextBtn) nextBtn.addEventListener('click', () => picker.value && picker.value < latestIso() && go(addDays(picker.value, 1)));
    picker.addEventListener('change', () => picker.value && loadSummary(picker.value));

    const qd = document.getElementById('quickDates');
    if (qd) {
        qd.innerHTML = '';
        const latest = latestIso();
        for (let i = 0; i < 7; i++) {
            const ds = addDays(latest, -i);
            const btn = document.createElement('button');
            btn.className = 'quick-date-btn';
            btn.dataset.date = ds;
            btn.textContent = relativeDayLabel(ds);
            btn.title = formatDatePl(ds);
            btn.addEventListener('click', () => go(ds));
            qd.appendChild(btn);
        }
    }
    if (picker.value) loadSummary(picker.value);
}

function initSimilarity() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.similarity-date-btn');
        if (!btn) return;
        const cluster = allClusters[parseInt(btn.dataset.clusterIdx)];
        if (!cluster?.similarity) return;
        showSimilarityModal(btn.closest('.story')?.dataset.date || currentDate, cluster.similarity);
    });
}

function initCompare() {
    const toggle = document.getElementById('toggleCompare');
    const overlay = document.getElementById('compareOverlay');
    const close = document.getElementById('closeCompare');
    const d1 = document.getElementById('compareDate1');
    const d2 = document.getElementById('compareDate2');
    if (!toggle || !overlay) return;

    toggle.addEventListener('click', () => {
        if (overlay.style.display !== 'none') { hide('compareOverlay'); return; }
        hide('bookmarksOverlay');
        show('compareOverlay');
        const base = document.getElementById('datePicker')?.value || latestIso();
        if (d1 && !d1.value) d1.value = base;
        if (d2 && !d2.value) d2.value = addDays(base, -1);
        doCompare();
    });
    if (close) close.addEventListener('click', () => hide('compareOverlay'));
    if (d1) d1.addEventListener('change', doCompare);
    if (d2) d2.addEventListener('change', doCompare);
}

async function doCompare() {
    const d1 = document.getElementById('compareDate1')?.value;
    const d2 = document.getElementById('compareDate2')?.value;
    if (!d1 || !d2) return;
    const r1 = document.getElementById('compareResult1');
    const r2 = document.getElementById('compareResult2');
    r1.innerHTML = r2.innerHTML = '<div class="spinner-border spinner-border-sm" style="color:var(--accent)"></div>';
    const [s1, s2] = await Promise.all([API.summary(d1).catch(() => ({})), API.summary(d2).catch(() => ({}))]);
    const fmt = (s) => {
        if (!s.stats) return '<div class="compare-stats-box text-muted">Brak podsumowania</div>';
        const p = s.stats.polarity || {}; const sum = (p.positive || 0) + (p.negative || 0) + (p.ambivalent || 0);
        const good = sum ? Math.round((p.positive || 0) / sum * 100) : 0;
        return `<div class="compare-stats-box">
            <div><span class="big">${s.stats.total_clusters}</span> tematów</div>
            <div>${plural(s.stats.total_articles, 'artykuł', 'artykuły', 'artykułów')}</div>
            <div>${plural(s.stats.unique_domains || 0, 'serwis', 'serwisy', 'serwisów')}</div>
            <div class="mt-1" style="color:var(--positive)">${good}% dobrych wieści</div>
        </div>`;
    };
    r1.innerHTML = `<div class="fw-semibold mb-1" style="font-size:0.85rem;">${formatDatePl(d1)}</div>${fmt(s1)}`;
    r2.innerHTML = `<div class="fw-semibold mb-1" style="font-size:0.85rem;">${formatDatePl(d2)}</div>${fmt(s2)}`;
}

function initBookmarksPanel() {
    const toggle = document.getElementById('toggleBookmarks');
    const overlay = document.getElementById('bookmarksOverlay');
    const close = document.getElementById('closeBookmarks');
    if (!toggle || !overlay) return;
    toggle.addEventListener('click', () => {
        if (overlay.style.display !== 'none') { hide('bookmarksOverlay'); return; }
        hide('compareOverlay');
        show('bookmarksOverlay');
        renderBookmarkPanel();
    });
    if (close) close.addEventListener('click', () => hide('bookmarksOverlay'));
    document.addEventListener('keydown', (e) => { if (e.key === 'Escape') { hide('bookmarksOverlay'); hide('compareOverlay'); } });
}

function initThemeToggle() {
    const btn = document.getElementById('toggleTheme');
    const saved = localStorage.getItem('iv_theme');
    if (saved === 'dark') document.documentElement.setAttribute('data-bs-theme', 'dark');
    if (!btn) return;
    const paint = () => {
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        btn.innerHTML = isDark ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
        btn.title = isDark ? 'Tryb jasny' : 'Tryb ciemny';
    };
    paint();
    btn.addEventListener('click', () => {
        const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
        document.documentElement.setAttribute('data-bs-theme', isDark ? 'light' : 'dark');
        localStorage.setItem('iv_theme', isDark ? 'light' : 'dark');
        paint();
    });
}

/* ====== Pasek postępu czytania + przycisk „na górę” ====== */
function initScrollUi() {
    const btn = document.getElementById('scrollTopBtn');
    const bar = document.getElementById('readingProgress');
    const onScroll = () => {
        const y = window.scrollY;
        if (btn) btn.classList.toggle('visible', y > 400);
        if (bar) {
            const max = document.documentElement.scrollHeight - window.innerHeight;
            bar.style.width = max > 0 ? `${Math.min(100, y / max * 100)}%` : '0%';
        }
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
    if (btn) btn.addEventListener('click', () => window.scrollTo({ top: 0, behavior: 'smooth' }));
}

document.addEventListener('DOMContentLoaded', () => {
    initThemeToggle();
    initDateNav();
    initSearch();
    initSentimentFilter();
    initToc();
    initBookmarks();
    initBookmarksPanel();
    initCompare();
    initSimilarity();
    initScrollUi();
    API.status().catch(() => {});
});
