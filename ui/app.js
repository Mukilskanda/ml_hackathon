const $ = (id) => document.getElementById(id);
let api =
  new URLSearchParams(location.search).get("api") ||
  localStorage.getItem("pathsnap-api") ||
  location.origin;
let connectionVersion = 0;
let result = null,
  view = { scale: 1, x: 0, y: 0 },
  playing = false,
  timer = null,
  busy = false;
const layers = {
  roads: true,
  gps: true,
  classifier: false,
  route: true,
  reference: true,
  uncertainty: false,
};
const canvas = $("map"),
  ctx = canvas.getContext("2d");
const percent = (x) => (Number.isFinite(x) ? (100 * x).toFixed(1) + "%" : "—");
const modelNames = {
  LogisticRegression: "Logistic regression",
  GaussianNB: "Gaussian naive Bayes",
  DecisionTree: "Decision tree",
  RandomForest: "Random forest",
  ExtraTrees: "Extra trees",
  HistGradientBoosting: "Histogram gradient boosting",
  MLP: "Multilayer perceptron",
  HistGradientBoosting_tuned: "Histogram gradient boosting",
  HistGradientBoosting_tuned_adaptive_candidates: "Histogram gradient boosting",
};
const modelName = (name) => modelNames[name] || name.replaceAll("_", " ");
function setModel(name) {
  $("modelLabel").textContent = modelName(name);
  $("modelLabel").title = name;
}
async function get(path, options = {}) {
  const response = await fetch(api + path, {
    ...options,
    signal: AbortSignal.timeout(180000),
  });
  if (!response.ok) {
    const e = await response.json().catch(() => ({}));
    throw Error(
      typeof e.detail === "string"
        ? e.detail
        : `Request failed (${response.status})`,
    );
  }
  return response.json();
}
function message(text, error = false) {
  $("message").textContent = text;
  $("message").style.color = error ? "#b35b43" : "";
}
async function connect() {
  const version = ++connectionVersion;
  $("run").disabled = true;
  $("connection").textContent = "Connecting";
  $("statusDot").classList.remove("connected");
  try {
    const [health, list] = await Promise.all([
      get("/api/health"),
      get("/api/trips"),
    ]);
    if (version !== connectionVersion) return;
    const selected = $("trip").value;
    $("connection").textContent = "Model server online";
    $("statusDot").classList.add("connected");
    $("partition").textContent =
      list.mode === "evaluator" ? "EVALUATOR MODE" : "DEVELOPMENT";
    $("trip").replaceChildren(
      ...list.trips.map((t) => new Option(t.label, t.id)),
    );
    if (list.trips.some((t) => t.id === selected)) $("trip").value = selected;
    if (!result) setModel(health.model);
    $("run").disabled = !list.trips.length;
    message(
      (list.mode === "evaluator"
        ? "Reserved evaluation partition is active."
        : "Student-test trips loaded. Reserved evaluator data is not included in the supplied ZIP.") +
        " " +
        (list.warnings || []).join(" "),
    );
  } catch (e) {
    if (version !== connectionVersion) return;
    $("connection").textContent = "Server unavailable";
    $("statusDot").classList.remove("connected");
    $("run").disabled = true;
    message(
      "Connect to Laptop 1 using the settings button. " + e.message,
      true,
    );
  }
}
$("settings").onclick = () => {
  $("apiUrl").value = api;
  $("settingsDialog").showModal();
};
$("settingsDialog").addEventListener("close", () => {
  if ($("settingsDialog").returnValue === "save") {
    api = $("apiUrl").value.replace(/\/$/, "");
    localStorage.setItem("pathsnap-api", api);
    connect();
  }
});
$("run").onclick = async () => {
  if (busy) return;
  busy = true;
  stop();
  $("trip").disabled = true;
  $("run").disabled = true;
  $("settings").disabled = true;
  $("play").disabled = true;
  $("export").disabled = true;
  $("scrub").disabled = true;
  $("loading").hidden = false;
  $("mapView").setAttribute("aria-busy", "true");
  $("run").textContent = "Reconstructing…";
  const start = performance.now();
  let elapsed = setInterval(() => {
    $("runNote").textContent =
      `Live inference · ${((performance.now() - start) / 1000).toFixed(0)} s`;
  }, 1000);
  message(
    "Generating spatial candidates, scoring road segments and decoding directed network transitions…",
  );
  try {
    result = await get("/api/predict", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ trip_id: $("trip").value }),
    });
    $("empty").hidden = true;
    $("observations").textContent = result.observations.toLocaleString();
    $("accuracy").textContent = percent(result.metrics?.point_accuracy);
    $("continuity").textContent = percent(result.network_feasible_fraction);
    $("latency").textContent = result.timings.total_s.toFixed(2) + " s";
    setModel(result.model);
    $("uncertain").textContent = percent(result.uncertain_fraction);
    $("resets").textContent = result.resets.length;
    $("classifierAccuracy").textContent = percent(
      result.metrics?.classifier_top1,
    );
    $("metricBasis").textContent = result.metric_basis;
    $("accuracyNote").textContent = result.metrics
      ? "Derived alignment · not official accuracy"
      : "Reference unavailable";
    $("tripTag").textContent = "TRIP " + result.trip_id;
    $("referenceNote").textContent =
      "Loading the supplied actual-path reference separately from the prediction…";
    const referenceToggle = document.querySelector('[data-layer="reference"]');
    referenceToggle.disabled = true;
    try {
      const reference = await get("/api/reference/" + result.trip_id);
      result.reference = reference;
      referenceToggle.disabled = !reference.available;
      $("referenceNote").textContent = reference.available
        ? `Blue: actual path from the supplied .route (${reference.route_arc_count} arcs). Green: predicted path. Overlapping paths show a blue border. Reference is displayed after inference and never changes the prediction.`
        : "Actual path unavailable: " + reference.reason;
    } catch (error) {
      result.reference = { available: false, reason: error.message };
      $("referenceNote").textContent =
        "Prediction ready. Actual-path reference could not be loaded: " +
        error.message;
    }
    $("scrub").max = result.observations - 1;
    $("scrub").value = 0;
    $("scrub").disabled = false;
    $("play").disabled = false;
    $("export").disabled = false;
    fit();
    playback();
    message(
      `Request ${result.request_id} completed · ${result.observations.toLocaleString()} observations · ${result.geometry_gaps} disconnected geometry joins. ${result.warnings.join(" ")}`,
    );
  } catch (e) {
    message(
      "Reconstruction failed: " +
        e.message +
        (result
          ? ` Displaying the previous result: trip ${result.trip_id}.`
          : ""),
      true,
    );
  } finally {
    clearInterval(elapsed);
    busy = false;
    $("trip").disabled = false;
    $("run").disabled = false;
    $("settings").disabled = false;
    $("play").disabled = !result;
    $("export").disabled = !result;
    $("scrub").disabled = !result;
    $("loading").hidden = true;
    $("mapView").setAttribute("aria-busy", "false");
    $("run").innerHTML = "Reconstruct route <span>↗</span>";
    $("runNote").textContent = "Live model inference · no precomputed routes";
  }
};
$("trip").onchange = () => {
  if (result && $("trip").value !== result.trip_id) {
    message(
      `Showing trip ${result.trip_id}. Select Reconstruct route to load trip ${$("trip").value}.`,
    );
  } else if (result) {
    message(`Showing the completed reconstruction for trip ${result.trip_id}.`);
  }
};
function size() {
  const rect = canvas.getBoundingClientRect();
  const dpr = devicePixelRatio || 1;
  canvas.width = Math.round(rect.width * dpr);
  canvas.height = Math.round(rect.height * dpr);
  ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  if (result && rect.width > 0 && rect.height > 0) fit();
  else draw();
}
function project(p) {
  let lat = result ? result.gps[0][1] : 50;
  return [p[0] * Math.cos((lat * Math.PI) / 180), -p[1]];
}
function fit() {
  if (!result) return;
  const lo = [Infinity, Infinity],
    hi = [-Infinity, -Infinity];
  const include = (p) => {
    const q = project(p);
    for (let a = 0; a < 2; a++) {
      lo[a] = Math.min(lo[a], q[a]);
      hi[a] = Math.max(hi[a], q[a]);
    }
  };
  result.gps.forEach(include);
  result.route.forEach((line) => line.forEach(include));
  if (result.reference?.available)
    result.reference.geometry.forEach((line) => line.forEach(include));
  let w = canvas.clientWidth,
    h = canvas.clientHeight;
  view.scale = Math.min(
    (w - 70) / Math.max(hi[0] - lo[0], 0.0001),
    (h - 70) / Math.max(hi[1] - lo[1], 0.0001),
  );
  view.x = w / 2 - ((lo[0] + hi[0]) / 2) * view.scale;
  view.y = h / 2 - ((lo[1] + hi[1]) / 2) * view.scale;
  draw();
}
function point(p) {
  const a = project(p);
  return [a[0] * view.scale + view.x, a[1] * view.scale + view.y];
}
function lines(geometry, color, width, alpha = 1) {
  ctx.strokeStyle = color;
  ctx.lineWidth = width;
  ctx.globalAlpha = alpha;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  for (const line of geometry) {
    line.forEach((p, i) => {
      const q = point(p);
      i ? ctx.lineTo(...q) : ctx.moveTo(...q);
    });
  }
  ctx.stroke();
  ctx.globalAlpha = 1;
}
function draw() {
  let w = canvas.clientWidth,
    h = canvas.clientHeight;
  ctx.clearRect(0, 0, w, h);
  ctx.fillStyle = "#edf1e7";
  ctx.fillRect(0, 0, w, h);
  ctx.strokeStyle = "#e3e8dc";
  ctx.lineWidth = 1;
  ctx.beginPath();
  for (let x = 0; x < w; x += 45) {
    ctx.moveTo(x, 0);
    ctx.lineTo(x, h);
  }
  for (let y = 0; y < h; y += 45) {
    ctx.moveTo(0, y);
    ctx.lineTo(w, y);
  }
  ctx.stroke();
  if (!result) {
    ctx.strokeStyle = "#d0ddca";
    ctx.lineWidth = 10;
    for (let i = 0; i < 5; i++) {
      ctx.beginPath();
      ctx.moveTo(-40, i * 110 + 30);
      ctx.bezierCurveTo(
        w * 0.3,
        i * 110 - 110,
        w * 0.6,
        i * 110 + 140,
        w + 20,
        i * 110 - 20,
      );
      ctx.stroke();
    }
    return;
  }
  if (layers.roads) {
    lines(result.roads, "#fffef8", 4);
    lines(result.roads, "#cbd4c4", 0.7);
  }
  if (layers.classifier) lines(result.classifier_route, "#9683bc", 4, 0.7);
  if (layers.reference && result.reference?.available) {
    lines(result.reference.geometry, "#ffffff", 11, 0.95);
    lines(result.reference.geometry, "#4e81c5", 8, 0.85);
  }
  if (layers.route) {
    lines(result.route, "#fffef8", 5, 0.95);
    lines(result.route, "#176d56", 3.5);
  }
  if (layers.gps) {
    ctx.fillStyle = "#d28b51";
    for (const p of result.gps) {
      const q = point(p);
      ctx.beginPath();
      ctx.arc(...q, 1.7, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  if (layers.uncertainty) {
    for (let i = 0; i < result.gps.length; i++) {
      if (result.entropy[i] < 0.7) continue;
      let q = point(result.gps[i]);
      ctx.fillStyle = "#e57b5f55";
      ctx.beginPath();
      ctx.arc(...q, 5, 0, Math.PI * 2);
      ctx.fill();
    }
  }
  const pos = +$("scrub").value;
  const q = point(result.matched_points[pos]);
  ctx.fillStyle = "#176d56";
  ctx.strokeStyle = "#fff";
  ctx.lineWidth = 3;
  ctx.beginPath();
  ctx.arc(...q, 7, 0, Math.PI * 2);
  ctx.fill();
  ctx.stroke();
  for (const [p, color, label] of [
    [result.gps[0], "#176d56", "S"],
    [result.gps.at(-1), "#c17e4b", "E"],
  ]) {
    let a = point(p);
    ctx.fillStyle = color;
    ctx.beginPath();
    ctx.arc(...a, 10, 0, Math.PI * 2);
    ctx.fill();
    ctx.fillStyle = "white";
    ctx.font = "bold 9px sans-serif";
    ctx.textAlign = "center";
    ctx.fillText(label, a[0], a[1] + 3);
  }
}
function zoom(factor, x = canvas.clientWidth / 2, y = canvas.clientHeight / 2) {
  view.x = x + (view.x - x) * factor;
  view.y = y + (view.y - y) * factor;
  view.scale *= factor;
  draw();
}
$("zoomIn").onclick = () => zoom(1.3);
$("zoomOut").onclick = () => zoom(1 / 1.3);
$("fit").onclick = fit;
canvas.addEventListener(
  "wheel",
  (e) => {
    e.preventDefault();
    const r = canvas.getBoundingClientRect();
    zoom(e.deltaY < 0 ? 1.12 : 1 / 1.12, e.clientX - r.left, e.clientY - r.top);
  },
  { passive: false },
);
let drag = null;
canvas.onpointerdown = (e) => {
  drag = [e.clientX, e.clientY];
  canvas.setPointerCapture(e.pointerId);
};
canvas.onpointerup = () => (drag = null);
canvas.onpointercancel = () => (drag = null);
canvas.style.touchAction = "none";
canvas.tabIndex = 0;
canvas.onkeydown = (e) => {
  if (e.key === "Home") {
    fit();
    e.preventDefault();
  } else if (e.key === "+" || e.key === "=") {
    zoom(1.2);
    e.preventDefault();
  } else if (e.key === "-") {
    zoom(1 / 1.2);
    e.preventDefault();
  } else if (
    ["ArrowLeft", "ArrowRight", "ArrowUp", "ArrowDown"].includes(e.key)
  ) {
    view.x += e.key === "ArrowLeft" ? 30 : e.key === "ArrowRight" ? -30 : 0;
    view.y += e.key === "ArrowUp" ? 30 : e.key === "ArrowDown" ? -30 : 0;
    draw();
    e.preventDefault();
  }
};
canvas.onpointermove = (e) => {
  if (drag) {
    view.x += e.clientX - drag[0];
    view.y += e.clientY - drag[1];
    drag = [e.clientX, e.clientY];
    draw();
  }
  if (result) {
    let i = +$("scrub").value;
    $("coords").textContent = result.gps[i]
      .map((x) => x.toFixed(5))
      .join(" / ");
  }
};
document.querySelectorAll("[data-layer]").forEach(
  (input) =>
    (input.onchange = () => {
      layers[input.dataset.layer] = input.checked;
      draw();
    }),
);
function playback() {
  if (!result) return;
  let i = +$("scrub").value,
    seconds = result.timestamps[i] - result.timestamps[0];
  $("timeLabel").textContent =
    Math.floor(seconds / 60)
      .toString()
      .padStart(2, "0") +
    ":" +
    Math.floor(seconds % 60)
      .toString()
      .padStart(2, "0");
  $("playbackLabel").textContent =
    `Observation ${i + 1} / ${result.observations} · confidence ${percent(result.confidence[i])}`;
  $("coords").textContent = result.gps[i].map((x) => x.toFixed(5)).join(" / ");
  draw();
}
function stop() {
  playing = false;
  clearInterval(timer);
  $("play").textContent = "▶";
  $("play").setAttribute("aria-label", "Play trajectory");
}
$("scrub").oninput = playback;
$("play").onclick = () => {
  if (playing) return stop();
  playing = true;
  if (+$("scrub").value >= +$("scrub").max) $("scrub").value = 0;
  $("play").textContent = "Ⅱ";
  $("play").setAttribute("aria-label", "Pause trajectory");
  timer = setInterval(() => {
    if (+$("scrub").value >= +$("scrub").max) return stop();
    $("scrub").value = Math.min(
      +$("scrub").max,
      +$("scrub").value + Math.max(1, Math.floor(result.observations / 600)),
    );
    playback();
  }, 50);
};
$("export").onclick = () => {
  const url = URL.createObjectURL(
    new Blob([JSON.stringify(result, null, 2)], { type: "application/json" }),
  );
  let a = document.createElement("a");
  a.href = url;
  a.download = `pathsnap_${result.trip_id}.json`;
  a.click();
  URL.revokeObjectURL(url);
};
document.querySelectorAll("[data-view]").forEach(
  (button) =>
    (button.onclick = () => {
      document.querySelectorAll("[data-view]").forEach((b) => {
        b.classList.toggle("active", b === button);
        b.setAttribute("aria-current", b === button ? "page" : "false");
      });
      stop();
      let bench = button.dataset.view === "experiments";
      $("mapView").hidden = bench;
      $("experimentsView").hidden = !bench;
      $("pageTitle").textContent = bench
        ? "Experiment bench."
        : "Route explorer.";
      $("pageSubtitle").textContent = bench
        ? "Compare the models. Understand the selected pipeline."
        : "Turn noisy GPS observations into a connected journey.";
      if (bench) loadExperiments();
      else size();
    }),
);
async function loadExperiments() {
  try {
    let e = await get("/api/experiments");
    $("experimentSummary").replaceChildren();
    for (const [number, label] of [
      [e.models.length, "model configurations"],
      [e.manifest.training_trips, "training trips"],
      [3, "trip-grouped CV folds"],
      [e.manifest.trials, "Bayesian trials"],
    ]) {
      const stat = document.createElement("span");
      stat.className = "bench-stat";
      const value = document.createElement("b");
      value.textContent = number;
      stat.append(value, label);
      $("experimentSummary").append(stat);
    }
    let fragment = document.createDocumentFragment();
    for (let m of e.models) {
      let row = document.createElement("tr");
      if (m.model === e.manifest.model) row.className = "winner";
      for (let value of [
        modelName(m.model),
        percent(m.cv_macro_f1),
        percent(m.cv_top1_accuracy),
        percent(m.test_macro_f1),
        percent(m.test_top1_accuracy),
        Number(m.test_log_loss).toFixed(3),
        Number(m.test_inference_s).toFixed(2) + " s",
      ]) {
        let cell = document.createElement("td");
        cell.textContent = value;
        row.append(cell);
      }
      row.firstChild.title = m.model;
      if (m.model.includes("tuned")) {
        const detail = document.createElement("small");
        detail.className = "model-detail";
        detail.textContent = m.model.includes("adaptive_candidates")
          ? "Bayesian tuned · historical candidate profile"
          : "Bayesian tuned · nearest candidates";
        row.firstChild.append(detail);
      }
      if (m.model === e.manifest.model) {
        const badge = document.createElement("span");
        badge.className = "selected-tag";
        badge.textContent = "SELECTED";
        row.firstChild.append(badge);
      }
      fragment.append(row);
    }
    $("experimentRows").replaceChildren(fragment);
    $("ablations").replaceChildren(
      ...[
        "nearest_road",
        "classifier_only",
        "fixed_hmm",
        "adaptive_hmm",
        "audited_hmm",
      ]
        .filter((name) => e.routes[name])
        .map((name) => {
          const m = e.routes[name];
          let div = document.createElement("div");
          div.className = "ablation";
          let label = document.createElement("span");
          label.textContent =
            {
              nearest_road: "Nearest road",
              classifier_only: "Classifier only",
              fixed_hmm: "Fixed HMM",
              adaptive_hmm: "Adaptive HMM",
              audited_hmm: "Final audited HMM",
            }[name] || name.replaceAll("_", " ");
          if (name === "audited_hmm") div.classList.add("final-ablation");
          let score = document.createElement("strong");
          score.textContent = Number.isFinite(m.point_accuracy)
            ? (100 * m.point_accuracy).toFixed(2) + "%"
            : "—";
          let sub = document.createElement("small");
          sub.textContent = "Equal-trip derived reference agreement";
          div.append(label, score, sub);
          return div;
        }),
    );
  } catch (e) {
    $("experimentSummary").textContent =
      "Unable to load experiment results: " + e.message;
    message(e.message, true);
  }
}
new ResizeObserver(size).observe(canvas);
$("clock").textContent = new Date().toLocaleDateString(undefined, {
  day: "numeric",
  month: "short",
  year: "numeric",
});
connect();
