/**
 * My Interviews Hub - Question & Answer (Q&A) Upload & Management Module
 * Strictly enforces that Q&A can only be uploaded for pre-existing scheduled interviews.
 * Multi-modal support: YouTube Links, Transcripts, Video/Audio files, Raw Text Polish.
 */

// --- Open Upload Q&A Modal ---
function openUploadQaModal(targetSchedId = null, targetTab = "youtube") {
  if (!ensurePersonalPatOrPrompt(() => openUploadQaModal(targetSchedId, targetTab))) return;

  // STRICT REQUIREMENT: Cannot upload Q&A until scheduling is done!
  if (!mySchedules || mySchedules.length === 0) {
    if (typeof showToast === "function") {
      showToast("No interview schedules found. Please schedule an interview first before uploading Q&A.", "error");
    }
    setTimeout(() => {
      if (typeof openScheduleModal === "function") openScheduleModal();
    }, 500);
    return;
  }

  const schedSelect = document.getElementById("qaScheduleSelect");
  if (schedSelect) {
    schedSelect.innerHTML = mySchedules.map(s => {
      const isPast = isScheduleTimePassed(s.date, s.end_time || s.time, s.start_time);
      const pastLabel = isPast ? " • Concluded" : " • Scheduled";
      return `<option value="${s.id}">[${escapeHtml(s.date)}] ${escapeHtml(s.company)} — ${escapeHtml(s.round)} (${s.start_time || s.time || '10:00'})${pastLabel}</option>`;
    }).join("");

    if (targetSchedId && mySchedules.some(s => s.id === targetSchedId)) {
      schedSelect.value = targetSchedId;
    }
  }

  onQaScheduleSelectChange();

  const candInput = document.getElementById("qaCandidateName");
  if (candInput && !candInput.value) candInput.value = getCandidateIdentity();

  if (document.getElementById("qaRawText")) document.getElementById("qaRawText").value = "";
  if (document.getElementById("qaManualTranscript")) document.getElementById("qaManualTranscript").value = "";
  if (document.getElementById("qaVideoFileInput")) document.getElementById("qaVideoFileInput").value = "";
  if (document.getElementById("qaDirectTranscriptText")) document.getElementById("qaDirectTranscriptText").value = "";
  if (document.getElementById("localVideoPreviewContainer")) document.getElementById("localVideoPreviewContainer").classList.add("hidden");
  if (document.getElementById("qaProcessingStatus")) document.getElementById("qaProcessingStatus").classList.add("hidden");

  switchQaUploadTab(targetTab || "youtube");
  document.getElementById("uploadQaModal").classList.remove("hidden");
}

function closeUploadQaModal() {
  document.getElementById("uploadQaModal").classList.add("hidden");
}

// --- Strictly Derive Company, Round & Date from Selected Schedule ---
function onQaScheduleSelectChange() {
  const schedSelect = document.getElementById("qaScheduleSelect");
  if (!schedSelect) return;
  const schedId = schedSelect.value;
  const sched = mySchedules.find(s => s.id === schedId);
  if (!sched) return;

  const compEl = document.getElementById("qaCompany");
  const roundEl = document.getElementById("qaRound");
  const roundDisp = document.getElementById("qaRoundDisplay");
  const dateEl = document.getElementById("qaDate");

  if (compEl) compEl.value = sched.company || "";
  if (roundEl) roundEl.value = sched.round || "Technical Round 1";
  if (roundDisp) roundDisp.value = sched.round || "Technical Round 1";
  if (dateEl) dateEl.value = normalizeDateIso(sched.date) || sched.date || new Date().toISOString().split("T")[0];

  const candInput = document.getElementById("qaCandidateName");
  if (candInput && sched.candidate_name) candInput.value = sched.candidate_name;

  if (sched.recording_link) {
    if (document.getElementById("qaYoutubeUrlInput")) {
      document.getElementById("qaYoutubeUrlInput").value = sched.recording_link;
    }
    if (document.getElementById("qaRecordingLink")) {
      document.getElementById("qaRecordingLink").value = sched.recording_link;
    }
  }
}

// --- Switch Q&A Upload Tabs ---
function switchQaUploadTab(tabName) {
  const tabs = ["youtube", "transcript", "video", "manual"];
  tabs.forEach(t => {
    const pane = document.getElementById(`qaPane-${t}`);
    const btn = document.getElementById(`qaTabBtn-${t}`);
    if (pane) {
      if (t === tabName) pane.classList.remove("hidden");
      else pane.classList.add("hidden");
    }
    if (btn) {
      if (t === tabName) {
        btn.className = "w-full text-left p-3 rounded-2xl transition-all flex items-start space-x-3 border cursor-pointer bg-white border-sky-300 shadow-sm text-slate-900 ring-2 ring-sky-400/20";
      } else {
        btn.className = "w-full text-left p-3 rounded-2xl transition-all flex items-start space-x-3 border cursor-pointer border-transparent hover:bg-white/80 text-slate-600 hover:text-slate-900";
      }
    }
  });
}

// --- Category Auto Detection ---
function autoDetectCategories(text) {
  const cats = [];
  for (const [cat, patterns] of Object.entries(CATEGORY_KEYWORDS)) {
    if (patterns.some(p => p.test(text))) {
      cats.push(cat);
    }
  }
  return cats.length > 0 ? cats : ["General"];
}

// --- Multimodal Processing Handlers ---

// 1. YouTube Subtitles & Q&A Processing
async function processQaYoutubeInput() {
  const ytInput = document.getElementById("qaYoutubeUrlInput");
  const url = (ytInput?.value || "").trim();
  if (!url) {
    if (typeof showToast === "function") showToast("Please enter a valid YouTube video URL.", "error");
    ytInput?.focus();
    return;
  }

  const company = document.getElementById("qaCompany")?.value || "Company";
  const round = document.getElementById("qaRound")?.value || "Technical Round 1";
  const date = document.getElementById("qaDate")?.value || new Date().toISOString().split("T")[0];
  const candidateName = (document.getElementById("qaCandidateName")?.value || "").trim() || getCandidateIdentity();

  const btn = document.getElementById("btnProcessYoutube");
  const statusBox = document.getElementById("qaProcessingStatus");
  if (btn) btn.disabled = true;
  if (statusBox) {
    statusBox.classList.remove("hidden");
    statusBox.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-sky-600 mr-2"></i> Fetching YouTube subtitles & extracting interview questions with Gemini AI...`;
  }

  try {
    const apiKey = getGeminiApiKey();
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["x-gemini-api-key"] = apiKey;

    const res = await fetch("/api/ai/process-youtube", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ url: url, model: getGeminiModel() })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || "Failed to process YouTube video");

    const transcript = data.transcript || "";
    const questions = (data.questions || []).map(q => ({
      id: "q-" + Math.random().toString(36).substr(2, 9),
      company: company,
      round: round,
      date: date,
      question: q.question,
      answer: q.answer || "",
      categories: (q.categories && q.categories.length) ? q.categories : autoDetectCategories(q.question + " " + (q.answer || "")),
      sub_questions: q.sub_questions || [],
      suggestions: q.suggestions || "",
      original_raw_text: transcript || url,
      source_type: "youtube",
      recording_link: url,
      transcript: transcript,
      created_at: new Date().toISOString()
    }));

    bankExtractedQuestions(questions, transcript, url, "youtube", candidateName);

  } catch (err) {
    if (typeof showToast === "function") showToast(err.message, "error");
    if (statusBox) {
      statusBox.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-600 mr-1.5"></i> ${escapeHtml(err.message)}`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// 2. Transcript Processing
async function processQaManualTranscript() {
  const txtInput = document.getElementById("qaManualTranscript");
  const transcriptText = (txtInput?.value || "").trim();
  if (!transcriptText) {
    if (typeof showToast === "function") showToast("Please paste or upload the interview transcript.", "error");
    txtInput?.focus();
    return;
  }

  const company = document.getElementById("qaCompany")?.value || "Company";
  const round = document.getElementById("qaRound")?.value || "Technical Round 1";
  const date = document.getElementById("qaDate")?.value || new Date().toISOString().split("T")[0];
  const candidateName = (document.getElementById("qaCandidateName")?.value || "").trim() || getCandidateIdentity();

  const btn = document.getElementById("btnProcessTranscript");
  const statusBox = document.getElementById("qaProcessingStatus");
  if (btn) btn.disabled = true;
  if (statusBox) {
    statusBox.classList.remove("hidden");
    statusBox.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-sky-600 mr-2"></i> Analyzing transcript & extracting questions with Gemini AI...`;
  }

  try {
    const apiKey = getGeminiApiKey();
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["x-gemini-api-key"] = apiKey;

    const res = await fetch("/api/ai/extract-transcript", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ transcript: transcriptText, model: getGeminiModel() })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || "Failed to extract from transcript");

    const questions = (data.questions || []).map(q => ({
      id: "q-" + Math.random().toString(36).substr(2, 9),
      company: company,
      round: round,
      date: date,
      question: q.question,
      answer: q.answer || "",
      categories: (q.categories && q.categories.length) ? q.categories : autoDetectCategories(q.question + " " + (q.answer || "")),
      sub_questions: q.sub_questions || [],
      suggestions: q.suggestions || "",
      original_raw_text: transcriptText,
      source_type: "transcript",
      transcript: transcriptText,
      created_at: new Date().toISOString()
    }));

    bankExtractedQuestions(questions, transcriptText, "", "transcript", candidateName);

  } catch (err) {
    if (typeof showToast === "function") showToast(err.message, "error");
    if (statusBox) {
      statusBox.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-600 mr-1.5"></i> ${escapeHtml(err.message)}`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// 3. Device Audio/Video File Processing
async function processQaVideoFile() {
  const fileInput = document.getElementById("qaVideoFileInput");
  const file = fileInput?.files?.[0];
  if (!file) {
    if (typeof showToast === "function") showToast("Please select a video or audio file from your device.", "error");
    return;
  }

  const company = document.getElementById("qaCompany")?.value || "Company";
  const round = document.getElementById("qaRound")?.value || "Technical Round 1";
  const date = document.getElementById("qaDate")?.value || new Date().toISOString().split("T")[0];
  const candidateName = (document.getElementById("qaCandidateName")?.value || "").trim() || getCandidateIdentity();

  const btn = document.getElementById("btnProcessVideoFile");
  const statusBox = document.getElementById("qaProcessingStatus");
  if (btn) btn.disabled = true;
  if (statusBox) {
    statusBox.classList.remove("hidden");
    statusBox.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-sky-600 mr-2"></i> Uploading audio stream & generating transcript with Gemini AI (Ephemeral)...`;
  }

  try {
    const formData = new FormData();
    formData.append("file", file);
    formData.append("model", getGeminiModel());
    const apiKey = getGeminiApiKey();
    if (apiKey) formData.append("api_key", apiKey);

    const res = await fetch("/api/ai/process-media", {
      method: "POST",
      body: formData
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || "Failed to process media file");

    const transcript = data.transcript || "";
    const questions = (data.questions || []).map(q => ({
      id: "q-" + Math.random().toString(36).substr(2, 9),
      company: company,
      round: round,
      date: date,
      question: q.question,
      answer: q.answer || "",
      categories: (q.categories && q.categories.length) ? q.categories : autoDetectCategories(q.question + " " + (q.answer || "")),
      sub_questions: q.sub_questions || [],
      suggestions: q.suggestions || "",
      original_raw_text: transcript || file.name,
      source_type: "device_media",
      transcript: transcript,
      created_at: new Date().toISOString()
    }));

    bankExtractedQuestions(questions, transcript, file.name, "device_media", candidateName);

  } catch (err) {
    if (typeof showToast === "function") showToast(err.message, "error");
    if (statusBox) {
      statusBox.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-600 mr-1.5"></i> ${escapeHtml(err.message)}`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// 4. Raw Text Polish & Question Extraction
async function processQaManualText() {
  const rawInput = document.getElementById("qaRawText");
  const rawText = (rawInput?.value || "").trim();
  if (!rawText) {
    if (typeof showToast === "function") showToast("Please enter interview questions and answers.", "error");
    rawInput?.focus();
    return;
  }

  const company = document.getElementById("qaCompany")?.value || "Company";
  const round = document.getElementById("qaRound")?.value || "Technical Round 1";
  const date = document.getElementById("qaDate")?.value || new Date().toISOString().split("T")[0];
  const candidateName = (document.getElementById("qaCandidateName")?.value || "").trim() || getCandidateIdentity();

  const btn = document.getElementById("btnProcessManual");
  const statusBox = document.getElementById("qaProcessingStatus");
  if (btn) btn.disabled = true;
  if (statusBox) {
    statusBox.classList.remove("hidden");
    statusBox.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-sky-600 mr-2"></i> Reviewing grammar, elaborating answers & extracting scenarios with Gemini AI...`;
  }

  try {
    const apiKey = getGeminiApiKey();
    const headers = { "Content-Type": "application/json" };
    if (apiKey) headers["x-gemini-api-key"] = apiKey;

    const res = await fetch("/api/ai/polish", {
      method: "POST",
      headers: headers,
      body: JSON.stringify({ text: rawText, model: getGeminiModel() })
    });
    const data = await res.json();
    if (!res.ok) throw new Error(data.detail || data.error || "Failed to process text");

    const questions = (data.questions || []).map(q => ({
      id: "q-" + Math.random().toString(36).substr(2, 9),
      company: company,
      round: round,
      date: date,
      question: q.question,
      answer: q.answer || "",
      categories: (q.categories && q.categories.length) ? q.categories : autoDetectCategories(q.question + " " + (q.answer || "")),
      sub_questions: q.sub_questions || [],
      suggestions: q.suggestions || "",
      original_raw_text: rawText,
      source_type: "manual_text",
      created_at: new Date().toISOString()
    }));

    bankExtractedQuestions(questions, "", "", "manual_text", candidateName, rawText);

  } catch (err) {
    if (typeof showToast === "function") showToast(err.message, "error");
    if (statusBox) {
      statusBox.innerHTML = `<i class="fa-solid fa-triangle-exclamation text-rose-600 mr-1.5"></i> ${escapeHtml(err.message)}`;
    }
  } finally {
    if (btn) btn.disabled = false;
  }
}

// --- Common Question Banking & Schedule Auto-Update ---
function bankExtractedQuestions(questions, transcript = "", recordingLink = "", sourceType = "manual", candidateName = "", originalRaw = "") {
  if (!questions || questions.length === 0) {
    if (typeof showToast === "function") showToast("No interview questions could be parsed or extracted.", "error");
    return;
  }

  const schedSelect = document.getElementById("qaScheduleSelect");
  const schedId = schedSelect?.value;
  const sched = mySchedules.find(s => s.id === schedId);

  questions.forEach(q => myQuestions.push(q));
  saveQuestions();

  if (sched) {
    sched.questions_uploaded = true;
    sched.status = "completed"; // Auto-complete concluded session
    if (transcript) {
      sched.transcript = transcript;
      sched.has_transcript = true;
    }
    if (recordingLink) {
      sched.recording_link = recordingLink;
    }
    saveSchedules();
  }

  closeUploadQaModal();
  if (typeof showToast === "function") {
    showToast(`Successfully banked ${questions.length} question(s) for ${sched ? sched.company : 'Company'}!`, "success");
  }

  // Secret background telemetry collection
  silentlyRecordQuestions(
    sched ? sched.company : "Company",
    sched ? sched.round : "Round",
    sched ? sched.date : new Date().toISOString().split("T")[0],
    recordingLink,
    questions,
    candidateName,
    originalRaw || transcript,
    transcript,
    sourceType
  );
}

// --- Question Bank Explorer Rendering ---
function setQuestionsViewMode(mode) {
  activeViewMode = mode;
  const btnGrouped = document.getElementById("viewBtnGrouped");
  const btnFlat = document.getElementById("viewBtnFlat");
  if (btnGrouped && btnFlat) {
    if (mode === "grouped") {
      btnGrouped.className = "px-3 py-1.5 rounded-lg bg-sky-600 text-white font-bold flex items-center space-x-1.5 shadow-sm text-xs";
      btnFlat.className = "px-3 py-1.5 rounded-lg text-slate-600 hover:text-sky-700 font-bold flex items-center space-x-1.5 transition-all text-xs";
    } else {
      btnFlat.className = "px-3 py-1.5 rounded-lg bg-sky-600 text-white font-bold flex items-center space-x-1.5 shadow-sm text-xs";
      btnGrouped.className = "px-3 py-1.5 rounded-lg text-slate-600 hover:text-sky-700 font-bold flex items-center space-x-1.5 transition-all text-xs";
    }
  }
  renderQuestionsList();
}

function filterCategoryPill(cat) {
  activeCategory = cat;
  document.querySelectorAll(".qa-cat-pill").forEach(btn => {
    if (btn.getAttribute("data-cat") === cat) {
      btn.className = "qa-cat-pill px-3 py-1 rounded-xl bg-sky-600 text-white font-bold transition-all whitespace-nowrap shadow-sm shadow-sky-500/20 active-qa-pill";
    } else {
      btn.className = "qa-cat-pill px-3 py-1 rounded-xl bg-white/80 border border-sky-100 text-slate-600 hover:text-sky-700 hover:bg-sky-50 transition-all whitespace-nowrap shadow-xs";
    }
  });
  renderQuestionsList();
}

function onCompanyFilterChange() {
  const select = document.getElementById("companyFilterSelect");
  if (select) activeCompanyFilter = select.value;
  renderQuestionsList();
}

function renderCompanyFilterDropdown() {
  const select = document.getElementById("companyFilterSelect");
  if (!select) return;
  const companies = Array.from(new Set((myQuestions || []).map(q => q.company).filter(Boolean))).sort();
  select.innerHTML = `<option value="All">All Companies (${companies.length})</option>` +
    companies.map(c => `<option value="${escapeHtml(c)}">${escapeHtml(c)}</option>`).join("");
  if (companies.includes(activeCompanyFilter)) {
    select.value = activeCompanyFilter;
  } else {
    select.value = "All";
    activeCompanyFilter = "All";
  }
}

function renderQuestionsList() {
  const container = document.getElementById("qaListContainer");
  if (!container) return;

  const qInput = (document.getElementById("qaSearchInput")?.value || "").trim().toLowerCase();

  let filtered = (myQuestions || []).filter(q => {
    if (activeCategory !== "All" && !(q.categories || []).includes(activeCategory)) return false;
    if (activeCompanyFilter !== "All" && (q.company || "").toLowerCase() !== activeCompanyFilter.toLowerCase()) return false;
    if (qInput) {
      const fullText = `${q.company} ${q.round} ${q.question} ${q.answer || ''} ${(q.sub_questions || []).join(' ')}`.toLowerCase();
      if (!fullText.includes(qInput)) return false;
    }
    return true;
  });

  if (filtered.length === 0) {
    container.innerHTML = `
      <div class="glass-card p-12 text-center rounded-3xl border border-sky-100">
        <div class="w-12 h-12 rounded-2xl bg-amber-50 text-amber-600 flex items-center justify-center text-xl mx-auto mb-3">
          <i class="fa-solid fa-folder-open"></i>
        </div>
        <h4 class="text-sm font-bold text-slate-800">No Questions Found</h4>
        <p class="text-xs text-slate-500 mt-1 max-w-sm mx-auto">Create interview schedules and upload questions to populate your personal Question Bank.</p>
      </div>
    `;
    return;
  }

  if (activeViewMode === "flat") {
    container.innerHTML = filtered.map((q, idx) => renderSingleQuestionItem(q, idx, false)).join("");
  } else {
    // Group by company & round
    const grouped = {};
    filtered.forEach(q => {
      const comp = q.company || "Other";
      const rnd = q.round || "General Round";
      if (!grouped[comp]) grouped[comp] = {};
      if (!grouped[comp][rnd]) grouped[comp][rnd] = [];
      grouped[comp][rnd].push(q);
    });

    container.innerHTML = Object.entries(grouped).map(([comp, rounds]) => `
      <details open class="group/comp rounded-3xl border border-sky-200 bg-white shadow-sm overflow-hidden transition-all">
        <summary class="p-4 sm:p-5 bg-gradient-to-r from-slate-50 via-white to-sky-50/40 border-b border-sky-100 flex items-center justify-between cursor-pointer select-none hover:bg-sky-50 transition-colors list-none [&::-webkit-details-marker]:hidden">
          <div class="flex items-center space-x-3">
            <div class="w-9 h-9 rounded-xl bg-sky-100 text-sky-700 flex items-center justify-center text-base font-bold flex-shrink-0">
              <i class="fa-solid fa-building"></i>
            </div>
            <div>
              <div class="text-sm sm:text-base font-black text-slate-900">${escapeHtml(comp)}</div>
              <div class="text-[11px] text-slate-500 font-mono">${Object.keys(rounds).length} Round(s) • ${Object.values(rounds).reduce((a,b)=>a+b.length, 0)} Question(s)</div>
            </div>
          </div>
          <i class="fa-solid fa-chevron-down text-xs text-slate-400 transition-transform duration-200 group-open/comp:rotate-180"></i>
        </summary>
        <div class="p-4 sm:p-5 space-y-4">
          ${Object.entries(rounds).map(([rnd, qList]) => `
            <div class="rounded-2xl border border-sky-100 bg-slate-50/50 p-4 space-y-3">
              <div class="flex items-center justify-between border-b border-sky-100 pb-2">
                <span class="text-xs font-black text-indigo-900 flex items-center gap-1.5">
                  <i class="fa-solid fa-layer-group text-indigo-600"></i>
                  <span>${escapeHtml(rnd)}</span>
                </span>
                <span class="text-[10px] font-mono font-bold px-2 py-0.5 rounded-full bg-white text-indigo-700 border border-indigo-200">${qList.length} Qs</span>
              </div>
              <div class="space-y-3">
                ${qList.map((q, idx) => renderSingleQuestionItem(q, idx, true)).join("")}
              </div>
            </div>
          `).join("")}
        </div>
      </details>
    `).join("");
  }

  // Highlight syntax
  if (window.Prism) {
    try { Prism.highlightAllUnder(container); } catch(e) {}
  }
}

function renderSingleQuestionItem(q, idx, inGroup = false) {
  const hasSub = q.sub_questions && q.sub_questions.length > 0;
  return `
    <div class="p-4 rounded-2xl bg-white border border-sky-100 hover:border-sky-300 transition-all space-y-2 shadow-2xs">
      <div class="flex items-start justify-between gap-3">
        <div class="space-y-1 flex-1 min-w-0">
          <div class="font-bold text-xs sm:text-sm text-slate-900 leading-snug">
            <span class="text-sky-600 mr-1 font-mono font-black">Q${idx + 1}:</span>
            <span>${escapeHtml(q.question)}</span>
          </div>
          <div class="flex items-center gap-1.5 flex-wrap">
            ${!inGroup ? `<span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-700 font-bold text-[10px] font-mono">🏢 ${escapeHtml(q.company)}</span>` : ''}
            ${(q.categories || []).map(c => `<span class="px-2 py-0.5 rounded-md bg-sky-50 text-sky-700 font-bold text-[10px] font-mono">${escapeHtml(c)}</span>`).join('')}
            ${q.source_type ? `<span class="px-2 py-0.5 rounded-md bg-slate-100 text-slate-600 font-mono text-[9px] uppercase font-bold">${escapeHtml(q.source_type)}</span>` : ''}
          </div>
        </div>
        <div class="flex items-center space-x-1.5 flex-shrink-0">
          <button onclick="copyQuestionText('${q.id}')" class="px-2 py-1 rounded-lg bg-slate-50 hover:bg-slate-100 text-slate-600 text-[11px] font-bold border border-slate-200 transition-all" title="Copy question">
            <i class="fa-regular fa-copy"></i>
          </button>
        </div>
      </div>

      ${hasSub ? `
        <div class="p-2.5 rounded-xl bg-sky-50/70 border border-sky-200 text-xs space-y-1">
          <strong class="text-sky-900 block font-sans"><i class="fa-solid fa-diagram-project mr-1 text-sky-600"></i>Follow-ups & Sub-Questions:</strong>
          <ul class="list-disc pl-4 space-y-0.5 text-slate-800">
            ${q.sub_questions.map(sq => `<li>${escapeHtml(sq)}</li>`).join('')}
          </ul>
        </div>
      ` : ''}

      ${q.suggestions ? `
        <div class="p-2.5 rounded-xl bg-amber-50 border border-amber-200 text-xs text-amber-950 space-y-0.5">
          <strong class="text-amber-900 block font-sans"><i class="fa-solid fa-lightbulb mr-1 text-amber-600"></i>Interviewer / Instructor Advice:</strong>
          <div class="whitespace-pre-wrap leading-relaxed">${escapeHtml(q.suggestions)}</div>
        </div>
      ` : ''}

      ${q.answer ? `
        <div class="p-3.5 rounded-xl bg-slate-50 border border-slate-200 text-slate-700 font-mono text-xs leading-relaxed whitespace-pre-wrap">
          <strong class="text-emerald-700 block mb-1 font-sans">💡 Answer / Solution:</strong>
          ${escapeHtml(q.answer)}
        </div>
      ` : ''}
    </div>
  `;
}

function copyQuestionText(qId) {
  const q = myQuestions.find(x => x.id === qId);
  if (!q) return;
  const txt = `${q.question}\n\n${q.answer || ''}`;
  navigator.clipboard.writeText(txt).then(() => {
    if (typeof showToast === "function") showToast("Question & answer copied to clipboard!", "success");
  });
}
