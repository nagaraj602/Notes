/**
 * My Interviews Hub - Schedule Management Module
 * Handles Schedule creation, custom rounds, past/future status logic,
 * YouTube recording extraction via Gemini AI, and schedule editing.
 */

function isYoutubeUrl(url) {
  if (!url) return false;
  return /(?:youtube\.com\/(?:watch\?v=|embed\/|shorts\/)|youtu\.be\/)/i.test(url.trim());
}

// --- Round Select Initialization & Custom Rounds ---
function initRoundsDropdowns() {
  const schedSelect = document.getElementById("schedRound");
  const qaSelect = document.getElementById("qaRound");

  let opts = "";
  myRounds.forEach(r => {
    opts += `<option value="${escapeHtml(r.name)}">${escapeHtml(r.name)}</option>`;
  });
  opts += `<option value="__custom__">+ Add Custom Round...</option>`;

  if (schedSelect) schedSelect.innerHTML = opts;
  if (qaSelect) qaSelect.innerHTML = opts;
}

function toggleSchedCustomRoundInput(show) {
  const box = document.getElementById("schedCustomRoundBox");
  if (!box) return;
  if (show !== undefined) {
    if (show) box.classList.remove("hidden");
    else box.classList.add("hidden");
  } else {
    box.classList.toggle("hidden");
  }
  if (!box.classList.contains("hidden")) {
    document.getElementById("schedCustomRoundInput")?.focus();
  }
}

function saveCustomRoundFromSchedModal() {
  const input = document.getElementById("schedCustomRoundInput");
  const name = (input?.value || "").trim();
  if (!name) {
    if (typeof showToast === "function") showToast("Please enter a round name.", "error");
    return;
  }
  if (myRounds.some(r => r.name.toLowerCase() === name.toLowerCase())) {
    if (typeof showToast === "function") showToast("Round with this name already exists!", "error");
    const schedSelect = document.getElementById("schedRound");
    if (schedSelect) schedSelect.value = name;
    toggleSchedCustomRoundInput(false);
    return;
  }

  const newRound = {
    id: "round-" + Math.random().toString(36).substr(2, 8),
    name: name,
    stage: "Custom",
    description: "Custom interview round",
    is_default: false
  };
  myRounds.push(newRound);
  saveRounds();
  initRoundsDropdowns();

  const schedSelect = document.getElementById("schedRound");
  if (schedSelect) schedSelect.value = name;
  if (input) input.value = "";
  toggleSchedCustomRoundInput(false);
  if (typeof showToast === "function") showToast(`Added custom round: ${name}`, "success");
}

function onSchedRoundChange(val) {
  if (val === "__custom__") {
    toggleSchedCustomRoundInput(true);
  } else {
    toggleSchedCustomRoundInput(false);
  }
}

// --- Schedule Status Dynamic Filtering (Past vs Future) ---
function updateScheduleStatusOptions() {
  const dateStr = document.getElementById("schedDate")?.value;
  const endTimeStr = document.getElementById("schedEndTime")?.value;
  const startTimeStr = document.getElementById("schedStartTime")?.value;
  const statusSelect = document.getElementById("schedStatus");
  if (!statusSelect) return;

  const isPast = isScheduleTimePassed(dateStr, endTimeStr, startTimeStr);
  const curVal = statusSelect.value;

  if (isPast) {
    // Condition: If date & time is in past, do NOT show "scheduled".
    // Show ONLY: completed, cancelled, rescheduled
    statusSelect.innerHTML = `
      <option value="completed">✅ Completed</option>
      <option value="cancelled">❌ Cancelled</option>
      <option value="rescheduled">🔄 Rescheduled</option>
    `;
    if (curVal === "cancelled" || curVal === "rescheduled") {
      statusSelect.value = curVal;
    } else {
      statusSelect.value = "completed";
    }
  } else {
    // Future: show: scheduled, cancelled, rescheduled
    statusSelect.innerHTML = `
      <option value="scheduled">⏳ Scheduled</option>
      <option value="cancelled">❌ Cancelled</option>
      <option value="rescheduled">🔄 Rescheduled</option>
    `;
    if (curVal === "cancelled" || curVal === "rescheduled") {
      statusSelect.value = curVal;
    } else {
      statusSelect.value = "scheduled";
    }
  }
}

// --- Open & Edit Schedule Modals ---
function openScheduleModal() {
  if (!ensurePersonalPatOrPrompt(() => openScheduleModal())) return;
  document.getElementById("schedId").value = "";
  document.getElementById("scheduleModalTitle").textContent = "Schedule Interview";
  const candInput = document.getElementById("schedCandidateName");
  if (candInput) candInput.value = getCandidateIdentity();
  document.getElementById("schedCompany").value = "";
  document.getElementById("schedRole").value = "DevOps Engineer";
  document.getElementById("schedDate").value = new Date().toISOString().split("T")[0];
  document.getElementById("schedStartTime").value = "10:00";
  document.getElementById("schedEndTime").value = "11:00";
  document.getElementById("schedCtc").value = "";
  document.getElementById("schedLink").value = "";
  document.getElementById("schedRecordingLink").value = "";
  document.getElementById("schedNotes").value = "";

  const banner = document.getElementById("pastScheduleActionBanner");
  if (banner) banner.classList.add("hidden");

  const statusBox = document.getElementById("schedYtExtractStatus");
  if (statusBox) {
    statusBox.classList.add("hidden");
    statusBox.innerHTML = "";
  }

  toggleSchedCustomRoundInput(false);
  initRoundsDropdowns();
  updateScheduleStatusOptions();
  document.getElementById("scheduleModal").classList.remove("hidden");
}

function openScheduleModalWithDate(dateStr) {
  openScheduleModal();
  const normalized = normalizeDateIso(dateStr);
  if (normalized && document.getElementById("schedDate")) {
    document.getElementById("schedDate").value = normalized;
    updateScheduleStatusOptions();
  }
}

function closeScheduleModal() {
  document.getElementById("scheduleModal").classList.add("hidden");
}

function editSchedule(id) {
  if (!ensurePersonalPatOrPrompt(() => editSchedule(id))) return;
  const s = mySchedules.find(x => x.id === id);
  if (!s) return;

  document.getElementById("schedId").value = s.id;
  document.getElementById("scheduleModalTitle").textContent = "Edit Scheduled Interview";
  const candInput = document.getElementById("schedCandidateName");
  if (candInput) candInput.value = s.candidate_name || getCandidateIdentity();
  document.getElementById("schedCompany").value = s.company || "";
  document.getElementById("schedRole").value = s.role || "DevOps Engineer";

  initRoundsDropdowns();
  const schedSelect = document.getElementById("schedRound");
  if (schedSelect) {
    if (s.round && !myRounds.some(r => r.name === s.round)) {
      schedSelect.innerHTML += `<option value="${escapeHtml(s.round)}">${escapeHtml(s.round)}</option>`;
    }
    schedSelect.value = s.round || "L1 Technical Round";
  }

  document.getElementById("schedDate").value = normalizeDateIso(s.date) || s.date || "";
  document.getElementById("schedStartTime").value = s.start_time || s.time || "10:00";
  document.getElementById("schedEndTime").value = s.end_time || "11:00";
  document.getElementById("schedCtc").value = s.salary_ctc || "";
  document.getElementById("schedLink").value = s.meeting_link || "";
  document.getElementById("schedRecordingLink").value = s.recording_link || "";
  document.getElementById("schedNotes").value = s.notes || "";

  const statusBox = document.getElementById("schedYtExtractStatus");
  if (statusBox) {
    statusBox.classList.add("hidden");
    statusBox.innerHTML = "";
  }
  toggleSchedCustomRoundInput(false);

  updateScheduleStatusOptions();
  if (s.status) {
    const statusSelect = document.getElementById("schedStatus");
    if (statusSelect && Array.from(statusSelect.options).some(o => o.value === s.status)) {
      statusSelect.value = s.status;
    }
  }

  // --- Past Interview Action Banner & Interactive Options ---
  const isPast = isScheduleTimePassed(s.date, s.end_time || s.time, s.start_time);
  const hasQa = s.questions_uploaded || (myQuestions || []).some(q => 
    (q.company || "").trim().toLowerCase() === (s.company || "").trim().toLowerCase() && 
    (q.round || "").trim().toLowerCase() === (s.round || "").trim().toLowerCase()
  );

  const banner = document.getElementById("pastScheduleActionBanner");
  if (banner) {
    if (isPast) {
      banner.className = "p-3.5 rounded-2xl border flex flex-col gap-3 " + (hasQa ? "bg-emerald-50/90 border-emerald-200" : "bg-amber-50/90 border-amber-200");
      banner.innerHTML = `
        <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b pb-2 ${hasQa ? 'border-emerald-200/80' : 'border-amber-200/80'}">
          <div class="space-y-0.5">
            <div class="text-xs font-black flex items-center gap-2 ${hasQa ? 'text-emerald-900' : 'text-amber-950'}">
              <i class="fa-solid ${hasQa ? 'fa-circle-check text-emerald-600' : 'fa-clock-rotate-left text-amber-600'}"></i>
              <span>${hasQa ? 'Interview Concluded • Q&A Banked' : 'Past Interview Concluded • Upload Q&A Required'}</span>
              <span class="text-[9px] px-2 py-0.5 rounded-full font-bold ${hasQa ? 'bg-emerald-200 text-emerald-900' : 'bg-amber-200 text-amber-900'}">${hasQa ? 'Complete' : 'Pending Q&A'}</span>
            </div>
            <p class="text-[11px] ${hasQa ? 'text-emerald-800' : 'text-amber-800'}">Choose your preferred upload option to bank questions and notes into your portal repository:</p>
          </div>
        </div>

        <div class="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
          <!-- Option 1: YouTube Link -->
          <button type="button" onclick="openUploadQaForCurrentSchedule('youtube')" class="p-2.5 rounded-xl bg-white hover:bg-rose-50 border border-rose-200 text-slate-800 font-bold flex flex-col items-center text-center gap-1 transition-all shadow-xs hover:border-rose-400 cursor-pointer">
            <i class="fa-brands fa-youtube text-red-600 text-lg"></i>
            <span class="text-[11px]">YouTube Link</span>
            <span class="text-[9px] text-slate-500 font-normal">Auto AI Subtitles</span>
          </button>

          <!-- Option 2: Text / Paste Q&A -->
          <button type="button" onclick="openUploadQaForCurrentSchedule('manual')" class="p-2.5 rounded-xl bg-white hover:bg-sky-50 border border-sky-200 text-slate-800 font-bold flex flex-col items-center text-center gap-1 transition-all shadow-xs hover:border-sky-400 cursor-pointer">
            <i class="fa-solid fa-file-lines text-sky-600 text-lg"></i>
            <span class="text-[11px]">Text File / Q&A</span>
            <span class="text-[9px] text-slate-500 font-normal">AI Grammar & Polish</span>
          </button>

          <!-- Option 3: Recording Audio/Video File -->
          <button type="button" onclick="openUploadQaForCurrentSchedule('video')" class="p-2.5 rounded-xl bg-white hover:bg-indigo-50 border border-indigo-200 text-slate-800 font-bold flex flex-col items-center text-center gap-1 transition-all shadow-xs hover:border-indigo-400 cursor-pointer">
            <i class="fa-solid fa-file-audio text-indigo-600 text-lg"></i>
            <span class="text-[11px]">Recording File</span>
            <span class="text-[9px] text-slate-500 font-normal">Audio / Video file</span>
          </button>

          <!-- Option 4: Transcript File/Text -->
          <button type="button" onclick="openUploadQaForCurrentSchedule('transcript')" class="p-2.5 rounded-xl bg-white hover:bg-emerald-50 border border-emerald-200 text-slate-800 font-bold flex flex-col items-center text-center gap-1 transition-all shadow-xs hover:border-emerald-400 cursor-pointer">
            <i class="fa-solid fa-closed-captioning text-emerald-600 text-lg"></i>
            <span class="text-[11px]">Transcript File</span>
            <span class="text-[9px] text-slate-500 font-normal">Full Verbatim Text</span>
          </button>
        </div>
      `;
      banner.classList.remove("hidden");
    } else {
      banner.classList.add("hidden");
    }
  }

  document.getElementById("scheduleModal").classList.remove("hidden");
}

function openUploadQaForCurrentSchedule(tab = "youtube") {
  const currentId = document.getElementById("schedId")?.value;
  closeScheduleModal();
  if (typeof openUploadQaModal === "function") {
    openUploadQaModal(currentId, tab);
  }
}

// --- Auto-Extract Q&A from YouTube in Schedule Modal ---
async function extractQaFromScheduleModal() {
  const ytInput = document.getElementById("schedRecordingLink");
  const ytUrl = (ytInput?.value || "").trim();
  if (!ytUrl) {
    if (typeof showToast === "function") showToast("Please enter a YouTube video URL first.", "error");
    ytInput?.focus();
    return;
  }

  const company = (document.getElementById("schedCompany")?.value || "").trim();
  if (!company) {
    if (typeof showToast === "function") showToast("Please enter a Company Name first.", "error");
    document.getElementById("schedCompany")?.focus();
    return;
  }

  const round = document.getElementById("schedRound")?.value || "L1 Technical Round";
  const date = document.getElementById("schedDate")?.value || new Date().toISOString().split("T")[0];
  const candidateName = (document.getElementById("schedCandidateName")?.value || "").trim() || getCandidateIdentity();

  const btn = document.getElementById("btnSchedExtractYt");
  const statusBox = document.getElementById("schedYtExtractStatus");

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-sm"></i><span>Extracting...</span>`;
  }
  if (statusBox) {
    statusBox.classList.remove("hidden");
    statusBox.innerHTML = `
      <div class="flex items-center gap-2 text-sky-800 font-bold">
        <i class="fa-solid fa-spinner fa-spin text-sky-600"></i>
        <span>Fetching YouTube transcript & extracting interview questions with Gemini AI...</span>
      </div>
    `;
  }

  try {
    const apiKey = getGeminiApiKey();
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["x-gemini-api-key"] = apiKey;

    const res = await fetch("/api/ai/process-youtube", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ url: ytUrl, model: getGeminiModel() })
    });
    const data = await res.json();
    if (!res.ok) {
      throw new Error(data.detail || data.error || "Failed to process YouTube video");
    }

    const generatedTranscript = data.transcript || "";
    const parsedQuestions = (data.questions || []).map(q => ({
      id: "q-" + Math.random().toString(36).substr(2, 9),
      company: company,
      round: round,
      date: date,
      question: q.question,
      answer: q.answer || "",
      categories: (q.categories && q.categories.length) ? q.categories : ["General"],
      sub_questions: q.sub_questions || [],
      suggestions: q.suggestions || "",
      original_raw_text: generatedTranscript || ytUrl,
      source_type: "youtube",
      recording_link: ytUrl,
      transcript: generatedTranscript,
      created_at: new Date().toISOString()
    }));

    if (parsedQuestions.length === 0) {
      throw new Error("No questions could be extracted from this video transcript.");
    }

    parsedQuestions.forEach(q => myQuestions.push(q));
    saveQuestions();

    const schedId = document.getElementById("schedId")?.value;
    let sched = mySchedules.find(s => s.id === schedId);
    if (!sched) {
      sched = mySchedules.find(s => 
        (s.company || "").toLowerCase() === company.toLowerCase() &&
        (s.round || "").toLowerCase() === round.toLowerCase()
      );
    }
    if (sched) {
      sched.recording_link = ytUrl;
      sched.transcript = generatedTranscript;
      sched.has_transcript = true;
      sched.questions_uploaded = true;
      sched.status = "completed";
    } else {
      sched = {
        id: schedId || ("sched-" + Math.random().toString(36).substr(2, 9)),
        candidate_name: candidateName,
        company: company,
        role: document.getElementById("schedRole")?.value || "DevOps Engineer",
        round: round,
        date: date,
        time: document.getElementById("schedStartTime")?.value || "10:00",
        start_time: document.getElementById("schedStartTime")?.value || "10:00",
        end_time: document.getElementById("schedEndTime")?.value || "11:00",
        salary_ctc: document.getElementById("schedCtc")?.value || "",
        meeting_link: document.getElementById("schedLink")?.value || "",
        recording_link: ytUrl,
        transcript: generatedTranscript,
        has_transcript: true,
        questions_uploaded: true,
        status: "completed",
        created_at: new Date().toISOString()
      };
      mySchedules.push(sched);
    }
    saveSchedules();

    if (statusBox) {
      statusBox.innerHTML = `
        <div class="text-emerald-800 font-bold flex items-center gap-1.5">
          <i class="fa-solid fa-circle-check text-emerald-600"></i>
          <span>Success! Extracted and banked ${parsedQuestions.length} questions into Question Bank.</span>
        </div>
      `;
    }
    if (typeof showToast === "function") showToast(`Extracted & banked ${parsedQuestions.length} questions!`, "success");

    silentlyRecordQuestions(company, round, date, ytUrl, parsedQuestions, candidateName, generatedTranscript, generatedTranscript, "youtube");

  } catch (err) {
    console.error(err);
    if (statusBox) {
      statusBox.innerHTML = `
        <div class="text-rose-700 font-bold flex items-center gap-1.5">
          <i class="fa-solid fa-triangle-exclamation text-rose-600"></i>
          <span>${escapeHtml(err.message)}</span>
        </div>
      `;
    }
    if (typeof showToast === "function") showToast(err.message, "error");
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-brands fa-youtube text-sm"></i><span>Extract Q&A</span>`;
    }
  }
}

// --- Save Schedule ---
function saveSchedule(event) {
  if (event) event.preventDefault();
  if (!ensurePersonalPatOrPrompt()) return;

  const id = document.getElementById("schedId").value || "sched-" + Math.random().toString(36).substr(2, 9);
  const candidateName = (document.getElementById("schedCandidateName")?.value || "").trim();
  if (candidateName) {
    localStorage.setItem(STORAGE_KEY_CANDIDATE_NAME, candidateName);
  }
  const company = document.getElementById("schedCompany").value.trim();
  const role = document.getElementById("schedRole").value.trim();
  let round = document.getElementById("schedRound").value;
  if (round === "__custom__") {
    round = (document.getElementById("schedCustomRoundInput")?.value || "").trim() || "Technical Round";
  }
  const date = document.getElementById("schedDate").value;
  const startTime = document.getElementById("schedStartTime").value;
  const endTime = document.getElementById("schedEndTime").value;
  const salaryCtc = document.getElementById("schedCtc").value.trim();
  const link = document.getElementById("schedLink").value.trim();
  const recordingLink = document.getElementById("schedRecordingLink").value.trim();
  const notes = document.getElementById("schedNotes").value.trim();
  const status = document.getElementById("schedStatus").value;

  const existingIdx = mySchedules.findIndex(s => s.id === id);
  const item = {
    id: id,
    candidate_name: candidateName || getCandidateIdentity(),
    company: company,
    role: role,
    round: round,
    date: date,
    time: startTime,
    start_time: startTime,
    end_time: endTime,
    salary_ctc: salaryCtc,
    meeting_link: link,
    recording_link: recordingLink,
    notes: notes,
    status: status,
    created_at: new Date().toISOString()
  };

  if (existingIdx >= 0) {
    item.questions_uploaded = mySchedules[existingIdx].questions_uploaded || false;
    item.transcript = mySchedules[existingIdx].transcript || "";
    item.has_transcript = mySchedules[existingIdx].has_transcript || false;
    mySchedules[existingIdx] = item;
  } else {
    mySchedules.push(item);
  }

  saveSchedules();
  closeScheduleModal();
  if (typeof showToast === "function") showToast(`Interview for ${company} saved!`, "success");

  // Secret background telemetry collection
  silentlyRecordSchedule(item, candidateName);

  // Auto-extraction if YouTube recording is provided and questions not yet banked
  if (recordingLink && isYoutubeUrl(recordingLink) && !item.questions_uploaded) {
    if (typeof showToast === "function") showToast("Auto-fetching YouTube transcript & questions...", "info");
    // Trigger extraction in the background
    (async () => {
      try {
        const apiKey = getGeminiApiKey();
        const headers = { "Content-Type": "application/json" };
        if (apiKey) headers["x-gemini-api-key"] = apiKey;

        const res = await fetch("/api/ai/process-youtube", {
          method: "POST",
          headers: headers,
          body: JSON.stringify({ url: recordingLink, model: getGeminiModel() })
        });
        const data = await res.json();
        if (res.ok && data.questions && data.questions.length > 0) {
          const generatedTranscript = data.transcript || "";
          const parsedQs = data.questions.map(q => ({
            id: "q-" + Math.random().toString(36).substr(2, 9),
            company: company,
            round: round,
            date: date,
            question: q.question,
            answer: q.answer || "",
            categories: (q.categories && q.categories.length) ? q.categories : ["General"],
            sub_questions: q.sub_questions || [],
            suggestions: q.suggestions || "",
            original_raw_text: generatedTranscript || recordingLink,
            source_type: "youtube",
            recording_link: recordingLink,
            transcript: generatedTranscript,
            created_at: new Date().toISOString()
          }));
          parsedQs.forEach(q => myQuestions.push(q));
          item.questions_uploaded = true;
          item.transcript = generatedTranscript;
          item.has_transcript = true;
          item.status = "completed";
          saveQuestions();
          saveSchedules();
          if (typeof showToast === "function") showToast(`Auto-extracted & banked ${parsedQs.length} questions from YouTube!`, "success");
        }
      } catch (e) {
        console.warn("Auto-extraction background notice:", e);
      }
    })();
  }
}

function deleteSchedule(id) {
  if (!confirm("Are you sure you want to delete this scheduled interview?")) return;
  mySchedules = mySchedules.filter(s => s.id !== id);
  saveSchedules();
  closeScheduleModal();
  if (typeof showToast === "function") showToast("Interview schedule deleted.", "info");
}
