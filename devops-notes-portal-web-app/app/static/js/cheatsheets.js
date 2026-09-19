/**
 * DevOps Commands & Manifests Cheat Sheets - Client-Side Controller
 * Handles live search, section filtering, card view vs table view toggling,
 * one-click command and code copying, and real-time counter updates.
 */

let activeCategoryId = "all";
let activeSectionId = "ALL";
let currentSearchQuery = "";
let currentViewMode = "cards"; // 'cards' or 'table'

// Check for saved view mode preference
try {
  const savedMode = localStorage.getItem("devops_cheatsheet_view_mode");
  if (savedMode === "cards" || savedMode === "table") {
    currentViewMode = savedMode;
  }
} catch (e) {
  // Ignore localStorage access errors
}

document.addEventListener("DOMContentLoaded", () => {
  if (window.INITIAL_ACTIVE_CATEGORY) {
    activeCategoryId = window.INITIAL_ACTIVE_CATEGORY;
  }
  updateViewModeToggleUI();
  renderCheatsheetsView();
});

function setViewMode(mode) {
  if (mode !== "cards" && mode !== "table") return;
  currentViewMode = mode;
  try {
    localStorage.setItem("devops_cheatsheet_view_mode", mode);
  } catch (e) {}
  updateViewModeToggleUI();
  renderCheatsheetsView();
}

function updateViewModeToggleUI() {
  const btnCards = document.getElementById("viewModeCardsBtn");
  const btnTable = document.getElementById("viewModeTableBtn");
  if (!btnCards || !btnTable) return;

  if (currentViewMode === "cards") {
    btnCards.className = "px-2.5 py-1 text-xs font-bold rounded-lg bg-sky-600 text-white shadow-xs border border-sky-600 transition-all flex items-center gap-1.5 cursor-pointer";
    btnTable.className = "px-2.5 py-1 text-xs font-semibold rounded-lg bg-white text-slate-600 hover:text-sky-700 hover:bg-sky-50 border border-slate-200 transition-all flex items-center gap-1.5 cursor-pointer";
  } else {
    btnCards.className = "px-2.5 py-1 text-xs font-semibold rounded-lg bg-white text-slate-600 hover:text-sky-700 hover:bg-sky-50 border border-slate-200 transition-all flex items-center gap-1.5 cursor-pointer";
    btnTable.className = "px-2.5 py-1 text-xs font-bold rounded-lg bg-sky-600 text-white shadow-xs border border-sky-600 transition-all flex items-center gap-1.5 cursor-pointer";
  }
}

function selectCategory(catId) {
  activeCategoryId = catId;
  activeSectionId = "ALL"; // Reset section filter on category change

  // Update category pill styles
  document.querySelectorAll(".category-pill").forEach(p => {
    p.className = "category-pill whitespace-nowrap px-3 py-1.5 rounded-xl font-bold transition-all flex items-center space-x-1.5 border cursor-pointer bg-white hover:bg-sky-50 text-slate-700 hover:text-sky-700 border-sky-100 shadow-2xs";
  });
  const activePill = document.getElementById(`pill-${catId}`);
  if (activePill) {
    activePill.className = "category-pill whitespace-nowrap px-3 py-1.5 rounded-xl font-bold transition-all flex items-center space-x-1.5 border cursor-pointer bg-sky-600 text-white border-sky-600 shadow-sm shadow-sky-500/20";
  }

  renderCheatsheetsView();
}

function selectSection(secName) {
  activeSectionId = secName;
  renderCheatsheetsView();
}

function onSearchChange(val) {
  currentSearchQuery = (val || "").trim().toLowerCase();
  const clearBtn = document.getElementById("searchClearBtn");
  if (clearBtn) {
    if (currentSearchQuery) clearBtn.classList.remove("hidden");
    else clearBtn.classList.add("hidden");
  }
  renderCheatsheetsView();
}

function clearSearch() {
  const input = document.getElementById("cheatsheetSearchInput");
  if (input) input.value = "";
  onSearchChange("");
}

function copyToClipboard(text, btnElement) {
  if (!text) return;
  navigator.clipboard.writeText(text).then(() => {
    const originalHtml = btnElement.innerHTML;
    btnElement.innerHTML = `<i class="fa-solid fa-check text-emerald-600 text-xs"></i> <span class="text-emerald-700 font-bold text-[10px]">Copied!</span>`;
    btnElement.classList.add("border-emerald-300", "bg-emerald-50");
    setTimeout(() => {
      btnElement.innerHTML = originalHtml;
      btnElement.classList.remove("border-emerald-300", "bg-emerald-50");
    }, 1600);
    if (typeof showToast === "function") {
      showToast("Copied to clipboard!", "success");
    }
  }).catch(err => {
    console.error("Clipboard copy failed:", err);
  });
}

function renderSectionNavPills(sections, totalItemsCount) {
  const sectionNavContainer = document.getElementById("sectionFilterNav");
  if (!sectionNavContainer) return;

  if (!sections || sections.length <= 1 || activeCategoryId === "all") {
    sectionNavContainer.classList.add("hidden");
    sectionNavContainer.innerHTML = "";
    return;
  }

  sectionNavContainer.classList.remove("hidden");

  let html = `
    <div class="flex items-center space-x-1.5 overflow-x-auto pb-1 scrollbar-thin text-xs py-1">
      <span class="text-[11px] font-bold text-slate-500 mr-1 flex items-center gap-1 flex-shrink-0">
        <i class="fa-solid fa-filter text-[10px] text-sky-500"></i> Section:
      </span>
      <button 
        onclick="selectSection('ALL')" 
        class="whitespace-nowrap px-2.5 py-1 rounded-lg font-bold transition-all text-xs cursor-pointer border ${activeSectionId === 'ALL' ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs' : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200'}"
      >
        All Sections (${totalItemsCount})
      </button>
  `;

  sections.forEach((sec, idx) => {
    const isActive = (activeSectionId === sec);
    html += `
      <button 
        onclick="selectSection('${escapeJs(sec)}')" 
        class="whitespace-nowrap px-2.5 py-1 rounded-lg font-semibold transition-all text-xs cursor-pointer border ${isActive ? 'bg-indigo-600 text-white border-indigo-600 shadow-xs font-bold' : 'bg-white hover:bg-slate-100 text-slate-700 border-slate-200'}"
        title="${escapeHtml(sec)}"
      >
        <span>${escapeHtml(sec)}</span>
      </button>
    `;
  });

  html += `</div>`;
  sectionNavContainer.innerHTML = html;
}

function renderCheatsheetsView() {
  const container = document.getElementById("cheatsheetsContainer");
  if (!container) return;

  const categories = (window.ALL_CHEATSHEETS_DATA && window.ALL_CHEATSHEETS_DATA.categories) || [];
  let filteredCategories = [];

  if (activeCategoryId === "all") {
    filteredCategories = categories;
  } else {
    filteredCategories = categories.filter(c => c.id === activeCategoryId);
  }

  // Update Section Nav Bar for active category
  if (activeCategoryId !== "all" && filteredCategories.length > 0) {
    const activeCat = filteredCategories[0];
    renderSectionNavPills(activeCat.sections || [], activeCat.total_items || 0);
  } else {
    renderSectionNavPills([], 0);
  }

  let renderedCount = 0;
  let html = "";

  filteredCategories.forEach(cat => {
    const isExampleType = (cat.type === "examples");
    let items = cat.items || [];

    // Filter by Section if selected
    if (activeSectionId !== "ALL" && !isExampleType) {
      items = items.filter(it => (it.section || "General Commands") === activeSectionId);
    }

    // Apply Search Query Filter if active
    if (currentSearchQuery) {
      if (isExampleType) {
        items = items.filter(it => 
          (it.title || "").toLowerCase().includes(currentSearchQuery) ||
          (it.description || "").toLowerCase().includes(currentSearchQuery) ||
          (it.code || "").toLowerCase().includes(currentSearchQuery)
        );
      } else {
        items = items.filter(it => 
          (it.command || "").toLowerCase().includes(currentSearchQuery) ||
          (it.explanation || "").toLowerCase().includes(currentSearchQuery) ||
          (it.flags || "").toLowerCase().includes(currentSearchQuery) ||
          (it.tags || "").toLowerCase().includes(currentSearchQuery) ||
          (it.section || "").toLowerCase().includes(currentSearchQuery)
        );
      }
    }

    if (items.length === 0 && activeCategoryId !== "all") {
      html += `
        <div class="text-center py-12 text-slate-400 glass-card rounded-2xl border border-sky-100 p-8">
          <i class="fa-solid fa-magnifying-glass text-3xl text-slate-300 mb-2 block"></i>
          <p class="font-bold text-slate-700">No matching items found in ${escapeHtml(cat.name)}</p>
          <p class="text-xs text-slate-400 mt-1">Try another search keyword, reset the section filter, or select All Categories.</p>
          ${activeSectionId !== 'ALL' ? `
            <button onclick="selectSection('ALL')" class="mt-3 px-3 py-1.5 rounded-xl bg-sky-50 text-sky-700 border border-sky-200 font-bold text-xs hover:bg-sky-100">
              Clear Section Filter
            </button>
          ` : ''}
        </div>
      `;
      return;
    }

    if (items.length === 0) return; // Skip empty category in "all" view when filtering

    renderedCount += items.length;

    // Category Section Header Container
    html += `
      <div class="glass-card rounded-2xl border border-sky-100 overflow-hidden shadow-xs space-y-4 p-5 bg-white/95">
        <!-- Category Top Title Bar -->
        <div class="flex items-center justify-between pb-3.5 border-b border-sky-100">
          <div class="flex items-center space-x-3">
            <div class="w-9 h-9 rounded-xl bg-${cat.color || 'sky'}-50 text-${cat.color || 'sky'}-600 border border-${cat.color || 'sky'}-200/80 flex items-center justify-center font-bold shadow-2xs">
              <i class="${cat.icon} text-base"></i>
            </div>
            <div>
              <h2 class="text-sm font-extrabold text-slate-900 tracking-tight flex items-center gap-2">
                <span>${escapeHtml(cat.name)}</span>
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-slate-100 text-slate-700 font-bold border border-slate-200">
                  ${items.length} ${isExampleType ? 'examples' : 'commands'}
                </span>
                ${activeSectionId !== 'ALL' ? `
                  <span class="text-[10px] font-sans px-2 py-0.5 rounded-full bg-indigo-50 text-indigo-700 font-bold border border-indigo-200 flex items-center gap-1">
                    <i class="fa-solid fa-folder-open text-[9px]"></i> ${escapeHtml(activeSectionId)}
                  </span>
                ` : ''}
              </h2>
              <p class="text-xs text-slate-500 mt-0.5">${escapeHtml(cat.description || '')}</p>
            </div>
          </div>
          
          <div class="flex items-center gap-2">
            <button onclick="downloadCategoryRaw('${cat.id}')" class="px-2.5 py-1.5 text-xs font-bold rounded-xl bg-white hover:bg-slate-50 text-slate-600 border border-slate-200 transition-all flex items-center space-x-1.5 shadow-2xs cursor-pointer" title="View / Download raw markdown">
              <i class="fa-solid fa-file-arrow-down text-slate-400"></i>
              <span class="hidden sm:inline">Raw .md</span>
            </button>
          </div>
        </div>
    `;

    if (isExampleType) {
      // Code Snippets View (Manifests, Scripts, Dockerfiles, Playbooks)
      html += `<div class="space-y-4 pt-1">`;
      items.forEach((ex, idx) => {
        const codeId = `code_${cat.id}_${idx}`;
        html += `
          <div class="rounded-2xl border border-indigo-100 bg-white shadow-xs overflow-hidden">
            <div class="p-3.5 bg-slate-50/90 border-b border-indigo-100 flex flex-col sm:flex-row sm:items-center justify-between gap-2">
              <div>
                <h3 class="font-extrabold text-xs text-slate-900 flex items-center gap-2">
                  <span class="w-5 h-5 rounded-full bg-indigo-100 text-indigo-700 flex items-center justify-center text-[10px] font-mono font-bold">${idx + 1}</span>
                  <span>${escapeHtml(ex.title)}</span>
                </h3>
                <p class="text-[11px] text-slate-600 mt-1 pl-7 leading-relaxed">${escapeHtml(ex.description)}</p>
              </div>
              <div class="flex items-center space-x-2 self-end sm:self-center flex-shrink-0">
                <span class="text-[10px] font-mono px-2 py-0.5 rounded-md bg-indigo-50 text-indigo-700 font-bold uppercase border border-indigo-100">${escapeHtml(ex.language || 'yaml')}</span>
                <button onclick="copyToClipboard(document.getElementById('${codeId}').textContent, this)" class="px-3 py-1.5 rounded-xl bg-white hover:bg-indigo-50 text-indigo-700 border border-indigo-200 text-xs font-bold transition-all shadow-xs flex items-center space-x-1.5 cursor-pointer">
                  <i class="fa-solid fa-copy text-xs"></i>
                  <span>Copy Code</span>
                </button>
              </div>
            </div>
            <div class="p-4 bg-slate-950 text-slate-100 font-mono text-xs overflow-x-auto selection:bg-indigo-500 selection:text-white">
              <pre class="m-0"><code id="${codeId}" class="language-${escapeHtml(ex.language || 'yaml')} leading-relaxed">${escapeHtml(ex.code)}</code></pre>
            </div>
          </div>
        `;
      });
      html += `</div>`;
    } else {
      // Commands: Group by Section
      const groupedSections = {};
      items.forEach(it => {
        const sec = it.section || "General Commands";
        if (!groupedSections[sec]) groupedSections[sec] = [];
        groupedSections[sec].push(it);
      });

      const sectionKeys = Object.keys(groupedSections);

      sectionKeys.forEach((secName, sIdx) => {
        const secItems = groupedSections[secName];
        
        html += `
          <div class="rounded-2xl border border-sky-100 bg-sky-50/30 overflow-hidden shadow-2xs">
            <!-- Section Header -->
            <div class="px-4 py-2.5 bg-gradient-to-r from-sky-100/70 via-sky-50 to-white border-b border-sky-100 flex items-center justify-between">
              <div class="flex items-center space-x-2">
                <span class="w-6 h-6 rounded-lg bg-sky-600 text-white flex items-center justify-center text-xs font-bold shadow-2xs">
                  <i class="fa-solid fa-terminal text-[10px]"></i>
                </span>
                <h3 class="text-xs font-bold text-slate-800 tracking-tight">${escapeHtml(secName)}</h3>
              </div>
              <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-white text-sky-800 border border-sky-200">
                ${secItems.length} command${secItems.length === 1 ? '' : 's'}
              </span>
            </div>
        `;

        if (currentViewMode === "cards") {
          // Modern Cards View: Clear separation, command box, highlighted flags, AI explanation
          html += `<div class="p-3.5 space-y-3">`;
          secItems.forEach((item, idx) => {
            const cmdId = `cmd_${cat.id}_${sIdx}_${idx}`;
            html += `
              <div class="p-3.5 rounded-xl border border-sky-100 bg-white hover:border-sky-300 hover:shadow-xs transition-all space-y-2.5 group">
                <!-- Command Box & Copy Button -->
                <div class="flex items-center justify-between gap-2 bg-slate-900 rounded-xl p-2.5 border border-slate-800">
                  <div class="font-mono text-xs text-sky-200 break-all select-all font-semibold overflow-x-auto" id="${cmdId}">${escapeHtml(item.command)}</div>
                  <button onclick="copyToClipboard('${escapeJs(item.command)}', this)" class="px-2.5 py-1 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-300 hover:text-white border border-slate-700 text-xs font-bold transition-all flex items-center gap-1.5 flex-shrink-0 cursor-pointer" title="Copy command">
                    <i class="fa-regular fa-copy text-xs"></i>
                    <span class="text-[10px]">Copy</span>
                  </button>
                </div>

                <!-- AI Explanation -->
                <div class="text-xs text-slate-700 leading-relaxed font-normal pl-0.5">
                  ${escapeHtml(item.explanation)}
                </div>

                <!-- Flags Breakdown & Tags Row -->
                <div class="flex flex-wrap items-center justify-between gap-2 pt-1 border-t border-slate-100">
                  ${item.flags ? `
                    <div class="flex items-center gap-1.5 text-[11px] text-slate-600">
                      <span class="font-bold text-sky-700 flex items-center gap-1">
                        <i class="fa-solid fa-sliders text-[10px] text-sky-500"></i> Syntax:
                      </span>
                      <span class="font-mono text-[10px] px-2 py-0.5 rounded-md bg-amber-50 text-amber-900 border border-amber-200/80 font-medium">
                        ${escapeHtml(item.flags)}
                      </span>
                    </div>
                  ` : '<div></div>'}

                  ${item.tags ? `
                    <div class="flex flex-wrap gap-1">
                      ${item.tags.split(',').map(t => `<span class="text-[9px] font-mono px-1.5 py-0.2 rounded bg-sky-50 text-sky-800 border border-sky-100 font-semibold">${escapeHtml(t.trim())}</span>`).join('')}
                    </div>
                  ` : ''}
                </div>
              </div>
            `;
          });
          html += `</div>`;
        } else {
          // Condensed Table View
          html += `
            <div class="overflow-x-auto">
              <table class="w-full text-left text-xs border-collapse bg-white">
                <thead>
                  <tr class="bg-slate-50 border-b border-sky-100 text-[10px] font-bold text-slate-600 uppercase tracking-wider">
                    <th class="py-2.5 px-4 w-5/12">Command</th>
                    <th class="py-2.5 px-4 w-4/12">Description & AI Explanation</th>
                    <th class="py-2.5 px-4 w-3/12">Flags / Tags</th>
                  </tr>
                </thead>
                <tbody class="divide-y divide-sky-50">
          `;

          secItems.forEach((item, idx) => {
            const cmdId = `tbl_cmd_${cat.id}_${sIdx}_${idx}`;
            html += `
              <tr class="hover:bg-sky-50/40 transition-colors">
                <td class="py-3 px-4 align-top">
                  <div class="flex items-start justify-between gap-2">
                    <div class="font-mono text-xs bg-slate-900 text-sky-200 px-2 py-1.5 rounded-lg border border-slate-800 flex-1 break-all select-all font-semibold" id="${cmdId}">${escapeHtml(item.command)}</div>
                    <button onclick="copyToClipboard('${escapeJs(item.command)}', this)" class="w-7 h-7 rounded-lg bg-white hover:bg-sky-50 text-slate-400 hover:text-sky-600 border border-sky-200 flex items-center justify-center transition-all flex-shrink-0 cursor-pointer shadow-2xs" title="Copy command">
                      <i class="fa-solid fa-copy text-xs"></i>
                    </button>
                  </div>
                </td>
                <td class="py-3 px-4 align-top leading-relaxed text-slate-700 font-normal">
                  ${escapeHtml(item.explanation)}
                </td>
                <td class="py-3 px-4 align-top space-y-1.5">
                  ${item.flags ? `
                    <div class="font-mono text-[10px] px-1.5 py-0.5 rounded bg-amber-50 text-amber-900 border border-amber-200/80 leading-tight font-medium">
                      ${escapeHtml(item.flags)}
                    </div>
                  ` : ''}
                  ${item.tags ? `
                    <div class="flex flex-wrap gap-1">
                      ${item.tags.split(',').map(t => `<span class="text-[9px] font-mono px-1.5 py-0.2 rounded bg-sky-50 text-sky-800 border border-sky-100">${escapeHtml(t.trim())}</span>`).join('')}
                    </div>
                  ` : ''}
                </td>
              </tr>
            `;
          });

          html += `
                </tbody>
              </table>
            </div>
          `;
        }

        html += `</div>`; // Close Section Box
      });
    }

    html += `</div>`; // Close Category Section
  });

  if (renderedCount === 0 && !html) {
    html = `
      <div class="text-center py-16 text-slate-400 glass-card rounded-2xl border border-sky-100 p-8">
        <i class="fa-solid fa-magnifying-glass text-4xl text-slate-300 mb-3 block"></i>
        <p class="font-bold text-slate-700 text-sm">No commands or code examples found matching "${escapeHtml(currentSearchQuery)}"</p>
        <p class="text-xs text-slate-400 mt-1">Try another keyword or select a different category above.</p>
        <button onclick="clearSearch()" class="mt-4 px-4 py-1.5 rounded-xl bg-sky-50 hover:bg-sky-100 text-sky-800 font-bold border border-sky-200 text-xs cursor-pointer">
          Clear Search Filter
        </button>
      </div>
    `;
  }

  container.innerHTML = html;

  const countEl = document.getElementById("searchResultCount");
  if (countEl) countEl.textContent = renderedCount;
}

function downloadCategoryRaw(catId) {
  window.open(`/api/cheatsheets/${catId}`, '_blank');
}

function escapeHtml(str) {
  if (!str) return "";
  return String(str)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#039;");
}

function escapeJs(str) {
  if (!str) return "";
  return String(str)
    .replace(/\\/g, "\\\\")
    .replace(/'/g, "\\'")
    .replace(/"/g, '\\"')
    .replace(/\n/g, " ");
}
