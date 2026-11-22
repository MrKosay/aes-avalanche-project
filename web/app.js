"use strict";

const $ = id => document.getElementById(id);

let pair = null;
let trace = null;
let batch = null;

let roundOrigin = null;
let oracleRevision = 0;
let roundRevision = 0;

function showError(message = "") {
  $("error").textContent = message;
  $("error").hidden = !message;
}

async function api(path, data) {
  let response;

  try {
    response = await fetch(path, {
      method: data === undefined ? "GET" : "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: data === undefined ? undefined : JSON.stringify(data)
    });
  } catch {
    throw new Error(
      "Cannot reach the server. Check that FastAPI is running."
    );
  }

  if (!response.ok) {
    let detail;

    try {
      detail = (await response.json()).detail;
    } catch {
      detail = null;
    }

    if (Array.isArray(detail)) {
      detail = detail
        .map(item => {
          const field = item.loc.slice(1).join(".");
          return `${field}: ${item.msg}`;
        })
        .join("; ");
    }

    throw new Error(detail || `Request failed (${response.status}).`);
  }

  return response.json();
}

async function busy(buttonId, action) {
  const button = $(buttonId);

  if (button.disabled) return;

  const originalText = button.textContent;

  button.disabled = true;
  button.textContent = "Working…";
  showError();

  try {
    await action();
  } catch (error) {
    showError(error.message || "The operation failed.");
  } finally {
    button.disabled = false;
    button.textContent = originalText;
  }
}

/* ---------------- Tabs ---------------- */

function openTab(name) {
  document.querySelectorAll('[role="tab"]').forEach(button => {
    const active = button.dataset.tab === name;

    button.setAttribute("aria-selected", String(active));
    button.tabIndex = active ? 0 : -1;
  });

  document.querySelectorAll('[role="tabpanel"]').forEach(panel => {
    panel.hidden = panel.id !== name;
  });
}

const tabs = [...document.querySelectorAll('[role="tab"]')];

tabs.forEach((button, index) => {
  button.addEventListener("click", () => {
    openTab(button.dataset.tab);
  });

  button.addEventListener("keydown", event => {
    let nextIndex;

    if (event.key === "ArrowRight") {
      nextIndex = (index + 1) % tabs.length;
    } else if (event.key === "ArrowLeft") {
      nextIndex = (index - 1 + tabs.length) % tabs.length;
    } else if (event.key === "Home") {
      nextIndex = 0;
    } else if (event.key === "End") {
      nextIndex = tabs.length - 1;
    } else {
      return;
    }

    event.preventDefault();

    openTab(tabs[nextIndex].dataset.tab);
    tabs[nextIndex].focus();
  });
});

/* ---------------- Input handling ---------------- */

function getPayload(isRound = false) {
  const bitValue = $(isRound ? "round-bit" : "bit").value;

  return {
    plaintext: $(isRound ? "round-plain" : "plain").value.trim(),
    key: $(isRound ? "round-key" : "key").value.trim(),
    bit_index: bitValue === "" ? NaN : Number(bitValue)
  };
}

function validatePayload(input) {
  if (
    !/^[0-9a-f]{32}$/i.test(input.plaintext) ||
    !/^[0-9a-f]{32}$/i.test(input.key)
  ) {
    throw new Error(
      "Plaintext and key must each contain exactly 32 hexadecimal characters."
    );
  }

  if (
    !Number.isInteger(input.bit_index) ||
    input.bit_index < 0 ||
    input.bit_index > 127
  ) {
    throw new Error("Bit index must be an integer from 0 to 127.");
  }
}

function clearRounds() {
  roundRevision++;
  trace = null;

  $("round-result").hidden = true;
  $("round-empty").hidden = false;
}

function clearPair() {
  oracleRevision++;
  pair = null;

  $("oracle-result").hidden = true;
  $("oracle-empty").hidden = false;

  if (roundOrigin === "oracle") {
    clearRounds();
    roundOrigin = null;

    $("round-source").textContent =
      "ORACLE INPUTS CHANGED · INSPECT AGAIN";
  }
}

["plain", "key", "bit"].forEach(id => {
  $(id).addEventListener("input", () => {
    clearPair();
    $("bit-label").textContent = $("bit").value;
  });
});

["round-plain", "round-key", "round-bit"].forEach(id => {
  $(id).addEventListener("input", () => {
    clearRounds();
    roundOrigin = null;
    $("round-source").textContent = "INDEPENDENT INPUTS";
  });
});

/* ---------------- Shared rendering ---------------- */

function renderMetrics(containerId, items) {
  const container = $(containerId);

  container.replaceChildren();

  items.forEach(([label, value]) => {
    const card = document.createElement("div");
    const caption = document.createElement("small");
    const number = document.createElement("b");

    card.className = "metric";
    caption.textContent = label;
    number.textContent = value;

    card.append(caption, number);
    container.append(card);
  });
}

function renderValues(containerId, entries) {
  const container = $(containerId);

  container.replaceChildren();

  Object.entries(entries).forEach(([label, value]) => {
    const term = document.createElement("dt");
    const description = document.createElement("dd");

    term.textContent = label;
    description.textContent = value;

    container.append(term, description);
  });
}

function xorBits(first, second) {
  const result = [];

  for (let i = 0; i < first.length; i += 2) {
    const a = parseInt(first.slice(i, i + 2), 16);
    const b = parseInt(second.slice(i, i + 2), 16);
    const bits = (a ^ b).toString(2).padStart(8, "0");

    result.push(...bits.split("").map(Number));
  }

  return result;
}

function renderBits(containerId, bits) {
  const container = $(containerId);

  container.replaceChildren();

  bits.forEach((value, index) => {
    const bit = document.createElement("span");

    bit.className = `bit ${value ? "changed" : ""}`;
    bit.textContent = value;
    bit.title = `Bit ${index}: ${value ? "changed" : "unchanged"}`;

    container.append(bit);
  });
}

/* ---------------- Oracle ---------------- */

function renderPair(result) {
  $("oracle-empty").hidden = true;
  $("oracle-result").hidden = false;

  renderMetrics("pair-metrics", [
    ["Changed ciphertext bits", `${result.changed_bits} / 128`],
    ["Avalanche percentage", `${result.avalanche_percentage.toFixed(2)}%`]
  ]);

  renderValues("pair-values", {
    "Original plaintext": result.plaintext,
    "Modified plaintext": result.modified_plaintext,
    "Original ciphertext": result.ciphertext,
    "Modified ciphertext": result.modified_ciphertext
  });

  renderBits(
    "pair-bits",
    xorBits(result.ciphertext, result.modified_ciphertext)
  );
}

$("oracle-form").addEventListener("submit", event => {
  event.preventDefault();

  busy("compare", async () => {
    const input = getPayload();

    validatePayload(input);

    const revision = ++oracleRevision;
    const result = await api("/api/oracle/compare", input);

    if (revision !== oracleRevision) return;

    pair = result;
    renderPair(result);
  });
});

$("random-oracle").addEventListener("click", () => {
  busy("random-oracle", async () => {
    const revision = oracleRevision;
    const result = await api("/api/random-input");

    if (revision !== oracleRevision) return;

    clearPair();

    $("plain").value = result.plaintext;
    $("key").value = result.key;
  });
});

/* ---------------- Round inspection ---------------- */

async function sendToRounds(result, origin) {
  $("round-plain").value = result.plaintext;
  $("round-key").value = result.key;
  $("round-bit").value = result.flipped_bit_index;

  clearRounds();
  roundOrigin = origin;

  $("round-source").textContent =
    origin === "oracle"
      ? "SAME PAIR AS ORACLE"
      : `STATISTICS TRIAL ${result.trial}`;

  openTab("rounds");

  await runInspection(result);
}

$("inspect-pair").addEventListener("click", () => {
  if (!pair) return;

  busy("inspect-pair", () => sendToRounds(pair, "oracle"));
});

$("round-form").addEventListener("submit", event => {
  event.preventDefault();

  busy("run-rounds", () => runInspection());
});

async function runInspection(expectedPair = null) {
  const input = getPayload(true);

  validatePayload(input);

  const revision = ++roundRevision;
  const result = await api("/api/rounds/inspect", input);

  if (revision !== roundRevision) return;

  if (
    expectedPair &&
    (
      result.ciphertext !== expectedPair.ciphertext ||
      result.modified_ciphertext !== expectedPair.modified_ciphertext
    )
  ) {
    throw new Error(
      "Round inspection does not match the selected encryption pair."
    );
  }

  trace = result;

  $("round-empty").hidden = true;
  $("round-result").hidden = false;

  $("step").max = result.steps.length - 1;
  $("step").value = 0;

  renderStep();
}

const explanations = {
  Input:
    "The two plaintext blocks differ in exactly one selected input bit.",

  SubBytes:
    "Nonlinear byte substitution changes the bit differences within affected bytes.",

  ShiftRows:
    "Rows shift left, moving byte differences into other columns. The number of differing bits stays unchanged.",

  MixColumns:
    "Bytes are mixed within each column, spreading differences across that column.",

  AddRoundKey:
    "Both states are XORed with the same round key. Their XOR difference and differing-bit count stay unchanged."
};

function currentStepIndex() {
  if (!trace) return 0;

  return Math.max(
    0,
    Math.min(
      trace.steps.length - 1,
      Math.floor(Number($("step").value) || 0)
    )
  );
}

function goToStep(index) {
  if (!trace) return;

  $("step").value = Math.max(
    0,
    Math.min(trace.steps.length - 1, index)
  );

  renderStep();
}

function renderMatrix(containerId, matrix, difference) {
  const container = $(containerId);

  container.replaceChildren();

  matrix.forEach((row, rowIndex) => {
    row.forEach((value, columnIndex) => {
      const cell = document.createElement("div");
      const changed = difference[rowIndex][columnIndex] !== "00";

      cell.className = `cell ${changed ? "changed" : ""}`;
      cell.textContent = value.toUpperCase();

      cell.title =
        `Row ${rowIndex}, column ${columnIndex}; ` +
        `byte index ${rowIndex + 4 * columnIndex}`;

      container.append(cell);
    });
  });
}

function renderStep() {
  if (!trace) return;

  const index = currentStepIndex();
  const step = trace.steps[index];

  $("step").value = index;

  $("step-title").textContent =
    step.round < 0
      ? "Input plaintext"
      : step.round === 0
        ? "Initial AddRoundKey"
        : `Round ${step.round} · ${step.operation}`;

  $("step-count").textContent =
    `STEP ${index + 1} / ${trace.steps.length}`;

  $("step-explanation").textContent =
    explanations[step.operation] || "";

  $("round-select").value = String(step.round);

  document.querySelectorAll("[data-operation]").forEach(button => {
    const operation = button.dataset.operation;

    const available = trace.steps.some(
      entry =>
        entry.round === step.round &&
        entry.operation === operation
    );

    button.disabled = !available;

    const active = operation === step.operation && available;

    button.classList.toggle("active", active);
    button.setAttribute("aria-pressed", String(active));
  });

  renderMatrix(
    "matrix-a",
    step.original_state_matrix,
    step.xor_matrix
  );

  renderMatrix(
    "matrix-b",
    step.modified_state_matrix,
    step.xor_matrix
  );

  renderMatrix(
    "matrix-x",
    step.xor_matrix,
    step.xor_matrix
  );

  renderMetrics("step-metrics", [
    ["Changed bits", `${step.changed_bits} / 128`],
    ["Changed bytes", `${step.changed_bytes} / 16`],
    ["Avalanche", `${step.avalanche_percentage.toFixed(2)}%`]
  ]);

  const changedIndices = new Set(step.changed_bit_indices);

  renderBits(
    "step-bits",
    Array.from(
      { length: 128 },
      (_, bit) => Number(changedIndices.has(bit))
    )
  );

  $("previous").disabled = index === 0;
  $("next").disabled = index === trace.steps.length - 1;

  drawChart(
    "round-chart",
    trace.rounds.map(entry => [
      entry.round,
      entry.avalanche_percentage
    ]),
    {
      xMax: 10,
      xLabel: "Round",
      yLabel: "Changed state bits (%)",
      line50: true,
      selectedX: step.round >= 0 ? step.round : null
    }
  );
}

$("step").addEventListener("input", renderStep);

$("previous").addEventListener("click", () => {
  goToStep(currentStepIndex() - 1);
});

$("next").addEventListener("click", () => {
  goToStep(currentStepIndex() + 1);
});

$("round-select").addEventListener("change", () => {
  if (!trace) return;

  const round = Number($("round-select").value);
  const current = trace.steps[currentStepIndex()];

  let index = trace.steps.findIndex(
    entry =>
      entry.round === round &&
      entry.operation === current.operation
  );

  if (index === -1) {
    index = trace.steps.findIndex(entry => entry.round === round);
  }

  if (index !== -1) goToStep(index);
});

document.querySelectorAll("[data-operation]").forEach(button => {
  button.addEventListener("click", () => {
    if (!trace) return;

    const round = trace.steps[currentStepIndex()].round;
    const operation = button.dataset.operation;

    const index = trace.steps.findIndex(
      entry =>
        entry.round === round &&
        entry.operation === operation
    );

    if (index !== -1) goToStep(index);
  });
});

/* ---------------- Charts ---------------- */

function drawChart(containerId, series, options) {
  const {
    xMax,
    yMax = 100,
    xLabel,
    yLabel,
    line50 = false,
    bars = false,
    selectedX = null
  } = options;

  const width = 640;
  const height = 290;

  const left = 54;
  const right = 20;
  const top = 28;
  const bottom = 48;

  const plotWidth = width - left - right;
  const plotHeight = height - top - bottom;

  const maximumY = Math.max(1, yMax);

  const x = value => left + (value / Math.max(1, xMax)) * plotWidth;

  const y = value =>
    top + plotHeight - (value / maximumY) * plotHeight;

  const gradientId = `gradient-${containerId}`;
  const areaId = `area-${containerId}`;

  let svg = `
    <svg
      viewBox="0 0 ${width} ${height}"
      role="img"
      aria-label="${yLabel} by ${xLabel}"
    >
      <defs>
        <linearGradient id="${gradientId}" x1="0" y1="0" x2="1" y2="0">
          <stop offset="0%" stop-color="#309bff"/>
          <stop offset="100%" stop-color="#a074ff"/>
        </linearGradient>

        <linearGradient id="${areaId}" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stop-color="#6c67ff" stop-opacity="0.25"/>
          <stop offset="100%" stop-color="#6c67ff" stop-opacity="0"/>
        </linearGradient>
      </defs>
  `;

  for (let i = 0; i <= 4; i++) {
    const value = (maximumY * i) / 4;

    svg += `
      <line
        x1="${left}" y1="${y(value)}"
        x2="${width - right}" y2="${y(value)}"
        stroke="#2a3650"
      />

      <text
        x="${left - 9}" y="${y(value) + 4}"
        text-anchor="end"
        fill="#9aa8c4"
        font-size="11"
      >${Math.round(value)}</text>
    `;
  }

  const tickCount = xMax === 10 ? 10 : 4;

  for (let i = 0; i <= tickCount; i++) {
    const value = (xMax * i) / tickCount;

    svg += `
      <text
        x="${x(value)}" y="${height - 27}"
        text-anchor="middle"
        fill="#9aa8c4"
        font-size="11"
      >${Math.round(value)}</text>
    `;
  }

  if (line50) {
    svg += `
      <line
        x1="${left}" y1="${y(50)}"
        x2="${width - right}" y2="${y(50)}"
        stroke="#d8ad67"
        stroke-dasharray="5 5"
        opacity="0.8"
      />
    `;
  }

  if (bars) {
    const barWidth = Math.min(
      18,
      (plotWidth / Math.max(1, series.length)) * 0.8
    );

    series.forEach(([horizontal, vertical]) => {
      svg += `
        <rect
          x="${x(horizontal) - barWidth / 2}"
          y="${y(vertical)}"
          width="${barWidth}"
          height="${Math.max(0, y(0) - y(vertical))}"
          rx="1"
          fill="#648bff"
        >
          <title>
            ${horizontal.toFixed(2)}%: ${vertical} trials
          </title>
        </rect>
      `;
    });
  } else {
    const points = series
      .map(([horizontal, vertical]) => `${x(horizontal)},${y(vertical)}`)
      .join(" ");

    if (series.length) {
      const first = series[0];
      const last = series[series.length - 1];

      svg += `
        <polygon
          points="
            ${x(first[0])},${y(0)}
            ${points}
            ${x(last[0])},${y(0)}
          "
          fill="url(#${areaId})"
        />
      `;
    }

    svg += `
      <polyline
        points="${points}"
        fill="none"
        stroke="url(#${gradientId})"
        stroke-width="2.6"
        stroke-linejoin="round"
        stroke-linecap="round"
      />
    `;

    if (series.length <= 20) {
      series.forEach(([horizontal, vertical]) => {
        const selected = horizontal === selectedX;

        svg += `
          <circle
            cx="${x(horizontal)}"
            cy="${y(vertical)}"
            r="${selected ? 6 : 3.5}"
            fill="${selected ? "#ffffff" : "#8e86ff"}"
            stroke="${selected ? "#309bff" : "#aaa1ff"}"
            stroke-width="${selected ? 3 : 1}"
          >
            <title>
              Round ${horizontal}: ${vertical.toFixed(2)}%
            </title>
          </circle>
        `;
      });
    }
  }

  svg += `
      <text
        x="${left + plotWidth / 2}"
        y="${height - 5}"
        text-anchor="middle"
        fill="#aab8d2"
        font-size="12"
      >${xLabel}</text>

      <text
        x="${left}" y="14"
        fill="#aab8d2"
        font-size="11"
      >${yLabel}</text>
    </svg>
  `;

  $(containerId).innerHTML = svg;
}

/* ---------------- Statistics ---------------- */

$("run-stats").addEventListener("click", () => {
  busy("run-stats", async () => {
    $("stats-status").textContent = "Running 1,000 experiments…";

    try {
      const result = await api("/api/experiments", {
        trials: 1000
      });

      batch = result;

      $("stats-result").hidden = false;

      $("stats-status").textContent =
        `Completed ${result.num_trials.toLocaleString()} trials. ` +
        "Download the results before closing or refreshing this page.";

      const summary = result.summary;

      const deviation =
        summary.sample_std_changed_bits == null
          ? "N/A"
          : summary.sample_std_changed_bits.toFixed(2);

      renderMetrics("stats-metrics", [
        ["Trials", result.num_trials.toLocaleString()],
        ["Average avalanche", `${summary.mean_percentage.toFixed(2)}%`],
        ["Mean changed bits", summary.mean_changed_bits.toFixed(2)],
        [
          "Range / sample SD in bits",
          `${summary.min_changed_bits}–${summary.max_changed_bits} / ${deviation}`
        ]
      ]);

      drawChart(
        "hist-chart",
        result.histogram.map((count, index) => [
          (index / 128) * 100,
          count
        ]),
        {
          xMax: 100,
          yMax: Math.max(...result.histogram) * 1.1,
          bars: true,
          xLabel: "Changed ciphertext bits (%)",
          yLabel: "Number of trials"
        }
      );

      drawChart(
        "average-chart",
        result.running_average.map((value, index) => [
          index + 1,
          value
        ]),
        {
          xMax: result.num_trials,
          line50: true,
          xLabel: "Trials included",
          yLabel: "Average avalanche (%)"
        }
      );

      drawChart(
        "frequency-chart",
        result.bit_change_percentages.map((value, index) => [
          index,
          value
        ]),
        {
          xMax: 127,
          line50: true,
          xLabel: "Ciphertext bit index",
          yLabel: "Trials in which the bit changed (%)"
        }
      );

      $("trial-number").max = result.num_trials;
      $("trial-number").value = 1;

      renderTrial();
    } catch (error) {
      $("stats-status").textContent =
        "The experiment failed. Please try again.";

      throw error;
    }
  });
});

function renderTrial() {
  if (!batch) return null;

  const requested = Math.floor(Number($("trial-number").value) || 1);

  const number = Math.max(
    1,
    Math.min(batch.num_trials, requested)
  );

  $("trial-number").value = number;

  const result = batch.trials[number - 1];

  $("trial-info").textContent =
    `Trial ${number} · input bit ${result.flipped_bit_index} flipped · ` +
    `${result.changed_bits}/128 ciphertext bits changed ` +
    `(${result.avalanche_percentage.toFixed(2)}%).`;

  renderValues("trial-values", {
    "Shared key": result.key,
    "Original plaintext": result.plaintext,
    "Modified plaintext": result.modified_plaintext,
    "Original ciphertext": result.ciphertext,
    "Modified ciphertext": result.modified_ciphertext
  });

  renderBits(
    "trial-bits",
    xorBits(result.ciphertext, result.modified_ciphertext)
  );

  return result;
}

$("trial-number").addEventListener("change", renderTrial);

$("inspect-trial").addEventListener("click", () => {
  const selected = renderTrial();

  if (!selected) return;

  busy(
    "inspect-trial",
    () => sendToRounds(selected, "statistics")
  );
});

/* ---------------- Downloads ---------------- */

function download(filename, content, type = "application/json") {
  const blob = new Blob([content], { type });
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");

  link.href = url;
  link.download = filename;

  document.body.append(link);
  link.click();
  link.remove();

  setTimeout(() => URL.revokeObjectURL(url), 1000);
}

$("download-rounds").addEventListener("click", () => {
  if (!trace) return;

  download(
    "round_inspection.json",
    JSON.stringify(trace, null, 2)
  );
});

$("download-stats").addEventListener("click", () => {
  if (!batch) return;

  download(
    "avalanche_results.json",
    JSON.stringify(batch, null, 2)
  );
});

$("download-csv").addEventListener("click", () => {
  if (!batch) return;

  const fields = Object.keys(batch.trials[0]);

  const lines = [
    fields.join(","),
    ...batch.trials.map(row =>
      fields.map(field => row[field]).join(",")
    )
  ];

  download(
    "trials.csv",
    lines.join("\r\n"),
    "text/csv;charset=utf-8"
  );
});

/* ---------------- Connection ---------------- */

api("/api/health")
  .then(() => {
    $("connection").textContent = "● SERVER CONNECTED";
  })
  .catch(() => {
    $("connection").textContent = "SERVER UNAVAILABLE";

    showError(
      "Start FastAPI and open http://127.0.0.1:8000. " +
      "Do not open index.html directly."
    );
  });