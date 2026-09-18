/**
 * My Interviews Hub - Stats & Stat List Modal Module
 * Computes interview metrics and powers interactive detail modals for metric cards:
 * Attended Rounds, Unique Companies, Weekly Activity, Upcoming Scheduled, and Questions Bank.
 */

function getDistinctCompanies() {
  const compMap = new Map();
  (mySchedules || []).forEach(s => {
    if (!s.company) return;
    const norm = s.company.trim();
    if (!norm) return;
    const lower = norm.toLowerCase();
    if (!compMap.has(lower)) {
      compMap.set(lower, {
        company: norm,
        role: s.role || "DevOps Engineer",
        rounds_count: 1,
        latest_date: s.date || "",
        salary_ctc: s.salary_ctc || ""
      });
    } else {
      const existing = compMap.get(lower);
      existing.rounds_count += 1;
      if (s.date && (!existing.latest_date || s.date > existing.latest_date)) {
        existing.latest_date = s.date;
      }
      if (s.salary_ctc && !existing.salary_ctc) {
        existing.salary_ctc = s.salary_ctc;
      }
    }
  });

  (myQuestions || []).forEach(q => {
    if (!q.company) return;
    const norm = q.company.trim();
    if (!norm) return;
    const lower = norm.toLowerCase();
    if (!compMap.has(lower)) {
      compMap.set(lower, {
        company: norm,
        role: "DevOps Engineer",
        rounds_count: 1,
        latest_date: q.date || "",
        salary_ctc: ""
      });
    }
  });

  return Array.from(compMap.values()).sort((a, b) => a.company.localeCompare(b.company));
}

function calculateAndRenderStats() {
  if (typeof autoUpdatePastSchedules === "function") {
    autoUpdatePastSchedules();
  }

  const now = new Date();
  const startOfWeek = new Date(now);
  const dayOfWeek = (now.getDay() + 6) % 7; // Monday = 0
  startOfWeek.setDate(now.getDate() - dayOfWeek);
  startOfWeek.setHours(0, 0, 0, 0);

  const endOfWeek = new Date(startOfWeek);
  endOfWeek.setDate(startOfWeek.getDate() + 6);
  endOfWeek.setHours(23, 59, 59, 999);

  const attendedList = [];
  const upcomingList = [];
  const weeklyList = [];

  (mySchedules || []).forEach(s => {
    const isPast = typeof isScheduleTimePassed === "function" 
      ? isScheduleTimePassed(s.date, s.end_time || s.time, s.start_time)
      : false;
    
    if (s.status === "completed" || isPast) {
      attendedList.push(s);
    } else if (s.status === "scheduled") {
      upcomingList.push(s);
    }

    if (s.date) {
      const p = typeof normalizeDateParts === "function" ? normalizeDateParts(s.date) : null;
      if (p) {
        const d = new Date(p.y, p.m, p.d);
        if (d >= startOfWeek && d <= endOfWeek) {
          weeklyList.push(s);
        }
      }
    }
  });

  const companiesList = getDistinctCompanies();

  currentStats = {
    attended_list: attendedList,
    companies_list: companiesList,
    weekly_list: weeklyList,
    upcoming_list: upcomingList,
    questions_list: myQuestions || []
  };

  const totalAttendedEl = document.getElementById("statTotalAttended");
  const totalCompaniesEl = document.getElementById("statTotalCompanies");
  const weeklyActivityEl = document.getElementById("statWeeklyActivity");
  const weeklySubEl = document.getElementById("statWeeklySub");
  const upcomingCountEl = document.getElementById("statUpcomingCount");
  const totalQuestionsEl = document.getElementById("statTotalQuestions");
  const questionsSubEl = document.getElementById("statQuestionsSub");

  if (totalAttendedEl) totalAttendedEl.textContent = attendedList.length;
  if (totalCompaniesEl) totalCompaniesEl.textContent = companiesList.length;
  if (weeklyActivityEl) weeklyActivityEl.textContent = weeklyList.length;
  if (weeklySubEl) weeklySubEl.textContent = `${weeklyList.length} rounds this week`;
  if (upcomingCountEl) upcomingCountEl.textContent = upcomingList.length;
  if (totalQuestionsEl) totalQuestionsEl.textContent = (myQuestions || []).length;
  if (questionsSubEl) questionsSubEl.textContent = `${(myQuestions || []).length} questions recorded`;
}

// Alias for backward compatibility
function renderStats() {
  calculateAndRenderStats();
}

// --- Interactive Stat List Modal ---
function showStatListModal(type) {
  calculateAndRenderStats();

  const titleElem = document.getElementById("statListTitle");
  const iconElem = document.getElementById("statListIcon");
  const container = document.getElementById("statListContent");
  const modal = document.getElementById("statListModal");

  if (!titleElem || !container || !modal) return;

  if (type === "attended") {
    titleElem.innerText = "Completed Interview Rounds";
    if (iconElem) {
      iconElem.className = "w-8 h-8 rounded-xl bg-emerald-100 text-emerald-600 flex items-center justify-center font-bold";
      iconElem.innerHTML = `<i class="fa-solid fa-user-check text-xs"></i>`;
    }
    const list = currentStats.attended_list || [];
    if (list.length === 0) {
      container.innerHTML = `
        <div class="text-center py-10 text-slate-400">
          <i class="fa-solid fa-user-check text-3xl text-slate-300 mb-2 block"></i>
          <p class="font-bold text-slate-600">No completed interviews yet</p>
          <p class="text-xs text-slate-400 mt-0.5">Interviews whose date and time have passed or marked completed will appear here.</p>
        </div>
      `;
    } else {
      container.innerHTML = list.map(s => `
        <div class="p-3.5 rounded-2xl bg-white border border-emerald-100 shadow-xs space-y-1.5 hover:border-emerald-300 transition-all">
          <div class="flex items-center justify-between">
            <div>
              <div class="font-extrabold text-sm text-slate-900">${escapeHtml(s.company)}</div>
              <div class="text-xs text-sky-700 font-bold mt-0.5"><i class="fa-solid fa-bullseye text-[10px] mr-1"></i>${escapeHtml(s.round || 'Technical Round')} (${escapeHtml(s.role || 'DevOps')})</div>
              <div class="text-[11px] text-slate-500 font-mono mt-0.5"><i class="fa-regular fa-clock text-emerald-600 mr-1"></i>${typeof formatDateCustom === 'function' ? formatDateCustom(s.date) : s.date} • ${typeof formatTimeRange === 'function' ? formatTimeRange(s.start_time, s.end_time, s.time) : (s.time || '10:00')}</div>
            </div>
            <div class="flex items-center space-x-2">
              <span class="px-2.5 py-1 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 font-mono">Completed</span>
              <button onclick="closeStatListModal(); if(typeof editSchedule === 'function') editSchedule('${s.id}')" class="px-2.5 py-1 rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-700 font-bold text-xs cursor-pointer">Details</button>
            </div>
          </div>
          ${s.salary_ctc ? `<div class="text-[11px] text-emerald-800 font-bold bg-emerald-50 px-2 py-0.5 rounded-md"><i class="fa-solid fa-money-bill-wave mr-1"></i>CTC: ${escapeHtml(s.salary_ctc)} ${s.monthly_salary ? `(~${escapeHtml(s.monthly_salary)})` : ''}</div>` : ''}
          ${s.notes ? `<div class="text-[11px] text-slate-600 bg-slate-50 p-2 rounded-xl"><i class="fa-solid fa-comment-dots text-indigo-500 mr-1"></i>${escapeHtml(s.notes)}</div>` : ''}
        </div>
      `).join("");
    }
  } else if (type === "companies") {
    titleElem.innerText = "Companies Interviewed With";
    if (iconElem) {
      iconElem.className = "w-8 h-8 rounded-xl bg-sky-100 text-sky-600 flex items-center justify-center font-bold";
      iconElem.innerHTML = `<i class="fa-solid fa-building text-xs"></i>`;
    }
    const list = currentStats.companies_list || [];
    if (list.length === 0) {
      container.innerHTML = `
        <div class="text-center py-10 text-slate-400">
          <i class="fa-solid fa-building text-3xl text-slate-300 mb-2 block"></i>
          <p class="font-bold text-slate-600">No companies recorded yet</p>
          <p class="text-xs text-slate-400 mt-0.5">Companies will appear here as soon as you schedule interviews.</p>
        </div>
      `;
    } else {
      container.innerHTML = list.map(c => `
        <div class="p-3.5 rounded-2xl bg-white border border-sky-100 shadow-xs flex items-center justify-between hover:border-sky-300 transition-all">
          <div>
            <div class="font-extrabold text-sm text-slate-900">${escapeHtml(c.company)}</div>
            <div class="text-xs text-slate-500 font-medium mt-0.5"><i class="fa-solid fa-briefcase text-slate-400 mr-1"></i>${escapeHtml(c.role || 'DevOps Engineer')}</div>
            ${c.salary_ctc ? `<div class="text-[10px] text-emerald-700 font-bold font-mono mt-0.5"><i class="fa-solid fa-coins mr-1"></i>${escapeHtml(c.salary_ctc)}</div>` : ''}
          </div>
          <div class="text-right space-y-1">
            <span class="px-2.5 py-1 rounded-full text-[10px] font-extrabold bg-sky-100 text-sky-800 border border-sky-200 font-mono">${c.rounds_count} Round(s)</span>
            <div class="text-[10px] text-slate-400 font-mono">Latest: ${typeof formatDateCustom === 'function' ? formatDateCustom(c.latest_date) : c.latest_date}</div>
          </div>
        </div>
      `).join("");
    }
  } else if (type === "week" || type === "weekly") {
    titleElem.innerText = "This Week's Activity";
    if (iconElem) {
      iconElem.className = "w-8 h-8 rounded-xl bg-indigo-100 text-indigo-600 flex items-center justify-center font-bold";
      iconElem.innerHTML = `<i class="fa-solid fa-calendar-week text-xs"></i>`;
    }
    const list = currentStats.weekly_list || [];
    if (list.length === 0) {
      container.innerHTML = `
        <div class="text-center py-10 text-slate-400">
          <i class="fa-solid fa-calendar-week text-3xl text-slate-300 mb-2 block"></i>
          <p class="font-bold text-slate-600">No interviews scheduled for this week</p>
          <p class="text-xs text-slate-400 mt-0.5">Add an interview in the calendar or click 'Schedule Interview'.</p>
        </div>
      `;
    } else {
      container.innerHTML = list.map(s => `
        <div class="p-3.5 rounded-2xl bg-white border border-indigo-100 shadow-xs flex items-center justify-between hover:border-indigo-300 transition-all">
          <div>
            <div class="font-extrabold text-sm text-slate-900">${escapeHtml(s.company)}</div>
            <div class="text-xs text-indigo-700 font-bold mt-0.5"><i class="fa-solid fa-bullseye text-[10px] mr-1"></i>${escapeHtml(s.round || 'Technical Round')}</div>
            <div class="text-[11px] text-slate-500 font-mono mt-0.5"><i class="fa-regular fa-clock text-indigo-600 mr-1"></i>${typeof formatDateCustom === 'function' ? formatDateCustom(s.date) : s.date} • ${typeof formatTimeRange === 'function' ? formatTimeRange(s.start_time, s.end_time, s.time) : (s.time || '10:00')}</div>
          </div>
          <div class="flex items-center space-x-2">
            <span class="px-2 py-0.5 rounded-md text-[10px] font-bold font-mono uppercase bg-slate-100 text-slate-700 border border-slate-200">${s.status || 'scheduled'}</span>
            <button onclick="closeStatListModal(); if(typeof editSchedule === 'function') editSchedule('${s.id}')" class="px-2.5 py-1 rounded-xl bg-indigo-50 hover:bg-indigo-100 text-indigo-800 font-bold border border-indigo-200 text-xs cursor-pointer">Details</button>
          </div>
        </div>
      `).join("");
    }
  } else if (type === "scheduled" || type === "upcoming") {
    titleElem.innerText = "Upcoming Scheduled Interviews";
    if (iconElem) {
      iconElem.className = "w-8 h-8 rounded-xl bg-violet-100 text-violet-600 flex items-center justify-center font-bold";
      iconElem.innerHTML = `<i class="fa-solid fa-calendar-days text-xs"></i>`;
    }
    const list = currentStats.upcoming_list || [];
    if (list.length === 0) {
      container.innerHTML = `
        <div class="text-center py-10 text-slate-400">
          <i class="fa-solid fa-calendar-xmark text-3xl text-slate-300 mb-2 block"></i>
          <p class="font-bold text-slate-600">No upcoming interviews scheduled</p>
          <p class="text-xs text-slate-400 mt-0.5">Schedule upcoming rounds to track preparation and dates.</p>
        </div>
      `;
    } else {
      container.innerHTML = list.map(s => `
        <div class="p-3.5 rounded-2xl bg-white border border-violet-100 shadow-xs flex items-center justify-between hover:border-violet-300 transition-all">
          <div>
            <div class="font-extrabold text-sm text-slate-900">${escapeHtml(s.company)}</div>
            <div class="text-xs text-violet-700 font-bold mt-0.5"><i class="fa-solid fa-bullseye text-[10px] mr-1"></i>${escapeHtml(s.round || 'Technical Round')}</div>
            <div class="text-[11px] text-violet-600 font-bold mt-0.5 font-mono"><i class="fa-regular fa-clock mr-1"></i>${typeof formatDateCustom === 'function' ? formatDateCustom(s.date) : s.date} • ${typeof formatTimeRange === 'function' ? formatTimeRange(s.start_time, s.end_time, s.time) : (s.time || '10:00')}</div>
            ${s.salary_ctc ? `<div class="text-[10px] text-emerald-800 font-bold mt-0.5"><i class="fa-solid fa-coins mr-1"></i>${escapeHtml(s.salary_ctc)}</div>` : ''}
          </div>
          <div class="flex items-center space-x-2">
            ${s.recording_link ? `<a href="${escapeHtml(s.recording_link)}" target="_blank" rel="noopener noreferrer" class="px-2 py-1 rounded-xl bg-rose-50 text-rose-700 font-bold border border-rose-200 text-xs flex items-center space-x-1 hover:bg-rose-100"><i class="fa-brands fa-youtube text-red-600"></i><span>Video</span></a>` : ''}
            <button onclick="closeStatListModal(); if(typeof editSchedule === 'function') editSchedule('${s.id}')" class="px-3 py-1.5 rounded-xl bg-violet-50 hover:bg-violet-100 text-violet-800 font-bold border border-violet-200 text-xs cursor-pointer">Details</button>
          </div>
        </div>
      `).join("");
    }
  } else if (type === "questions") {
    titleElem.innerText = "Questions Bank Repository";
    if (iconElem) {
      iconElem.className = "w-8 h-8 rounded-xl bg-amber-100 text-amber-600 flex items-center justify-center font-bold";
      iconElem.innerHTML = `<i class="fa-solid fa-circle-question text-xs"></i>`;
    }
    const list = myQuestions || [];
    if (list.length === 0) {
      container.innerHTML = `
        <div class="text-center py-10 text-slate-400">
          <i class="fa-solid fa-folder-open text-3xl text-slate-300 mb-2 block"></i>
          <p class="font-bold text-slate-600">No questions recorded yet</p>
          <p class="text-xs text-slate-400 mt-0.5">Use 'Upload Q&A' from your scheduled interviews to populate your questions bank.</p>
        </div>
      `;
    } else {
      container.innerHTML = `
        <div class="mb-3 flex items-center justify-between pb-2 border-b border-amber-100">
          <div>
            <span class="font-extrabold text-xs text-slate-800">${list.length} Questions Recorded</span>
            <span class="text-[10px] text-slate-500 ml-1">in personal questions bank</span>
          </div>
          <button onclick="closeStatListModal(); document.getElementById('qaSearchInput')?.scrollIntoView({behavior:'smooth'}); document.getElementById('qaSearchInput')?.focus();" class="px-2.5 py-1 text-[11px] font-bold rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-800 border border-amber-200 transition-all flex items-center space-x-1 cursor-pointer">
            <span>Go to Explorer</span>
            <i class="fa-solid fa-arrow-down text-[10px]"></i>
          </button>
        </div>
        <div class="space-y-2.5 max-h-[60vh] overflow-y-auto pr-1">
          ${list.map((q, idx) => `
            <div class="p-3 rounded-2xl bg-white border border-amber-100 shadow-xs space-y-1 hover:border-amber-200 transition-all">
              <div class="flex items-center justify-between">
                <div class="flex items-center space-x-2">
                  <span class="font-extrabold text-xs text-slate-900">${escapeHtml(q.company)}</span>
                  <span class="text-[10px] text-slate-500 font-mono font-bold">${typeof formatDateCustom === 'function' ? formatDateCustom(q.date) : q.date}</span>
                </div>
                <span class="px-2 py-0.5 rounded-md text-[10px] font-bold bg-amber-50 text-amber-800 border border-amber-200 font-mono">${escapeHtml(q.round || 'Technical Round')}</span>
              </div>
              <div class="font-bold text-xs text-slate-800 pt-0.5">${escapeHtml(q.question)}</div>
            </div>
          `).join("")}
        </div>
      `;
    }
  }

  modal.classList.remove("hidden");
}

function closeStatListModal() {
  const modal = document.getElementById("statListModal");
  if (modal) modal.classList.add("hidden");
}

function onMetricCardClick(type) {
  showStatListModal(type);
}

function filterByScheduleStatus(st) {
  onMetricCardClick(st === 'completed' ? 'attended' : 'scheduled');
}
