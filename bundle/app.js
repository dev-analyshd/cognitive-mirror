/**
 * Cognitive Mirror — Anna App UI Bundle
 *
 * Connects to Anna Runtime, invokes the coherence engine tool,
 * and renders real-time 5-plane cognitive coherence visualization.
 *
 * Standalone mode: if Anna Runtime is unavailable, runs with sample data.
 */

const TOOL_ID = "tool-CHANGEME-coherence-engine-CHANGEME";

const ARCHETYPE_DATA = {
  'Hero':      { icon: '⚔', desc: 'Peak coherence. All planes aligned. Execute your hardest work.' },
  'Sage':      { icon: '◎', desc: 'Deep inference, high consensus. Analyze. Research. Write.' },
  'Creator':   { icon: '✦', desc: 'Balanced creativity. Build something new. Experiment.' },
  'Innocent':  { icon: '◇', desc: 'Emerging patterns. Explore gently. No major decisions.' },
  'Jester':    { icon: '◈', desc: 'Scattered energy. Play first, then refocus.' },
  'Rebel':     { icon: '◉', desc: 'Contradictory signals. Question everything — but do not act yet.' },
  'Shadow':    { icon: '●', desc: 'Low coherence. Rest. This passes. Do not judge yourself.' },
  'Caregiver': { icon: '◌', desc: 'Minimal coherence. Help others, not yourself. Rest first.' }
};

const PLANE_COLORS = {
  'perceptual':      '#FF9E6C',
  'inferential':     '#B388FF',
  'consensus':       '#82B1FF',
  'self-reflection': '#7FD49C',
  'world-model':     '#FFD166'
};

let anna = null;
let coherenceChart = null;
let planesChart = null;
let currentState = {
  psi: 0, theta: 0, gateOpen: false, archetype: 'Innocent',
  limitingPlane: 'perceptual', planes: {}, features: {}, history: [],
  moatCalibrations: 0
};

async function init() {
  try {
    // Try to connect to Anna Runtime SDK
    const { AnnaAppRuntime } = await import('/static/anna-apps/_sdk/latest/index.js')
      .catch(() => ({ AnnaAppRuntime: null }));

    if (AnnaAppRuntime) {
      anna = await AnnaAppRuntime.connect();
      console.log('[Cognitive Mirror] Connected to Anna Runtime');

      await loadState();
      initCharts();

      if (anna.entryPayload && anna.entryPayload.messages) {
        await analyzeMessages(anna.entryPayload.messages);
      } else if (currentState.history.length === 0) {
        await loadSampleData();
      } else {
        renderState();
      }

      anna.on('entry_payload', (payload) => {
        if (payload && payload.messages) analyzeMessages(payload.messages);
      });

      anna.on('runtime_state_synced', (state) => {
        console.log('[Cognitive Mirror] Runtime synced:', state);
      });

      updateStatus('active', 'Connected');
    } else {
      throw new Error('Anna SDK not available');
    }
  } catch (err) {
    console.log('[Cognitive Mirror] Running in standalone mode:', err.message);
    initCharts();
    await loadSampleData();
    updateStatus('active', 'Standalone Mode');
  }
}

async function loadState() {
  try {
    const { value } = await anna.storage.get({ key: 'cognitive_state' });
    if (value) {
      currentState = { ...currentState, ...value };
      updateMoat();
    }
  } catch (err) {
    console.log('[Cognitive Mirror] No persisted state found');
  }
}

async function saveState() {
  try {
    if (anna && anna.storage) {
      await anna.storage.set({ key: 'cognitive_state', value: currentState });
    }
  } catch (err) {
    console.warn('[Cognitive Mirror] Could not save state:', err.message);
  }
}

async function analyzeMessages(messages) {
  updateStatus('computing', 'Computing coherence...');

  try {
    let result;

    if (anna && anna.tools) {
      // Call the coherence engine Executa via Anna tools.invoke
      const response = await anna.tools.invoke({
        tool_id: TOOL_ID,
        method: 'evaluate',
        args: { messages }
      });
      result = response.result;
    } else {
      // Standalone: compute coherence locally (mirrors Python engine)
      result = computeCoherenceLocally(messages);
    }

    console.log('[Cognitive Mirror] Engine result:', result);

    currentState = {
      ...currentState,
      psi: result.psi,
      theta: result.theta,
      gateOpen: result.gate_open,
      archetype: result.archetype,
      limitingPlane: result.limiting_plane,
      planes: result.planes,
      features: result.features,
      structuredSilence: result.structured_silence || null,
      timestamp: Date.now()
    };

    currentState.history.push({
      psi: result.psi, theta: result.theta,
      gateOpen: result.gate_open, archetype: result.archetype,
      timestamp: Date.now()
    });

    if (currentState.history.length > 30) {
      currentState.history = currentState.history.slice(-30);
    }

    await saveState();
    renderState();
    updateMoat();

    // Append artifact to Anna chat
    try {
      if (anna && anna.chat) {
        await anna.chat.write_message({
          role: 'assistant',
          content: formatArtifact(result)
        });
      }
    } catch (e) {
      console.log('[Cognitive Mirror] Chat artifact skipped:', e.message);
    }

    updateStatus(result.gate_open ? 'active' : 'silence',
                 result.gate_open ? 'Gate Open' : 'Silence Signal');
  } catch (err) {
    console.error('[Cognitive Mirror] Analysis failed:', err);
    updateStatus('silence', 'Error: ' + err.message);
  }
}

/**
 * Standalone coherence computation (mirrors coherence_engine.py).
 * Used when the Anna Executa tool is not available.
 */
function computeCoherenceLocally(messages) {
  const n = Math.max(messages.length, 1);

  // Shannon entropy (normalized)
  function shannonEntropy(values) {
    const total = values.reduce((a, b) => a + b, 0);
    if (total === 0) return 0;
    const probs = values.filter(v => v > 0).map(v => v / total);
    const raw = -probs.reduce((s, p) => s + p * Math.log2(p), 0);
    const maxH = probs.length > 1 ? Math.log2(probs.length) : 1;
    return maxH > 0 ? raw / maxH : 0;
  }

  function countMap(arr) {
    return Object.values(arr.reduce((m, v) => { m[v] = (m[v] || 0) + 1; return m; }, {}));
  }

  // F1: length entropy
  const lengths = messages.map(m => (m.content || '').length);
  const F1 = shannonEntropy(countMap(lengths));

  // F2: vocabulary diversity
  const words = messages.map(m => m.content || '').join(' ').split(/\s+/);
  const F2 = new Set(words.map(w => w.toLowerCase())).size / Math.max(words.length, 1);

  // F3: temporal spacing entropy
  const ts = messages.map(m => m.timestamp || 0).sort((a, b) => a - b);
  const intervals = ts.length > 1 ? ts.slice(1).map((t, i) => t - ts[i]) : [1];
  const F3 = shannonEntropy(countMap(intervals));

  // F4: topic entropy
  const topics = messages.map(m => m.topic || 'general');
  const F4 = shannonEntropy(countMap(topics));

  // F5: punctuation entropy
  const punctCounts = messages.map(m => (m.content || '').split('').filter(c => '?!.,;:-'.includes(c)).length);
  const F5 = shannonEntropy(countMap(punctCounts));

  // F6: question ratio
  const F6 = messages.filter(m => (m.content || '').includes('?')).length / n;

  // F7: code block ratio
  const F7 = messages.filter(m => (m.content || '').includes('```')).length / n;

  // F8: length consistency
  const meanLen = lengths.reduce((a, b) => a + b, 0) / lengths.length;
  const stdLen = lengths.length > 1
    ? Math.sqrt(lengths.reduce((s, v) => s + (v - meanLen) ** 2, 0) / lengths.length)
    : 0;
  const F8 = Math.max(0, 1 - Math.min(1, stdLen / (meanLen + 1)));

  // F9: topic transition entropy
  const transitions = topics.length > 1 ? topics.slice(1).map((t, i) => `${topics[i]}->${t}`) : ['none'];
  const F9 = shannonEntropy(countMap(transitions));

  // 5 planes
  const P = (F1 + F3 + F5) / 3;
  const I = Math.max(0, 1 - F6 * 0.8);
  const C = (F4 + F2) / 2;
  const S = Math.max(0, Math.min(1, 1 - Math.abs(F6 - 0.25) * 2));
  const W = Math.max(0, Math.min(1, 1 - Math.abs(F7 - 0.3) * 2));

  const planes = {
    perceptual: round4(P),
    inferential: round4(I),
    consensus: round4(C),
    'self-reflection': round4(S),
    'world-model': round4(W)
  };

  // Psi(t)
  const psi = round4(Math.max(0, Math.min(1, 0.25*P + 0.30*I + 0.20*C + 0.15*S + 0.10*W)));

  // Theta(t) = 0.55 + 0.37 * V(t)
  const planeVals = Object.values(planes);
  const mean = planeVals.reduce((a, b) => a + b, 0) / planeVals.length;
  const vol = Math.sqrt(planeVals.reduce((s, v) => s + (v - mean) ** 2, 0) / planeVals.length);
  const theta = round4(Math.min(1, 0.55 + 0.37 * vol));

  const limitingPlane = Object.entries(planes).sort((a, b) => a[1] - b[1])[0][0];
  const archetype = matchArchetype(psi);
  const gate_open = psi >= theta;

  const result = {
    psi, theta, gate_open,
    limiting_plane: limitingPlane,
    archetype,
    planes,
    features: { F1: round4(F1), F2: round4(F2), F3: round4(F3), F4: round4(F4), F5: round4(F5), F6: round4(F6), F7: round4(F7), F8: round4(F8), F9: round4(F9) }
  };

  if (!gate_open) {
    const silenceTypes = {
      'perceptual': 'COGNITIVE_OVERLOAD',
      'inferential': 'REASONING_COLLAPSE',
      'consensus': 'IDENTITY_DRIFT',
      'self-reflection': 'META_COGNITIVE_FATIGUE',
      'world-model': 'ENVIRONMENTAL_MISMATCH'
    };
    const recs = {
      'perceptual': 'Your perceptual entropy is too high. Take a 15-minute break. Return to one task.',
      'inferential': 'Your reasoning chains are contradicting. Take 20 minutes. Revisit your last coherent thought.',
      'consensus': 'You are drifting from your usual patterns. Do something familiar.',
      'self-reflection': 'Set a 10-minute timer. Write one clear sentence about what you want.',
      'world-model': 'Step back. Verify assumptions before proceeding.'
    };
    result.structured_silence = {
      silence_type: silenceTypes[limitingPlane] || 'COGNITIVE_SUBTHRESHOLD',
      limiting_plane: limitingPlane,
      coherence_deficit: round4(theta - psi),
      archetype,
      recommendation: recs[limitingPlane] || 'Rest. The silence is information.',
      plane_scores: planes,
      timestamp: new Date().toISOString()
    };
  }

  return result;
}

function matchArchetype(psi) {
  if (psi >= 0.85) return 'Hero';
  if (psi >= 0.75) return 'Sage';
  if (psi >= 0.65) return 'Creator';
  if (psi >= 0.55) return 'Innocent';
  if (psi >= 0.45) return 'Jester';
  if (psi >= 0.35) return 'Rebel';
  if (psi >= 0.25) return 'Shadow';
  return 'Caregiver';
}

function round4(v) { return Math.round(v * 10000) / 10000; }

async function refreshAnalysis() {
  const messages = generateSampleMessages();
  await analyzeMessages(messages);
}

function renderState() {
  const { psi, theta, gateOpen, archetype, limitingPlane, planes, features, structuredSilence } = currentState;

  const gateBadge = document.getElementById('gateBadge');
  const gateIcon = document.getElementById('gateIcon');
  const gateLabel = document.getElementById('gateLabel');
  const gateReason = document.getElementById('gateReason');

  gateBadge.className = 'gate-badge ' + (gateOpen ? 'open' : 'silence');
  gateIcon.textContent = gateOpen ? '▶' : '◼';
  gateLabel.textContent = gateOpen ? 'ACT' : 'SILENCE';

  const archetypeInfo = ARCHETYPE_DATA[archetype] || ARCHETYPE_DATA['Innocent'];
  const planePct = planes[limitingPlane] !== undefined ? (planes[limitingPlane] * 100).toFixed(0) + '%' : '—';

  if (gateOpen) {
    gateReason.textContent = `${archetypeInfo.desc} Limiting plane: ${limitingPlane} (${planePct}).`;
  } else {
    gateReason.textContent = `Your ${limitingPlane} plane is at ${planePct}. ${archetypeInfo.desc} The silence is information.`;
  }

  document.getElementById('psiValue').textContent = psi.toFixed(3);
  document.getElementById('thetaValue').textContent = theta.toFixed(3);
  document.getElementById('deltaValue').textContent = Math.abs(theta - psi).toFixed(3);

  document.getElementById('archetypeIcon').textContent = archetypeInfo.icon;
  document.getElementById('archetypeName').textContent = archetype;
  document.getElementById('archetypeDesc').textContent = archetypeInfo.desc;

  updateCharts();
  renderFeatures(features);

  const silencePanel = document.getElementById('silencePanel');
  if (!gateOpen && structuredSilence) {
    silencePanel.style.display = 'block';
    document.getElementById('silenceJson').textContent = JSON.stringify(structuredSilence, null, 2);
  } else {
    silencePanel.style.display = 'none';
  }

  try {
    if (anna && anna.window) {
      anna.window.set_title({
        title: `Mirror: ${archetype} | Psi=${psi.toFixed(2)} | ${gateOpen ? 'ACT' : 'SILENCE'}`
      });
    }
  } catch (e) {}
}

function renderFeatures(features) {
  const grid = document.getElementById('featuresGrid');
  if (!grid || !features) return;
  grid.innerHTML = '';

  const featureLabels = {
    'F1': 'Length H', 'F2': 'Vocabulary', 'F3': 'Temporal H',
    'F4': 'Topic H', 'F5': 'Punct H', 'F6': 'Questions',
    'F7': 'Code', 'F8': 'Consistency', 'F9': 'Drift H'
  };

  for (const [key, value] of Object.entries(features)) {
    const item = document.createElement('div');
    item.className = 'feature-item';
    item.innerHTML = `
      <div class="feature-name">${featureLabels[key] || key}</div>
      <div class="feature-value">${(value * 100).toFixed(0)}%</div>
    `;
    grid.appendChild(item);
  }
}

function updateStatus(type, text) {
  const dot = document.getElementById('statusDot');
  const label = document.getElementById('statusText');
  if (dot) dot.className = 'status-dot ' + type;
  if (label) label.textContent = text;
}

function formatArtifact(result) {
  const status = result.gate_open ? 'GATE OPEN' : 'STRUCTURED SILENCE';
  return `**Cognitive Mirror Report**\n\n` +
         `**Status:** ${status}\n` +
         `**Psi (Coherence):** ${result.psi.toFixed(3)}\n` +
         `**Theta (Threshold):** ${result.theta.toFixed(3)}\n` +
         `**Archetype:** ${result.archetype}\n` +
         `**Limiting Plane:** ${result.limiting_plane}\n` +
         `**Recommendation:** ${result.gate_open
           ? 'Act now. Your cognitive state supports deep work.'
           : (result.structured_silence && result.structured_silence.recommendation) || 'Rest. The silence is information.'}`;
}

function initCharts() {
  const ctx1 = document.getElementById('coherenceChart');
  const ctx2 = document.getElementById('planesChart');
  if (!ctx1 || !ctx2) return;

  coherenceChart = new Chart(ctx1.getContext('2d'), {
    type: 'line',
    data: {
      labels: [],
      datasets: [
        {
          label: 'Psi (Coherence)',
          data: [],
          borderColor: '#B388FF',
          backgroundColor: 'rgba(179, 136, 255, 0.1)',
          fill: true,
          tension: 0.4,
          pointRadius: 3,
          pointBackgroundColor: '#B388FF'
        },
        {
          label: 'Theta (Threshold)',
          data: [],
          borderColor: '#FF9E6C',
          borderDash: [5, 5],
          pointRadius: 0,
          fill: false,
          tension: 0.4
        }
      ]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { labels: { color: '#a6a8b5', font: { family: 'monospace', size: 10 } } }
      },
      scales: {
        x: { display: false, grid: { display: false } },
        y: {
          min: 0, max: 1,
          grid: { color: 'rgba(255, 158, 108, 0.1)' },
          ticks: { color: '#6b6d7b', font: { family: 'monospace', size: 9 } }
        }
      },
      interaction: { intersect: false, mode: 'index' }
    }
  });

  planesChart = new Chart(ctx2.getContext('2d'), {
    type: 'bar',
    data: {
      labels: ['Perceptual', 'Inferential', 'Consensus', 'Self-Reflect', 'World Model'],
      datasets: [{
        label: 'Plane Score',
        data: [0, 0, 0, 0, 0],
        backgroundColor: [
          PLANE_COLORS['perceptual'],
          PLANE_COLORS['inferential'],
          PLANE_COLORS['consensus'],
          PLANE_COLORS['self-reflection'],
          PLANE_COLORS['world-model']
        ],
        borderRadius: 6,
        borderSkipped: false
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: { legend: { display: false } },
      scales: {
        x: {
          grid: { display: false },
          ticks: { color: '#a6a8b5', font: { family: 'monospace', size: 9 } }
        },
        y: {
          min: 0, max: 1,
          grid: { color: 'rgba(255, 158, 108, 0.1)' },
          ticks: { color: '#6b6d7b', font: { family: 'monospace', size: 9 } }
        }
      }
    }
  });
}

function updateCharts() {
  if (!coherenceChart || !planesChart) return;

  const history = currentState.history;
  coherenceChart.data.labels = history.map((_, i) => `S-${history.length - i}`);
  coherenceChart.data.datasets[0].data = history.map(h => h.psi);
  coherenceChart.data.datasets[1].data = history.map(h => h.theta);
  coherenceChart.update('none');

  const planes = currentState.planes;
  planesChart.data.datasets[0].data = [
    planes.perceptual || 0,
    planes.inferential || 0,
    planes.consensus || 0,
    planes['self-reflection'] || 0,
    planes['world-model'] || 0
  ];
  planesChart.update('none');
}

function updateMoat() {
  const history = currentState.history;
  const days = Math.max(1, Math.floor(history.length / 3));
  const checks = history.length;
  const cals = currentState.moatCalibrations || 0;
  const accuracy = Math.min(95, 50 + (cals * 5) + (checks * 1));
  const moatScore = Math.min(100, (days * 5) + (accuracy * 0.3) + (checks * 0.5));

  const fill = document.getElementById('moatFill');
  if (fill) fill.style.width = moatScore + '%';
  const el = (id) => document.getElementById(id);
  if (el('moatDays')) el('moatDays').textContent = days;
  if (el('moatAccuracy')) el('moatAccuracy').textContent = accuracy + '%';
  if (el('moatChecks')) el('moatChecks').textContent = checks;
}

async function calibrateMoat() {
  currentState.moatCalibrations = (currentState.moatCalibrations || 0) + 1;
  await saveState();
  updateMoat();

  const btn = document.getElementById('calibrateBtn');
  const original = btn.textContent;
  btn.textContent = 'Calibrated!';
  btn.style.background = 'rgba(127, 212, 156, 0.2)';
  btn.style.borderColor = '#7FD49C';
  setTimeout(() => {
    btn.textContent = original;
    btn.style.background = '';
    btn.style.borderColor = '';
  }, 1500);
}

async function loadSampleData() {
  const messages = generateSampleMessages();
  await analyzeMessages(messages);
}

function generateSampleMessages() {
  const topics = ['coding', 'design', 'research', 'planning', 'debugging', 'writing'];
  const now = Date.now() / 1000;
  const messages = [];

  for (let i = 0; i < 30; i++) {
    const isCode = Math.random() > 0.7;
    const hasQuestion = Math.random() > 0.6;
    const length = 50 + Math.floor(Math.random() * 200);

    let content = '';
    if (isCode) content = '```python\ndef analyze():\n    return compute()\n```\n';
    content += `Working on ${topics[i % topics.length]}. `;
    if (hasQuestion) content += 'How should I approach this? ';
    content += 'Let me think through the steps carefully. ';
    content += 'x'.repeat(Math.max(0, length - content.length));

    messages.push({
      content,
      timestamp: now - (30 - i) * 3600,
      topic: topics[i % topics.length],
      role: i % 3 === 0 ? 'assistant' : 'user'
    });
  }

  return messages;
}

// Expose to HTML onclick handlers
window.refreshAnalysis = refreshAnalysis;
window.calibrateMoat = calibrateMoat;
window.loadSampleData = loadSampleData;

document.addEventListener('DOMContentLoaded', init);
