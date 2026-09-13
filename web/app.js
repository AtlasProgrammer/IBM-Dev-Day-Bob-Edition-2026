const AGENT_ORDER = [
  {id: "document-analyst", name: "Document Analyst", icon: "DOCS"},
  {id: "code-investigator", name: "Code Investigator", icon: "CODE"},
  {id: "log-analyst", name: "Log Analyst", icon: "LOGS"},
  {id: "git-historian", name: "Git Historian", icon: "GIT"},
  {id: "test-engineer", name: "Test Engineer", icon: "TEST"}
];
const PHASES = ["Understand", "Investigate", "Synthesize", "Fix", "Verify", "Ready"];

let catalog = null;
let selected = "BUG-1842";
let source = null;
let lastFix = null;

function esc(value) {
  return String(value ?? "").replace(/[&<>"']/g, (ch) => ({
    "&": "&amp;",
    "<": "&lt;",
    ">": "&gt;",
    "\"": "&quot;",
    "'": "&#39;"
  }[ch]));
}

function incidentById(id) {
  return (catalog?.incidents || []).find((item) => item.id === id);
}

function renderPhases(active) {
  document.getElementById("phases").innerHTML = PHASES.map((label, index) =>
    `<div class="step${index <= active ? " on" : ""}">${index + 1} · ${label}</div>`
  ).join("");
}

function renderAgents(states = {}, running = "") {
  document.getElementById("agents").innerHTML = AGENT_ORDER.map((meta) => {
    const item = states[meta.name];
    const isRun = running === meta.name;
    const status = item ? "done" : isRun ? "run" : "";
    const label = item ? "Complete" : isRun ? "Running" : "Waiting";
    const body = item
      ? `<div class="finding">${esc(item.findings?.[0]?.title || "No issues found")}</div><div class="evidence">${esc((item.evidence || []).join(" · "))}</div>`
      : `<div class="sub" style="margin-top:18px">${isRun ? "Collecting evidence" : "Parallel task queued"}</div>`;
    return `<div class="card"><h3>${meta.icon} · ${esc(meta.name)}</h3><div class="status ${status}">${label}</div>${body}</div>`;
  }).join("");
}

function renderIncidents() {
  document.getElementById("incidents").innerHTML = (catalog.incidents || []).map((item) =>
    `<button class="incident${item.id === selected ? " active" : ""}" data-id="${esc(item.id)}" type="button"><b>${esc(item.id)} · ${esc(item.severity)}</b><span>${esc(item.title)}</span></button>`
  ).join("");
}

function renderCaps() {
  document.getElementById("caps").innerHTML = (catalog.capabilities || []).map((item) =>
    `<div class="cap"><b>${esc(item.feature)}</b><span>${esc(item.use)}</span></div>`
  ).join("");
  const project = catalog.project || {};
  document.getElementById("project").innerHTML =
    `<b>${esc(project.name)} ${esc(project.version)}</b><div>${(project.files || []).length} files · ${(project.documents || []).length} documents</div>`;
}

function showIssue() {
  const incident = incidentById(selected);
  if (!incident) return;
  document.getElementById("issueMeta").textContent = `${incident.id} · ${incident.workflow} · ${incident.tenant}`;
  document.getElementById("issueTitle").textContent = incident.title;
  document.getElementById("issueSummary").textContent = incident.summary;
  document.getElementById("issueTags").innerHTML = [
    `<span class="tag warn">${esc(incident.severity)}</span>`,
    `<span class="tag">${esc(incident.manual_minutes)} min manual</span>`,
    ...incident.bob_features.map((item) => `<span class="tag blue">${esc(item)}</span>`)
  ].join("");
}

function resetWorkspace() {
  lastFix = null;
  document.getElementById("root").classList.add("hidden");
  document.getElementById("fix").classList.add("hidden");
  document.getElementById("result").classList.add("hidden");
  document.getElementById("fixBtn").disabled = true;
  document.getElementById("valBtn").disabled = true;
  renderPhases(0);
  renderAgents();
}

function selectIncident(id) {
  if (source) {
    source.close();
    source = null;
  }
  selected = id;
  renderIncidents();
  showIssue();
  resetWorkspace();
  document.getElementById("run").disabled = false;
  document.getElementById("run").textContent = "Run investigation";
}

function applySynthesis(data) {
  document.getElementById("root").classList.remove("hidden");
  document.getElementById("rootTitle").textContent = data.title;
  document.getElementById("rootText").textContent = data.explanation;
  const pct = Math.round((data.confidence || 0) * 100);
  document.getElementById("confidence").textContent = `${pct}%`;
  document.getElementById("confBar").style.width = `${pct}%`;
  document.getElementById("agree").textContent = `${data.agreeing_agents || 0} agents in agreement`;
  document.getElementById("evidence").innerHTML = (data.evidence || []).map((item) =>
    `<span class="tag">${esc(item)}</span>`
  ).join("");
}

async function runInvestigation() {
  const button = document.getElementById("run");
  button.disabled = true;
  button.textContent = "Investigating…";
  resetWorkspace();
  renderPhases(1);
  const states = {};
  renderAgents(states, "Document Analyst");
  if (source) source.close();
  source = new EventSource(`/api/stream?id=${encodeURIComponent(selected)}`);
  source.addEventListener("phase", (event) => {
    const payload = JSON.parse(event.data);
    if (payload.phase === "investigate") renderPhases(1);
  });
  source.addEventListener("agent", (event) => {
    const payload = JSON.parse(event.data);
    states[payload.agent] = payload;
    const next = AGENT_ORDER.find((item) => !states[item.name]);
    renderAgents(states, next ? next.name : "");
  });
  source.addEventListener("synthesis", (event) => {
    applySynthesis(JSON.parse(event.data));
    renderPhases(2);
  });
  source.addEventListener("complete", () => {
    source.close();
    source = null;
    renderAgents(states);
    renderPhases(2);
    document.getElementById("fixBtn").disabled = false;
    button.textContent = "Investigation complete";
  });
  source.addEventListener("error", () => {
    if (source) source.close();
    source = null;
    button.disabled = false;
    button.textContent = "Retry investigation";
  });
}

async function generateFix() {
  const button = document.getElementById("fixBtn");
  button.disabled = true;
  const data = await fetch("/api/fix", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({id: selected})
  }).then((res) => res.json());
  lastFix = data;
  document.getElementById("fix").classList.remove("hidden");
  document.getElementById("fixMeta").textContent = `${data.title} · risk ${data.risk} · ${data.files} files`;
  document.getElementById("patch").textContent = (data.patch || []).map((item) =>
    `${item.file}\n  → ${item.change}`
  ).join("\n\n");
  renderPhases(3);
  document.getElementById("valBtn").disabled = false;
  button.disabled = false;
}

async function validateFix() {
  const button = document.getElementById("valBtn");
  button.disabled = true;
  renderPhases(4);
  const data = await fetch("/api/validate", {
    method: "POST",
    headers: {"Content-Type": "application/json"},
    body: JSON.stringify({id: selected})
  }).then((res) => res.json());
  const after = data.tests?.after_fix || {};
  const review = data.review || {};
  const reviewPass = Object.values(review).every((item) => item === "PASS");
  document.getElementById("result").classList.remove("hidden");
  document.getElementById("testScore").textContent = `${after.passed ?? 0} / ${after.total ?? 0}`;
  document.getElementById("testTag").textContent = after.failed === 0 ? "PASS" : "HOLD";
  document.getElementById("reviewScore").textContent = `${Object.values(review).filter((item) => item === "PASS").length} / ${Object.keys(review).length || 5}`;
  document.getElementById("reviewTag").textContent = reviewPass ? "PASS" : "HOLD";
  document.getElementById("ready").textContent = `${data.readiness}%`;
  document.getElementById("readyTag").textContent = data.decision || "HOLD";
  document.getElementById("saved").textContent = `${data.saved_minutes} min`;
  document.getElementById("savedTag").textContent = `${data.reduction_pct}% faster`;
  document.getElementById("summary").textContent =
`MANUAL WORKFLOW    ${data.manual_minutes} min
ORCHESTRA WORKFLOW  ${data.orchestra_minutes} min
TIME REDUCTION      ${data.reduction_pct}%

Security     ${review.security || "—"}
Logic        ${review.logic || "—"}
Performance  ${review.performance || "—"}
Tests        ${review.tests || "—"}
Architecture ${review.architecture || "—"}

DECISION: ${data.decision}`;
  const impact = data.impact || {};
  document.getElementById("impactList").innerHTML = (impact.orchestra_steps || []).map((item) =>
    `<li>${esc(item)}</li>`
  ).join("");
  renderPhases(5);
  button.disabled = false;
}

async function openSkills() {
  const data = await fetch("/api/skills").then((res) => res.json());
  document.getElementById("skills").innerHTML = (data.skills || []).map((item) =>
    `<article><b>${esc(item.title)}</b><div class="tiny">${esc(item.path)}</div><pre>${esc(item.body)}</pre></article>`
  ).join("");
  document.getElementById("drawer").classList.remove("hidden");
}

async function boot() {
  catalog = await fetch("/api/catalog").then((res) => res.json());
  renderIncidents();
  renderCaps();
  showIssue();
  renderPhases(0);
  renderAgents();
  document.getElementById("incidents").addEventListener("click", (event) => {
    const button = event.target.closest("[data-id]");
    if (button) selectIncident(button.getAttribute("data-id"));
  });
  document.getElementById("run").addEventListener("click", runInvestigation);
  document.getElementById("fixBtn").addEventListener("click", generateFix);
  document.getElementById("valBtn").addEventListener("click", validateFix);
  document.getElementById("skillsBtn").addEventListener("click", openSkills);
  document.getElementById("closeSkills").addEventListener("click", () => {
    document.getElementById("drawer").classList.add("hidden");
  });
}

boot();
