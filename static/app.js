const form = document.getElementById("range-form");
const startYearInput = document.getElementById("start-year");
const endYearInput = document.getElementById("end-year");
const resetButton = document.getElementById("reset-range");

const status = document.getElementById("status");
const reportSection = document.getElementById("report");
const error = document.getElementById("error");

function formatCelsius(value) {
  return `${Number(value).toFixed(2)} degrees Celsius`;
}

function showError(message) {
  status.hidden = true;
  reportSection.hidden = true;
  error.textContent = message;
  error.hidden = false;
  error.focus();
}

async function loadReport(startYear, endYear) {
  status.hidden = false;
  status.textContent = "Loading climate report...";
  error.hidden = true;

  const parameters = new URLSearchParams();

  if (startYear) {
    parameters.set("start_year", startYear);
  }

  if (endYear) {
    parameters.set("end_year", endYear);
  }

  const query = parameters.toString();
  const url = query ? `/report?${query}` : "/report";

  try {
    const response = await fetch(url);
    const report = await response.json();

    if (!response.ok) {
      throw new Error(report.detail || "The report could not be loaded.");
    }

    document.getElementById("interpretation").textContent =
      report.interpretation;

    document.getElementById("coverage").textContent =
      `${report.coverage_start_year} through ${report.coverage_end_year}`;

    document.getElementById("latest-anomaly").textContent =
      formatCelsius(report.latest_anomaly_c);

    document.getElementById("five-year-average").textContent =
      formatCelsius(report.latest_five_year_average_c);

    document.getElementById("trend").textContent =
      `${formatCelsius(report.trend_c_per_decade)} per decade`;

    const observationsResponse = await fetch(
      query ? `/observations?${query}` : "/observations"
    );
    const observationsData = await observationsResponse.json();

    if (!observationsResponse.ok) {
      throw new Error(
        observationsData.detail || "The chart data could not be loaded."
      );
    }

    drawChart(observationsData.observations || observationsData);

    status.hidden = true;
    reportSection.hidden = false;
  } catch (problem) {
    showError(problem.message);
  }
}

form.addEventListener("submit", (event) => {
  event.preventDefault();

  const startYear = startYearInput.value;
  const endYear = endYearInput.value;

  if (!startYear || !endYear) {
    showError("Enter both a start year and an end year.");
    return;
  }

  if (Number(startYear) > Number(endYear)) {
    showError("The start year must be earlier than or equal to the end year.");
    return;
  }

  loadReport(startYear, endYear);
});

resetButton.addEventListener("click", () => {
  form.reset();
  loadReport();
});

function drawChart(observations) {
  const chart = document.getElementById("trend-chart");
  const width = 800;
  const height = 360;
  const margin = { top: 25, right: 30, bottom: 55, left: 70 };

  const years = observations.map((item) => item.year);
  const values = observations.map((item) => item.anomaly_c);

  const minimumYear = Math.min(...years);
  const maximumYear = Math.max(...years);

  const rawMinimum = Math.min(...values, 0);
  const rawMaximum = Math.max(...values, 0);
  const padding = Math.max((rawMaximum - rawMinimum) * 0.1, 0.1);

  const minimumValue = Math.floor((rawMinimum - padding) * 10) / 10;
  const maximumValue = Math.ceil((rawMaximum + padding) * 10) / 10;

  const plotWidth = width - margin.left - margin.right;
  const plotHeight = height - margin.top - margin.bottom;

  const x = (year) =>
    margin.left +
    ((year - minimumYear) / (maximumYear - minimumYear || 1)) * plotWidth;

  const y = (value) =>
    margin.top +
    ((maximumValue - value) / (maximumValue - minimumValue || 1)) * plotHeight;

  const zeroY = y(0);
  const points = observations
    .map((item) => `${x(item.year).toFixed(1)},${y(item.anomaly_c).toFixed(1)}`)
    .join(" ");

  const yTicks = 5;
  const gridLines = Array.from({ length: yTicks }, (_, index) => {
    const value =
      minimumValue +
      ((maximumValue - minimumValue) * index) / (yTicks - 1);

    const position = y(value);

    return `
      <line
        x1="${margin.left}"
        y1="${position}"
        x2="${width - margin.right}"
        y2="${position}"
        class="chart-grid"
      />
      <text
        x="${margin.left - 10}"
        y="${position + 4}"
        text-anchor="end"
        class="chart-label"
      >${value.toFixed(1)}°C</text>
    `;
  }).join("");

  chart.innerHTML = `
    <desc id="chart-description">
      Annual global temperature anomalies from ${minimumYear} through
      ${maximumYear}. The latest displayed anomaly is
      ${values[values.length - 1].toFixed(2)} degrees Celsius.
    </desc>

    ${gridLines}

    <line
      x1="${margin.left}"
      y1="${zeroY}"
      x2="${width - margin.right}"
      y2="${zeroY}"
      class="chart-zero-line"
    />

    <line
      x1="${margin.left}"
      y1="${height - margin.bottom}"
      x2="${width - margin.right}"
      y2="${height - margin.bottom}"
      class="chart-axis"
    />

    <line
      x1="${margin.left}"
      y1="${margin.top}"
      x2="${margin.left}"
      y2="${height - margin.bottom}"
      class="chart-axis"
    />

    <polyline
      points="${points}"
      class="chart-line"
    />

    <text
      x="${width / 2}"
      y="${height - 12}"
      text-anchor="middle"
      class="chart-label"
    >Year</text>

    <text
      x="18"
      y="${height / 2}"
      text-anchor="middle"
      transform="rotate(-90 18 ${height / 2})"
      class="chart-label"
    >Temperature anomaly (°C)</text>

    <text
      x="${margin.left}"
      y="${height - margin.bottom + 25}"
      class="chart-label"
    >${minimumYear}</text>

    <text
      x="${width - margin.right}"
      y="${height - margin.bottom + 25}"
      text-anchor="end"
      class="chart-label"
    >${maximumYear}</text>
  `;
}

loadReport();
const observationsResponse = await fetch(
  query ? `/observations?${query}` : "/observations"
);

const observationsData = await observationsResponse.json();

if (!observationsResponse.ok) {
  throw new Error(
    observationsData.detail || "The chart data could not be loaded."
  );
}
