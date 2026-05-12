/**
 * Info Viewer — Przeglądarka informacji
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
function formatDatePl(ds) {
    const m = ['stycznia','lutego','marca','kwietnia','maja','czerwca','lipca','sierpnia','września','października','listopada','grudnia'];
    const d = new Date(ds + 'T00:00:00');
    if (isNaN(d)) return ds;
    return `${d.getDate()} ${m[d.getMonth()]} ${d.getFullYear()}`;
}

function addDays(ds, n) {
    const parts = ds.split('-').map(Number);
    const d = new Date(Date.UTC(parts[0], parts[1] - 1, parts[2] + n));
    return d.toISOString().split('T')[0];
}

function getDominantPolarity(p3c) {
    if (!p3c) return 'ambivalent';
    let mx = -1, k = 'ambivalent';
    for (const [k2, v] of Object.entries(p3c)) { if (v > mx) { mx = v; k = k2; } }
    return k;
}
function getClusterColor(p) { return { positive: '#2d703a', negative: '#a03030', ambivalent: '#7a7a7a' }[p] || '#7a7a7a'; }

function renderMarkdown(md) {
    if (!md) return '';
    marked.setOptions({ breaks: true, gfm: true });
    return marked.parse(md);
}

function polarityBadge(p) {
    const m = { positive: {c:'badge-positive', l:'Pozytywna'}, negative: {c:'badge-negative', l:'Negatywna'}, ambivalent: {c:'badge-ambivalent', l:'Ambivalentna'} };
    const p2 = m[p] || m.ambivalent;
    return `<span class="badge ${p2.c}">${p2.l}</span>`;
}

/* ====== Bookmarks ====== */
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
let currentDayArticles = 0;
let sidebarInitialized = false;

/* ====== Hot topic threshold (top quartile by source count) ====== */
function computeHotThreshold(clusters) {
    const counts = clusters.map(c => (c.news_urls || []).length).sort((a, b) => a - b);
    if (counts.length < 4) return 0;
    const qIdx = Math.ceil(counts.length * 0.75) - 1;
    return counts[qIdx];
}

/* ====== Day sentiment — compact gradient bar ====== */
function renderSentimentBar(polarity, total) {
    const el = document.getElementById('sentimentBar');
    if (!el || total === 0) { el.innerHTML = ''; return; }
    const pos = polarity.positive || 0;
    const neg = polarity.negative || 0;
    const amb = polarity.ambivalent || 0;
    const totalP = pos + neg + amb;
    const posPct = totalP > 0 ? (pos / totalP * 100).toFixed(1) : 0;
    const ambPct = totalP > 0 ? (amb / totalP * 100).toFixed(1) : 0;
    const negPct = totalP > 0 ? (neg / totalP * 100).toFixed(1) : 0;
    el.innerHTML = `
        <div class="stats-bar-gradient-labels">
            <span class="sl positive"><i class="bi bi-check-circle"></i> +${pos}</span>
            <span class="sl ambivalent">${amb}</span>
            <span class="sl negative">−${neg}</span>
        </div>
        <div class="stats-bar-gradient-track">
            <div class="sseg sseg-positive" style="width:${posPct}%"></div>
            <div class="sseg sseg-ambivalent" style="width:${ambPct}%"></div>
            <div class="sseg sseg-negative" style="width:${negPct}%"></div>
        </div>
    `;
}

/* ====== Render cluster card ====== */
function renderClusterCard(cluster, idx, dateStr) {
    const p3c = cluster.stats?.polarity_3c || {};
    const dominant = getDominantPolarity(p3c);
    const color = getClusterColor(dominant);
    const headline = cluster.label_str || 'Bez tytułu';
    const articleMd = cluster.article_text || '';
    const sources = cluster.news_urls || [];
    // Unikalne domeny — count and top list for tags
    const domainCount = new Set(sources.map(u => { try { return new URL(u).hostname; } catch { return ''; } })).size;
    const domainMap = {};
    sources.forEach(u => { try { const h = new URL(u).hostname; domainMap[h] = (domainMap[h] || 0) + 1; } catch {} });
    const topDomains = Object.entries(domainMap).sort((a, b) => b[1] - a[1]).slice(0, 3).map(([d]) => d);
    const domainTags = topDomains.length > 0 ? topDomains.map(d => `<span class="domain-tag" title="${d}: ${domainMap[d]} źródeł">${escapeHtml(d)}</span>`).join('') : '';
    const similarities = cluster.similarity || {};
    const hasSim = Object.keys(similarities).length > 0;
    const delay = idx * 0.05;
    const articleHtml = renderMarkdown(articleMd);
    const bookKey = `iv_bk_${dateStr.replace(/-/g,'')}_${idx}`;
    const bookMarked = isBookmarked(bookKey);

    const pos = p3c.positive||0;
    const neg = p3c.negative||0;
    const amb = p3c.ambivalent||0;
    const p3cTotal = pos + neg + amb;
    const posPct = p3cTotal > 0 ? (pos / p3cTotal * 100).toFixed(1) : 0;
    const ambPct = p3cTotal > 0 ? (amb / p3cTotal * 100).toFixed(1) : 0;
    const negPct = p3cTotal > 0 ? (neg / p3cTotal * 100).toFixed(1) : 0;
    const statsHtml = p3cTotal > 0 ? `
        <div class="cluster-sentiment-bar-wrap">
            <div class="cluster-sentiment-bar-track">
                <div class="cseg cseg-positive" style="width:${posPct}%"></div>
                <div class="cseg cseg-ambivalent" style="width:${ambPct}%"></div>
                <div class="cseg cseg-negative" style="width:${negPct}%"></div>
            </div>
            <div class="cluster-sentiment-bar-labels">
                <span class="cs-label positive"><i class="bi bi-check-circle"></i> +${pos}</span>
                <span class="cs-label ambivalent">${amb}</span>
                <span class="cs-label negative">−${neg}</span>
            </div>
        </div>
    ` : `
        <div class="cluster-stats">
            <div class="stat-inline"><div class="stat-val" style="color:${color}">${Object.keys(p3c).length}</div><div class="stat-lbl">Sentyment</div></div>
            <div class="stat-inline"><div class="stat-val" style="color:var(--positive)">${pos||0}</div><div class="stat-lbl">+</div></div>
            <div class="stat-inline"><div class="stat-val" style="color:var(--negative)">${neg||0}</div><div class="stat-lbl">−</div></div>
            <div class="stat-inline"><div class="stat-val" style="color:var(--ambivalent)">${amb||0}</div><div class="stat-lbl">A</div></div>
        </div>
    `;

    let sourcesHtml = '';
    const displayUrls = sources.slice(0, 6);
    const remaining = sources.length - displayUrls.length;
    if (displayUrls.length > 0) {
        const items = displayUrls.map(u => {
            let host = u; try { host = new URL(u).hostname; } catch {}
            return `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener">${escapeHtml(host)}</a></li>`;
        }).join('');
        sourcesHtml = `
            <div class="cluster-sources-header"><i class="bi bi-link-45deg me-1"></i>Źródła: ${sources.length} (z ${domainCount} domen)</div>
            <ul class="cluster-sources-list" id="srcList_${idx}">${items}</ul>
            ${remaining > 0 ? `<button class="btn btn-sm btn-link source-expand-btn" data-cluster-idx="${idx}" data-remaining="${remaining}" style="padding:0;font-size:0.78rem;color:var(--accent-light);">Pokaż wszystkie źródła (${remaining} więcej)</button>` : ''}`;
    }

    let simHtml = '';
    if (hasSim) {
        const simDates = Object.keys(similarities).sort();
        const btns = simDates.map(d => `<button class="btn btn-sm btn-outline-secondary similarity-date-btn" data-date="${escapeHtml(d)}" data-cluster-idx="${idx}">${d}</button>`).join('');
        simHtml = `<div class="similarity-section"><h6><i class="bi bi-diagram-3 me-1"></i>Podobne dni</h6><div class="similarity-dates">${btns}</div></div>`;
    }

    let metaExtra = '';
    const pli = cluster.stats?.pli_value;
    if (pli !== undefined) {
        const pliLabel = pli > 0.7 ? 'Wysoka' : pli > 0.3 ? 'Średnia' : 'Niska';
        metaExtra += `<span class="cluster-meta-item"><i class="bi bi-speedometer2 me-1"></i>PLI: <strong>${pli.toFixed(3)}</strong> (${pliLabel})</span>`;
    }
    const langs = cluster.stats?.language || {};
    if (Object.keys(langs).length > 0) {
        const langStr = Object.entries(langs).filter(([l]) => l !== 'pl').map(([l, n]) => `${l}(${n})`).join(', ');
        metaExtra += `<span class="cluster-meta-item">${escapeHtml(langStr)}</span>`;
    }

    const hotBadge = cluster._hot ? `<span class="badge hot-topic-badge">⚡ Hot temat</span>` : '';
    const hotClass = cluster._hot ? ' is-hot' : '';

    return `
    <div class="cluster-card fade-in${hotClass}" data-idx="${idx}" data-date="${escapeHtml(dateStr)}" style="animation-delay:${delay}s">
        <div class="card-header">
            <div class="d-flex align-items-start justify-content-between">
                <div style="flex:1; min-width:0;">
                    ${hotBadge}
                    <div class="cluster-headline">${escapeHtml(headline)}</div>
                    ${domainTags ? `<div class="cluster-domains mt-1">${domainTags}</div>` : ''}
                    <div class="cluster-meta">
                        ${polarityBadge(dominant)}
                        <button class="btn btn-sm btn-link bookmark-btn" data-bookkey="${bookKey}" data-keywords="${escapeHtml(headline)}" style="padding:0;font-size:0.75rem;color:${bookMarked ? 'var(--accent)' : 'var(--ink-light)'};">
                            <i class="bi ${bookMarked ? 'bi-bookmark-fill' : 'bi-bookmark'}"></i>
                        </button>
                    </div>
                </div>
            </div>
        </div>
        <div class="card-body">
            <div class="cluster-article">
                ${articleHtml}
            </div>
            ${metaExtra ? `<div class="cluster-meta">${metaExtra}</div>` : ''}
            ${sourcesHtml}
            ${statsHtml}
            ${simHtml}
        </div>
    </div>`;
}

/* ====== Render card for similar days — same style as main page ====== */
function renderSimilarDayCard(cluster, dateStr) {
    const p3c = cluster.stats?.polarity_3c || {};
    const dominant = getDominantPolarity(p3c);
    const color = getClusterColor(dominant);
    const headline = cluster.label_str || 'Bez tytułu';
    const articleMd = cluster.article_text || '';
    const sources = cluster.news_urls || [];
    const articleHtml = renderMarkdown(articleMd);

    let sourcesHtml = '';
    if (sources.length > 0) {
        const items = sources.slice(0, 3).map(u => {
            let host = u; try { host = new URL(u).hostname; } catch {}
            return `<li><a href="${escapeHtml(u)}" target="_blank">${escapeHtml(host)}</a></li>`;
        }).join('');
        sourcesHtml = `<div class="cluster-sources-header"><i class="bi bi-link-45deg me-1"></i>Źródła (${sources.length})</div><ul class="cluster-sources-list">${items}</ul>`;
    }

    const metaExtra = cluster.stats?.pli_value !== undefined ? `
        <span class="cluster-meta-item"><i class="bi bi-speedometer2 me-1"></i>PLI: <strong>${cluster.stats.pli_value.toFixed(3)}</strong></span>` : '';

    return `
    <div class="cluster-card fade-in sim-day-card">
        <div class="card-header">
            <div class="cluster-meta">
                <span class="badge badge-positive">Podobny dzień</span>
                <small class="text-muted">${escapeHtml(dateStr)}</small>
            </div>
            <div class="cluster-headline">${escapeHtml(headline)}</div>
        </div>
        <div class="card-body">
            <div class="cluster-article">${articleHtml}</div>
            ${metaExtra ? `<div class="cluster-meta">${metaExtra}</div>` : ''}
            ${sourcesHtml}
        </div>
    </div>`;
}

function show(id) { const e = document.getElementById(id); if (e) e.style.display = 'block'; }
function hide(id) { const e = document.getElementById(id); if (e) e.style.display = 'none'; }

/* ====== Floating right sidebar ====== */
function createFloatingSidebar() {
    if (sidebarInitialized || document.getElementById('floatingSidebar')) return;
    const datePage = document.getElementById('dateNewspaperGrid') || document.getElementById('newspaperGrid');
    if (!datePage) return;

    const sidebar = document.createElement('div');
    sidebar.id = 'floatingSidebar';
    sidebar.className = 'floating-sidebar collapsed';
    sidebar.innerHTML = `
        <div class="floating-sidebar-content" id="sidebarContent">
            <div class="floating-sidebar-toggle" id="sidebarToggle">
                <i class="bi bi-list-nested"></i>
            </div>
            <div class="floating-sidebar-inner">
            <h6 class="floating-sidebar-title"><i class="bi bi-list-ul me-1"></i>Tematy dnia</h6>
            <div class="floating-sidebar-list" id="sidebarList"></div>
            </div>
        </div>
    `;
    document.body.appendChild(sidebar);
    sidebarInitialized = true;

    const toggle = document.getElementById('sidebarToggle');
    if (toggle) {
        toggle.addEventListener('click', () => {
            sidebar.classList.toggle('collapsed');
            toggle.innerHTML = sidebar.classList.contains('collapsed')
                ? '<i class="bi bi-list-nested"></i>'
                : '<i class="bi bi-x-lg"></i>';
        });
    }
}

function updateFloatingSidebar() {
    if (!sidebarInitialized) return;
    const list = document.getElementById('sidebarList');
    if (!list) return;

    list.innerHTML = allClusters.map((c, i) => {
        const headline = c.label_str || `Temat ${i + 1}`;
        const p3c = c.stats?.polarity_3c || {};
        const dominant = getDominantPolarity(p3c);
        const dotColor = { positive: 'var(--positive)', negative: 'var(--negative)', ambivalent: 'var(--ambivalent)' }[dominant] || 'var(--ink-light)';
        const short = headline.length > 45 ? headline.substring(0, 45) + '…' : headline;
        return `<div class="sidebar-item" data-target="${i}">
            <span class="sidebar-dot" style="background:${dotColor}"></span>
            <span class="sidebar-text">${escapeHtml(short)}</span>
        </div>`;
    }).join('');

    list.querySelectorAll('.sidebar-item').forEach(item => {
        item.addEventListener('click', () => {
            const idx = parseInt(item.dataset.target);
            const card = document.querySelector(`.cluster-card[data-idx="${idx}"]`);
            if (card) {
                card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                card.classList.add('sidebar-highlight');
                // Collapse sidebar on mobile
                if (window.innerWidth <= 991) {
                    const sb = document.getElementById('floatingSidebar');
                    sb.classList.add('collapsed');
                    const tg = document.getElementById('sidebarToggle');
                    tg.innerHTML = '<i class="bi bi-list-nested"></i>';
                }
                setTimeout(() => card.classList.remove('sidebar-highlight'), 2000);
            }
        });
    });
}

/* ====== Scroll spy for sidebar ====== */
function initScrollSpy() {
    const grid = document.getElementById('newspaperGrid');
    if (!grid) return;
    let ticking = false;

    function onScroll() {
        if (!ticking) {
            requestAnimationFrame(() => {
                const cards = document.querySelectorAll('.cluster-card');
                const sidebarItems = document.querySelectorAll('.sidebar-item');
                if (cards.length === 0 || sidebarItems.length === 0) return;
                const scrollY = window.scrollY + 150;
                let activeIdx = 0;
                cards.forEach((card, i) => {
                    if (card.offsetTop <= scrollY) activeIdx = i;
                });
                sidebarItems.forEach((item, i) => {
                    item.classList.toggle('active', i === activeIdx);
                });
                ticking = false;
            });
            ticking = true;
        }
    }
    window.addEventListener('scroll', onScroll);
}

/* ====== Daily stats (redesigned) ====== */
function renderDailyStats(stats) {
    if (!stats) { hide('statsSection'); return; }
    show('statsSection');
    const total = stats.total_articles || 0;
    const clusters = stats.total_clusters || 0;
    const pol = stats.polarity || {};
    const totalPol = (pol.positive||0) + (pol.negative||0) + (pol.ambivalent||0);
    const langs = stats.languages || {};
    const langLabels = Object.entries(langs).map(([l, n]) => {
        const flag = { pl:'🇵🇱', en:'🇬🇧', de:'🇩🇪', fr:'🇫🇷', ru:'🇷🇺', ua:'🇺🇦' }[l] || l.toUpperCase();
        return `<span class="lang-tag" title="${l}: ${n}">${flag} ${l.toUpperCase()}</span>`;
    }).join(' ');
    document.getElementById('statArticles').textContent = total;
    document.getElementById('statClusters').textContent = clusters;
    document.getElementById('statLangs').innerHTML = langLabels || '—';
    const elDomains = document.getElementById('statDomains');
    if (elDomains) {
        elDomains.innerHTML = `<i class="bi bi-globe2" style="font-size:0.82rem"></i> ${stats.unique_domains || 0} domen`;
    }
    const polColor = totalPol > 0 ? (pol.positive > pol.negative ? 'var(--positive)' : 'var(--negative)') : 'var(--ambivalent)';
    renderSentimentBar(pol, total);
    currentDayArticles = total;
}

/* ====== Similarity modal — styled like main page ====== */
function showSimilarityModal(dateStr, similarities) {
    const mid = 'simModal';
    let existing = document.getElementById(mid);
    if (existing) existing.remove();

    const simDates = Object.keys(similarities).sort();
    if (simDates.length === 0) return;

    let currentIndex = 0;

    function renderModalDay() {
        const day = simDates[currentIndex];
        const list = similarities[day] || [];
        const cards = list.map(item => {
            const t = item.target || {};
            return renderSimilarDayCard(t, day);
        }).join('');

        const title = simDates.length > 1
            ? `${escapeHtml(day)} (${currentIndex + 1}/${simDates.length})`
            : escapeHtml(day);

        const prevBtn = currentIndex > 0
            ? `<button class="btn btn-sm btn-outline-secondary" id="simPrev"><i class="bi bi-chevron-left"></i> Poprzedni</button>`
            : '<span></span>';
        const nextBtn = currentIndex < simDates.length - 1
            ? `<button class="btn btn-sm btn-outline-secondary" id="simNext">Następny <i class="bi bi-chevron-right"></i></button>`
            : '<span></span>';

        return `
            <div class="sim-nav mb-3 d-flex justify-content-between align-items-center">
                <small class="text-muted"><i class="bi bi-diagram-3 me-1"></i>Podobne dni:</small>
                <div class="sim-dates-list">${simDates.map((d, i) =>
                    `<button class="btn btn-sm ${i === currentIndex ? 'btn-primary' : 'btn-outline-secondary'} sim-date-pill" data-idx="${i}">${d}</button>`
                ).join('')}</div>
            </div>
            <div class="modal-day-nav mb-2 d-flex justify-content-between">${prevBtn}${nextBtn}</div>
            <div class="similar-day-section">
                <h5 class="similar-day-title">${title}</h5>
                <div class="newspaper-grid">${cards}</div>
            </div>`;
    }

    const items = renderModalDay();

    document.body.insertAdjacentHTML('beforeend', `
    <div class="modal fade sim-modal" id="${mid}" tabindex="-1"><div class="modal-dialog modal-xl modal-dialog-scrollable"><div class="modal-content">
        <div class="modal-header"><h5 class="modal-title"><i class="bi bi-diagram-3 me-2"></i>Podobne dni — ${escapeHtml(dateStr)}</h5><button type="button" class="btn-close" data-bs-dismiss="modal"></button></div>
        <div class="modal-body">${items}</div>
    </div></div></div>`);
    const modal = new bootstrap.Modal(document.getElementById(mid));
    modal.show();

    // Prev/Next buttons
    const prevBtn = document.getElementById('simPrev');
    const nextBtn = document.getElementById('simNext');
    if (prevBtn) prevBtn.addEventListener('click', () => {
        if (currentIndex > 0) { currentIndex--; updateModalBody(); }
    });
    if (nextBtn) nextBtn.addEventListener('click', () => {
        if (currentIndex < simDates.length - 1) { currentIndex++; updateModalBody(); }
    });

    // Date pill buttons
    document.querySelectorAll('.sim-date-pill').forEach(btn => {
        btn.addEventListener('click', () => {
            const idx = parseInt(btn.dataset.idx);
            if (idx !== currentIndex) { currentIndex = idx; updateModalBody(); }
        });
    });

    function updateModalBody() {
        const body = document.querySelector('#simModal .modal-body');
        if (body) body.innerHTML = renderModalDay();
        // Re-attach listeners after innerHTML update
        const newPrev = document.getElementById('simPrev');
        const newNext = document.getElementById('simNext');
        if (newPrev) newPrev.addEventListener('click', () => {
            if (currentIndex > 0) { currentIndex--; updateModalBody(); }
        });
        if (newNext) newNext.addEventListener('click', () => {
            if (currentIndex < simDates.length - 1) { currentIndex++; updateModalBody(); }
        });
        document.querySelectorAll('.sim-date-pill').forEach(btn => {
            btn.addEventListener('click', () => {
                const idx = parseInt(btn.dataset.idx);
                if (idx !== currentIndex) { currentIndex = idx; updateModalBody(); }
            });
        });
    }

    document.getElementById(mid).addEventListener('hidden.bs.modal', () => document.getElementById(mid)?.remove(), { once: true });
}

/* ====== Bookmark panel ====== */
function renderBookmarkPanel() {
    const bms = getBookmarks();
    const list = document.getElementById('bookmarksFullList');
    const empty = document.getElementById('bookmarkEmpty');
    if (!list) return;
    if (bms.length === 0) {
        list.innerHTML = '<p class="text-muted text-center py-3">Brak zapisanych tematów. Kliknij <i class="bi bi-bookmark"></i> przy temacie, aby zapisać.</p>';
        if (empty) empty.style.display = 'block';
        return;
    }
    if (empty) empty.style.display = 'none';
    list.innerHTML = bms.map(b => `
        <div class="bookmark-item d-flex justify-content-between align-items-center mb-2 p-2 border-bottom" data-key="${escapeHtml(b.key)}" style="border-color:var(--paper-border) !important;">
            <div>
                <div class="fw-bold" style="font-size:0.85rem;">${escapeHtml(b.keywords)}</div>
                <small class="text-muted">${b.date}</small>
            </div>
            <div>
                <button class="btn btn-sm btn-link link-btn" style="font-size:0.75rem;">Otwórz</button>
                <button class="btn btn-sm btn-outline-danger bookmark-remove" data-key="${escapeHtml(b.key)}" style="font-size:0.7rem;">Usuń</button>
            </div>
        </div>
    `).join('');
}

function renderBookmarkSidebar() {
    const bms = getBookmarks();
    const el = document.getElementById('bookmarkList');
    const emptyEl = document.getElementById('bookmarkEmpty');
    if (!el) return;
    if (bms.length === 0) { el.innerHTML = ''; if (emptyEl) emptyEl.style.display = 'block'; return; }
    if (emptyEl) emptyEl.style.display = 'none';
    el.innerHTML = bms.slice(0, 5).map(b => `<span class="badge bg-light text-dark me-1" style="cursor:pointer;font-size:0.72rem;">${escapeHtml(b.keywords)}</span>`).join('');
}

/* ====== Compare dates ====== */
async function compareDates(d1, d2) {
    const [r1, r2] = await Promise.all([
        API.summary(d1).catch(() => ({})),
        API.summary(d2).catch(() => ({})),
    ]);
    const s1 = r1.stats || {}, s2 = r2.stats || {};
    const fmt = (k) => s1[k] !== undefined ? s1[k] : '—';
    const fmt2 = (k) => s2[k] !== undefined ? s2[k] : '—';
    const html = (k) => `<div class="compare-row"><span>${k}</span><span>${fmt(k)}</span><span>→</span><span>${fmt2(k)}</span></div>`;
    return `${html('total_articles')}${html('total_clusters')}
        <div class="compare-row"><span>polarity +</span><span>${fmt('polarity')?.positive ?? '—'}</span><span>→</span><span>${fmt2('polarity')?.positive ?? '—'}</span></div>
        <div class="compare-row"><span>polarity −</span><span>${fmt('polarity')?.negative ?? '—'}</span><span>→</span><span>${fmt2('polarity')?.negative ?? '—'}</span></div>
        <div class="compare-row"><span>PLI avg</span><span>${fmt('avg_polarity_index')}</span><span>→</span><span>${fmt2('avg_polarity_index')}</span></div>`;
}

/* ====== Filter clusters ====== */
let currentSentiment = 'all';
let currentSearch = '';

function applyFilters() {
    const cards = document.querySelectorAll('.cluster-card');
    let visible = 0;
    cards.forEach(card => {
        const idx = parseInt(card.dataset.idx);
        const cluster = allClusters[idx];
        if (!cluster) return;
        const sentiment = getDominantPolarity(cluster.stats?.polarity_3c || {});
        const headline = cluster.label_str || '';
        const text = cluster.article_text || '';
        if (currentSentiment !== 'all' && sentiment !== currentSentiment) { card.style.display = 'none'; return; }
        if (card.dataset.bookmarked === 'false') { card.style.display = 'none'; return; }
        if (currentSearch) {
            const searchLower = currentSearch.toLowerCase();
            if (!headline.toLowerCase().includes(searchLower) && !text.toLowerCase().includes(searchLower)) { card.style.display = 'none'; return; }
        }
        card.style.display = '';
        visible++;
    });
    const vc = document.getElementById('visibleCount');
    if (vc) vc.textContent = `${visible} widocznych`;
}

/* ====== Main load ====== */
async function loadSummary(dateStr, gridId = 'newspaperGrid') {
    const grid = document.getElementById(gridId);
    if (grid) grid.innerHTML = '';
    hide('loadingSection'); hide('errorBox'); hide('emptySection'); hide('mainGrid');
    show('loadingSection');

    try {
        const data = await API.summary(dateStr);
        hide('loadingSection');
        const summary = data.summaries?.[0] || null;
        const clusters = summary?.clusters || [];

        if (clusters.length > 0) {
            // Pokaż statystyki
            renderDailyStats(data.stats);

            document.getElementById('resultsDate').textContent = formatDatePl(data.date);
            document.getElementById('visibleCount').textContent = `${clusters.length} widocznych`;

            // Sortowanie i hot temat
            const hotThreshold = computeHotThreshold(clusters);
            const enriched = clusters.map((c, i) => ({
                ...c,
                _hot: (c.news_urls || []).length >= hotThreshold
            }));
            const sorted = [...enriched].sort((a, b) => (b.news_urls || []).length - (a.news_urls || []).length);
            allClusters = sorted;

            sorted.forEach((c, i) => {
                if (grid) grid.insertAdjacentHTML('beforeend', renderClusterCard(c, i, data.date));
            });

            // Pokaż sidebar + mainGrid, ukryj loading/empty
            hide('loadingSection'); hide('emptySection');
            document.getElementById('statsSection').style.visibility = '';
            show('mainGrid');
            applyFilters();
            updateFloatingSidebar();
        } else {
            // Brak wyników — ukryj stats/mainGrid, pokaż empty
            document.getElementById('statsSection').style.visibility = 'hidden';
            hide('loadingSection'); hide('mainGrid');
            document.getElementById('emptyMsg').textContent = data.message || 'Brak wyników na wybrany dzień.';
            show('emptySection');
        }
    } catch (err) {
        hide('loadingSection');
        const box = document.getElementById('errorBox');
        if (box) { box.textContent = `Błąd: ${err.message}`; show('errorBox'); }
    }
}


/* ====== Load date page summary ====== */
async function loadDateSummary(dateStr, gridId) {
    const grid = document.getElementById(gridId);
    if (grid) grid.innerHTML = '';
    const dateLoading = document.getElementById('dateLoading');
    const dateEmpty = document.getElementById('dateEmptySection');
    if (dateEmpty) dateEmpty.style.display = 'none';
    if (dateLoading) dateLoading.style.display = 'block';

    try {
        const data = await API.summary(dateStr);
        if (dateLoading) dateLoading.style.display = 'none';

        const summary = data.summaries?.[0] || null;
        const clusters = summary?.clusters || [];

        if (clusters.length > 0) {
            // Sortowanie i hot temat
            const hotThreshold = computeHotThreshold(clusters);
            const enriched = clusters.map((c, i) => ({
                ...c,
                _hot: (c.news_urls || []).length >= hotThreshold
            }));
            const sorted = [...enriched].sort((a, b) => (b.news_urls || []).length - (a.news_urls || []).length);
            allClusters = sorted;

            sorted.forEach((c, i) => {
                if (grid) grid.insertAdjacentHTML('beforeend', renderClusterCard(c, i, data.date));
            });
            applyFilters();
            createFloatingSidebar();
            updateFloatingSidebar();
        } else {
            if (dateEmpty) dateEmpty.style.display = 'block';
        }
    } catch (err) {
        if (dateLoading) dateLoading.innerHTML = `<p class="mt-3 text-danger">Błąd: ${err.message}</p>`;
    }
}

/* ====== Event initializers ====== */
function initSourceExpand() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.source-expand-btn');
        if (!btn) return;
        const clusterIdx = parseInt(btn.dataset.clusterIdx);
        const remaining = parseInt(btn.dataset.remaining);
        if (!clusterIdx && clusterIdx !== 0) return;
        const allUrls = allClusters[clusterIdx]?.news_urls || [];
        const displayCount = Math.min(6, allUrls.length);
        const remainingUrls = allUrls.slice(displayCount, displayCount + remaining);
        const listId = `srcList_${clusterIdx}`;
        const list = document.getElementById(listId);
        if (!list || remainingUrls.length === 0) return;
        const items = remainingUrls.map(u => {
            let host = u; try { host = new URL(u).hostname; } catch {}
            return `<li><a href="${escapeHtml(u)}" target="_blank" rel="noopener">${escapeHtml(host)}</a></li>`;
        }).join('');
        list.insertAdjacentHTML('beforeend', items);
        btn.style.display = 'none';
    });
}

function initBookmarks() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.bookmark-btn');
        if (btn) {
            const key = btn.dataset.bookkey;
            const keywords = btn.dataset.keywords;
            const card = btn.closest('.cluster-card');
            const idx = parseInt(card?.dataset.idx || 0);
            const date = card?.dataset.date || '';
            toggleBookmark(key, { keywords, date, idx });
            const bms = getBookmarks();
            const isBk = bms.some(b => b.key === key);
            btn.innerHTML = `<i class="bi ${isBk ? 'bi-bookmark-fill' : 'bi-bookmark'}"></i>`;
            btn.style.color = isBk ? 'var(--accent)' : 'var(--ink-light)';
            renderBookmarkPanel();
            renderBookmarkSidebar();
        }
        const rmBtn = e.target.closest('.bookmark-remove');
        if (rmBtn) {
            const key = rmBtn.dataset.key;
            toggleBookmark(key, { keywords: '', date: '', idx: 0 });
            renderBookmarkPanel();
            renderBookmarkSidebar();
        }
        // Otwórz — navigate to bookmarked date or scroll to card
        const okBtn = e.target.closest('.link-btn');
        if (okBtn) {
            const item = okBtn.closest('.bookmark-item');
            if (!item) return;
            const key = item.dataset?.key || '';
            const bm = getBookmarks().find(b => b.key === key);
            if (!bm) return;

            // Check if we're already on the date page for this bookmark
            if (bm.date) {
                let currentDate = null;
                const urlPath = window.location.pathname;
                const dateMatch = urlPath.match(/^\/date\/(.+)$/);
                if (dateMatch) {
                    currentDate = dateMatch[1];
                } else {
                    const dp = document.getElementById('datePicker');
                    if (dp) currentDate = dp.value;
                }

                if (currentDate && currentDate === bm.date) {
                    // Already on the correct date page — scroll to card
                    const cards = document.querySelectorAll('.cluster-card');
                    let found = false;
                    cards.forEach(card => {
                        if (parseInt(card.dataset.idx) === bm.idx) {
                            card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                            card.classList.add('sidebar-highlight');
                            setTimeout(() => card.classList.remove('sidebar-highlight'), 2500);
                            found = true;
                        }
                    });
                    if (found) return;
                }
                // Different date — navigate to that page
                window.open('/date/' + bm.date + '?topic=' + (bm.idx || 0), '_blank');
                return;
            }

            // Fallback: try to find card on current page
            const cards = document.querySelectorAll('.cluster-card');
            cards.forEach(card => {
                const idx = parseInt(card.dataset.idx);
                if (idx === bm.idx && card.dataset.date === bm.date) {
                    card.scrollIntoView({ behavior: 'smooth', block: 'start' });
                    card.classList.add('sidebar-highlight');
                // Collapse sidebar on mobile
                if (window.innerWidth <= 991) {
                    const sb = document.getElementById('floatingSidebar');
                    sb.classList.add('collapsed');
                    const tg = document.getElementById('sidebarToggle');
                    tg.innerHTML = '<i class="bi bi-list-nested"></i>';
                }
                    setTimeout(() => card.classList.remove('sidebar-highlight'), 2500);
                }
            });
        }
    });
}

function initSentimentFilter() {
    document.addEventListener('click', (e) => {
        const btn = e.target.closest('.sentiment-btn');
        if (btn) {
            document.querySelectorAll('.sentiment-btn').forEach(b => b.classList.remove('active'));
            btn.classList.add('active');
            currentSentiment = btn.dataset.sentiment;
            applyFilters();
        }
    });
}

function initSearch() {
    const input = document.getElementById('searchInput');
    if (input) {
        input.addEventListener('input', (e) => {
            currentSearch = e.target.value;
            applyFilters();
        });
    }
}

function initDateNav() {
    const picker = document.getElementById('datePicker');
    const prevBtn = document.getElementById('prevDay');
    const nextBtn = document.getElementById('nextDay');

    if (prevBtn) prevBtn.addEventListener('click', () => { if (picker?.value) { picker.value = addDays(picker.value, -1); loadSummary(picker.value); } });
    if (nextBtn) nextBtn.addEventListener('click', () => { if (picker?.value) { picker.value = addDays(picker.value, 1); loadSummary(picker.value); } });
    if (picker) picker.addEventListener('change', () => { if (picker.value) loadSummary(picker.value); });

    const qd = document.getElementById('quickDates');
    if (qd) {
        qd.innerHTML = '';
        const today = new Date();
        for (let i = 0; i < 7; i++) {
            const d = new Date(today.getFullYear(), today.getMonth(), today.getDate() - i);
            const ds = d.toISOString().split('T')[0];
            const btn = document.createElement('button');
            btn.className = 'quick-date-btn';
            btn.textContent = formatDatePl(ds);
            btn.addEventListener('click', () => {
                if (picker) picker.value = ds;
                loadSummary(ds);
                qd.querySelectorAll('.quick-date-btn').forEach(b => b.classList.remove('active'));
                btn.classList.add('active');
            });
            qd.appendChild(btn);
        }
    // Auto-load yesterday on page entry
    if (picker?.value) loadSummary(picker.value);
    }
}

function initSimilarity() {
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('similarity-date-btn')) {
            const card = e.target.closest('.cluster-card');
            if (!card) return;
            const idx = parseInt(card.dataset.idx);
            const cluster = allClusters[idx];
            if (!cluster?.similarity) return;
            showSimilarityModal(card.dataset.date, cluster.similarity);
        }
    });
}

function initCompare() {
    const toggle = document.getElementById('toggleCompare');
    const overlay = document.getElementById('compareOverlay');
    const close = document.getElementById('closeCompare');
    const d1 = document.getElementById('compareDate1');
    const d2 = document.getElementById('compareDate2');

    if (toggle) {
        toggle.addEventListener('click', () => {
            if (overlay.style.display === 'block') { hide('compareOverlay'); return; }
            show('compareOverlay');
            if (d1 && !d1.value) { d1.value = document.getElementById('datePicker')?.value || addDays(new Date().toISOString(), -1); }
            if (d2 && !d2.value) { d2.value = document.getElementById('datePicker')?.value || addDays(new Date().toISOString(), -2); }
            doCompare();
        });
    }
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
    r1.innerHTML = '<div class="spinner-border spinner-border-sm text-primary"></div>';
    r2.innerHTML = '<div class="spinner-border spinner-border-sm text-primary"></div>';
    const [s1, s2] = await Promise.all([
        API.summary(d1).catch(() => ({})),
        API.summary(d2).catch(() => ({})),
    ]);
    const fmtStats = (s) => {
        if (!s.stats) return '<span class="text-muted">Brak danych</span>';
        return `<div class="compare-stats-box mt-2">
            <div class="d-flex gap-3" style="font-size:0.82rem;">
                <div><strong>${s.stats.total_articles}</strong> artykułów</div>
                <div><strong>${s.stats.total_clusters}</strong> tematów</div>
                <div><strong>${s.stats.avg_polarity_index}</strong> PLI</div>
            </div>
        </div>`;
    };
    r1.innerHTML = `<div style="font-size:0.8rem;font-weight:bold;">${formatDatePl(d1)}</div>${fmtStats(s1)}`;
    r2.innerHTML = `<div style="font-size:0.8rem;font-weight:bold;">${formatDatePl(d2)}</div>${fmtStats(s2)}`;
}

function initBookmarksPanel() {
    const toggle = document.getElementById('toggleBookmarks');
    const overlay = document.getElementById('bookmarksOverlay');
    const close = document.getElementById('closeBookmarks');
    if (toggle) toggle.addEventListener('click', () => {
        if (overlay.style.display === 'block') { hide('bookmarksOverlay'); return; }
        show('bookmarksOverlay');
        renderBookmarkPanel();
    });
    if (close) close.addEventListener('click', () => hide('bookmarksOverlay'));
}

function initThemeToggle() {
    const btn = document.getElementById('toggleTheme');
    const saved = localStorage.getItem('iv_theme');
    if (saved === 'dark') { document.documentElement.setAttribute('data-bs-theme', 'dark'); }
    if (btn) {
        btn.innerHTML = saved === 'dark' ? '<i class="bi bi-sun"></i>' : '<i class="bi bi-moon-stars"></i>';
        btn.addEventListener('click', () => {
            const isDark = document.documentElement.getAttribute('data-bs-theme') === 'dark';
            const newTheme = isDark ? 'light' : 'dark';
            document.documentElement.setAttribute('data-bs-theme', newTheme);
            localStorage.setItem('iv_theme', newTheme);
            btn.innerHTML = isDark ? '<i class="bi bi-moon-stars"></i>' : '<i class="bi bi-sun"></i>';
        });
    }
}

function initExport() {
    document.addEventListener('click', (e) => {
        if (e.target.closest('#exportBtn')) {
            const date = document.getElementById('resultsDate')?.textContent || 'unknown';
            let md = `# ${date}\n\n`;
            allClusters.forEach((c, i) => {
                md += `## ${c.label_str}\n\n${c.article_text}\n\n---\n\n`;
            });
            const blob = new Blob([md], { type: 'text/markdown' });
            const a = document.createElement('a');
            a.href = URL.createObjectURL(blob);
            a.download = `info-viewer-${date.replace(/ /g, '-')}.md`;
            a.click();
            URL.revokeObjectURL(a.href);
        }
    });
}

document.addEventListener('DOMContentLoaded', () => {
    initDateNav();
    initSearch();
    initSentimentFilter();
    initSourceExpand();
    initBookmarks();
    initBookmarksPanel();
    initThemeToggle();
    initCompare();
    initExport();
    initSimilarity();
    createFloatingSidebar();
    initScrollSpy();
    initScrollTop();
    API.status().catch(() => {});
});

/* ====== Scroll to top ====== */
function initScrollTop() {
    const btn = document.getElementById('scrollTopBtn');
    if (!btn) return;
    window.addEventListener('scroll', () => {
        btn.classList.toggle('visible', window.scrollY > 400);
    }, { passive: true });
    btn.addEventListener('click', () => {
        window.scrollTo({ top: 0, behavior: 'smooth' });
    });
}
