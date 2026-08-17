const SYMPTOM_TYPES = [
  "fever", "cough", "fatigue", "shortness_of_breath",
  "headache", "diarrhea", "vomiting", "rash",
  "joint_pain", "chest_pain", "sore_throat", "runny_nose",
];

const SCENARIOS = {
  respiratory: {
    patient_id: "demo-resp-001",
    age: 45,
    gender: "MALE",
    district: "Gasabo",
    symptoms: { fever: 4, cough: 5, shortness_of_breath: 4, fatigue: 3 },
  },
  gastro: {
    patient_id: "demo-gi-002",
    age: 28,
    gender: "FEMALE",
    district: "Kicukiro",
    symptoms: { diarrhea: 5, vomiting: 4, fever: 2, fatigue: 3 },
  },
  febrile: {
    patient_id: "demo-feb-003",
    age: 19,
    gender: "FEMALE",
    district: "Nyarugenge",
    symptoms: { fever: 4, headache: 4, fatigue: 3, joint_pain: 2 },
  },
  low: {
    patient_id: "demo-low-004",
    age: 35,
    gender: "MALE",
    district: "Musanze",
    symptoms: { sore_throat: 2, runny_nose: 1 },
  },
};

const form = document.getElementById("triage-form");
const symptomsGrid = document.getElementById("symptoms-grid");
const requestPreview = document.getElementById("request-preview");
const responsePreview = document.getElementById("response-preview");
const resultCard = document.getElementById("result-card");
const errorBox = document.getElementById("error-box");
const submitBtn = document.getElementById("submit-predict");

function formatLabel(name) {
  return name.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase());
}

function buildSymptomInputs() {
  symptomsGrid.innerHTML = "";
  SYMPTOM_TYPES.forEach((type) => {
    const row = document.createElement("div");
    row.className = "symptom-row";
    row.innerHTML = `
      <label for="sym-${type}">${formatLabel(type)}</label>
      <input type="range" id="sym-${type}" name="${type}" min="0" max="5" value="0" />
      <span class="severity-val" id="val-${type}">0 — none</span>
    `;
    symptomsGrid.appendChild(row);

    const slider = row.querySelector("input");
    const valEl = row.querySelector(".severity-val");
    slider.addEventListener("input", () => {
      const v = Number(slider.value);
      valEl.textContent = v === 0 ? "0 — none" : `${v} / 5`;
      updateRequestPreview();
    });
  });
}

function getFormPayload() {
  const symptoms = [];
  SYMPTOM_TYPES.forEach((type) => {
    const val = Number(document.getElementById(`sym-${type}`).value);
    if (val >= 1) {
      symptoms.push({ symptom_type: type, severity: val });
    }
  });

  return {
    patient_id: document.getElementById("patient_id").value.trim(),
    age: Number(document.getElementById("age").value),
    gender: document.getElementById("gender").value,
    district: document.getElementById("district").value,
    symptoms,
  };
}

function updateRequestPreview() {
  requestPreview.textContent = JSON.stringify(getFormPayload(), null, 2);
}

function showStep(n) {
  document.querySelectorAll(".step-content").forEach((el) => el.classList.remove("active"));
  document.getElementById(`step-${n}`).classList.add("active");

  document.querySelectorAll(".step").forEach((el) => {
    const stepNum = Number(el.dataset.step);
    el.classList.remove("active", "done");
    if (stepNum < n) el.classList.add("done");
    if (stepNum === n) el.classList.add("active");
  });
}

function applyScenario(key) {
  const s = SCENARIOS[key];
  if (!s) return;

  document.getElementById("patient_id").value = s.patient_id;
  document.getElementById("age").value = s.age;
  document.getElementById("gender").value = s.gender;
  document.getElementById("district").value = s.district;

  SYMPTOM_TYPES.forEach((type) => {
    const slider = document.getElementById(`sym-${type}`);
    const valEl = document.getElementById(`val-${type}`);
    const v = s.symptoms[type] || 0;
    slider.value = v;
    valEl.textContent = v === 0 ? "0 — none" : `${v} / 5`;
  });

  updateRequestPreview();
  showStep(2);
}

function renderResult(data, payload) {
  resultCard.classList.remove("hidden");
  errorBox.classList.add("hidden");

  const badge = document.getElementById("priority-badge");
  badge.textContent = data.priority_level;
  badge.className = "priority-badge " + data.priority_level.toLowerCase();

  const score = Math.round(data.risk_score * 100);
  document.getElementById("risk-score").textContent = `${score}%`;
  document.getElementById("risk-fill").style.width = `${score}%`;
  document.getElementById("predicted-disease").textContent = data.predicted_disease;
  document.getElementById("model-version").textContent = data.model_version;
  document.getElementById("result-patient").textContent =
    `${payload.patient_id} · ${payload.age}y · ${payload.district}`;
}

function setLoading(loading) {
  submitBtn.disabled = loading;
  submitBtn.querySelector(".btn-text").textContent = loading ? "Running…" : "Run triage prediction";
  submitBtn.querySelector(".spinner").classList.toggle("hidden", !loading);
}

document.getElementById("to-step-2").addEventListener("click", () => {
  if (!document.getElementById("patient_id").value.trim()) {
    document.getElementById("patient_id").focus();
    return;
  }
  updateRequestPreview();
  showStep(2);
});

document.getElementById("back-to-1").addEventListener("click", () => showStep(1));
document.getElementById("back-to-2").addEventListener("click", () => showStep(2));
document.getElementById("restart").addEventListener("click", () => {
  form.reset();
  SYMPTOM_TYPES.forEach((type) => {
    document.getElementById(`val-${type}`).textContent = "0 — none";
  });
  resultCard.classList.add("hidden");
  errorBox.classList.add("hidden");
  responsePreview.textContent = "Submit the form to see the live response.";
  responsePreview.classList.add("muted");
  document.getElementById("patient_id").value = `demo-${Date.now().toString(36)}`;
  updateRequestPreview();
  showStep(1);
});

document.querySelectorAll(".btn-scenario").forEach((btn) => {
  btn.addEventListener("click", () => applyScenario(btn.dataset.scenario));
});

["patient_id", "age", "gender", "district"].forEach((id) => {
  document.getElementById(id).addEventListener("input", updateRequestPreview);
  document.getElementById(id).addEventListener("change", updateRequestPreview);
});

form.addEventListener("submit", async (e) => {
  e.preventDefault();
  const payload = getFormPayload();

  if (payload.symptoms.length === 0) {
    errorBox.textContent = "Add at least one symptom with severity ≥ 1.";
    errorBox.classList.remove("hidden");
    showStep(3);
    return;
  }

  setLoading(true);
  updateRequestPreview();

  try {
    const res = await fetch("/ml/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });

    const body = await res.json();
    responsePreview.textContent = JSON.stringify(body, null, 2);
    responsePreview.classList.remove("muted");

    if (!res.ok) {
      throw new Error(body.detail || `HTTP ${res.status}`);
    }

    renderResult(body, payload);
    showStep(3);
  } catch (err) {
    resultCard.classList.add("hidden");
    errorBox.textContent = `API error: ${err.message}`;
    errorBox.classList.remove("hidden");
    showStep(3);
  } finally {
    setLoading(false);
  }
});

buildSymptomInputs();
document.getElementById("patient_id").value = `demo-${Date.now().toString(36)}`;
updateRequestPreview();
