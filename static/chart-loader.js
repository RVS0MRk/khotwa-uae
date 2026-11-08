let chartLibraryPromise = null;
let qrLibraryPromise = null;
function loadQRCodeLibrary() {
  if (typeof QRCode !== "undefined") return Promise.resolve(true);
  if (!qrLibraryPromise)
    qrLibraryPromise = new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = document.body.dataset.qrSrc;
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.head.append(script);
    });
  return qrLibraryPromise;
}
function loadChartLibrary() {
  if (typeof Chart !== "undefined") return Promise.resolve(true);
  if (!chartLibraryPromise)
    chartLibraryPromise = new Promise((resolve) => {
      const script = document.createElement("script");
      script.src = document.body.dataset.chartSrc;
      script.onload = () => resolve(true);
      script.onerror = () => resolve(false);
      document.head.append(script);
    });
  return chartLibraryPromise;
}
function requestPlanCharts() {
  loadChartLibrary().then((ok) => {
    if (ok && currentPlan) {
      drawPlanCharts(currentPlan);
      for (const id of ["timeline-fallback", "cost-fallback"]) {
        const node = document.getElementById(id);
        if (node) node.hidden = true;
      }
      const timeline = document.getElementById("timeline-chart");
      timeline.hidden = false;
      timeline.parentElement.style.height = "200px";
      const cost = document.getElementById("cost-chart");
      cost.hidden =
        currentPlan.total_estimated_cost_aed == null ||
        Number(currentPlan.total_estimated_cost_aed) === 0;
      cost.parentElement.style.height = "200px";
      styleCharts();
    } else styleCharts();
  });
}

function drawPlanCharts(rawPlan) {
  const p = escapePlan(rawPlan);
  if (timelineChart) {
    timelineChart.destroy();
    timelineChart = null;
  }
  if (costChart) {
    costChart.destroy();
    costChart = null;
  }
  if (typeof Chart !== "undefined") {
    timelineChart = new Chart(document.getElementById("timeline-chart"), {
      type: "bar",
      data: {
        labels: p.steps.map(
          (s) => (lang === "ar" ? "خطوة " : "Step ") + s.step_number,
        ),
        datasets: [
          {
            data: p.steps.map((s) => s.timeline_days),
            backgroundColor: "#378ADD",
            borderRadius: 6,
          },
        ],
      },
      options: {
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { display: false } },
      },
    });
    if (
      rawPlan.total_estimated_cost_aed !== null &&
      rawPlan.total_estimated_cost_aed > 0
    )
      costChart = new Chart(document.getElementById("cost-chart"), {
        type: "doughnut",
        data: {
          labels: p.steps.map((s) => s.action),
          datasets: [
            {
              data: p.steps.map((s) => s.estimated_cost_aed),
              backgroundColor: [
                "#534AB7",
                "#1D9E75",
                "#D85A30",
                "#378ADD",
                "#BA7517",
              ],
              borderWidth: 0,
            },
          ],
        },
        options: {
          responsive: true,
          maintainAspectRatio: false,
          plugins: {
            legend: { position: "bottom", labels: { font: { size: 12 } } },
          },
        },
      });
  }
}
