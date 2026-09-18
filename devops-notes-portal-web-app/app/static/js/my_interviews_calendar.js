/**
 * My Interviews Hub - Calendar & Date/Time Engine Module
 * Handles date normalization, 12h/24h time parsing, past schedule detection,
 * week & month calendar grids, and auto-completion tracking.
 */

// --- Robust Date Normalization ---
function normalizeDateParts(dateStr) {
  if (!dateStr) return null;
  const raw = String(dateStr).trim();

  // Match "15-Sep-2026", "15-09-2026", "2026-09-15"
  if (raw.includes("-")) {
    const parts = raw.split("-");
    if (parts[0].length === 4) {
      // YYYY-MM-DD
      return { y: parseInt(parts[0], 10), m: parseInt(parts[1], 10) - 1, d: parseInt(parts[2], 10) };
    } else {
      // DD-MMM-YYYY or DD-MM-YYYY
      const d = parseInt(parts[0], 10);
      const mNames = ["jan", "feb", "mar", "apr", "may", "jun", "jul", "aug", "sep", "oct", "nov", "dec"];
      const mStr = (parts[1] || "").toLowerCase().slice(0, 3);
      const mIdx = mNames.indexOf(mStr);
      const m = mIdx !== -1 ? mIdx : (parseInt(parts[1], 10) - 1);
      const y = parseInt(parts[2], 10);
      return { y, m, d };
    }
  }

  // Match "15/09/2026" or "2026/09/15"
  if (raw.includes("/")) {
    const parts = raw.split("/");
    if (parts[0].length === 4) {
      return { y: parseInt(parts[0], 10), m: parseInt(parts[1], 10) - 1, d: parseInt(parts[2], 10) };
    } else {
      return { y: parseInt(parts[2], 10), m: parseInt(parts[1], 10) - 1, d: parseInt(parts[0], 10) };
    }
  }

  const parsed = new Date(raw);
  if (!isNaN(parsed.getTime())) {
    return { y: parsed.getFullYear(), m: parsed.getMonth(), d: parsed.getDate() };
  }
  return null;
}

function normalizeDateIso(dateStr) {
  const p = normalizeDateParts(dateStr);
  if (!p) return dateStr;
  return `${p.y}-${String(p.m + 1).padStart(2, '0')}-${String(p.d).padStart(2, '0')}`;
}

function formatIsoDate(d) {
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
}

function formatDateCustom(dateStr) {
  const p = normalizeDateParts(dateStr);
  if (!p) return dateStr || "N/A";
  const mNames = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"];
  return `${p.d}-${mNames[p.m]}-${p.y}`;
}

// --- Robust Time Parsing (Handles "10am to 11am", "10:00 - 11:00", "11:30 PM", etc.) ---
function parseTimeToHoursMinutes(timeStr, isEnd = true) {
  if (!timeStr) return isEnd ? { hh: 23, mm: 59 } : { hh: 10, mm: 0 };
  let raw = String(timeStr).trim().toLowerCase();

  // If format is like "10am to 11am" or "10:00 - 11:00"
  if (raw.includes(" to ") || raw.includes(" - ")) {
    const parts = raw.split(/\s*(?:to|-)\s*/i);
    raw = (isEnd ? parts[parts.length - 1] : parts[0]).trim();
  }

  const isPm = raw.includes("pm");
  const isAm = raw.includes("am");
  const cleaned = raw.replace(/[a-z\s]/gi, "");

  let hh = 0;
  let mm = 0;
  if (cleaned.includes(":")) {
    const [hStr, mStr] = cleaned.split(":");
    hh = parseInt(hStr, 10) || 0;
    mm = parseInt(mStr, 10) || 0;
  } else {
    hh = parseInt(cleaned, 10) || (isEnd ? 23 : 10);
    mm = 0;
  }

  if (isPm && hh < 12) hh += 12;
  if (isAm && hh === 12) hh = 0;

  return { hh, mm };
}

function formatTimeRange(startTime, endTime, time) {
  if (startTime && endTime) return `${startTime} - ${endTime}`;
  if (time) return time;
  if (startTime) return startTime;
  return "10:00 - 11:00";
}

// --- Schedule Past Checking ---
function isScheduleTimePassed(dateStr, endTimeStr, startTimeStr) {
  const dateParts = normalizeDateParts(dateStr);
  if (!dateParts) return false;

  const timeToUse = endTimeStr || startTimeStr || "23:59";
  const timeInfo = parseTimeToHoursMinutes(timeToUse, true);
  const schedDate = new Date(dateParts.y, dateParts.m, dateParts.d, timeInfo.hh, timeInfo.mm, 0);
  return schedDate.getTime() < Date.now();
}

// --- Auto-Update Schedules Past Concluded Time ---
function autoUpdatePastSchedules() {
  let changed = false;
  (mySchedules || []).forEach(s => {
    if (s.status === "scheduled" && isScheduleTimePassed(s.date, s.end_time || s.time, s.start_time)) {
      s.status = "completed";
      changed = true;
    }
  });
  if (changed) {
    localStorage.setItem(STORAGE_KEY_SCHEDULES, JSON.stringify(mySchedules));
  }
}

// --- Calendar View & UI Handlers ---
function setCalendarView(view) {
  currentCalendarView = view;
  localStorage.setItem(STORAGE_KEY_CALENDAR_VIEW, view);
  updateCalendarViewUI();
}

function updateCalendarViewUI() {
  const weekBtn = document.getElementById("calViewWeekBtn");
  const monthBtn = document.getElementById("calViewMonthBtn");
  const todayBtn = document.getElementById("calTodayBtn");
  const weekGrid = document.getElementById("weekDaysGrid");
  const monthContainer = document.getElementById("monthDaysContainer");

  if (!weekBtn || !monthBtn || !weekGrid || !monthContainer) return;

  if (currentCalendarView === "week") {
    weekBtn.className = "px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 bg-white text-sky-700 shadow-xs cursor-pointer";
    monthBtn.className = "px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 text-slate-600 hover:text-sky-700 cursor-pointer";
    if (todayBtn) todayBtn.textContent = "Today";
    weekGrid.classList.remove("hidden");
    monthContainer.classList.add("hidden");
    renderCalendar();
  } else {
    monthBtn.className = "px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 bg-white text-sky-700 shadow-xs cursor-pointer";
    weekBtn.className = "px-3 py-1 rounded-lg text-xs font-bold transition-all flex items-center space-x-1.5 text-slate-600 hover:text-sky-700 cursor-pointer";
    if (todayBtn) todayBtn.textContent = "This Month";
    weekGrid.classList.add("hidden");
    monthContainer.classList.remove("hidden");
    renderMonthCalendar();
  }
}

function navigateCalendar(direction) {
  if (currentCalendarView === "week") {
    if (direction === 0) currentWeekOffset = 0;
    else currentWeekOffset += direction;
    renderCalendar();
  } else {
    if (direction === 0) currentMonthOffset = 0;
    else currentMonthOffset += direction;
    renderMonthCalendar();
  }
}

function navigateWeek(direction) {
  navigateCalendar(direction);
}

// --- Week View Calendar Renderer ---
function renderCalendar() {
  autoUpdatePastSchedules();
  const container = document.getElementById("calendarGrid");
  const label = document.getElementById("calendarWeekLabel");
  if (!container || !label) return;

  const today = new Date();
  today.setHours(0, 0, 0, 0);

  const curr = new Date(today);
  curr.setDate(today.getDate() + (currentWeekOffset * 7));
  const dayOfWeek = (curr.getDay() + 6) % 7; // Monday as first day
  const firstDayOfWeek = new Date(curr);
  firstDayOfWeek.setDate(curr.getDate() - dayOfWeek);

  const lastDayOfWeek = new Date(firstDayOfWeek);
  lastDayOfWeek.setDate(firstDayOfWeek.getDate() + 6);

  label.innerHTML = `<i class="fa-regular fa-calendar text-sky-600"></i><span>${formatDateCustom(formatIsoDate(firstDayOfWeek))} — ${formatDateCustom(formatIsoDate(lastDayOfWeek))}</span>`;

  const dayNames = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"];
  const daysHtml = [];

  for (let i = 0; i < 7; i++) {
    const d = new Date(firstDayOfWeek);
    d.setDate(firstDayOfWeek.getDate() + i);
    const isoStr = formatIsoDate(d);
    const isToday = d.getTime() === today.getTime();

    // Match schedules for this date
    const dayScheds = mySchedules.filter(s => normalizeDateIso(s.date) === isoStr);

    let eventsHtml = "";
    dayScheds.forEach(s => {
      const isPast = isScheduleTimePassed(s.date, s.end_time || s.time, s.start_time);
      const isComp = s.status === "completed";
      const hasQa = s.questions_uploaded || (myQuestions || []).some(q => 
        (q.company || "").trim().toLowerCase() === (s.company || "").trim().toLowerCase() && 
        (q.round || "").trim().toLowerCase() === (s.round || "").trim().toLowerCase()
      );
      const needsQa = isPast && !hasQa;

      let badgeBg = "bg-violet-50 text-violet-800 border-violet-200";
      if (isComp && !needsQa) {
        badgeBg = "bg-emerald-50 text-emerald-800 border-emerald-200";
      } else if (needsQa) {
        badgeBg = "bg-amber-50 text-amber-950 border-amber-300";
      }

      const timeStr = `${s.start_time || s.time || "10:00"}`;
      eventsHtml += `
        <div onclick="editSchedule('${s.id}')" class="p-1.5 rounded-lg border text-[10px] cursor-pointer hover:shadow-xs transition-all ${badgeBg} space-y-0.5" title="${escapeHtml(s.company)} • ${escapeHtml(s.round || '')} (${timeStr}) - Click to view details / upload Q&A">
          <div class="font-bold truncate flex items-center justify-between">
            <span class="truncate font-extrabold"><i class="fa-solid fa-building text-[8px] text-sky-600 mr-1"></i>${escapeHtml(s.company)}</span>
            <span class="font-mono text-[9px]">${timeStr}</span>
          </div>
          <div class="text-[9px] text-slate-600 truncate font-semibold">${escapeHtml(s.round)}</div>
          ${s.salary_ctc ? `<div class="text-[8px] text-emerald-700 font-bold font-mono truncate"><i class="fa-solid fa-coins text-[8px] mr-1"></i>${escapeHtml(s.salary_ctc)}</div>` : ''}
          ${needsQa ? `
            <div class="pt-0.5">
              <span class="text-[8px] font-extrabold px-1.5 py-0.2 rounded bg-amber-200/90 text-amber-950 border border-amber-300 flex items-center gap-1 w-max">
                <i class="fa-solid fa-triangle-exclamation text-[8px] text-amber-600"></i>Upload Q&A Required
              </span>
            </div>
          ` : (hasQa ? `
            <div class="pt-0.5">
              <span class="text-[8px] font-bold px-1 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1 w-max">
                <i class="fa-solid fa-check-double text-[8px] text-emerald-600"></i>Q&A Banked
              </span>
            </div>
          ` : '')}
        </div>
      `;
    });

    daysHtml.push(`
      <div onclick="openScheduleModalWithDate('${isoStr}')" class="p-2.5 min-h-[110px] flex flex-col justify-between cursor-pointer group transition-all ${isToday ? 'bg-sky-50/60 font-semibold ring-1 ring-inset ring-sky-300' : 'bg-transparent hover:bg-sky-50/20'}">
        <div class="flex items-center justify-between text-xs mb-1.5">
          <span class="text-[10px] font-bold uppercase text-slate-400">${dayNames[i]}</span>
          <span class="w-5 h-5 rounded-full flex items-center justify-center text-[11px] ${isToday ? 'bg-sky-600 text-white font-bold' : 'text-slate-700'}">${d.getDate()}</span>
        </div>
        <div class="space-y-1 flex-1 overflow-y-auto max-h-24">
          ${eventsHtml || '<div class="text-[10px] text-slate-300 italic group-hover:text-sky-400 transition-all">+ Schedule</div>'}
        </div>
      </div>
    `);
  }

  container.innerHTML = daysHtml.join("");
}

// --- Month View Calendar Renderer ---
function renderMonthCalendar() {
  autoUpdatePastSchedules();
  const container = document.getElementById("calendarMonthGrid");
  const label = document.getElementById("calendarWeekLabel");
  if (!container || !label) return;

  const now = new Date();
  const targetMonth = new Date(now.getFullYear(), now.getMonth() + currentMonthOffset, 1);
  const monthName = targetMonth.toLocaleString('default', { month: 'long', year: 'numeric' });
  label.innerHTML = `<i class="fa-regular fa-calendar text-sky-600"></i><span>${monthName}</span>`;

  // Monday as first day of week
  const firstDayIndex = (targetMonth.getDay() + 6) % 7;
  const daysInMonth = new Date(targetMonth.getFullYear(), targetMonth.getMonth() + 1, 0).getDate();
  const prevMonthDays = new Date(targetMonth.getFullYear(), targetMonth.getMonth(), 0).getDate();

  const todayIso = formatIsoDate(now);
  const cellsHtml = [];

  // Previous month trailing days
  for (let i = firstDayIndex - 1; i >= 0; i--) {
    const prevDay = prevMonthDays - i;
    cellsHtml.push(`
      <div class="p-2 rounded-xl bg-slate-50/50 border border-slate-100/60 min-h-[95px] opacity-40 select-none">
        <div class="text-[10px] font-mono text-slate-400 font-bold">${prevDay}</div>
      </div>
    `);
  }

  // Days in current month
  for (let day = 1; day <= daysInMonth; day++) {
    const dateStr = `${targetMonth.getFullYear()}-${String(targetMonth.getMonth() + 1).padStart(2, '0')}-${String(day).padStart(2, '0')}`;
    const dayScheds = mySchedules.filter(s => normalizeDateIso(s.date) === dateStr);
    const isToday = dateStr === todayIso;

    let eventsHtml = "";
    dayScheds.forEach(s => {
      const isPast = isScheduleTimePassed(s.date, s.end_time || s.time, s.start_time);
      const isComp = s.status === "completed";
      const hasQa = s.questions_uploaded || (myQuestions || []).some(q => 
        (q.company || "").trim().toLowerCase() === (s.company || "").trim().toLowerCase() && 
        (q.round || "").trim().toLowerCase() === (s.round || "").trim().toLowerCase()
      );
      const needsQa = isPast && !hasQa;

      let badgeBg = "bg-violet-50 text-violet-800 border-violet-200";
      if (isComp && !needsQa) {
        badgeBg = "bg-emerald-50 text-emerald-800 border-emerald-200";
      } else if (needsQa) {
        badgeBg = "bg-amber-50 text-amber-950 border-amber-300";
      }

      const timeStr = `${s.start_time || s.time || "10:00"}`;
      eventsHtml += `
        <div onclick="editSchedule('${s.id}')" class="p-1 rounded-lg border text-[9px] cursor-pointer hover:shadow-xs transition-all ${badgeBg} space-y-0.5" title="${escapeHtml(s.company)} • ${escapeHtml(s.round || '')} (${timeStr}) - Click to view details / upload Q&A">
          <div class="font-bold truncate flex items-center justify-between">
            <span class="truncate font-extrabold"><i class="fa-solid fa-building text-[8px] text-sky-600 mr-1"></i>${escapeHtml(s.company)}</span>
            <span class="font-mono text-[8px] font-bold">${timeStr}</span>
          </div>
          <div class="text-[9px] text-slate-600 truncate font-semibold">${escapeHtml(s.round || 'Round')}</div>
          ${s.salary_ctc ? `<div class="text-[8px] text-emerald-700 font-bold font-mono truncate"><i class="fa-solid fa-coins text-[8px] mr-1"></i>${escapeHtml(s.salary_ctc)}</div>` : ''}
          ${needsQa ? `
            <div class="pt-0.5">
              <span class="text-[8px] font-extrabold px-1.5 py-0.2 rounded bg-amber-200/90 text-amber-950 border border-amber-300 flex items-center gap-1 w-max">
                <i class="fa-solid fa-triangle-exclamation text-[8px] text-amber-600"></i>Upload Q&A Required
              </span>
            </div>
          ` : (hasQa ? `
            <div class="pt-0.5">
              <span class="text-[8px] font-bold px-1 py-0.2 rounded bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1 w-max">
                <i class="fa-solid fa-check-double text-[8px] text-emerald-600"></i>Q&A Banked
              </span>
            </div>
          ` : '')}
        </div>
      `;
    });

    cellsHtml.push(`
      <div onclick="openScheduleModalWithDate('${dateStr}')" class="p-2 rounded-xl border transition-all flex flex-col justify-between min-h-[95px] cursor-pointer group ${isToday ? 'bg-sky-50/70 border-sky-400 ring-2 ring-sky-400/20 shadow-xs' : 'bg-white hover:bg-sky-50/30 border-sky-100 hover:border-sky-300'}">
        <div class="flex items-center justify-between mb-1">
          <span class="w-5 h-5 rounded-full flex items-center justify-center text-[11px] font-bold ${isToday ? 'bg-sky-600 text-white shadow-2xs' : 'text-slate-700 group-hover:text-sky-700'}">${day}</span>
          ${dayScheds.length > 0 ? `<span class="text-[9px] font-mono font-bold px-1.5 py-0.2 rounded-full bg-sky-100 text-sky-800 border border-sky-200">${dayScheds.length}</span>` : ''}
        </div>
        <div class="space-y-1 flex-1 overflow-y-auto max-h-24">
          ${eventsHtml || '<div class="text-[9px] text-slate-300 italic group-hover:text-sky-400/80 transition-all">+ Add</div>'}
        </div>
      </div>
    `);
  }

  // Next month trailing days
  const totalRendered = firstDayIndex + daysInMonth;
  const remaining = (7 - (totalRendered % 7)) % 7;
  for (let i = 1; i <= remaining; i++) {
    cellsHtml.push(`
      <div class="p-2 rounded-xl bg-slate-50/50 border border-slate-100/60 min-h-[95px] opacity-40 select-none">
        <div class="text-[10px] font-mono text-slate-400 font-bold">${i}</div>
      </div>
    `);
  }

  container.innerHTML = cellsHtml.join("");
}
