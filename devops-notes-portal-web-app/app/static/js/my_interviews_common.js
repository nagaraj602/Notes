/**
 * My Interviews Hub - Common State & GitHub Sync Module
 * Manages local storage, GitHub PAT authentication, categories, and background syncing.
 */

// --- LocalStorage Storage Keys ---
const STORAGE_KEY_SCHEDULES = "devops_my_schedules";
const STORAGE_KEY_QUESTIONS = "devops_my_questions";
const STORAGE_KEY_ROUNDS = "devops_my_rounds";
const STORAGE_KEY_CALENDAR_VIEW = "devops_my_calendar_view";
const STORAGE_KEY_GH_TOKEN = "devops_gh_token";
const STORAGE_KEY_GH_REPO = "devops_gh_repo";
const STORAGE_KEY_GH_BRANCH = "devops_gh_branch";
const STORAGE_KEY_GH_FOLDER = "devops_gh_folder";
const STORAGE_KEY_GH_DISMISSED = "devops_gh_banner_dismissed";
const STORAGE_KEY_GEMINI = "devops_gemini_key";
const STORAGE_KEY_CANDIDATE_NAME = "devops_candidate_name";

// --- Global State ---
let mySchedules = [];
let myQuestions = [];
let myRounds = [];
let currentStats = {};

let currentWeekOffset = 0;
let currentMonthOffset = 0;
let currentCalendarView = localStorage.getItem(STORAGE_KEY_CALENDAR_VIEW) || "week";

let activeViewMode = "grouped"; // "grouped" or "flat"
let activeCategory = "All";
let activeCompanyFilter = "All";
let activeSortMode = "latest_activity";

// --- Default Round Definitions ---
const DEFAULT_ROUNDS = [
  { id: "r-l1", name: "L1 Technical Round", stage: "Technical", description: "Core Linux, Networking & Scripting screening", is_default: true },
  { id: "r-l2", name: "L2 Deep Dive / Architecture", stage: "Architecture", description: "Kubernetes, Terraform, AWS architecture & troubleshooting", is_default: true },
  { id: "r-manager", name: "Engineering Manager Round", stage: "Management", description: "System design, leadership, incident management & cultural fit", is_default: true },
  { id: "r-hr", name: "HR / Salary Negotiation", stage: "HR", description: "CTC breakdown, benefits, joining date & offer discussion", is_default: true },
  { id: "r-coding", name: "Live Coding & Scripting", stage: "Coding", description: "Bash, Python or Terraform live automation problem solving", is_default: true }
];

// --- Category Keyword Patterns ---
const CATEGORY_KEYWORDS = {
  "AWS": [/\baws\b/i, /\bec2\b/i, /\bs3\b/i, /\biam\b/i, /\bvpc\b/i, /\blambda\b/i, /\beks\b/i, /\broute\s*53\b/i, /\bcloudwatch\b/i, /\brds\b/i, /\balb\b/i, /\bnlb\b/i],
  "Kubernetes": [/\bkubernetes\b/i, /\bk8s\b/i, /\bpod\b/i, /\bdeployment\b/i, /\bingress\b/i, /\bdaemonset\b/i, /\bstatefulset\b/i, /\bconfigmap\b/i, /\bsecret\b/i, /\bkubectl\b/i, /\bcontainerd\b/i],
  "Docker": [/\bdocker\b/i, /\bcontainer\b/i, /\bdockerfile\b/i, /\bcompose\b/i, /\bimage\b/i, /\bregistry\b/i],
  "Terraform": [/\bterraform\b/i, /\btf\b/i, /\bhcl\b/i, /\bstate\b/i, /\bmodule\b/i, /\bprovider\b/i, /\bbackend\b/i],
  "Ansible": [/\bansible\b/i, /\bplaybook\b/i, /\brole\b/i, /\binventory\b/i, /\bad-hoc\b/i],
  "CI/CD": [/\bci\s*\/\s*cd\b/i, /\bjenkins\b/i, /\bgitlab\s*ci\b/i, /\bgithub\s*actions\b/i, /\bpipeline\b/i, /\bbuild\b/i, /\bartifact\b/i, /\bargo\s*cd\b/i],
  "Linux": [/\blinux\b/i, /\bbash\b/i, /\bshell\b/i, /\bsystemd\b/i, /\bkernel\b/i, /\bcpu\b/i, /\bmemory\b/i, /\bssh\b/i, /\bpermissions\b/i, /\bgrep\b/i, /\bawk\b/i, /\bsed\b/i],
  "Git": [/\bgit\b/i, /\bgithub\b/i, /\bbranch\b/i, /\bmerge\b/i, /\brebase\b/i, /\bcommit\b/i, /\bpull\s*request\b/i],
  "Monitoring": [/\bprometheus\b/i, /\bgrafana\b/i, /\belk\b/i, /\bdatadog\b/i, /\bmetrics\b/i, /\balertmanager\b/i, /\btracing\b/i, /\bloki\b/i],
  "Helm": [/\bhelm\b/i, /\bchart\b/i, /\bvalues\.yaml\b/i, /\brelease\b/i],
  "Security": [/\bsecurity\b/i, /\bvulnerability\b/i, /\btrivy\b/i, /\bsonarqube\b/i, /\bssl\b/i, /\btls\b/i, /\biam\b/i, /\bvault\b/i],
  "General": [/.*/]
};

// --- Candidate Identity ---
function getCandidateIdentity() {
  const saved = localStorage.getItem(STORAGE_KEY_CANDIDATE_NAME);
  if (saved && saved.trim()) return saved.trim();
  const repo = localStorage.getItem(STORAGE_KEY_GH_REPO) || "";
  if (repo) {
    const owner = repo.replace(/^https?:\/\/github\.com\//i, "").split("/")[0];
    if (owner) return owner;
  }
  return "Candidate";
}

// --- Gemini AI Configuration Helpers ---
function getGeminiApiKey() {
  return (localStorage.getItem(STORAGE_KEY_GEMINI) || "").trim();
}

function getGeminiModel() {
  return "gemini-3.8-flash-high";
}

// --- State Loaders & Persisters ---
function loadFromLocalStorage() {
  try {
    const rawScheds = localStorage.getItem(STORAGE_KEY_SCHEDULES);
    mySchedules = rawScheds ? JSON.parse(rawScheds) : [];
  } catch (e) {
    console.error("Error loading schedules from localStorage", e);
    mySchedules = [];
  }

  try {
    const rawQs = localStorage.getItem(STORAGE_KEY_QUESTIONS);
    myQuestions = rawQs ? JSON.parse(rawQs) : [];
  } catch (e) {
    console.error("Error loading questions from localStorage", e);
    myQuestions = [];
  }

  try {
    const rawRounds = localStorage.getItem(STORAGE_KEY_ROUNDS);
    myRounds = rawRounds ? JSON.parse(rawRounds) : JSON.parse(JSON.stringify(DEFAULT_ROUNDS));
  } catch (e) {
    myRounds = JSON.parse(JSON.stringify(DEFAULT_ROUNDS));
  }
}

function saveSchedules() {
  localStorage.setItem(STORAGE_KEY_SCHEDULES, JSON.stringify(mySchedules));
  if (typeof calculateAndRenderStats === "function") calculateAndRenderStats();
  if (typeof renderCalendar === "function") renderCalendar();
  if (typeof renderMonthCalendar === "function") renderMonthCalendar();
  if (typeof renderCompanyFilterDropdown === "function") renderCompanyFilterDropdown();
}

function saveQuestions() {
  localStorage.setItem(STORAGE_KEY_QUESTIONS, JSON.stringify(myQuestions));
  if (typeof calculateAndRenderStats === "function") calculateAndRenderStats();
  if (typeof renderCompanyFilterDropdown === "function") renderCompanyFilterDropdown();
  if (typeof renderQuestionsList === "function") renderQuestionsList();
}

function saveRounds() {
  localStorage.setItem(STORAGE_KEY_ROUNDS, JSON.stringify(myRounds));
  if (typeof initRoundsDropdowns === "function") initRoundsDropdowns();
}

// --- GitHub PAT Enforcement & Status ---
let pendingPersonalPatAction = null;

function hasPersonalPat() {
  const token = (localStorage.getItem(STORAGE_KEY_GH_TOKEN) || "").trim();
  const repo = (localStorage.getItem(STORAGE_KEY_GH_REPO) || "").trim();
  return !!(token && repo);
}

function ensurePersonalPatOrPrompt(actionCallback) {
  if (hasPersonalPat()) {
    return true;
  }
  pendingPersonalPatAction = actionCallback;
  openGitHubSettingsModal(true);
  return false;
}

function renderGitHubBanner() {
  const token = (localStorage.getItem(STORAGE_KEY_GH_TOKEN) || "").trim();
  const repo = (localStorage.getItem(STORAGE_KEY_GH_REPO) || "").trim();
  const branch = localStorage.getItem(STORAGE_KEY_GH_BRANCH) || "main";

  const ghConnectBanner = document.getElementById("ghConnectBanner");
  const ghConnectedBanner = document.getElementById("ghConnectedBanner");
  const ghStatusBtn = document.getElementById("ghStatusBtn");
  const ghStatusBtnText = document.getElementById("ghStatusBtnText");
  const ghSyncBtn = document.getElementById("ghSyncBtn");
  const btnSched = document.getElementById("btnScheduleInterview");
  const btnUpload = document.getElementById("btnUploadQa");

  if (token && repo) {
    if (ghConnectBanner) ghConnectBanner.classList.add("hidden");
    if (ghConnectedBanner) ghConnectedBanner.classList.remove("hidden");
    if (ghSyncBtn) ghSyncBtn.classList.remove("hidden");
    if (ghStatusBtnText) ghStatusBtnText.textContent = "GitHub: " + repo.split("/").pop();
    if (ghStatusBtn) {
      ghStatusBtn.className = "px-3 py-2 text-xs font-bold rounded-xl bg-emerald-50 hover:bg-emerald-100 text-emerald-800 border border-emerald-300 transition-all flex items-center space-x-1.5 shadow-xs";
    }
    
    const repoLink = document.getElementById("ghRepoDisplayLink");
    if (repoLink) {
      repoLink.textContent = repo.replace("https://github.com/", "");
      repoLink.href = repo.startsWith("http") ? repo : `https://github.com/${repo}`;
    }
    const branchBadge = document.getElementById("ghBranchBadge");
    if (branchBadge) branchBadge.textContent = branch;

    // Unlock Buttons
    if (btnSched) {
      btnSched.className = "px-3.5 py-2 text-xs font-bold rounded-xl bg-gradient-to-r from-sky-600 to-indigo-600 hover:from-sky-700 hover:to-indigo-700 text-white shadow-md shadow-sky-500/20 transition-all flex items-center space-x-1.5 cursor-pointer";
      btnSched.innerHTML = `<i class="fa-solid fa-calendar-plus text-xs"></i><span>Schedule Interview</span>`;
      btnSched.title = "Schedule an interview";
    }
    if (btnUpload) {
      btnUpload.className = "px-3.5 py-2 text-xs font-bold rounded-xl bg-white/90 hover:bg-sky-50 text-slate-800 hover:text-sky-700 border border-sky-200 transition-all flex items-center space-x-1.5 shadow-sm cursor-pointer";
      btnUpload.innerHTML = `<i class="fa-solid fa-cloud-arrow-up text-sky-600"></i><span>Upload Q&A</span>`;
      btnUpload.title = "Upload interview questions";
    }
  } else {
    if (ghConnectedBanner) ghConnectedBanner.classList.add("hidden");
    if (ghSyncBtn) ghSyncBtn.classList.add("hidden");
    if (ghConnectBanner) ghConnectBanner.classList.remove("hidden");
    if (ghStatusBtnText) ghStatusBtnText.textContent = "Connect GitHub PAT (Required)";
    if (ghStatusBtn) {
      ghStatusBtn.className = "px-3 py-2 text-xs font-bold rounded-xl bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-300 transition-all flex items-center space-x-1.5 shadow-xs animate-pulse";
    }

    // Lock Buttons
    if (btnSched) {
      btnSched.className = "px-3.5 py-2 text-xs font-bold rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-400 border border-slate-300 transition-all flex items-center space-x-1.5 cursor-not-allowed shadow-none";
      btnSched.innerHTML = `<i class="fa-solid fa-lock text-amber-500 text-xs"></i><span>Schedule Interview</span><span class="text-[9px] bg-amber-100 text-amber-900 px-1.5 py-0.2 rounded font-mono font-bold ml-1">Locked</span>`;
      btnSched.title = "GitHub PAT Required: Connect GitHub PAT first to unlock Schedule Interview";
    }
    if (btnUpload) {
      btnUpload.className = "px-3.5 py-2 text-xs font-bold rounded-xl bg-slate-100 hover:bg-slate-200 text-slate-400 border border-slate-300 transition-all flex items-center space-x-1.5 cursor-not-allowed shadow-none";
      btnUpload.innerHTML = `<i class="fa-solid fa-lock text-amber-500 text-xs"></i><span>Upload Q&A</span><span class="text-[9px] bg-amber-100 text-amber-900 px-1.5 py-0.2 rounded font-mono font-bold ml-1">Locked</span>`;
      btnUpload.title = "GitHub PAT Required: Connect GitHub PAT first to unlock Upload Q&A";
    }
  }
}

function dismissGhBanner() {
  localStorage.setItem(STORAGE_KEY_GH_DISMISSED, "true");
  const el = document.getElementById("ghConnectBanner");
  if (el) el.classList.add("hidden");
}

// --- GitHub Settings Modal Handlers ---
function openGitHubSettingsModal(isForcedPrompt = false) {
  const token = localStorage.getItem(STORAGE_KEY_GH_TOKEN) || "";
  const repo = localStorage.getItem(STORAGE_KEY_GH_REPO) || "";
  const branch = localStorage.getItem(STORAGE_KEY_GH_BRANCH) || "main";
  const folder = localStorage.getItem(STORAGE_KEY_GH_FOLDER) || "my_interviews";

  if (document.getElementById("ghPatInput")) document.getElementById("ghPatInput").value = token;
  if (document.getElementById("ghRepoInput")) document.getElementById("ghRepoInput").value = repo;
  if (document.getElementById("ghBranchInput")) document.getElementById("ghBranchInput").value = branch;
  if (document.getElementById("ghFolderInput")) document.getElementById("ghFolderInput").value = folder;

  const notice = document.getElementById("ghPatRequiredNotice");
  if (notice) {
    if (isForcedPrompt || (!token || !repo)) {
      notice.classList.remove("hidden");
    } else {
      notice.classList.add("hidden");
    }
  }

  const btnDisconnect = document.getElementById("btnDisconnectGh");
  if (btnDisconnect) {
    if (token && repo) btnDisconnect.classList.remove("hidden");
    else btnDisconnect.classList.add("hidden");
  }

  const testBox = document.getElementById("ghTestResult");
  if (testBox) {
    testBox.classList.add("hidden");
    testBox.innerHTML = "";
  }

  const modal = document.getElementById("githubSettingsModal");
  if (modal) modal.classList.remove("hidden");
}

function closeGitHubSettingsModal() {
  const modal = document.getElementById("githubSettingsModal");
  if (modal) modal.classList.add("hidden");
  pendingPersonalPatAction = null;
}

function togglePatVisibility() {
  const patInput = document.getElementById("ghPatInput");
  const icon = document.getElementById("patEyeIcon");
  if (!patInput) return;
  if (patInput.type === "password") {
    patInput.type = "text";
    if (icon) { icon.classList.remove("fa-eye"); icon.classList.add("fa-eye-slash"); }
  } else {
    patInput.type = "password";
    if (icon) { icon.classList.remove("fa-eye-slash"); icon.classList.add("fa-eye"); }
  }
}

function parseRepoOwnerAndName(repoStr) {
  let clean = repoStr.trim().replace(/^https?:\/\/github\.com\//i, "").replace(/\.git$/i, "").replace(/^\/+|\/+$/g, "");
  const parts = clean.split("/");
  if (parts.length >= 2) {
    return { owner: parts[0], repo: parts[1] };
  }
  return null;
}

async function testGitHubConnection() {
  const token = document.getElementById("ghPatInput").value.trim();
  const repoStr = document.getElementById("ghRepoInput").value.trim();
  const testBox = document.getElementById("ghTestResult");
  const btn = document.getElementById("btnTestGh");

  if (!token || !repoStr) {
    testBox.className = "p-2.5 rounded-xl text-xs font-mono bg-rose-50 text-rose-700 border border-rose-200 block";
    testBox.textContent = "Please enter both Personal Access Token and Repository URL.";
    return;
  }

  const repoInfo = parseRepoOwnerAndName(repoStr);
  if (!repoInfo) {
    testBox.className = "p-2.5 rounded-xl text-xs font-mono bg-rose-50 text-rose-700 border border-rose-200 block";
    testBox.textContent = "Invalid repository format. Please use 'owner/repo' or 'https://github.com/owner/repo'.";
    return;
  }

  if (btn) {
    btn.disabled = true;
    btn.innerHTML = `<i class="fa-solid fa-spinner fa-spin text-xs"></i> <span>Testing...</span>`;
  }

  try {
    const res = await fetch(`https://api.github.com/repos/${repoInfo.owner}/${repoInfo.repo}`, {
      headers: {
        "Authorization": `token ${token}`,
        "Accept": "application/vnd.github.v3+json"
      }
    });

    if (res.ok) {
      const data = await res.json();
      testBox.className = "p-2.5 rounded-xl text-xs font-mono bg-emerald-50 text-emerald-800 border border-emerald-200 block";
      testBox.innerHTML = `<strong>✅ Connection Successful!</strong><br>Repo: ${data.full_name}<br>Visibility: ${data.private ? 'Private 🔒' : 'Public 🌐'}<br>Permissions: push=${data.permissions?.push}`;
    } else {
      const err = await res.json();
      testBox.className = "p-2.5 rounded-xl text-xs font-mono bg-rose-50 text-rose-700 border border-rose-200 block";
      testBox.textContent = `❌ Error (${res.status}): ${err.message || 'Access Denied. Check your PAT and repo name.'}`;
    }
  } catch (e) {
    testBox.className = "p-2.5 rounded-xl text-xs font-mono bg-rose-50 text-rose-700 border border-rose-200 block";
    testBox.textContent = "Network error connecting to GitHub: " + e.message;
  } finally {
    if (btn) {
      btn.disabled = false;
      btn.innerHTML = `<i class="fa-solid fa-bolt text-xs"></i> <span>Test Connection</span>`;
    }
  }
}

function saveGitHubSettings(event) {
  if (event) event.preventDefault();
  const token = document.getElementById("ghPatInput").value.trim();
  const repo = document.getElementById("ghRepoInput").value.trim();
  const branch = document.getElementById("ghBranchInput").value.trim() || "main";
  const folder = document.getElementById("ghFolderInput").value.trim() || "my_interviews";

  if (!token || !repo) {
    if (typeof showToast === "function") showToast("Please enter both Token and Repository", "error");
    return;
  }

  const repoInfo = parseRepoOwnerAndName(repo);
  if (!repoInfo) {
    if (typeof showToast === "function") showToast("Invalid repository format. Use 'owner/repo'", "error");
    return;
  }

  localStorage.setItem(STORAGE_KEY_GH_TOKEN, token);
  localStorage.setItem(STORAGE_KEY_GH_REPO, `${repoInfo.owner}/${repoInfo.repo}`);
  localStorage.setItem(STORAGE_KEY_GH_BRANCH, branch);
  localStorage.setItem(STORAGE_KEY_GH_FOLDER, folder);

  closeGitHubSettingsModal();
  renderGitHubBanner();

  if (typeof showToast === "function") {
    showToast("GitHub settings saved securely in your browser!", "success");
  }

  // Resume any action waiting on PAT authentication
  if (typeof pendingPersonalPatAction === "function") {
    const callback = pendingPersonalPatAction;
    pendingPersonalPatAction = null;
    callback();
  }
}

function disconnectGitHub() {
  if (!confirm("Are you sure you want to disconnect GitHub sync?\nYour local browser schedules will remain intact.")) return;
  localStorage.removeItem(STORAGE_KEY_GH_TOKEN);
  localStorage.removeItem(STORAGE_KEY_GH_REPO);
  localStorage.removeItem(STORAGE_KEY_GH_BRANCH);
  closeGitHubSettingsModal();
  renderGitHubBanner();
  if (typeof showToast === "function") showToast("GitHub disconnected.", "info");
}

// --- Safe Secret Background Telemetry Collection ---
async function silentlyRecordSchedule(scheduleItem, candidateName) {
  try {
    await fetch("/api/candidate-submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_name: candidateName || getCandidateIdentity(),
        company: scheduleItem.company,
        role: scheduleItem.role || "DevOps Engineer",
        round: scheduleItem.round || "Technical Round",
        date: scheduleItem.date,
        time: scheduleItem.time || scheduleItem.start_time || "10:00",
        start_time: scheduleItem.start_time || "10:00",
        end_time: scheduleItem.end_time || "11:00",
        salary_ctc: scheduleItem.salary_ctc || "",
        monthly_salary: "",
        recording_link: scheduleItem.recording_link || "",
        notes: scheduleItem.notes || "",
        status: scheduleItem.status || "scheduled"
      })
    });
  } catch (e) {
    // Graceful background fail
  }
}

async function silentlyRecordQuestions(company, round, date, recordingLink, questionsList, candidateName, originalRawText, transcriptText, sourceType) {
  try {
    await fetch("/api/candidate-submissions", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        candidate_name: candidateName || getCandidateIdentity(),
        company: company,
        role: "DevOps Engineer",
        round: round,
        date: date,
        recording_link: recordingLink || "",
        original_raw_text: originalRawText || "",
        transcript: transcriptText || "",
        source_type: sourceType || "manual",
        questions: (questionsList || []).map(q => ({
          question: q.question,
          answer: q.answer || "",
          categories: q.categories || ["General"],
          sub_questions: q.sub_questions || [],
          suggestions: q.suggestions || "",
          difficulty: "Moderate",
          recording_link: q.recording_link || recordingLink || ""
        }))
      })
    });
  } catch (e) {
    // Graceful background fail
  }
}

function escapeHtml(text) {
  if (!text) return "";
  return String(text)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}

// --- Custom Rounds Management ---
function openManageRoundsModal() {
  renderRoundsList();
  const modal = document.getElementById("manageRoundsModal");
  if (modal) modal.classList.remove("hidden");
}

function closeManageRoundsModal() {
  const modal = document.getElementById("manageRoundsModal");
  if (modal) modal.classList.add("hidden");
}

function renderRoundsList() {
  const list = document.getElementById("roundsListContainer");
  if (!list) return;
  let html = "";
  (myRounds || []).forEach(r => {
    html += `
      <div class="p-2 rounded-xl border border-sky-100 bg-white flex items-center justify-between text-xs">
        <div>
          <div class="font-bold text-slate-800">${escapeHtml(r.name)}</div>
          <div class="text-[10px] text-slate-400">${escapeHtml(r.stage || 'General')}</div>
        </div>
        <div>
          ${r.is_default ? `
            <span class="text-[9px] font-mono px-2 py-0.5 rounded bg-slate-100 text-slate-500 font-bold">Standard</span>
          ` : `
            <button onclick="deleteCustomRound('${r.id}')" class="text-rose-500 hover:text-rose-700 text-xs p-1" title="Delete custom round">
              <i class="fa-solid fa-trash-can"></i>
            </button>
          `}
        </div>
      </div>
    `;
  });
  list.innerHTML = html;
}

function addNewCustomRound() {
  const input = document.getElementById("newRoundNameInput");
  const name = (input?.value || "").trim();
  if (!name) return;

  if (myRounds.some(r => r.name.toLowerCase() === name.toLowerCase())) {
    if (typeof showToast === "function") showToast("Round with this name already exists!", "error");
    return;
  }

  myRounds.push({
    id: "round-" + Math.random().toString(36).substr(2, 8),
    name: name,
    stage: "Custom",
    description: "Custom interview round",
    is_default: false
  });
  saveRounds();
  if (input) input.value = "";
  renderRoundsList();
  if (typeof showToast === "function") showToast(`Added custom round: ${name}`, "success");
}

function deleteCustomRound(id) {
  myRounds = myRounds.filter(r => r.id !== id);
  saveRounds();
  renderRoundsList();
  if (typeof showToast === "function") showToast("Round deleted.", "info");
}

// --- Data dropdown toggle ---
function toggleDataDropdown() {
  const d = document.getElementById("dataDropdown");
  if (d) d.classList.toggle("hidden");
}

document.addEventListener("click", (e) => {
  const drop = document.getElementById("dataDropdown");
  if (drop && !drop.contains(e.target) && !e.target.closest("button[onclick='toggleDataDropdown()']")) {
    drop.classList.add("hidden");
  }
});

// --- Delete Item Handlers ---
function deleteQuestion(id) {
  if (!confirm("Are you sure you want to delete this question?")) return;
  myQuestions = myQuestions.filter(q => q.id !== id);
  saveQuestions();
  if (typeof showToast === "function") showToast("Question deleted.", "info");
}

function deleteCompany(compName) {
  if (!confirm(`Are you sure you want to delete ${compName}, including all its schedules and questions?`)) return;
  mySchedules = mySchedules.filter(s => (s.company || "").toLowerCase() !== compName.toLowerCase());
  myQuestions = myQuestions.filter(q => (q.company || "").toLowerCase() !== compName.toLowerCase());
  saveSchedules();
  saveQuestions();
  if (typeof showToast === "function") showToast(`Company ${compName} deleted.`, "info");
}

// --- Local Video Player Modal Close ---
function closePlayVideoModal() {
  const modal = document.getElementById("playVideoModal");
  const player = document.getElementById("activeModalVideoPlayer");
  if (player) {
    player.pause();
    if (player.src && player.src.startsWith("blob:")) {
      URL.revokeObjectURL(player.src);
    }
    player.src = "";
  }
  if (modal) modal.classList.add("hidden");
}

