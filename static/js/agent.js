const sidebar = document.getElementById("sidebar");
const mainContent = document.getElementById("main-content");
const overlay = document.getElementById("overlay");
const toggleIcon = document.getElementById("sidebar-toggle-icon");

function toggleSidebar() {
  const isExpanded = sidebar.classList.contains("sidebar-expanded");

  // Toggle sidebar classes
  sidebar.classList.toggle("sidebar-collapsed");
  sidebar.classList.toggle("sidebar-expanded");

  // Toggle overlay on mobile
  if (window.innerWidth < 768) {
    overlay.classList.toggle("hidden");
  }

  // Toggle menu icon
  toggleIcon.classList.toggle("mdi-menu");
  toggleIcon.classList.toggle("mdi-menu-open");
}

// Initial setup
const mediaQuery = window.matchMedia("(min-width: 768px)");

function handleScreenChange(e) {
  const isDesktop = e.matches;
  const isExpanded = sidebar.classList.contains("sidebar-expanded");

  if (isDesktop && !isExpanded) {
    toggleSidebar();
  } else if (!isDesktop && isExpanded) {
    toggleSidebar();
  }

  // Always hide overlay on desktop
  if (isDesktop) {
    overlay.classList.add("hidden");
  }
}

// Set up initial state
handleScreenChange(mediaQuery);
mediaQuery.addListener(handleScreenChange);

function loadClientFiles(client) {
  fetch(`/client_files?client=${client}`)
    .then((response) => response.json())
    .then((data) => {
      const fileList = document.getElementById("fileList");
      fileList.innerHTML = ""; // Clear previous files

      data.files.forEach((item) => {
        const listItem = document.createElement("li");
        listItem.classList.add(
          "py-4",
          "flex",
          "items-center",
          "justify-between"
        );

        let itemContent = "";
        if (item.is_dir) {
          itemContent = `<strong>${item.name}/</strong>`;
        } else {
          itemContent = `${item.name} <a href="/view_file?file_path=${item.path}" class="ml-2 inline-flex items-center px-2 py-1 border border-transparent text-xs font-medium rounded text-blue-700 bg-blue-100 hover:bg-blue-200 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">View</a>`;
        }

        listItem.innerHTML = `
          <div class="flex items-center">
            ${itemContent}
          </div>
        `;
        fileList.appendChild(listItem);
      });
    })
    .catch((error) => console.error("Error loading files:", error));

  // Open the modal
  document.getElementById("fileExplorerModal").style.display = "block";
}

function closeModal() {
  // Close the modal
  document.getElementById("fileExplorerModal").style.display = "none";
}

function loadClientLog(client) {
  fetch(`/client_log?client=${client}`)
    .then((response) => {
      if (response.ok) {
        return response.text();
      } else {
        throw new Error("Error loading log: " + response.statusText);
      }
    })
    .then((data) => {
      document.getElementById("logContent").innerHTML = data;
      // Apply styles to table rows based on the class attribute
      const rows = document
        .getElementById("logContent")
        .getElementsByTagName("tr");
      for (let i = 0; i < rows.length; i++) {
        if (rows[i].classList.contains("bg-red-100")) {
          rows[i].style.backgroundColor = "#fecaca";
        }
      }
    })
    .catch((error) => {
      console.error(error);
      document.getElementById("logContent").textContent = "Error loading log.";
    });

  // Open the modal
  document.getElementById("logViewerModal").style.display = "block";
}

function closelogModal() {
  // Close the modal
  document.getElementById("logViewerModal").style.display = "none";
}
