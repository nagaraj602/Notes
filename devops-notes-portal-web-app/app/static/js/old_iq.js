/**
 * Old Interview Questions Repository - Client-Side Controller
 * Handles live search, multi-criteria sorting (rounds, companies, favorites, questions),
 * company and round accordions, favorites bookmarking in localStorage,
 * markdown answer rendering, and fast category filtering.
 */

let currentCategory = 'ALL';
let currentCompany = 'ALL';
let currentRound = 'ALL';
let currentSort = 'default';
let favoritesOnly = false;
let favoriteQuestions = new Set();

// Initialize favorites from localStorage
try {
  const savedFavs = JSON.parse(localStorage.getItem('devops_old_iq_favorites') || '[]');
  if (Array.isArray(savedFavs)) {
    favoriteQuestions = new Set(savedFavs);
  }
} catch (e) {
  favoriteQuestions = new Set();
}

// Toggle company accordion
function toggleCompany(compSafeName) {
  const content = document.getElementById(`content-comp-${compSafeName}`);
  const chevron = document.getElementById(`chevron-comp-${compSafeName}`);
  if (!content || !chevron) return;
  
  if (content.classList.contains('hidden')) {
    content.classList.remove('hidden');
    chevron.classList.add('rotate-180');
  } else {
    content.classList.add('hidden');
    chevron.classList.remove('rotate-180');
  }
}

// Toggle round accordion
function toggleRound(roundId) {
  const content = document.getElementById(`content-round-${roundId}`);
  const chevron = document.getElementById(`chevron-round-${roundId}`);
  if (!content || !chevron) return;

  if (content.classList.contains('hidden')) {
    content.classList.remove('hidden');
    chevron.classList.add('rotate-180');
  } else {
    content.classList.add('hidden');
    chevron.classList.remove('rotate-180');
  }
}

// Toggle individual question answer
function toggleQuestionAnswer(qId) {
  if (window.getSelection && window.getSelection().toString().trim().length > 0) {
    return; // User was highlighting or selecting text, do not toggle accordion
  }
  const ans = document.getElementById(`ans-${qId}`);
  const icon = document.getElementById(`icon-q-${qId}`);
  const badge = document.getElementById(`badge-q-${qId}`);
  const badgeText = document.getElementById(`badge-text-${qId}`);
  const card = document.getElementById(`card-q-${qId}`);
  if (!ans) return;

  if (ans.classList.contains('hidden')) {
    ans.classList.remove('hidden');
    if (icon) icon.classList.add('rotate-180');
    if (badge) {
      badge.className = "flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-sky-600 text-white border border-sky-600 text-xs font-bold transition-all flex-shrink-0 shadow-xs";
    }
    if (badgeText) badgeText.innerText = "Hide";
    if (card) {
      card.classList.add('border-sky-400', 'ring-2', 'ring-sky-100');
    }
    formatMarkdownAnswer(qId);
  } else {
    ans.classList.add('hidden');
    if (icon) icon.classList.remove('rotate-180');
    if (badge) {
      badge.className = "flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 group-hover:bg-sky-100 text-slate-700 group-hover:text-sky-800 border border-slate-200/80 group-hover:border-sky-300 text-xs font-bold transition-all flex-shrink-0 shadow-2xs";
    }
    if (badgeText) badgeText.innerText = "Answer";
    if (card) {
      card.classList.remove('border-sky-400', 'ring-2', 'ring-sky-100');
    }
  }
}

// Format markdown inside answer on demand from uncollapsed raw template
function formatMarkdownAnswer(qId) {
  const template = document.getElementById(`raw-ans-${qId}`);
  const ansEl = document.getElementById(`ans-text-${qId}`);
  if (!template || !ansEl || ansEl.dataset.formatted === 'true') return;
  try {
    let raw = template.innerHTML;
    raw = raw.replace(/&lt;/g, '<')
             .replace(/&gt;/g, '>')
             .replace(/&amp;/g, '&')
             .replace(/&quot;/g, '"')
             .replace(/&#39;/g, "'")
             .replace(/&#x27;/g, "'");

    if (window.marked) {
      marked.setOptions({
        breaks: true,
        gfm: true
      });
      ansEl.innerHTML = marked.parse(raw);
      if (window.Prism) {
        Prism.highlightAllUnder(ansEl);
      }
    } else {
      ansEl.textContent = raw;
    }
    ansEl.dataset.formatted = 'true';
  } catch (e) {
    console.warn('Formatting error:', e);
  }
}

// Expand / Collapse all companies & rounds
function toggleAllCompanies(expand) {
  document.querySelectorAll('.company-content').forEach(el => {
    if (expand) el.classList.remove('hidden');
    else el.classList.add('hidden');
  });
  document.querySelectorAll('[id^="chevron-comp-"]').forEach(ch => {
    if (expand) ch.classList.add('rotate-180');
    else ch.classList.remove('rotate-180');
  });
  document.querySelectorAll('.round-content').forEach(el => {
    if (expand) el.classList.remove('hidden');
    else el.classList.add('hidden');
  });
  document.querySelectorAll('[id^="chevron-round-"]').forEach(ch => {
    if (expand) ch.classList.add('rotate-180');
    else ch.classList.remove('rotate-180');
  });
}

// Show / Hide all answers
function toggleAllAnswers(show) {
  document.querySelectorAll('.ans-content').forEach(el => {
    const qId = el.id.replace('ans-', '');
    const icon = document.getElementById(`icon-q-${qId}`);
    const badge = document.getElementById(`badge-q-${qId}`);
    const badgeText = document.getElementById(`badge-text-${qId}`);
    const card = document.getElementById(`card-q-${qId}`);

    if (show) {
      el.classList.remove('hidden');
      if (icon) icon.classList.add('rotate-180');
      if (badge) badge.className = "flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-sky-600 text-white border border-sky-600 text-xs font-bold transition-all flex-shrink-0 shadow-xs";
      if (badgeText) badgeText.innerText = "Hide";
      if (card) card.classList.add('border-sky-400', 'ring-2', 'ring-sky-100');
      formatMarkdownAnswer(qId);
    } else {
      el.classList.add('hidden');
      if (icon) icon.classList.remove('rotate-180');
      if (badge) badge.className = "flex items-center space-x-1.5 px-3 py-1.5 rounded-xl bg-slate-100 group-hover:bg-sky-100 text-slate-700 group-hover:text-sky-800 border border-slate-200/80 group-hover:border-sky-300 text-xs font-bold transition-all flex-shrink-0 shadow-2xs";
      if (badgeText) badgeText.innerText = "Answer";
      if (card) card.classList.remove('border-sky-400', 'ring-2', 'ring-sky-100');
    }
  });
}

// Copy Question Text Only
function copyQuestionOnly(qId, event) {
  if (event) event.stopPropagation();
  const qTextEl = document.getElementById(`q-text-${qId}`);
  const copyIcon = document.getElementById(`copy-q-icon-${qId}`);
  if (!qTextEl) return;
  const text = qTextEl.innerText.trim();

  navigator.clipboard.writeText(text).then(() => {
    if (copyIcon) {
      copyIcon.className = 'fa-solid fa-check text-emerald-600';
      setTimeout(() => {
        copyIcon.className = 'fa-regular fa-copy text-[11px]';
      }, 2000);
    }
  }).catch(err => {
    console.error('Failed to copy question:', err);
  });
}

// Copy Answer Text
function copyAnswerText(qId, event) {
  event.stopPropagation();
  const template = document.getElementById(`raw-ans-${qId}`);
  const copyIcon = document.getElementById(`copy-icon-${qId}`);
  if (!template) return;
  
  let text = template.innerHTML
    .replace(/&lt;/g, '<')
    .replace(/&gt;/g, '>')
    .replace(/&amp;/g, '&')
    .replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'")
    .replace(/&#x27;/g, "'");

  navigator.clipboard.writeText(text).then(() => {
    if (copyIcon) {
      copyIcon.className = 'fa-solid fa-check text-emerald-400';
      setTimeout(() => {
        copyIcon.className = 'fa-regular fa-copy';
      }, 2000);
    }
  });
}

// Toggle individual question favorite/bookmark
function toggleFavoriteQuestion(qId, event) {
  if (event) event.stopPropagation();
  const card = document.getElementById(`card-q-${qId}`);
  
  if (favoriteQuestions.has(qId)) {
    favoriteQuestions.delete(qId);
    if (card) card.dataset.isFav = 'false';
    updateFavButtonUI(qId, false);
  } else {
    favoriteQuestions.add(qId);
    if (card) card.dataset.isFav = 'true';
    updateFavButtonUI(qId, true);
  }

  try {
    localStorage.setItem('devops_old_iq_favorites', JSON.stringify(Array.from(favoriteQuestions)));
  } catch (e) {
    console.warn("Could not save favorites to localStorage", e);
  }

  updateFavoriteCounters();

  if (currentSort === 'favorites-first') {
    applySorting();
  }

  if (favoritesOnly) {
    applyFilters();
  }
}

function updateFavButtonUI(qId, isFav) {
  const btn = document.getElementById(`fav-btn-${qId}`);
  const icon = document.getElementById(`fav-icon-${qId}`);
  const text = document.getElementById(`fav-text-${qId}`);
  if (!btn) return;

  if (isFav) {
    btn.className = "px-2.5 py-1.5 rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-600 border border-amber-300 ring-2 ring-amber-100/70 text-xs font-bold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer group/fav";
    btn.title = "Favorited! Click to remove from favorites";
    if (icon) icon.className = "fa-solid fa-star text-[11px] text-amber-500 scale-110 transition-transform";
    if (text) text.innerText = "Saved";
  } else {
    btn.className = "px-2.5 py-1.5 rounded-xl bg-white hover:bg-amber-50 text-slate-400 hover:text-amber-500 border border-slate-200/80 hover:border-amber-300 text-xs font-semibold transition-all flex items-center gap-1.5 shadow-2xs cursor-pointer group/fav";
    btn.title = "Bookmark / Mark as Favorite";
    if (icon) icon.className = "fa-regular fa-star text-[11px] group-hover/fav:scale-110 transition-transform";
    if (text) text.innerText = "Star";
  }
}

function updateFavoriteCounters() {
  const count = favoriteQuestions.size;
  const statEl = document.getElementById('statTotalFavorites');
  const pillEl = document.getElementById('favPillCount');
  if (statEl) statEl.innerText = count;
  if (pillEl) pillEl.innerText = count;
}

function toggleFavoritesOnlyFilter(forceState) {
  const chk = document.getElementById('favFilterCheckbox');
  if (forceState !== undefined) {
    favoritesOnly = !!forceState;
  } else {
    favoritesOnly = chk ? chk.checked : !favoritesOnly;
  }
  if (chk) chk.checked = favoritesOnly;

  updateFavFilterBtnUI();
  toggleAllAnswers(false);
  applyFilters();
}

function updateFavFilterBtnUI() {
  const label = document.getElementById('favFilterLabel');
  const icon = document.getElementById('favFilterIcon');
  const chk = document.getElementById('favFilterCheckbox');
  if (chk) chk.checked = favoritesOnly;
  if (!label) return;

  if (favoritesOnly) {
    label.className = "fav-pill active-fav-filter inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-bold transition-all bg-amber-50 text-amber-900 border border-amber-400 ring-2 ring-amber-200/60 cursor-pointer shadow-2xs mr-1 select-none";
    if (icon) icon.className = "fa-solid fa-star text-amber-500 text-xs";
  } else {
    label.className = "fav-pill inline-flex items-center space-x-2 px-3 py-1.5 rounded-xl text-xs font-bold transition-all bg-white text-slate-700 border border-slate-300 hover:border-amber-400 hover:bg-amber-50/60 cursor-pointer shadow-2xs mr-1 select-none";
    if (icon) icon.className = "fa-regular fa-star text-amber-500 text-xs";
  }
}

// Dynamic Round Selector Population
function populateRoundOptions() {
  const roundSelect = document.getElementById('roundSelect');
  if (!roundSelect) return;

  const previousSelected = currentRound;
  const roundMap = new Map();

  const companyCards = document.querySelectorAll('.company-card');
  companyCards.forEach(card => {
    const compName = card.getAttribute('data-company') || '';
    if (currentCompany !== 'ALL' && compName.toLowerCase() !== currentCompany.toLowerCase()) {
      return;
    }
    const roundCards = card.querySelectorAll('.round-card');
    roundCards.forEach(rc => {
      const rName = rc.getAttribute('data-round');
      if (!rName) return;
      const qCount = rc.querySelectorAll('.question-card').length;
      roundMap.set(rName, (roundMap.get(rName) || 0) + qCount);
    });
  });

  roundSelect.innerHTML = '';
  const allOpt = document.createElement('option');
  allOpt.value = 'ALL';
  allOpt.textContent = `All Rounds (${roundMap.size})`;
  roundSelect.appendChild(allOpt);

  const sortedRounds = Array.from(roundMap.keys()).sort((a, b) => {
    const wa = getRoundStageWeight(a);
    const wb = getRoundStageWeight(b);
    if (wa !== wb) return wa - wb;
    return a.localeCompare(b);
  });

  sortedRounds.forEach(rName => {
    const opt = document.createElement('option');
    opt.value = rName;
    opt.textContent = `${rName} (${roundMap.get(rName)} Qs)`;
    roundSelect.appendChild(opt);
  });

  if (roundMap.has(previousSelected)) {
    roundSelect.value = previousSelected;
    currentRound = previousSelected;
  } else {
    roundSelect.value = 'ALL';
    currentRound = 'ALL';
  }
}

function getRoundStageWeight(name) {
  const n = (name || '').toLowerCase();
  if (n.includes('assessment') || n.includes('hackerrank') || n.includes('screening') || n.includes('online')) return 1;
  if (n.includes('l1') || n.includes('level 1') || n.includes('round 1') || n.includes('tech 1') || n.includes('technical discussion - 1') || n.includes('technical 1')) return 2;
  if (n.includes('l2') || n.includes('level 2') || n.includes('round 2') || n.includes('tech 2') || n.includes('technical 2')) return 3;
  if (n.includes('l3') || n.includes('level 3') || n.includes('round 3') || n.includes('client round')) return 4;
  if (n.includes('manager') || n.includes('behavioral') || n.includes('hr')) return 5;
  return 6;
}

// Sorting
function handleSortChange() {
  const select = document.getElementById('sortSelect');
  currentSort = select ? select.value : 'default';
  applySorting();
}

function applySorting() {
  const sortMode = currentSort;
  const container = document.getElementById('companiesContainer');
  if (!container) return;

  // 1. Company-level sorting
  if (sortMode === 'company-asc' || sortMode === 'company-desc' || sortMode === 'most-questions' || sortMode === 'default') {
    const compCards = Array.from(container.querySelectorAll('.company-card'));
    compCards.sort((a, b) => {
      if (sortMode === 'company-asc') {
        const an = a.getAttribute('data-company') || '';
        const bn = b.getAttribute('data-company') || '';
        return an.localeCompare(bn);
      } else if (sortMode === 'company-desc') {
        const an = a.getAttribute('data-company') || '';
        const bn = b.getAttribute('data-company') || '';
        return bn.localeCompare(an);
      } else if (sortMode === 'most-questions') {
        const aq = parseInt(a.getAttribute('data-total-questions') || '0', 10);
        const bq = parseInt(b.getAttribute('data-total-questions') || '0', 10);
        return bq - aq;
      } else {
        const ai = parseInt(a.getAttribute('data-original-comp-index') || '0', 10);
        const bi = parseInt(b.getAttribute('data-original-comp-index') || '0', 10);
        return ai - bi;
      }
    });
    compCards.forEach(c => container.appendChild(c));
  }

  // 2. Round-level sorting
  const companyContents = document.querySelectorAll('.company-content');
  companyContents.forEach(compContent => {
    const rCards = Array.from(compContent.querySelectorAll('.round-card'));
    if (rCards.length <= 1) return;

    rCards.sort((a, b) => {
      if (sortMode === 'round-asc') {
        const wa = getRoundStageWeight(a.getAttribute('data-round'));
        const wb = getRoundStageWeight(b.getAttribute('data-round'));
        if (wa !== wb) return wa - wb;
        return (a.getAttribute('data-round') || '').localeCompare(b.getAttribute('data-round') || '');
      } else if (sortMode === 'round-desc') {
        const wa = getRoundStageWeight(a.getAttribute('data-round'));
        const wb = getRoundStageWeight(b.getAttribute('data-round'));
        if (wa !== wb) return wb - wa;
        return (b.getAttribute('data-round') || '').localeCompare(a.getAttribute('data-round') || '');
      } else if (sortMode === 'round-name') {
        return (a.getAttribute('data-round') || '').localeCompare(b.getAttribute('data-round') || '');
      } else {
        const ai = parseInt(a.getAttribute('data-original-round-index') || '0', 10);
        const bi = parseInt(b.getAttribute('data-original-round-index') || '0', 10);
        return ai - bi;
      }
    });
    rCards.forEach(rc => compContent.appendChild(rc));
  });

  // 3. Question-level sorting
  const roundContents = document.querySelectorAll('.round-content');
  roundContents.forEach(roundContainer => {
    const qCards = Array.from(roundContainer.querySelectorAll('.question-card'));
    if (qCards.length <= 1) return;

    qCards.sort((a, b) => {
      if (sortMode === 'favorites-first') {
        const aFav = a.dataset.isFav === 'true' ? 1 : 0;
        const bFav = b.dataset.isFav === 'true' ? 1 : 0;
        if (aFav !== bFav) return bFav - aFav;
        return (parseInt(a.dataset.originalIndex || 0)) - (parseInt(b.dataset.originalIndex || 0));
      } else if (sortMode === 'alpha-asc') {
        const aText = a.querySelector('.q-text')?.innerText.trim() || '';
        const bText = b.querySelector('.q-text')?.innerText.trim() || '';
        return aText.localeCompare(bText, undefined, { sensitivity: 'base' });
      } else if (sortMode === 'alpha-desc') {
        const aText = a.querySelector('.q-text')?.innerText.trim() || '';
        const bText = b.querySelector('.q-text')?.innerText.trim() || '';
        return bText.localeCompare(aText, undefined, { sensitivity: 'base' });
      } else if (sortMode === 'has-answer') {
        const aAns = a.getAttribute('data-has-answer') === 'true' ? 1 : 0;
        const bAns = b.getAttribute('data-has-answer') === 'true' ? 1 : 0;
        if (aAns !== bAns) return bAns - aAns;
        return (parseInt(a.dataset.originalIndex || 0)) - (parseInt(b.dataset.originalIndex || 0));
      } else {
        return (parseInt(a.dataset.originalIndex || 0)) - (parseInt(b.dataset.originalIndex || 0));
      }
    });
    qCards.forEach(card => roundContainer.appendChild(card));
  });
}

// Category Selection
function selectCategory(cat) {
  currentCategory = cat;
  document.querySelectorAll('.cat-pill').forEach(btn => {
    if (btn.getAttribute('data-cat') === cat) {
      btn.classList.add('active-cat');
    } else {
      btn.classList.remove('active-cat');
    }
  });

  toggleAllAnswers(false);

  if (cat === 'ALL' && !favoritesOnly && currentCompany === 'ALL' && currentRound === 'ALL') {
    toggleAllCompanies(false);
  }

  applyFilters();
}

// Company Dropdown Selection
function handleCompanyFilter() {
  const select = document.getElementById('companySelect');
  currentCompany = select ? select.value : 'ALL';
  currentRound = 'ALL';
  populateRoundOptions();
  applyFilters();
}

// Round Dropdown Selection
function handleRoundFilter() {
  const select = document.getElementById('roundSelect');
  currentRound = select ? select.value : 'ALL';
  applyFilters();
}

// Live Search
function handleSearch() {
  const input = document.getElementById('searchInput');
  const clearBtn = document.getElementById('clearSearchBtn');
  if (input && input.value.trim().length > 0) {
    if (clearBtn) clearBtn.classList.remove('hidden');
  } else {
    if (clearBtn) clearBtn.classList.add('hidden');
  }
  applyFilters();
}

function clearSearch() {
  const input = document.getElementById('searchInput');
  if (input) input.value = '';
  const clearBtn = document.getElementById('clearSearchBtn');
  if (clearBtn) clearBtn.classList.add('hidden');
  applyFilters();
}

function resetFilters() {
  favoritesOnly = false;
  currentCompany = 'ALL';
  currentRound = 'ALL';
  currentSort = 'default';
  currentCategory = 'ALL';

  const chk = document.getElementById('favFilterCheckbox');
  if (chk) chk.checked = false;
  updateFavFilterBtnUI();

  const sInput = document.getElementById('searchInput');
  if (sInput) sInput.value = '';
  const clrBtn = document.getElementById('clearSearchBtn');
  if (clrBtn) clrBtn.classList.add('hidden');

  const compSel = document.getElementById('companySelect');
  if (compSel) compSel.value = 'ALL';

  const sortSel = document.getElementById('sortSelect');
  if (sortSel) sortSel.value = 'default';

  populateRoundOptions();
  applySorting();
  selectCategory('ALL');
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");
}

// Core Filtering Logic
function applyFilters() {
  const searchInput = document.getElementById('searchInput');
  const searchVal = searchInput ? searchInput.value.trim().toLowerCase() : '';
  let visibleQuestions = 0;
  let visibleCompanies = 0;
  let visibleRounds = 0;

  const isDefaultInitialState = (currentCategory === 'ALL' && !searchVal && currentCompany === 'ALL' && currentRound === 'ALL' && !favoritesOnly && currentSort === 'default');

  if (isDefaultInitialState) {
    toggleAllCompanies(false);
    toggleAllAnswers(false);
  }

  const isFiltered = (searchVal.length > 0 || currentCategory !== 'ALL' || currentCompany !== 'ALL' || currentRound !== 'ALL' || favoritesOnly);

  const companyCards = document.querySelectorAll('.company-card');

  companyCards.forEach(card => {
    const compName = card.getAttribute('data-company') || '';
    let companyMatchesFilter = (currentCompany === 'ALL' || compName.toLowerCase() === currentCompany.toLowerCase());
    
    let companyHasMatchingQuestions = false;
    const roundCards = card.querySelectorAll('.round-card');

    roundCards.forEach(roundCard => {
      const roundName = roundCard.getAttribute('data-round') || '';
      let roundMatchesFilter = (currentRound === 'ALL' || roundName.toLowerCase() === currentRound.toLowerCase());

      let roundHasMatchingQuestions = false;
      const qItems = roundCard.querySelectorAll('.question-card');

      qItems.forEach(qItem => {
        const qCat = qItem.getAttribute('data-cat') || '';
        const qId = qItem.getAttribute('data-q-id');
        const qText = qItem.querySelector('.q-text')?.innerText.toLowerCase() || '';
        const rawTpl = document.getElementById(`raw-ans-${qId}`);
        const ansText = (rawTpl ? rawTpl.innerHTML : (qItem.querySelector('.answer-markdown')?.innerText || '')).toLowerCase();

        const isFav = (qItem.dataset.isFav === 'true');
        const matchesFav = (!favoritesOnly || isFav);
        const matchesCat = (currentCategory === 'ALL' || qCat.toLowerCase() === currentCategory.toLowerCase());
        const matchesSearch = (!searchVal || qText.includes(searchVal) || ansText.includes(searchVal) || compName.toLowerCase().includes(searchVal) || roundName.toLowerCase().includes(searchVal) || qCat.toLowerCase().includes(searchVal));

        if (companyMatchesFilter && roundMatchesFilter && matchesCat && matchesSearch && matchesFav) {
          qItem.classList.remove('hidden');
          roundHasMatchingQuestions = true;
          companyHasMatchingQuestions = true;
          visibleQuestions++;
        } else {
          qItem.classList.add('hidden');
        }
      });

      if (companyMatchesFilter && roundMatchesFilter && roundHasMatchingQuestions) {
        roundCard.classList.remove('hidden');
        visibleRounds++;
        if (isFiltered) {
          const rContent = roundCard.querySelector('.round-content');
          if (rContent) rContent.classList.remove('hidden');
          const rChevron = roundCard.querySelector('[id^="chevron-round-"]');
          if (rChevron) rChevron.classList.add('rotate-180');
        }
      } else {
        roundCard.classList.add('hidden');
        const rContent = roundCard.querySelector('.round-content');
        if (rContent) rContent.classList.add('hidden');
        const rChevron = roundCard.querySelector('[id^="chevron-round-"]');
        if (rChevron) rChevron.classList.remove('rotate-180');
      }
    });

    if (companyMatchesFilter && companyHasMatchingQuestions) {
      card.classList.remove('hidden');
      visibleCompanies++;
      if (isFiltered) {
        const content = card.querySelector('.company-content');
        if (content) content.classList.remove('hidden');
        const cChevron = card.querySelector('[id^="chevron-comp-"]');
        if (cChevron) cChevron.classList.add('rotate-180');
      }
    } else {
      card.classList.add('hidden');
      const content = card.querySelector('.company-content');
      if (content) content.classList.add('hidden');
      const cChevron = card.querySelector('[id^="chevron-comp-"]');
      if (cChevron) cChevron.classList.remove('rotate-180');
    }
  });

  // Update Filter Notice & Results Counter
  const filterNotice = document.getElementById('filterNotice');
  const resultsCount = document.getElementById('resultsCount');
  const emptyState = document.getElementById('emptyState');

  if (isFiltered) {
    if (filterNotice) filterNotice.classList.remove('hidden');
    let detailParts = [];
    if (currentCompany !== 'ALL') detailParts.push(`Company: <strong>${escapeHtml(currentCompany)}</strong>`);
    if (currentRound !== 'ALL') detailParts.push(`Round: <strong>${escapeHtml(currentRound)}</strong>`);
    if (currentCategory !== 'ALL') detailParts.push(`Category: <strong>${escapeHtml(currentCategory)}</strong>`);
    if (favoritesOnly) detailParts.push(`<span class="text-amber-600 font-bold"><i class="fa-solid fa-star text-amber-500"></i> Starred Favorites Only</span>`);
    if (searchVal) detailParts.push(`Query: "<strong>${escapeHtml(searchVal)}</strong>"`);

    const detailsStr = detailParts.length > 0 ? ` (${detailParts.join(' • ')})` : '';
    if (resultsCount) {
      resultsCount.innerHTML = `Showing <strong>${visibleQuestions}</strong> question${visibleQuestions === 1 ? '' : 's'} across <strong>${visibleCompanies}</strong> compan${visibleCompanies === 1 ? 'y' : 'ies'}${detailsStr}`;
    }
  } else {
    if (filterNotice) filterNotice.classList.add('hidden');
  }

  if (visibleCompanies === 0) {
    if (emptyState) {
      emptyState.classList.remove('hidden');
      const emptyTitle = emptyState.querySelector('h3');
      const emptyDesc = emptyState.querySelector('p');
      if (favoritesOnly) {
        if (emptyTitle) emptyTitle.innerText = "No Favorite Questions Found";
        if (emptyDesc) emptyDesc.innerText = currentCategory !== 'ALL' 
          ? `You have no favorite questions under category "${currentCategory}". Star any question in this category or switch categories.`
          : "You haven't bookmarked any favorite questions yet. Click the 'Star' button on any question to add it to your favorites!";
      } else {
        if (emptyTitle) emptyTitle.innerText = "No Interview Questions Found";
        if (emptyDesc) emptyDesc.innerText = "No questions match your current search, round, and company filters. Try adjusting your query or resetting filters.";
      }
    }
  } else {
    if (emptyState) emptyState.classList.add('hidden');
  }
}

// Initialize: Tag original indices, load favorites from storage, and set initial filter
document.addEventListener('DOMContentLoaded', () => {
  document.querySelectorAll('.question-card').forEach((card, idx) => {
    card.dataset.originalIndex = idx;
    const qId = card.getAttribute('data-q-id');
    const isFav = favoriteQuestions.has(qId);
    card.dataset.isFav = isFav ? 'true' : 'false';
    updateFavButtonUI(qId, isFav);
  });

  updateFavoriteCounters();
  populateRoundOptions();
  selectCategory('ALL');
});
