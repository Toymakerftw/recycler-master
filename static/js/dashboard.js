// Initial chart setup
let cpuChart, memoryChart, diskChart;

function initCharts() {
  const ctxCpu = document.getElementById("cpuChart").getContext("2d");
  const ctxMemory = document.getElementById("memoryChart").getContext("2d");
  const ctxDisk = document.getElementById("diskChart").getContext("2d");

  cpuChart = new Chart(ctxCpu, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "CPU Utilization",
          data: [],
          borderColor: "#3b82f6",
          fill: false,
        },
      ],
    },
  });

  memoryChart = new Chart(ctxMemory, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Memory Usage",
          data: [],
          borderColor: "#10b981",
          fill: false,
        },
      ],
    },
  });

  diskChart = new Chart(ctxDisk, {
    type: "line",
    data: {
      labels: [],
      datasets: [
        {
          label: "Disk Usage",
          data: [],
          borderColor: "#f43f5e",
          fill: false,
        },
      ],
    },
  });
}

function updateMetrics(data) {
  document.getElementById("cpu-usage").textContent = `${
    data.cpu_usages[data.cpu_usages.length - 1]
  }%`;
  document.getElementById("memory-usage").textContent = `${
    data.memory_usages[data.memory_usages.length - 1]
  }%`;
  document.getElementById("disk-usage").textContent = `${
    data.disk_usages[data.disk_usages.length - 1]
  }%`;
  document.getElementById("agent-count").textContent = data.agent_count;
  document.getElementById(
    "last-updated"
  ).textContent = `Last Updated: ${new Date().toLocaleTimeString()}`;
}

function updateCharts(data) {
  cpuChart.data.labels = data.timestamps;
  cpuChart.data.datasets[0].data = data.cpu_usages;
  cpuChart.update();

  memoryChart.data.labels = data.timestamps;
  memoryChart.data.datasets[0].data = data.memory_usages;
  memoryChart.update();

  diskChart.data.labels = data.timestamps;
  diskChart.data.datasets[0].data = data.disk_usages;
  diskChart.update();
}

function fetchData() {
  fetch("/metrics")
    .then((response) => response.json())
    .then((data) => {
      updateMetrics(data);
      updateCharts(data);
    })
    .catch((error) => console.error("Error fetching metrics:", error));
}

// Initialize charts and start fetching data every 5 seconds
initCharts();
fetchData();
setInterval(fetchData, 5000);