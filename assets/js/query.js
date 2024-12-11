document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("query-form");
    const queryInput = document.getElementById("query-input");
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
        });
    });

    // Form submission logic
    form.addEventListener("submit", async function (e) {
        e.preventDefault();

        const query = queryInput.value.trim();

        if (!query) {
            resultsJson.textContent = "Please enter a valid SQL SELECT query.";
            return;
        }

        if (!query.toUpperCase().startsWith("SELECT")) {
            resultsJson.textContent = "Only SELECT queries are allowed.";
            return;
        }

        try {
            const response = await fetch(
                `https://npsnav-query.rishikeshsreehari.workers.dev/query?query=${encodeURIComponent(query)}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                resultsJson.textContent = `Error: ${errorData.error || "Unknown error occurred"}`;
                return;
            }

            const data = await response.json();

            // Display JSON
            resultsJson.textContent = JSON.stringify(data, null, 2);

            // Populate table
            populateTable(data);

            // Enable CSV download
            enableCsvDownload(data);
        } catch (error) {
            resultsJson.textContent = `Error: ${error.message}`;
        }
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
