/**
 * CDWC Talent Recommendation Engine — Vanilla JS Frontend
 *
 * Talks to the FastAPI backend at /recommend (form) and /chat (chat mode).
 */

const API_BASE = window.location.origin;

// ── DOM refs ──────────────────────────────────────────────────────────
const tabs        = document.querySelectorAll('.tab');
const panelForm   = document.getElementById('panel-form');
const panelChat   = document.getElementById('panel-chat');
const resultsEl   = document.getElementById('results');

// Form
const searchForm  = document.getElementById('search-form');
const skillsInput = document.getElementById('skills');
const compSlider  = document.getElementById('competency');
const compOutput  = document.getElementById('competency-val');
const expInput    = document.getElementById('experience');
const roleSelect  = document.getElementById('role-level');
const availCheck  = document.getElementById('availability');
const btnSearch   = document.getElementById('btn-search');

// Chat
const chatForm    = document.getElementById('chat-form');
const chatInput   = document.getElementById('chat-input');
const chatMsgs    = document.getElementById('chat-messages');

// ── Init ──────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', () => {
  loadRoleLevels();
  compSlider.addEventListener('input', () => {
    compOutput.textContent = parseFloat(compSlider.value).toFixed(1);
  });
});

async function loadRoleLevels() {
  try {
    const res = await fetch(`${API_BASE}/config/role-levels`);
    const data = await res.json();
    roleSelect.innerHTML = data.role_levels
      .map(r => `<option value="${r}"${r === 'mid' ? ' selected' : ''}>${r.charAt(0).toUpperCase() + r.slice(1)}</option>`)
      .join('');
  } catch {
    roleSelect.innerHTML = ['junior','mid','senior','lead','principal']
      .map(r => `<option value="${r}"${r === 'mid' ? ' selected' : ''}>${r.charAt(0).toUpperCase() + r.slice(1)}</option>`)
      .join('');
  }
}

// ── Tab switching ─────────────────────────────────────────────────────
tabs.forEach(tab => {
  tab.addEventListener('click', () => {
    tabs.forEach(t => { t.classList.remove('active'); t.setAttribute('aria-selected', 'false'); });
    tab.classList.add('active');
    tab.setAttribute('aria-selected', 'true');

    const mode = tab.dataset.mode;
    panelForm.classList.toggle('hidden', mode !== 'form');
    panelChat.classList.toggle('hidden', mode !== 'chat');
    resultsEl.innerHTML = '';
  });
});

// ── Form search ───────────────────────────────────────────────────────
searchForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const rawSkills = skillsInput.value.trim();
  if (!rawSkills) {
    skillsInput.focus();
    return;
  }

  const skills = rawSkills.split(',').map(s => s.trim().toLowerCase().replace(/\s+/g, '_')).filter(Boolean);

  const payload = {
    required_skills: skills,
    required_competency_level: parseFloat(compSlider.value),
    min_experience: parseInt(expInput.value, 10) || 0,
    role_level: roleSelect.value,
    availability_required: availCheck.checked,
  };

  btnSearch.disabled = true;
  btnSearch.innerHTML = '<span class="spinner"></span> Searching...';
  resultsEl.innerHTML = '';

  try {
    const res = await fetch(`${API_BASE}/recommend`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    renderResults(data);
  } catch (err) {
    resultsEl.innerHTML = `<div class="error-msg">Error: ${escapeHtml(err.message)}</div>`;
  } finally {
    btnSearch.disabled = false;
    btnSearch.textContent = '🔍 Search Talent';
  }
});

// ── Chat ──────────────────────────────────────────────────────────────
chatForm.addEventListener('submit', async (e) => {
  e.preventDefault();

  const msg = chatInput.value.trim();
  if (!msg) return;

  appendBubble('user', msg);
  chatInput.value = '';
  resultsEl.innerHTML = '';

  const thinkingEl = appendBubble('assistant', '');
  thinkingEl.innerHTML = '<span class="spinner"></span> Searching talent pool...';

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || res.statusText);
    }

    const data = await res.json();
    thinkingEl.textContent = data.reply;
  } catch (err) {
    thinkingEl.textContent = `Error: ${err.message}`;
    thinkingEl.classList.add('error-msg');
  }

  chatMsgs.scrollTop = chatMsgs.scrollHeight;
});

function appendBubble(role, text) {
  const el = document.createElement('div');
  el.className = `chat-bubble ${role}`;
  el.textContent = text;
  chatMsgs.appendChild(el);
  chatMsgs.scrollTop = chatMsgs.scrollHeight;
  return el;
}

// ── Render result cards ───────────────────────────────────────────────
function renderResults(data) {
  const recs = data.recommendations || [];
  const total = data.total_candidates_evaluated || 0;
  const filtered = data.candidates_after_filtering || 0;

  if (!recs.length) {
    resultsEl.innerHTML = `<div class="no-results">
      Evaluated ${total} employees, ${filtered} passed filters — but none matched well enough.<br>
      Try relaxing your criteria.
    </div>`;
    return;
  }

  let html = `<p class="results-summary">${total} evaluated → ${filtered} filtered → ${recs.length} shown</p>`;

  recs.forEach((c, i) => {
    const bd = c.score_breakdown;
    const skillTags = (c.skills || []).map(s => `<span class="skill-tag">${escapeHtml(s)}</span>`).join('');

    html += `
      <article class="card" aria-label="Candidate ${i + 1}: ${escapeHtml(c.name)}">
        <div class="card-header">
          <span class="card-name">${i + 1}. ${escapeHtml(c.name)}</span>
          <span class="card-score">Score: ${c.total_score.toFixed(2)}</span>
        </div>
        <div class="card-meta">${escapeHtml(c.department)} · ${escapeHtml(c.role_level)} · ${c.years_experience} yrs exp</div>
        <div class="card-skills">${skillTags}</div>
        <div class="card-breakdown">
          <span class="breakdown-item">Skill <span>${pct(bd.skill_overlap)}</span></span>
          <span class="breakdown-item">Competency <span>${pct(bd.competency)}</span></span>
          <span class="breakdown-item">Experience <span>${pct(bd.experience)}</span></span>
          <span class="breakdown-item">Role <span>${pct(bd.role_match)}</span></span>
        </div>
      </article>`;
  });

  resultsEl.innerHTML = html;
}

// ── Helpers ────────────────────────────────────────────────────────────
function pct(v) { return Math.round(v * 100) + '%'; }

function escapeHtml(str) {
  const div = document.createElement('div');
  div.textContent = str;
  return div.innerHTML;
}
