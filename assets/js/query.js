document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("query-form");
    const queryInput = document.getElementById("query-input");
    const queryResults = document.getElementById("query-results");
    const spinner = document.getElementById("spinner");
    const resultsTable = document.getElementById("results-table");
    const resultsJson = document.getElementById("results-json");
    const downloadCsvButton = document.getElementById("download-csv");
    const tabs = document.querySelectorAll(".tab");
    const tabContents = document.querySelectorAll(".tab-content");

    // Tab switching logic
    tabs.forEach(tab => {
        tab.addEventListener("click", function () {
            tabs.forEach(t => t.classList.remove("active"));
            tabContents.forEach(content => content.style.display = "none");

            this.classList.add("active");
            document.getElementById(this.dataset.tab).style.display = "block";

            // Show or hide buttons based on the active tab
            if (this.dataset.tab === "table-view") {
                downloadCsvButton.style.display = "block";
                document.getElementById("copy-json").style.display = "none";
            } else if (this.dataset.tab === "json-view") {
                downloadCsvButton.style.display = "none";
                document.getElementById("copy-json").style.display = "block";
            }
        });
    });

    document.getElementById("copy-json").addEventListener("click", function () {
        const jsonContent = resultsJson.textContent.trim();
        if (jsonContent) {
            navigator.clipboard.writeText(jsonContent).then(() => {
                alert("JSON copied to clipboard!");
            }).catch(err => {
                console.error("Error copying JSON: ", err);
            });
        }
    });

    // Form submission logic
    form.addEventListener("submit", async function (e) {
        e.preventDefault();
    
        const query = queryInput.value.trim();
    
        if (!query) {
            alert("Please enter a valid SQL SELECT query.");
            return;
        }
    
        if (!query.toUpperCase().startsWith("SELECT")) {
            alert("Only SELECT queries are allowed.");
            return;
        }
    
        // Hide results and show spinner
        queryResults.style.display = "block";
        spinner.style.display = "block";
        document.querySelectorAll('.tab-content#table-view, .tab-content#json-view')
            .forEach(content => (content.style.display = "none"));
        downloadCsvButton.style.display = "none";
    
        try {
            const response = await fetch(
                `https://npsnav-query.rishikeshsreehari.workers.dev/query?query=${encodeURIComponent(query)}`
            );
    
            if (!response.ok) {
                const errorData = await response.json();
                resultsJson.textContent = `Error: ${errorData.error || "Unknown error occurred"}`;
                spinner.style.display = "none";
                return;
            }
    
            const data = await response.json();
    
            // Populate table results and switch to Table view by default
            spinner.style.display = "none";
            document.getElementById("table-view").style.display = "block";
            document.querySelector(".tab[data-tab='table-view']").classList.add("active");
    
            resultsJson.textContent = JSON.stringify(data, null, 2);
            populateTable(data);
            enableCsvDownload(data);
    
        } catch (error) {
            spinner.style.display = "none";
            resultsJson.textContent = `Error: ${error.message}`;
        }
    });
    
    function resetToDefaultTab() {
        // Ensure the Basic tab is reset and visible
        const defaultTab = document.querySelector('.example-tabs .tab[data-tab="basic-examples"]');
        const defaultContent = document.getElementById('basic-examples');
    
        // Reset all tabs and contents
        document.querySelectorAll('.example-tabs .tab').forEach(tab => tab.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => {
            content.classList.remove('active');
            content.style.display = 'none'; // Hide all tab contents
        });
    
        // Activate the Basic tab
        defaultTab.classList.add('active');
        defaultContent.classList.add('active');
        defaultContent.style.display = 'block'; // Explicitly show Basic tab content
    }
    
  
    
    // Tab switching logic for example tabs
    document.querySelectorAll('.example-tabs .tab').forEach(tab => {
        tab.addEventListener('click', function () {
            // Remove active class from all tabs and hide all contents
            document.querySelectorAll('.example-tabs .tab').forEach(t => t.classList.remove('active'));
            document.querySelectorAll('.tab-content').forEach(content => {
                content.classList.remove('active');
                content.style.display = 'none';
            });
    
            // Add active class to the clicked tab and its content
            this.classList.add('active');
            const activeTabContent = document.getElementById(this.dataset.tab);
            activeTabContent.classList.add('active');
            activeTabContent.style.display = 'block'; // Show the active tab's content
        });
    });
    
    // Click-to-insert functionality for example queries
    document.querySelectorAll('.tab-content code').forEach(code => {
        code.addEventListener('click', () => {
            const queryInput = document.getElementById('query-input');
            queryInput.value = code.textContent.trim();
    
            // Trigger input event
            queryInput.dispatchEvent(new Event('input', { bubbles: true }));
    
            // Reset to Basic tab when an example query is clicked
        });
    });
    
    

    function populateTable(data) {
        const thead = resultsTable.querySelector("thead");
        const tbody = resultsTable.querySelector("tbody");

        // Clear table
        thead.innerHTML = "";
        tbody.innerHTML = "";

        if (data.length === 0) {
            tbody.innerHTML = "<tr><td colspan='100%'>No results found</td></tr>";
            return;
        }

        // Generate table headers
        const headers = Object.keys(data[0]);
        const headerRow = document.createElement("tr");
        headers.forEach(header => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);

        // Generate table rows
        data.forEach(row => {
            const tr = document.createElement("tr");
            headers.forEach(header => {
                const td = document.createElement("td");
                td.textContent = row[header];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    function enableCsvDownload(data) {
        downloadCsvButton.style.display = "block";
        downloadCsvButton.addEventListener("click", () => {
            const headers = Object.keys(data[0]);
            const rows = data.map(row => headers.map(header => row[header]));

            let csvContent = headers.join(",") + "\n" + rows.map(r => r.join(",")).join("\n");

            const blob = new Blob([csvContent], { type: "text/csv" });
            const url = URL.createObjectURL(blob);

            const a = document.createElement("a");
            a.href = url;
            a.download = "query_results.csv";
            a.click();

            URL.revokeObjectURL(url);
        });
    }
});

document.querySelectorAll('.example-tabs .tab').forEach(tab => {
    tab.addEventListener('click', function () {
        // Remove active class from all tabs and hide all contents
        document.querySelectorAll('.example-tabs .tab').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.tab-content').forEach(content => content.classList.remove('active'));

        // Add active class to the clicked tab and its content
        this.classList.add('active');
        document.getElementById(this.dataset.tab).classList.add('active');
    });
});

// Click-to-insert functionality
document.querySelectorAll('.tab-content code').forEach(code => {
    code.addEventListener('click', () => {
        const queryInput = document.getElementById('query-input');
        queryInput.value = code.textContent.trim();

        // Trigger input event
        queryInput.dispatchEvent(new Event('input', { bubbles: true }));
    });
});

document.querySelector('.accordion-header').addEventListener('click', function () {
    const content = document.querySelector('.accordion-content');
    const isVisible = content.style.display === 'block';
    content.style.display = isVisible ? 'none' : 'block';
    this.textContent = isVisible ? 'About the Query Builder ▼' : 'About the Query Builder ▲';
});

