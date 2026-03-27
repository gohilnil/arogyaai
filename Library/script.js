'use strict';
/* ════════════════════════════════════════════════════
   ArogyaAI v6 — Frontend Script
   Features: Chat · Voice · Medicine · History · Share
   ════════════════════════════════════════════════════ */

/* ─── Config ─── */
const API_BASE = '';

const TIPS = [
  "Drink 8–10 glasses of water daily — hydration is the simplest health habit.",
  "Tulsi tea with ginger and honey is excellent for boosting immunity naturally.",
  "A 10-minute walk after meals aids digestion and stabilises blood sugar.",
  "Soak 5 almonds overnight; eat them in the morning for brain and heart health.",
  "Practice Pranayama deep breathing for 5 minutes daily to reduce stress.",
  "Turmeric milk (haldi doodh) before bed fights inflammation and improves sleep.",
  "Avoid heavy meals after 8 PM — give your digestive system time to rest.",
  "Neem leaves are a powerful natural antibacterial used in Ayurveda for centuries.",
  "Include curd/yogurt in your diet daily for better gut health and digestion.",
  "Methi seeds soaked overnight help regulate blood sugar in diabetics.",
  "Exercise at least 30 minutes, 5 days a week for a healthy heart and mind.",
  "Amla (Indian gooseberry) is the richest natural source of Vitamin C — eat daily.",
  "Garlic on an empty stomach in the morning helps lower blood pressure naturally.",
  "Ghee in moderation is healthy and helps absorb fat-soluble vitamins A, D, E, K.",
  "Oil pulling with coconut oil for 10 minutes each morning improves oral health.",
];

/* Curated local medicine database for instant lookup */
const MEDICINE_DATA = {
  paracetamol: {
    name:'Paracetamol', brand:'Crocin / Calpol / Dolo 650', generic:'Acetaminophen',
    icon:'💊', type:'OTC',
    use:'Relieves mild to moderate pain (headache, muscle ache, toothache, back pain) and reduces fever. First-line treatment for fever in adults and children.',
    mechanism:'Inhibits prostaglandin synthesis in the central nervous system, raising the pain threshold and reducing fever.',
    dosage:[{lbl:'Adults',val:'500–1000mg'},{lbl:'Interval',val:'4–6 hrs'},{lbl:'Max/Day',val:'4000mg'}],
    dosage_note:'Children: 10–15 mg/kg per dose. Do not exceed 5 doses in 24 hours.',
    effects:['Nausea (rare)','Skin rash (rare)','Liver damage (overdose)','Allergic reaction (very rare)'],
    precautions:[
      'Do NOT exceed 4g/day — liver damage risk.',
      'Avoid alcohol while taking paracetamol.',
      'Use with caution in liver or kidney disease.',
      'Many cold/flu drugs already contain paracetamol — check to avoid double dosing.',
      'Safe in pregnancy at recommended doses.',
    ],
  },
  ibuprofen: {
    name:'Ibuprofen', brand:'Brufen / Advil / Nurofen', generic:'Ibuprofen (NSAID)',
    icon:'💊', type:'OTC',
    use:'Reduces fever, relieves pain, and reduces inflammation. Used for headache, toothache, menstrual cramps, arthritis pain, and sports injuries.',
    mechanism:'Non-selective COX-1 and COX-2 inhibitor — reduces prostaglandin synthesis, producing anti-inflammatory, analgesic, and antipyretic effects.',
    dosage:[{lbl:'Adults',val:'200–400mg'},{lbl:'Interval',val:'4–8 hrs'},{lbl:'Max/Day',val:'1200mg (OTC)'}],
    dosage_note:'Always take with food or milk to protect the stomach.',
    effects:['Stomach upset','Heartburn','Headache','Dizziness','Raised BP (long-term)'],
    precautions:[
      'Take WITH food — never on empty stomach.',
      'Avoid if you have stomach ulcers or GI bleeding history.',
      'Not recommended in last trimester of pregnancy.',
      'Use with caution in asthma, kidney, or heart disease.',
      'Avoid with blood thinners without doctor advice.',
    ],
  },
  cetirizine: {
    name:'Cetirizine', brand:'Zyrtec / Okacet / Alerid', generic:'Cetirizine HCl',
    icon:'🌿', type:'OTC',
    use:'Antihistamine for allergy symptoms: runny nose, sneezing, itchy/watery eyes, skin hives, urticaria, and hay fever.',
    mechanism:'Selective H1-receptor antagonist — blocks histamine action, relieving allergy symptoms with minimal sedation.',
    dosage:[{lbl:'Adults',val:'10mg'},{lbl:'Frequency',val:'Once daily'},{lbl:'Best Time',val:'Evening'}],
    dosage_note:'Children 6–11 years: 5mg once daily. Children 2–5 years: 2.5mg once daily.',
    effects:['Drowsiness (mild)','Dry mouth','Headache','Fatigue','Nausea (rare)'],
    precautions:[
      'May cause drowsiness — avoid driving or heavy machinery.',
      'Do not combine with alcohol.',
      'Use with caution in kidney impairment.',
      'Safe in pregnancy if prescribed by doctor.',
      'Not for children under 2 without medical advice.',
    ],
  },
  metformin: {
    name:'Metformin', brand:'Glycomet / Glucophage / Obimet', generic:'Metformin HCl',
    icon:'⚕️', type:'Rx',
    use:'First-line medication for Type 2 Diabetes. Controls blood sugar by reducing glucose production in the liver and improving insulin sensitivity.',
    mechanism:'Activates AMPK pathway, reducing hepatic gluconeogenesis and increasing peripheral glucose uptake.',
    dosage:[{lbl:'Starting',val:'500mg'},{lbl:'Timing',val:'With meals'},{lbl:'Max/Day',val:'2000–2550mg'}],
    dosage_note:'Taken with meals to reduce GI side effects. Dose is gradually increased by doctor.',
    effects:['Nausea (common initially)','Diarrhoea','Stomach upset','Lactic acidosis (rare)','Vitamin B12 deficiency (long-term)'],
    precautions:[
      'PRESCRIPTION ONLY — do not self-medicate.',
      'Stop 48 hours before surgery or contrast dye procedure.',
      'Avoid if kidney function is impaired (eGFR < 30).',
      'Report unusual muscle pain or weakness.',
      'Take Vitamin B12 supplement with long-term use.',
    ],
  },
  aspirin: {
    name:'Aspirin', brand:'Ecosprin / Disprin / Aspro', generic:'Acetylsalicylic Acid',
    icon:'💊', type:'OTC',
    use:'Pain reliever, fever reducer, and anti-inflammatory. Low-dose aspirin (75–100mg) widely used to prevent blood clots in heart attack and stroke prevention.',
    mechanism:'Irreversibly inhibits COX-1 and COX-2, reducing prostaglandin and thromboxane A2. Anti-platelet effect lasts 7–10 days.',
    dosage:[{lbl:'Pain/Fever',val:'325–650mg'},{lbl:'Heart Prev.',val:'75–100mg/day'},{lbl:'Interval',val:'4–6 hrs (pain)'}],
    dosage_note:'For cardiac use: only as prescribed by cardiologist. Never use in children under 16.',
    effects:["Stomach irritation",'GI bleeding','Tinnitus (high doses)','Allergic reaction',"Reye's syndrome (children)"],
    precautions:[
      "NEVER give to children/teenagers (Reye's syndrome risk).",
      'Take with food to reduce stomach irritation.',
      'Avoid if you have a bleeding disorder or ulcers.',
      'Stop 7–10 days before surgery.',
      "Avoid with ibuprofen (reduces aspirin's anti-platelet effect).",
    ],
  },
  omeprazole: {
    name:'Omeprazole', brand:'Omez / Prilosec / Losec', generic:'Omeprazole',
    icon:'🫀', type:'OTC/Rx',
    use:'Proton Pump Inhibitor (PPI) that reduces stomach acid. Used for acid reflux (GERD), gastric and duodenal ulcers, and protection against NSAID-induced ulcers.',
    mechanism:'Irreversibly inhibits H+/K+ ATPase in gastric parietal cells, dramatically reducing stomach acid secretion.',
    dosage:[{lbl:'Standard',val:'20mg'},{lbl:'Frequency',val:'Once daily'},{lbl:'Best Time',val:'Before meals'}],
    dosage_note:'Take 30–60 minutes before breakfast. For ulcer: 20–40mg for 4–8 weeks.',
    effects:['Headache','Nausea','Diarrhoea','Abdominal pain','Hypomagnesaemia (long-term)'],
    precautions:[
      'Not for long-term use without medical supervision.',
      'May reduce absorption of Vitamin B12, magnesium, and iron.',
      'Avoid if on clopidogrel — consult doctor.',
      'Take 30–60 minutes before meals for best effect.',
      'Do not crush or chew capsules.',
    ],
  },
  amoxicillin: {
    name:'Amoxicillin', brand:'Mox / Amoxil / Trimox', generic:'Amoxicillin Trihydrate',
    icon:'⚠️', type:'Rx',
    use:'Antibiotic (penicillin class) for bacterial infections: throat, ear, UTIs, chest/lung infections, and H. pylori eradication.',
    mechanism:'Inhibits bacterial cell wall synthesis by binding to penicillin-binding proteins, causing cell lysis in susceptible bacteria.',
    dosage:[{lbl:'Adults',val:'250–500mg'},{lbl:'Interval',val:'Every 8 hrs'},{lbl:'Duration',val:'5–10 days'}],
    dosage_note:'Complete the full course even if you feel better. Stopping early causes antibiotic resistance.',
    effects:['Diarrhoea','Nausea','Skin rash (common)','Anaphylaxis (rare)','Oral thrush'],
    precautions:[
      'PRESCRIPTION ONLY — never self-prescribe antibiotics.',
      'Tell doctor of penicillin allergy before taking.',
      'Complete the FULL course — never stop early.',
      'Watch for rash, swelling, or breathing difficulty (allergy signs).',
      'May reduce effectiveness of oral contraceptives.',
    ],
  },
};

/* ─── App State ─── */
const S = {
  history: [],
  loading: false,
  dark: false,
  listening: false,
  tab: 'chat',
  currentImg: null,
  lastReply: '',
  speaking: false,
};

/* ─── Utils ─── */
const $ = id => document.getElementById(id);
const ts = () => new Date().toLocaleTimeString('en-IN', { hour: '2-digit', minute: '2-digit' });
const esc = s => {
  const d = document.createElement('div');
  d.appendChild(document.createTextNode(String(s || '')));
  return d.innerHTML;
};

/* ─── AI API Call ─── */
async function callAI(message) {
  const response = await fetch(`${API_BASE}/api/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      message,
      history: S.history.slice(-16),
      language: detectLang(message),
    }),
  });

  if (!response.ok) {
    const err = await response.json().catch(() => ({}));
    throw new Error(err.detail || `HTTP ${response.status}`);
  }
  return response.json();
}

function detectLang(t) {
  if (/[\u0900-\u097F]/.test(t)) return 'hi';
  if (/[\u0A80-\u0AFF]/.test(t)) return 'gu';
  return 'en';
}

/* ─── Input helpers ─── */
function resize() {
  const el = $('chat-input');
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 110) + 'px';
}

function updateSend() {
  const len = $('chat-input').value.length;
  $('char-count').textContent = `${len} / 1000`;
  $('send-btn').disabled = len === 0 || S.loading;
}

function scrollFeed() {
  requestAnimationFrame(() => {
    const f = $('feed');
    if (f) f.scrollTop = f.scrollHeight;
  });
}

function hideWelcome() {
  const w = $('welcome');
  if (w) w.style.display = 'none';
}

/* ─── Severity Badge ─── */
function sevBadge(s) {
  const MAP = {
    serious:  { cls: 'serious',  label: '🔴 Serious — Seek medical care' },
    moderate: { cls: 'moderate', label: '🟡 Moderate — Monitor closely' },
    mild:     { cls: 'mild',     label: '🟢 Mild — Manageable at home' },
  };
  const x = MAP[s] || MAP.mild;
  return `<div class="sev-badge ${x.cls}">${x.label}</div>`;
}

/* ─── Format AI Response ─── */
function formatReply(raw) {
  let h = esc(raw);

  // Bold text
  h = h.replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>');

  // Section headings (lines that start with bold)
  h = h.replace(/^(<strong>[🔍✅🍽️🏥⚠️🚨💊📋SEVERITY].+?<\/strong>)\s*$/gm, '<h4>$1</h4>');

  // List items
  h = h.replace(/^[•\-\*]\s+(.+)$/gm, '<li>$1</li>');
  h = h.replace(/(<li>.*?<\/li>\n?)+/gs, m => `<ul>${m}</ul>`);

  // Emergency alert
  if (/emergency|108|ambulance|immediately|तुरंत|hospital/i.test(raw)) {
    h += `<div class="emerg-alert">🚨 If symptoms are severe, call <strong>108</strong> immediately or visit the nearest emergency room.</div>`;
  }

  // Paragraphs
  h = h.split(/\n{2,}/)
    .map(p => p.trim())
    .filter(Boolean)
    .map(p => /^<(h4|ul|div)/.test(p) ? p : `<p>${p}</p>`)
    .join('');

  return h;
}

/* ─── Append User Message ─── */
function addUserMsg(text) {
  const el = document.createElement('div');
  el.className = 'msg user';
  el.innerHTML = `
    <div class="msg-body">
      <div class="bubble"><p>${esc(text)}</p></div>
      <div class="msg-time">${ts()}</div>
    </div>
    <div class="msg-av">You</div>`;
  $('feed').appendChild(el);
  scrollFeed();
}

/* ─── Typing Indicator ─── */
function showTyping() {
  const el = document.createElement('div');
  el.id = 'typing';
  el.className = 'typing-row';
  el.innerHTML = `
    <div class="msg-av" style="background:var(--c-forest-50);border:1.5px solid var(--c-forest-100);font-size:16px;border-radius:9px">🌿</div>
    <div class="typing-bub">
      <span class="td"></span><span class="td"></span><span class="td"></span>
      <span style="font-size:11px;color:var(--ink-300);margin-left:6px">Analysing…</span>
    </div>`;
  $('feed').appendChild(el);
  scrollFeed();
}

function hideTyping() {
  $('typing')?.remove();
}

/* ─── Append AI Message ─── */
function addAIMsg(text, severity, wiki) {
  S.lastReply = text;
  const el = document.createElement('div');
  el.className = 'msg ai';
  const msgId = 'ai-' + Date.now();
  const wikiTag = wiki
    ? `<span class="src-tag">📚 ${esc(wiki)}</span>`
    : '';

  el.innerHTML = `
    <div class="msg-av" style="background:var(--c-forest-50);border:1.5px solid var(--c-forest-100);font-size:16px;border-radius:9px">🌿</div>
    <div class="msg-body">
      ${sevBadge(severity)}
      <div class="bubble" id="${msgId}">${formatReply(text)}</div>
      <div class="msg-meta">
        <span class="src-tag">⚡ ArogyaAI</span>
        ${wikiTag}
        <button class="share-btn" onclick="openShare()">📤 Share</button>
        <span class="msg-time">ArogyaAI · ${ts()}</span>
      </div>
      <div class="voice-ctrl">
        <button class="vc-btn" id="speak-${msgId}" onclick="speakMsg('${msgId}','speak-${msgId}')">▶ Speak</button>
        <button class="vc-btn" onclick="stopSpeak()">⏹ Stop</button>
      </div>
    </div>`;
  $('feed').appendChild(el);
  scrollFeed();
}

/* ─── Error Message ─── */
function addErrMsg(msg) {
  const el = document.createElement('div');
  el.className = 'msg ai';
  el.innerHTML = `
    <div class="msg-av" style="font-size:16px;border-radius:9px">⚠️</div>
    <div class="err-bub">⚠️ ${esc(msg)}<br/><small style="opacity:0.7">Check your connection and try again.</small></div>`;
  $('feed').appendChild(el);
  scrollFeed();
}

/* ─── Loading State ─── */
function setLoading(on) {
  S.loading = on;
  $('send-btn').disabled = on;
  $('chat-input').disabled = on;
  const mic = $('mic-btn');
  if (mic) mic.disabled = on;

  const btn = $('send-btn');
  if (on) {
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="animation:spin 0.7s linear infinite"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>`;
  } else {
    btn.innerHTML = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round"><line x1="22" y1="2" x2="11" y2="13"/><polygon points="22 2 15 22 11 13 2 9 22 2"/></svg>`;
  }
}

/* ─── Send Message ─── */
async function sendMsg() {
  const text = $('chat-input').value.trim();
  if (!text || S.loading) return;

  hideWelcome();
  addUserMsg(text);
  $('chat-input').value = '';
  resize();
  updateSend();
  $('chat-input').focus();

  S.history.push({ role: 'user', content: text });
  setLoading(true);
  showTyping();

  try {
    const data = await callAI(text);
    hideTyping();
    addAIMsg(data.reply, data.severity || 'mild', data.wiki_context);
    S.history.push({ role: 'assistant', content: data.reply });
    saveSession(text, data.reply, data.severity || 'mild');
    updateHist();
  } catch (e) {
    hideTyping();
    const msg = e.message.includes('503')
      ? 'The AI service is starting up. Please wait a moment and try again.'
      : e.message;
    addErrMsg(msg);
  } finally {
    setLoading(false);
    updateSend();
  }
}

/* ─── Image Upload ─── */
function handleImage(input) {
  const f = input.files[0];
  if (!f) return;
  if (f.size > 5 * 1024 * 1024) { showToast('Image too large. Max 5MB.'); return; }
  const r = new FileReader();
  r.onload = e => {
    S.currentImg = e.target.result;
    $('img-thumb').src = e.target.result;
    $('img-strip').classList.remove('hidden');
    $('chat-input').placeholder = 'Describe what you see in the image…';
    showToast('📎 Image attached. Describe your concern below.');
  };
  r.readAsDataURL(f);
}

function removeImage() {
  S.currentImg = null;
  $('file-upload').value = '';
  $('img-strip').classList.add('hidden');
  $('chat-input').placeholder = 'Describe your symptoms… / अपने लक्षण बताएं… / તમારા લક્ષણો…';
}

/* ─── Session Storage ─── */
const LS_KEY = 'arogyaai_v6';

function saveSession(q, a, sev) {
  try {
    const sessions = JSON.parse(localStorage.getItem(LS_KEY) || '[]');
    sessions.unshift({
      id: Date.now(),
      q: q.slice(0, 70),
      a: a.slice(0, 300),
      sev,
      ts: new Date().toISOString(),
    });
    localStorage.setItem(LS_KEY, JSON.stringify(sessions.slice(0, 25)));
  } catch (e) { /* silently fail */ }
}

function loadSessions() {
  try { return JSON.parse(localStorage.getItem(LS_KEY) || '[]'); } catch (e) { return []; }
}

function updateHist() {
  const sessions = loadSessions();
  const list = $('hist-list');
  if (!list) return;

  if (!sessions.length) {
    list.innerHTML = '<div class="hist-empty">No chats yet</div>';
    return;
  }

  list.innerHTML = sessions.slice(0, 8).map(x => {
    const icon = x.sev === 'serious' ? '🔴' : x.sev === 'moderate' ? '🟡' : '🟢';
    return `<div class="hist-row" title="${esc(x.q)}" onclick="replaySession(${x.id})">${icon} ${esc(x.q)}</div>`;
  }).join('');
}

function replaySession(id) {
  const s = loadSessions().find(x => x.id === id);
  if (!s) return;
  hideWelcome();
  $('feed').querySelectorAll('.msg, .typing-row').forEach(el => el.remove());
  addUserMsg(s.q);
  addAIMsg(s.a, s.sev || 'mild', null);
  closeSidebar();
}

/* ─── Export Chat ─── */
function exportChat() {
  const msgs = [...$('feed').querySelectorAll('.msg')];
  if (!msgs.length) { showToast('No messages to export.'); return; }

  const lines = msgs.map(m => {
    const isUser = m.classList.contains('user');
    const t = m.querySelector('.bubble')?.textContent?.trim() || '';
    const time = m.querySelector('.msg-time')?.textContent?.trim() || '';
    return `[${isUser ? 'You' : 'ArogyaAI'}] ${time}\n${t}\n`;
  });

  const content = [
    'ArogyaAI Chat Export',
    '─'.repeat(44),
    `Exported: ${new Date().toLocaleString('en-IN')}`,
    '',
    ...lines,
    '',
    '⚕️ AI guidance only. Consult a doctor for medical decisions.',
    '© 2025 ArogyaAI — All rights reserved.',
  ].join('\n');

  const blob = new Blob([content], { type: 'text/plain' });
  const a = document.createElement('a');
  a.href = URL.createObjectURL(blob);
  a.download = `arogyaai-${Date.now()}.txt`;
  a.click();
  showToast('✅ Chat exported!');
}

function clearChat() {
  S.history = [];
  const w = $('welcome');
  if (w) w.style.display = '';
  $('feed').querySelectorAll('.msg, .typing-row').forEach(el => el.remove());
  window.speechSynthesis?.cancel();
  showToast('Conversation cleared.');
  $('chat-input').focus();
}

/* ─── Medicine Lookup ─── */
function quickDrug(name) {
  $('drug-q').value = name;
  lookupDrug();
}

async function lookupDrug() {
  const q = $('drug-q').value.trim().toLowerCase();
  if (!q) { showToast('Please enter a medicine name.'); return; }

  const res = $('drug-results');
  const btn = $('drug-go');
  btn.disabled = true;
  btn.textContent = 'Searching…';

  // Skeleton loading
  res.innerHTML = `<div class="empty-state">
    <div class="skel" style="height:80px;margin-bottom:14px;border-radius:12px"></div>
    <div class="skel" style="height:14px;width:60%;margin:0 auto 8px"></div>
    <div class="skel" style="height:14px;width:40%;margin:0 auto"></div>
  </div>`;

  // Check curated local database first
  const localKey = Object.keys(MEDICINE_DATA).find(k => q.includes(k) || k.includes(q));
  if (localKey) {
    await new Promise(r => setTimeout(r, 350)); // simulate network
    renderMedCard(MEDICINE_DATA[localKey]);
    btn.disabled = false;
    btn.textContent = 'Search';
    setDot('fda', 'on');
    return;
  }

  // Fallback to OpenFDA
  try {
    const url = `https://api.fda.gov/drug/label.json?search=brand_name:"${encodeURIComponent(q)}"+OR+generic_name:"${encodeURIComponent(q)}"&limit=3`;
    const r = await fetch(url);
    if (!r.ok) throw new Error('Not found');
    const data = await r.json();
    const item = data.results?.[0];
    if (!item) throw new Error('No results');

    const ofd = item.openfda || {};
    const med = {
      name: ofd.brand_name?.[0] || q,
      brand: ofd.brand_name?.[0] || q,
      generic: ofd.generic_name?.[0] || '',
      icon: '💊',
      type: 'OTC',
      use: (item.purpose?.[0] || item.indications_and_usage?.[0] || '').slice(0, 400),
      mechanism: '',
      dosage: [{ lbl: 'Dosage', val: 'See label' }],
      dosage_note: (item.dosage_and_administration?.[0] || '').slice(0, 300),
      effects: [],
      precautions: [],
      warnings: (item.warnings?.[0] || '').slice(0, 400),
      mfr: ofd.manufacturer_name?.[0] || '',
    };

    // Adverse events
    try {
      const ae = await (await fetch(`https://api.fda.gov/drug/event.json?search=patient.drug.medicinalproduct:"${encodeURIComponent(q)}"&count=patient.reaction.reactionmeddrapt.exact&limit=6`)).json();
      med.effects = (ae.results || []).slice(0, 6).map(x => x.term);
    } catch (e) { /* skip */ }

    renderMedCard(med, true);
    setDot('fda', 'on');
  } catch (e) {
    res.innerHTML = `<div class="empty-state">
      <div class="empty-ico">🔍</div>
      <div class="empty-txt">No results found for "<strong>${esc(q)}</strong>".<br/>Try the generic name (e.g. "acetaminophen" instead of "Tylenol").</div>
    </div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Search';
  }
}

function renderMedCard(m, isFda = false) {
  const res = $('drug-results');

  const dosageHtml = (m.dosage || []).map(d =>
    `<div class="dose-card"><div class="dose-label">${esc(d.lbl)}</div><div class="dose-val">${esc(d.val)}</div></div>`
  ).join('');

  const effectsHtml = (m.effects || []).length
    ? `<div class="side-effects-wrap">${m.effects.map(e => `<span class="se-pill">${esc(e)}</span>`).join('')}</div>`
    : '<span class="med-sect-val">Refer to package insert or pharmacist.</span>';

  const precsHtml = (m.precautions || []).length
    ? `<div class="prec-list">${m.precautions.map(p =>
        `<div class="prec-item"><span class="prec-ico">⚠️</span><span>${esc(p)}</span></div>`
      ).join('')}</div>`
    : (m.warnings ? `<div class="med-sect-val" style="color:var(--c-saffron-600)">${esc(m.warnings)}</div>` : '');

  const mechSection = m.mechanism
    ? `<div class="med-section">
        <div class="med-sect-lbl"><span class="med-sect-ico">🔬</span> How It Works</div>
        <div class="med-sect-val">${esc(m.mechanism)}</div>
       </div>`
    : '';

  const mfrTag = m.mfr
    ? `<div class="med-mfr">Manufacturer: ${esc(m.mfr)}</div>`
    : '';

  res.innerHTML = `
    <div class="med-card">
      <div class="med-card-head">
        <div class="med-icon">${m.icon || '💊'}</div>
        <div class="med-title-block">
          <div class="med-name">${esc(m.name)}</div>
          ${m.generic ? `<div class="med-generic">Generic: ${esc(m.generic)}</div>` : ''}
          ${m.brand && m.brand !== m.name ? `<div class="med-generic">Brand: ${esc(m.brand)}</div>` : ''}
          ${mfrTag}
        </div>
        <span class="rx-tag">${esc(m.type || 'OTC')}</span>
      </div>
      <div class="med-body">

        <div class="med-section">
          <div class="med-sect-lbl"><span class="med-sect-ico">🎯</span> What It's Used For</div>
          <div class="med-sect-val">${esc(m.use)}</div>
        </div>

        ${mechSection}

        <div class="med-section">
          <div class="med-sect-lbl"><span class="med-sect-ico">📏</span> Dosage Guide</div>
          <div class="dosage-grid">${dosageHtml}</div>
          ${m.dosage_note ? `<div class="med-sect-val" style="margin-top:8px;font-size:12.5px;color:var(--ink-400)">${esc(m.dosage_note)}</div>` : ''}
        </div>

        <div class="med-section">
          <div class="med-sect-lbl"><span class="med-sect-ico">⚡</span> Common Side Effects</div>
          ${effectsHtml}
        </div>

        ${precsHtml ? `<div class="med-section">
          <div class="med-sect-lbl"><span class="med-sect-ico">🛡️</span> Precautions &amp; Warnings</div>
          ${precsHtml}
        </div>` : ''}

        <div class="med-disclaimer">
          <span>⚕️</span>
          <span><strong>Important:</strong> Consult a licensed doctor or pharmacist before taking any medicine. This information is for educational purposes only. ${isFda ? 'Data sourced from FDA Drug Label Database.' : ''}</span>
        </div>

      </div>
    </div>`;
}

/* ─── Medical Info Lookup ─── */
async function lookupInfo() {
  const q = $('info-q').value.trim();
  if (!q) { showToast('Please enter a condition name.'); return; }

  const res = $('info-results');
  const btn = $('info-go');
  btn.disabled = true;
  btn.textContent = 'Searching…';

  res.innerHTML = `<div class="empty-state">
    <div class="skel" style="height:80px;margin-bottom:14px;border-radius:12px"></div>
    <div class="skel" style="height:14px;width:60%;margin:0 auto 8px"></div>
    <div class="skel" style="height:14px;width:40%;margin:0 auto"></div>
  </div>`;

  try {
    const term = q.replace(/\s+/g, '_');
    const r = await fetch(`https://en.wikipedia.org/api/rest_v1/page/summary/${encodeURIComponent(term)}`);
    if (!r.ok) throw new Error('Not found');
    const data = await r.json();
    if (data.type === 'disambiguation') throw new Error('Too ambiguous — please be more specific.');

    const thumb = data.thumbnail?.source || '';
    const wurl = data.content_urls?.desktop?.page || `https://en.wikipedia.org/wiki/${term}`;

    res.innerHTML = `
      <div class="med-card">
        <div class="med-card-head">
          <div class="med-icon">🔬</div>
          <div class="med-title-block">
            <div class="med-name">${esc(data.title)}</div>
            <div class="med-generic">Wikipedia Medical Encyclopedia</div>
          </div>
        </div>
        <div class="med-body">
          ${thumb ? `<img src="${esc(thumb)}" alt="${esc(data.title)}" style="width:100%;max-height:200px;object-fit:cover;border-radius:var(--r-sm);margin-bottom:4px"/>` : ''}
          <div class="med-section">
            <div class="med-sect-lbl"><span class="med-sect-ico">📋</span> Medical Overview</div>
            <div class="med-sect-val">${esc((data.extract || '').slice(0, 700))}</div>
          </div>
          <div class="med-section">
            <div class="med-sect-lbl"><span class="med-sect-ico">🔗</span> Full Article</div>
            <a href="${esc(wurl)}" target="_blank" rel="noopener noreferrer"
               style="font-size:13.5px;font-weight:600;color:var(--c-forest-500)">Read full article on Wikipedia →</a>
          </div>
          <div class="med-disclaimer">
            <span>📚</span>
            <span>Educational information only. Not a substitute for professional medical advice or diagnosis.</span>
          </div>
        </div>
      </div>`;
    setDot('wiki', 'on');
  } catch (e) {
    res.innerHTML = `<div class="empty-state">
      <div class="empty-ico">🔍</div>
      <div class="empty-txt">No results for "<strong>${esc(q)}</strong>".<br/>Try more specific terms (e.g. "Type 2 Diabetes" or "Dengue Fever").</div>
    </div>`;
  } finally {
    btn.disabled = false;
    btn.textContent = 'Search';
  }
}

/* ─── Navigation & Tabs ─── */
function toggleSidebar() {
  const sb = $('sidebar');
  const ov = $('mob-ov');
  if (window.innerWidth <= 780) {
    sb.classList.toggle('open');
    ov.classList.toggle('show');
  } else {
    sb.classList.toggle('collapsed');
  }
}

function closeSidebar() {
  $('sidebar').classList.remove('open');
  $('mob-ov').classList.remove('show');
}

function switchTab(t) {
  S.tab = t;
  ['chat', 'drug', 'info'].forEach(x => {
    $(`panel-${x}`)?.classList.toggle('on', x === t);
    $(`tab-${x}`)?.classList.toggle('on', x === t);
    $(`nav-${x}`)?.classList.toggle('active', x === t);
  });

  const subs = {
    chat: 'Multilingual · India-Focused · Private',
    drug: 'Verified medicine info from FDA & curated database',
    info: 'Condition info from Wikipedia Medical Encyclopedia',
  };
  const titles = {
    chat: 'AI Health Assistant',
    drug: 'Medicine Lookup',
    info: 'Medical Library',
  };
  const tb = $('tb-sub');
  const ttl = $('tb-title');
  if (tb) tb.textContent = subs[t] || '';
  if (ttl) ttl.textContent = titles[t] || 'ArogyaAI';
  closeSidebar();
}

/* ─── Theme ─── */
function toggleTheme() {
  S.dark = !S.dark;
  document.documentElement.setAttribute('data-theme', S.dark ? 'dark' : 'light');
  localStorage.setItem('arogyaai_theme', S.dark ? 'dark' : 'light');

  const isDark = S.dark;
  const ico = isDark ? '☀️' : '🌙';
  const lbl = isDark ? 'Light Mode' : 'Dark Mode';

  const thIco = $('th-ico-sb');
  const thLbl = $('th-lbl-sb');
  const thBtn = $('theme-btn');
  if (thIco) thIco.textContent = ico;
  if (thLbl) thLbl.textContent = lbl;
  if (thBtn) thBtn.textContent = ico;
}

/* ─── Modals ─── */
function openUpgradeModal() { $('upgrade-modal').classList.add('show'); }
function closeUpgradeModal() { $('upgrade-modal').classList.remove('show'); }

function openShare() {
  const t = S.lastReply.replace(/\*\*/g, '').slice(0, 300);
  $('share-txt').textContent = t + (t.length >= 300 ? '…' : '');
  $('share-modal').classList.add('show');
}
function closeShareModal() { $('share-modal').classList.remove('show'); }

function copyShare() {
  const text = `🌿 ArogyaAI Health Advice\n\n${S.lastReply.replace(/\*\*/g, '').slice(0, 600)}\n\n⚕️ AI guidance only — consult a doctor for serious concerns.\n© 2025 ArogyaAI — Your Health Companion`;
  navigator.clipboard.writeText(text)
    .then(() => { showToast('✅ Copied to clipboard!'); closeShareModal(); })
    .catch(() => showToast('Copy failed — try manually.'));
}

/* ─── Toast ─── */
let _toastTimer;
function showToast(msg, dur = 3500) {
  const t = $('toast');
  t.textContent = msg;
  t.classList.add('show');
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => t.classList.remove('show'), dur);
}

/* ─── API Status Dots ─── */
function setDot(id, state) {
  const d = $(`dot-${id}`);
  if (d) d.className = `s-dot ${state === 'on' ? 'on' : state === 'off' ? 'off' : 'loading'}`;
}

/* ─── Daily Tip ─── */
function setTip() {
  const tip = TIPS[new Date().getDate() % TIPS.length];
  [$('sb-tip'), $('welcome-tip')].forEach(el => { if (el) el.textContent = tip; });
}

/* ─── Voice Input (SpeechRecognition) ─── */
let _rec = null;

function initVoice() {
  const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
  if (!SR) {
    const mb = $('mic-btn');
    if (mb) { mb.disabled = true; mb.title = 'Voice not supported in this browser'; }
    return;
  }

  const r = new SR();
  r.continuous = false;
  r.interimResults = false;
  r.lang = 'hi-IN'; // supports Hindi; English works too

  r.onresult = ({ results }) => {
    $('chat-input').value = results[0][0].transcript;
    resize();
    updateSend();
    stopListening();
    showToast('🎙️ Voice captured!');
  };

  r.onerror = ({ error }) => {
    const msg = error === 'not-allowed'
      ? '🎙️ Microphone access denied — please allow in browser settings.'
      : 'Voice recognition error. Please retry.';
    showToast(msg);
    stopListening();
  };

  r.onend = () => stopListening();
  _rec = r;
}

function toggleVoice() {
  if (!_rec) return;
  if (S.listening) stopListening();
  else startListening();
}

function startListening() {
  S.listening = true;
  const mb = $('mic-btn');
  const ri = $('rec-indicator');
  if (mb) mb.classList.add('on');
  if (ri) ri.classList.add('show');
  try { _rec.start(); } catch (e) { /* ignore if already started */ }
}

function stopListening() {
  S.listening = false;
  const mb = $('mic-btn');
  const ri = $('rec-indicator');
  if (mb) mb.classList.remove('on');
  if (ri) ri.classList.remove('show');
  try { _rec.stop(); } catch (e) { /* ignore */ }
}

/* ─── Voice Output (SpeechSynthesis) ─── */
function speakMsg(msgId, btnId) {
  if (!window.speechSynthesis) { showToast('Voice not supported in this browser.'); return; }
  const el = document.getElementById(msgId);
  if (!el) return;

  // Clean text
  const raw = el.textContent
    .replace(/[*#_~`🔍✅🍽️🏥⚠️🚨💊📋🟢🟡🔴]/g, '')
    .trim()
    .slice(0, 400);

  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(raw);
  u.lang = 'en-IN';
  u.rate = 0.9;
  u.pitch = 1;
  u.volume = 0.9;

  const btn = document.getElementById(btnId);
  if (btn) { btn.classList.add('speaking'); btn.textContent = '▶ Speaking…'; }

  u.onend = () => { if (btn) { btn.classList.remove('speaking'); btn.textContent = '▶ Speak'; } };
  u.onerror = () => { if (btn) { btn.classList.remove('speaking'); btn.textContent = '▶ Speak'; } };

  window.speechSynthesis.speak(u);
  S.speaking = true;
}

function stopSpeak() {
  window.speechSynthesis?.cancel();
  S.speaking = false;
  document.querySelectorAll('.vc-btn.speaking').forEach(b => {
    b.classList.remove('speaking');
    b.textContent = '▶ Speak';
  });
}

/* ─── Health Check ─── */
async function healthCheck() {
  // AI backend
  try {
    const r = await fetch(`${API_BASE}/api/health`);
    setDot('ai', r.ok ? 'on' : 'off');
  } catch {
    setDot('ai', 'off');
  }
  // FDA
  try {
    const r = await fetch('https://api.fda.gov/drug/label.json?search=aspirin&limit=1');
    setDot('fda', r.ok ? 'on' : 'off');
  } catch {
    setDot('fda', 'off');
  }
  // Wikipedia
  try {
    const r = await fetch('https://en.wikipedia.org/api/rest_v1/page/summary/Fever');
    setDot('wiki', r.ok ? 'on' : 'off');
  } catch {
    setDot('wiki', 'off');
  }
}

/* ─── Keyboard Shortcuts ─── */
document.addEventListener('keydown', e => {
  if (e.key === 'Escape') {
    closeUpgradeModal();
    closeShareModal();
  }
});

/* ─── Init ─── */
function init() {
  // Restore theme
  const savedTheme = localStorage.getItem('arogyaai_theme');
  if (savedTheme === 'dark') {
    S.dark = true;
    document.documentElement.setAttribute('data-theme', 'dark');
    const thIco = $('th-ico-sb');
    const thLbl = $('th-lbl-sb');
    const thBtn = $('theme-btn');
    if (thIco) thIco.textContent = '☀️';
    if (thLbl) thLbl.textContent = 'Light Mode';
    if (thBtn) thBtn.textContent = '☀️';
  }

  setTip();
  updateHist();
  initVoice();

  // Mic button
  const mic = $('mic-btn');
  if (mic) mic.addEventListener('click', toggleVoice);

  // Input events
  const inp = $('chat-input');
  inp.addEventListener('input', () => { resize(); updateSend(); });
  inp.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (inp.value.trim()) sendMsg();
    }
  });

  $('send-btn').addEventListener('click', sendMsg);

  // Lookup keyboards
  $('drug-q')?.addEventListener('keydown', e => { if (e.key === 'Enter') lookupDrug(); });
  $('info-q')?.addEventListener('keydown', e => { if (e.key === 'Enter') lookupInfo(); });

  // Chips
  document.querySelectorAll('.chip[data-p]').forEach(c => {
    c.addEventListener('click', () => {
      inp.value = c.dataset.p;
      resize();
      updateSend();
      sendMsg();
    });
  });

  // Health check
  healthCheck();

  // Focus
  inp.focus();
}

document.addEventListener('DOMContentLoaded', init);