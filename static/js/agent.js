// Add this to static/js/file-explorer.js
function initFileExplorer() {
    const modal = document.getElementById('fileExplorerModal');
    const modalContent = document.querySelector('#fileExplorerModal .mt-2');
    const fileContentSection = document.getElementById('fileContentSection');
    const fileContent = document.getElementById('fileContent');
    let currentClientIp = null;
    let currentPath = '';

    // Show modal when clicking "View Files"
    document.querySelectorAll('.view-files-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const clientIp = e.target.closest('li').dataset.clientIp;
            currentClientIp = clientIp;
            currentPath = '';
            modal.style.display = 'block';
            loadFiles(clientIp, '');
        });
    });

    // Hide modal when clicking close button or outside
    document.querySelector('#fileExplorerModal .close-btn').addEventListener('click', () => {
        modal.style.display = 'none';
    });

    window.addEventListener('click', (e) => {
        if (e.target === modal) {
            modal.style.display = 'none';
        }
    });

    function loadFiles(clientIp, path) {
        fetch(`/files/${clientIp}?path=${encodeURIComponent(path)}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    modalContent.innerHTML = `<div class="text-red-600">${data.error}</div>`;
                    return;
                }

                // Create breadcrumbs
                let breadcrumbsHtml = `
                    <div class="flex items-center space-x-2 mb-4">
                        <button class="text-blue-600 hover:underline" onclick="loadFiles('${clientIp}', '')">Root</button>
                        ${data.breadcrumbs.map((crumb, index) => `
                            <span>/</span>
                            <button class="text-blue-600 hover:underline"
                                onclick="loadFiles('${clientIp}', '${crumb.path}')">${crumb.name}</button>
                        `).join('')}
                    </div>
                `;

                // Create file list
                let filesHtml = `
                    <div class="space-y-2">
                        ${data.directories.map(dir => `
                            <div class="flex items-center space-x-2 py-2 px-4 hover:bg-gray-100 cursor-pointer rounded"
                                onclick="loadFiles('${clientIp}', '${data.current_path ? data.current_path + '/' : ''}${dir.name}')">
                                <svg class="h-5 w-5 text-yellow-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                    <path d="M2 6a2 2 0 012-2h5l2 2h5a2 2 0 012 2v6a2 2 0 01-2 2H4a2 2 0 01-2-2V6z" />
                                </svg>
                                <span>${dir.name}/</span>
                            </div>
                        `).join('')}

                        ${data.files.map(file => `
                            <div class="flex items-center justify-between py-2 px-4 hover:bg-gray-100 rounded">
                                <div class="flex items-center space-x-2">
                                    <svg class="h-5 w-5 text-gray-500" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 20 20" fill="currentColor">
                                        <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                                    </svg>
                                    <span>${file.name}</span>
                                </div>
                                <div class="flex space-x-2">
                                    <a href="/download/${clientIp}/${data.current_path ? data.current_path + '/' : ''}${file.name}"
                                       class="text-blue-600 hover:underline">Download</a>
                                    <button class="text-blue-600 hover:underline"
                                            onclick="viewFileContent('${clientIp}', '${data.current_path ? data.current_path + '/' : ''}${file.name}')">View</button>
                                </div>
                            </div>
                        `).join('')}
                    </div>
                `;

                modalContent.innerHTML = breadcrumbsHtml + filesHtml;
            })
            .catch(error => {
                modalContent.innerHTML = `<div class="text-red-600">Error loading files: ${error}</div>`;
            });
    }

    function viewFileContent(clientIp, filePath) {
        fetch(`/view-file/${clientIp}/${encodeURIComponent(filePath)}`)
            .then(response => response.text())
            .then(content => {
                fileContent.textContent = content;
                fileContentSection.classList.remove('hidden');
            })
            .catch(error => {
                fileContent.textContent = `Error loading file content: ${error}`;
                fileContentSection.classList.remove('hidden');
            });
    }

    // Make loadFiles available globally
    window.loadFiles = loadFiles;
    window.viewFileContent = viewFileContent;
}

// Initialize when the DOM is loaded
document.addEventListener('DOMContentLoaded', initFileExplorer);

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
