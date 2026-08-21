/**
 * AegisCare - Patient Journey AI Web Application
 * Handles MongoDB state sync, patient intake chat, timeline rendering, and clinician HITL review.
 */

let activePatientId = 'PATIENT_101';
let currentPatients = [];
let currentReviews = [];
let currentTimeline = [];

// DOM Elements
const dbStatusPill = document.getElementById('dbStatusPill');
const dbStatusText = document.getElementById('dbStatusText');
const patientSelect = document.getElementById('patientSelect');
const tabPatientView = document.getElementById('tabPatientView');
const tabClinicianView = document.getElementById('tabClinicianView');
const patientViewSection = document.getElementById('patientViewSection');
const clinicianViewSection = document.getElementById('clinicianViewSection');
const hitlBadge = document.getElementById('hitlBadge');

// Patient Profile Elements
const patientAvatar = document.getElementById('patientAvatar');
const patientName = document.getElementById('patientName');
const patientIdBadge = document.getElementById('patientIdBadge');
const phasePill = document.getElementById('phasePill');
const patientAgeGender = document.getElementById('patientAgeGender');
const patientCondition = document.getElementById('patientCondition');
const patientPhysician = document.getElementById('patientPhysician');

// Metrics Elements
const metricTotalEvents = document.getElementById('metricTotalEvents');
const metricPendingLabs = document.getElementById('metricPendingLabs');
const metricOverdue = document.getElementById('metricOverdue');
const metricHitlPending = document.getElementById('metricHitlPending');

// Timeline & Summary
const timelineContainer = document.getElementById('timelineContainer');
const timelineCountBadge = document.getElementById('timelineCountBadge');
const summaryContent = document.getElementById('summaryContent');
const btnCopySummary = document.getElementById('btnCopySummary');
const btnTriggerCoordination = document.getElementById('btnTriggerCoordination');

// Chat Elements
const chatMessages = document.getElementById('chatMessages');
const chatForm = document.getElementById('chatForm');
const chatInput = document.getElementById('chatInput');

// Review Queue
const hitlQueueContainer = document.getElementById('hitlQueueContainer');
const filterAllReviews = document.getElementById('filterAllReviews');
const filterPendingReviews = document.getElementById('filterPendingReviews');
const filterResolvedReviews = document.getElementById('filterResolvedReviews');
let activeReviewFilter = 'all';

// Modals
const eventModal = document.getElementById('eventModal');
const btnAddEventModalBtn = document.getElementById('btnAddEventModalBtn');
const btnCloseEventModal = document.getElementById('btnCloseEventModal');
const btnCancelEventModal = document.getElementById('btnCancelEventModal');
const eventForm = document.getElementById('eventForm');

const newPatientModal = document.getElementById('newPatientModal');
const btnNewPatient = document.getElementById('btnNewPatient');
const btnClosePatientModal = document.getElementById('btnClosePatientModal');
const btnCancelPatientModal = document.getElementById('btnCancelPatientModal');
const newPatientForm = document.getElementById('newPatientForm');

const toastContainer = document.getElementById('toastContainer');

// --- Initialization ---
document.addEventListener('DOMContentLoaded', async () => {
  setupEventListeners();
  await checkDbStatus();
  await loadPatients();
  await refreshActivePatientData();
  await loadHitlReviews();
});

function setupEventListeners() {
  // Navigation Tabs
  tabPatientView.addEventListener('click', () => switchView('patient'));
  tabClinicianView.addEventListener('click', () => switchView('clinician'));

  // Patient Selector
  patientSelect.addEventListener('change', async (e) => {
    activePatientId = e.target.value;
    await refreshActivePatientData();
    await loadHitlReviews();
  });

  // Action Buttons
  btnTriggerCoordination.addEventListener('click', runAgentCoordination);
  btnCopySummary.addEventListener('click', copySummaryToClipboard);

  // Chat Form
  chatForm.addEventListener('submit', handlePatientChatSubmit);

  // Symptom Chips
  document.querySelectorAll('.symptom-chip').forEach((chip) => {
    chip.addEventListener('click', () => {
      const sym = chip.getAttribute('data-symptom');
      if (chatInput.value.trim()) {
        chatInput.value += `, ${sym}`;
      } else {
        chatInput.value = `I am experiencing ${sym}`;
      }
      chatInput.focus();
    });
  });

  // Review Filters
  filterAllReviews.addEventListener('click', () => setReviewFilter('all'));
  filterPendingReviews.addEventListener('click', () => setReviewFilter('pending'));
  filterResolvedReviews.addEventListener('click', () => setReviewFilter('resolved'));

  // Modals
  btnAddEventModalBtn.addEventListener('click', () => eventModal.classList.add('open'));
  btnCloseEventModal.addEventListener('click', () => eventModal.classList.remove('open'));
  btnCancelEventModal.addEventListener('click', () => eventModal.classList.remove('open'));
  eventForm.addEventListener('submit', handleAddEventSubmit);

  btnNewPatient.addEventListener('click', () => newPatientModal.classList.add('open'));
  btnClosePatientModal.addEventListener('click', () => newPatientModal.classList.remove('open'));
  btnCancelPatientModal.addEventListener('click', () => newPatientModal.classList.remove('open'));
  newPatientForm.addEventListener('submit', handleCreatePatientSubmit);
}

// --- View Switcher ---
function switchView(view) {
  if (view === 'patient') {
    tabPatientView.classList.add('active');
    tabClinicianView.classList.remove('active');
    patientViewSection.classList.add('active');
    clinicianViewSection.classList.remove('active');
  } else {
    tabClinicianView.classList.add('active');
    tabPatientView.classList.remove('active');
    clinicianViewSection.classList.add('active');
    patientViewSection.classList.remove('active');
    loadHitlReviews();
  }
}

// --- Database Status ---
async function checkDbStatus() {
  try {
    const res = await fetch('/api/db/status');
    const data = await res.json();
    if (data.mongodb_connected) {
      dbStatusPill.className = 'db-status-pill';
      dbStatusText.textContent = 'MongoDB: Connected (localhost:27017)';
    } else {
      dbStatusPill.className = 'db-status-pill offline';
      dbStatusText.textContent = 'MongoDB: Resilient Cache Active';
    }
  } catch (err) {
    dbStatusPill.className = 'db-status-pill offline';
    dbStatusText.textContent = 'MongoDB: Offline';
  }
}

// --- Patient Loading & Profile Rendering ---
async function loadPatients() {
  try {
    const res = await fetch('/api/patients');
    currentPatients = await res.json();
    patientSelect.innerHTML = '';
    currentPatients.forEach((p) => {
      const opt = document.createElement('option');
      opt.value = p.patient_id;
      opt.textContent = `${p.name} (${p.patient_id})`;
      if (p.patient_id === activePatientId) opt.selected = true;
      patientSelect.appendChild(opt);
    });
  } catch (err) {
    showToast('Failed to load patient list from database', 'error');
  }
}

async function refreshActivePatientData() {
  try {
    const res = await fetch(`/api/patients/${activePatientId}`);
    if (!res.ok) throw new Error('Patient not found');
    const data = await res.json();
    const p = data.patient;
    currentTimeline = data.timeline || [];
    currentReviews = data.pending_reviews || [];

    // Render Hero Card
    patientAvatar.textContent = p.avatar_initials || p.name.slice(0, 2).toUpperCase();
    patientName.textContent = p.name;
    patientIdBadge.textContent = p.patient_id;
    patientAgeGender.textContent = `${p.age || 'N/A'} / ${p.gender || 'N/A'}`;
    patientCondition.textContent = p.condition || 'General Evaluation';
    patientPhysician.textContent = p.primary_physician || 'Dr. Sarah Chen';

    // Render Metrics
    renderMetrics(currentTimeline, currentReviews);

    // Render Timeline
    renderTimeline(currentTimeline);

    // Update HITL Badge
    updateHitlBadge(currentReviews);
  } catch (err) {
    showToast(`Error fetching patient data: ${err.message}`, 'error');
  }
}

function renderMetrics(timeline, reviews) {
  metricTotalEvents.textContent = timeline.length;

  const pendingLabs = timeline.filter(
    (e) => e.event_type === 'LabOrder' && e.status === 'pending'
  ).length;
  metricPendingLabs.textContent = pendingLabs;

  const overdue = timeline.filter(
    (e) => ['overdue', 'unfulfilled'].includes(e.status)
  ).length;
  metricOverdue.textContent = overdue;

  const pendingReviews = reviews.filter(
    (r) => r.status === 'PENDING' || r.status === 'ReviewStatus.PENDING'
  ).length;
  metricHitlPending.textContent = pendingReviews;
}

function updateHitlBadge(reviews) {
  const pendingCount = reviews.filter(
    (r) => r.status === 'PENDING' || r.status === 'ReviewStatus.PENDING'
  ).length;
  if (pendingCount > 0) {
    hitlBadge.style.display = 'inline-block';
    hitlBadge.textContent = pendingCount;
  } else {
    hitlBadge.style.display = 'none';
  }
}

// --- Timeline Rendering ---
function renderTimeline(events) {
  timelineCountBadge.textContent = `${events.length} Records`;
  timelineContainer.innerHTML = '';

  if (events.length === 0) {
    timelineContainer.innerHTML = `
      <div class="glass-card" style="padding: 2rem; text-align: center; color: var(--text-muted);">
        No journey events recorded yet. Click "Add Record" or use the AI intake assistant.
      </div>`;
    return;
  }

  // Sort events chronologically (latest first)
  const sorted = [...events].sort((a, b) => new Date(b.timestamp) - new Date(a.timestamp));

  sorted.forEach((evt) => {
    const item = document.createElement('div');
    item.className = `timeline-item ${evt.event_type}`;

    let iconSvg = '<circle cx="12" cy="12" r="8"/>';
    if (evt.event_type === 'Consultation') {
      iconSvg = '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/><circle cx="12" cy="7" r="4"/>';
    } else if (evt.event_type === 'LabOrder' || evt.event_type === 'LabResult') {
      iconSvg = '<path d="M10 2v7.31M14 9.3V1.99M8.5 2h7M14 9.3a6.5 6.5 0 1 1-4 0"/>';
    } else if (evt.event_type === 'Referral') {
      iconSvg = '<path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/><polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>';
    } else if (evt.event_type === 'FollowUp') {
      iconSvg = '<path d="M12 8v4l3 3m6-3a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/>';
    }

    const dateStr = evt.timestamp ? new Date(evt.timestamp).toLocaleDateString(undefined, {
      year: 'numeric', month: 'short', day: 'numeric',
    }) : 'Recent';

    const detailsStr = Object.entries(evt.details || {})
      .map(([k, v]) => `<strong>${k}:</strong> ${typeof v === 'object' ? JSON.stringify(v) : v}`)
      .join(' &nbsp;•&nbsp; ');

    const statusClass = `status-${evt.status.toLowerCase()}`;

    item.innerHTML = `
      <div class="timeline-node">
        <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24">${iconSvg}</svg>
      </div>
      <div class="glass-card timeline-card">
        <div class="timeline-card-header">
          <div style="display: flex; align-items: center; gap: 0.5rem;">
            <span class="event-type-badge">${evt.event_type}</span>
            <span class="badge ${statusClass}">${evt.status.toUpperCase()}</span>
          </div>
          <span class="event-timestamp">${dateStr}</span>
        </div>
        <div class="timeline-details">${detailsStr || 'No additional details provided.'}</div>
        <div class="timeline-footer">
          <span>Event ID: <code>${evt.event_id}</code></span>
          <span class="fhir-tag">${evt.source_resource || 'CarePlan/General'}</span>
        </div>
      </div>
    `;
    timelineContainer.appendChild(item);
  });
}

// --- Multi-Agent Journey Coordination Trigger ---
async function runAgentCoordination() {
  btnTriggerCoordination.disabled = true;
  btnTriggerCoordination.innerHTML = `
    <svg class="spin" width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="12" y1="2" x2="12" y2="6"/><line x1="12" y1="18" x2="12" y2="22"/><line x1="4.93" y1="4.93" x2="7.76" y2="7.76"/><line x1="16.24" y1="16.24" x2="19.07" y2="19.07"/><line x1="2" y1="12" x2="6" y2="12"/><line x1="18" y1="12" x2="22" y2="12"/><line x1="4.93" y1="19.07" x2="7.76" y2="16.24"/><line x1="16.24" y1="7.76" x2="19.07" y2="4.93"/></svg>
    Coordinating Journey...
  `;

  try {
    const res = await fetch(`/journey/coordinate/${activePatientId}`, { method: 'POST' });
    const data = await res.json();

    if (data.phase) {
      phasePill.textContent = data.phase;
    }

    if (data.summary) {
      summaryContent.innerHTML = formatMarkdown(data.summary);
    }

    showToast(`Journey coordinated! Created ${data.hitl_items_created} clinician review proposal(s).`, 'success');
    await refreshActivePatientData();
    await loadHitlReviews();
  } catch (err) {
    showToast(`Coordination failed: ${err.message}`, 'error');
  } finally {
    btnTriggerCoordination.disabled = false;
    btnTriggerCoordination.innerHTML = `
      <svg width="18" height="18" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M13 2L3 14h9l-1 8 10-12h-9l1-8z"/></svg>
      Run Agent Coordination
    `;
  }
}

// --- Patient Chat Intake ---
async function handlePatientChatSubmit(e) {
  e.preventDefault();
  const msg = chatInput.value.trim();
  if (!msg) return;

  // Append patient message
  appendChatMessage(msg, 'patient');
  chatInput.value = '';

  // Show typing indicator
  const typingId = appendTypingIndicator();

  try {
    const res = await fetch(`/api/patients/${activePatientId}/intake`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message: msg, symptoms: [] }),
    });

    const data = await res.json();
    removeTypingIndicator(typingId);
    appendChatMessage(data.agent_response, 'agent');

    if (data.coordination_result && data.coordination_result.summary) {
      summaryContent.innerHTML = formatMarkdown(data.coordination_result.summary);
    }

    await refreshActivePatientData();
    await loadHitlReviews();
  } catch (err) {
    removeTypingIndicator(typingId);
    appendChatMessage("I've logged your notes. Your care coordinator is reviewing your record.", 'agent');
  }
}

function appendChatMessage(text, sender) {
  const msgDiv = document.createElement('div');
  msgDiv.className = `message msg-${sender}`;
  msgDiv.innerHTML = `
    <div class="msg-bubble">${text}</div>
    <span class="msg-time">Just now</span>
  `;
  chatMessages.appendChild(msgDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
}

function appendTypingIndicator() {
  const id = `typing_${Date.now()}`;
  const typingDiv = document.createElement('div');
  typingDiv.id = id;
  typingDiv.className = 'message msg-agent';
  typingDiv.innerHTML = `
    <div class="msg-bubble" style="font-style: italic; color: var(--text-muted);">
      AegisCare agent is analyzing your journey...
    </div>
  `;
  chatMessages.appendChild(typingDiv);
  chatMessages.scrollTop = chatMessages.scrollHeight;
  return id;
}

function removeTypingIndicator(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

// --- Clinician HITL Review Queue ---
async function loadHitlReviews() {
  try {
    const res = await fetch('/hitl/reviews');
    currentReviews = await res.json();
    renderHitlQueue();
    updateHitlBadge(currentReviews);
  } catch (err) {
    console.error('Error loading HITL reviews:', err);
  }
}

function setReviewFilter(filter) {
  activeReviewFilter = filter;
  filterAllReviews.classList.toggle('active', filter === 'all');
  filterPendingReviews.classList.toggle('active', filter === 'pending');
  filterResolvedReviews.classList.toggle('active', filter === 'resolved');
  renderHitlQueue();
}

function renderHitlQueue() {
  hitlQueueContainer.innerHTML = '';
  let filtered = currentReviews;

  if (activeReviewFilter === 'pending') {
    filtered = currentReviews.filter((r) => r.status === 'PENDING' || r.status === 'ReviewStatus.PENDING');
  } else if (activeReviewFilter === 'resolved') {
    filtered = currentReviews.filter((r) => r.status !== 'PENDING' && r.status !== 'ReviewStatus.PENDING');
  }

  if (filtered.length === 0) {
    hitlQueueContainer.innerHTML = `
      <div class="glass-card" style="padding: 3rem; grid-column: 1 / -1; text-align: center; color: var(--text-muted);">
        <svg width="40" height="40" fill="none" stroke="currentColor" stroke-width="1.5" viewBox="0 0 24 24" style="margin: 0 auto 1rem; opacity: 0.6;"><path d="M9 12l2 2 4-4m6 2a9 9 0 1 1-18 0 9 9 0 0 1 18 0z"/></svg>
        <h4>No ${activeReviewFilter} review proposals in queue.</h4>
        <p style="font-size: 0.85rem; margin-top: 0.4rem;">Run the agent coordination pipeline to evaluate overdue events and generate Tier-2 review proposals.</p>
      </div>`;
    return;
  }

  filtered.forEach((item) => {
    const card = document.createElement('div');
    const isPending = item.status === 'PENDING' || item.status === 'ReviewStatus.PENDING';
    const statusClean = isPending ? 'PENDING' : item.status.replace('ReviewStatus.', '');
    card.className = `glass-card review-card status-${statusClean}`;

    const dateStr = item.created_at ? new Date(item.created_at).toLocaleString() : 'Recent';

    card.innerHTML = `
      <div class="review-card-header">
        <div>
          <span class="review-id">${item.review_id}</span>
          <div style="font-size: 0.75rem; color: var(--text-secondary); margin-top: 2px;">Patient: <strong>${item.patient_id}</strong></div>
        </div>
        <span class="review-tier-tag">TIER 2 CLINICAL</span>
      </div>

      <div class="review-rationale">
        <strong>Clinical Rationale:</strong> ${item.clinical_rationale}
      </div>

      <div class="review-action-box">
        <h5>Proposed Action</h5>
        <p>${item.proposed_action ? item.proposed_action.action || 'Urgent Clinical Escalation' : 'Review action'}</p>
        <small>Target: ${item.proposed_action ? item.proposed_action.target_service || 'N/A' : 'N/A'} | Ref: ${item.proposed_action ? item.proposed_action.associated_resource || 'CarePlan' : 'FHIR'}</small>
      </div>

      ${
        isPending
          ? `
        <div class="review-btn-row">
          <button class="btn btn-approve btn-sm" onclick="handleResolveReview('${item.review_id}', 'APPROVED')">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><polyline points="20 6 9 17 4 12"/></svg>
            Approve Action
          </button>
          <button class="btn btn-reject btn-sm" onclick="handleResolveReview('${item.review_id}', 'REJECTED')">
            <svg width="14" height="14" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
            Reject
          </button>
        </div>`
          : `
        <div class="review-resolution-box">
          <div><strong>Status:</strong> <span style="color: ${statusClean === 'APPROVED' ? '#34D399' : '#F87171'}">${statusClean}</span></div>
          <div><strong>Reviewed By:</strong> ${item.reviewed_by || 'Staff Physician'}</div>
          <div><strong>Notes:</strong> ${item.review_comments || 'No notes.'}</div>
        </div>`
      }
    `;
    hitlQueueContainer.appendChild(card);
  });
}

// Global review resolution handler
window.handleResolveReview = async function (reviewId, decision) {
  const comments = prompt(`Enter clinician notes for ${decision} of ${reviewId}:`, `Approved by Clinician on duty.`);
  if (comments === null) return;

  try {
    const res = await fetch(`/hitl/reviews/${reviewId}/action`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        decision: decision,
        reviewer_id: 'Dr. Sarah Chen (Attending)',
        comments: comments || `${decision} recorded.`,
      }),
    });

    if (!res.ok) throw new Error('Failed to update review status');
    showToast(`Review ${reviewId} marked as ${decision}`, 'success');
    await loadHitlReviews();
    await refreshActivePatientData();
  } catch (err) {
    showToast(`Error: ${err.message}`, 'error');
  }
};

// --- Modal Handlers ---
async function handleAddEventSubmit(e) {
  e.preventDefault();
  const eventType = document.getElementById('eventType').value;
  const status = document.getElementById('eventStatus').value;
  const title = document.getElementById('eventTitle').value.trim();
  const source = document.getElementById('eventSourceResource').value.trim();

  try {
    const res = await fetch(`/api/patients/${activePatientId}/events`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        event_type: eventType,
        status: status,
        details: { description: title },
        source_resource: source || undefined,
      }),
    });

    if (!res.ok) throw new Error('Could not save event');
    eventModal.classList.remove('open');
    eventForm.reset();
    showToast('Event recorded in MongoDB successfully!', 'success');
    await refreshActivePatientData();
  } catch (err) {
    showToast(`Failed to add event: ${err.message}`, 'error');
  }
}

async function handleCreatePatientSubmit(e) {
  e.preventDefault();
  const patientId = document.getElementById('newPatientId').value.trim();
  const name = document.getElementById('newPatientName').value.trim();
  const age = parseInt(document.getElementById('newPatientAge').value, 10);
  const gender = document.getElementById('newPatientGender').value;
  const condition = document.getElementById('newPatientCondition').value.trim();
  const physician = document.getElementById('newPatientPhysician').value.trim();

  try {
    const res = await fetch('/api/patients', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        patient_id: patientId,
        name: name,
        age: age,
        gender: gender,
        condition: condition,
        primary_physician: physician,
      }),
    });

    if (!res.ok) throw new Error('Could not register patient');
    const created = await res.json();
    newPatientModal.classList.remove('open');
    newPatientForm.reset();
    showToast(`Patient ${created.name} registered in MongoDB!`, 'success');

    await loadPatients();
    activePatientId = created.patient_id;
    patientSelect.value = activePatientId;
    await refreshActivePatientData();
  } catch (err) {
    showToast(`Failed to create patient: ${err.message}`, 'error');
  }
}

// --- Utilities ---
function formatMarkdown(text) {
  return text
    .replace(/^### (.*$)/gim, '<h3>$1</h3>')
    .replace(/\*\*(.*?)\*\*/gim, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/gim, '<em>$1</em>')
    .replace(/\n/gim, '<br>');
}

function copySummaryToClipboard() {
  const text = summaryContent.innerText;
  navigator.clipboard.writeText(text).then(() => {
    showToast('Summary copied to clipboard!', 'success');
  });
}

function showToast(message, type = 'success') {
  const toast = document.createElement('div');
  toast.className = `toast ${type}`;
  toast.innerHTML = `
    <svg width="16" height="16" fill="none" stroke="currentColor" stroke-width="2" viewBox="0 0 24 24"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg>
    <span>${message}</span>
  `;
  toastContainer.appendChild(toast);
  setTimeout(() => toast.remove(), 4000);
}
