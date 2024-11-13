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

function updateAgentHealth(data) {
  const agentHealthSection = document.getElementById("agent-health-section");
  agentHealthSection.innerHTML = ""; // Clear any existing content

  if (data.agent_health) {
    // Check if data.agent_health is defined
    data.agent_health.forEach((agent) => {
      const healthBadge =
        agent.health_badge === "Healthy"
          ? '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-green-100 text-green-800">Healthy</span>'
          : '<span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-red-100 text-red-800">Unhealthy</span>';

      const agentInfo = `
        <p class="text-sm text-gray-500">
          ${agent.privateip} - ${agent.hostname} - ${healthBadge}
        </p>
      `;

      agentHealthSection.innerHTML += agentInfo;
    });
  } else {
    agentHealthSection.innerHTML =
      '<p class="text-sm text-gray-500">No agent health data available.</p>';
  }
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
      updateAgentHealth(data);
    })
    .catch((error) => console.error("Error fetching metrics:", error));
}

// Initialize charts and start fetching data every 5 seconds
initCharts();
fetchData();
setInterval(fetchData, 5000);

const sidebar = document.getElementById('sidebar');
const mainContent = document.getElementById('main-content');
const overlay = document.getElementById('overlay');
const toggleIcon = document.getElementById('sidebar-toggle-icon');

function toggleSidebar() {
  const isExpanded = sidebar.classList.contains('sidebar-expanded');

  // Toggle sidebar classes
  sidebar.classList.toggle('sidebar-collapsed');
  sidebar.classList.toggle('sidebar-expanded');

  // Toggle overlay on mobile
  if (window.innerWidth < 768) {
    overlay.classList.toggle('hidden');
  }

  // Toggle menu icon
  toggleIcon.classList.toggle('mdi-menu');
  toggleIcon.classList.toggle('mdi-menu-open');
}

// Initial setup
const mediaQuery = window.matchMedia('(min-width: 768px)');

function handleScreenChange(e) {
  const isDesktop = e.matches;
  const isExpanded = sidebar.classList.contains('sidebar-expanded');

  if (isDesktop && !isExpanded) {
    toggleSidebar();
  } else if (!isDesktop && isExpanded) {
    toggleSidebar();
  }

  // Always hide overlay on desktop
  if (isDesktop) {
    overlay.classList.add('hidden');
  }
}

// Set up initial state
handleScreenChange(mediaQuery);
mediaQuery.addListener(handleScreenChange);
