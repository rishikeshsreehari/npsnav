document.addEventListener("DOMContentLoaded", function () {
    // Basic Elements
    const form = document.getElementById("query-form");
    const queryInput = document.getElementById("query-input");
    const queryResults = document.getElementById("query-results");
    const spinner = document.getElementById("spinner");
    const resultsTable = document.getElementById("results-table");
    const resultsJson = document.getElementById("results-json");
    const downloadCsvButton = document.getElementById("download-csv");
    const resultTabs = document.querySelectorAll(".tabs .tab");
    const resultTabContents = document.querySelectorAll(".tab-content");
    const exampleTabs = document.querySelectorAll(".example-tabs .tab");
    const exampleTabContents = document.querySelectorAll(".example-tabs .tab-content");

    // Pagination Elements
    const paginationContainer = document.querySelector(".pagination");
    const prevPageButton = document.querySelector(".prev-page");
    const nextPageButton = document.querySelector(".next-page");
    const currentPageSpan = document.getElementById("current-page");
    const totalPagesSpan = document.getElementById("total-pages");

    // Pagination variables
    let allResults = [];
    let currentPage = 1;
    const resultsPerPage = 20;

    // Result Tab Switching Logic
    resultTabs.forEach((tab) => {
        tab.addEventListener("click", function () {
            resultTabs.forEach((t) => t.classList.remove("active"));
            resultTabContents.forEach((content) => (content.style.display = "none"));

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

    // Example Tab Switching Logic
    exampleTabs.forEach((tab) => {
        tab.addEventListener("click", function () {
            exampleTabs.forEach((t) => t.classList.remove("active"));
            exampleTabContents.forEach((content) => (content.style.display = "none"));

            this.classList.add("active");
            document.getElementById(this.dataset.tab).style.display = "block";

            // Ensure results remain visible after switching example tabs
            queryResults.style.display = "block";
        });
    });

    // Copy JSON Functionality
    document.getElementById("copy-json").addEventListener("click", function () {
        const jsonContent = resultsJson.textContent.trim();
        if (jsonContent) {
            navigator.clipboard.writeText(jsonContent)
                .then(() => alert("JSON copied to clipboard!"))
                .catch((err) => console.error("Error copying JSON: ", err));
        }
    });

    // Form Submission Logic
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
        resultTabContents.forEach((content) => (content.style.display = "none"));
        downloadCsvButton.style.display = "none";

        try {
            const response = await fetch(
                `https://npsnav-query.rishikeshsreehari.workers.dev/query?query=${encodeURIComponent(
                    query
                )}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                resultsJson.textContent = `Error: ${errorData.error || "Unknown error occurred"}`;
                spinner.style.display = "none";
                return;
            }

            const data = await response.json();
            allResults = data; // Store data for pagination
            currentPage = 1; // Reset to the first page
            updatePagination();
            displayCurrentPageResults();

            spinner.style.display = "none";
            document.getElementById("table-view").style.display = "block";
            document.querySelector(".tabs .tab[data-tab='table-view']").classList.add("active");

            resultsJson.textContent = JSON.stringify(data, null, 2);
            enableCsvDownload(data);
        } catch (error) {
            spinner.style.display = "none";
            resultsJson.textContent = `Error: ${error.message}`;
        }
    });

    // Pagination Logic
    function updatePagination() {
        const totalPages = Math.ceil(allResults.length / resultsPerPage);
        currentPageSpan.textContent = currentPage;
        totalPagesSpan.textContent = totalPages;

        prevPageButton.disabled = currentPage === 1;
        nextPageButton.disabled = currentPage === totalPages;
        paginationContainer.style.display = totalPages > 1 ? "flex" : "none";
    }

    function displayCurrentPageResults() {
        const start = (currentPage - 1) * resultsPerPage;
        const end = start + resultsPerPage;
        const paginatedResults = allResults.slice(start, end);
        populateTable(paginatedResults);
    }

    prevPageButton.addEventListener("click", () => {
        if (currentPage > 1) {
            currentPage--;
            displayCurrentPageResults();
            updatePagination();
        }
    });

    nextPageButton.addEventListener("click", () => {
        const totalPages = Math.ceil(allResults.length / resultsPerPage);
        if (currentPage < totalPages) {
            currentPage++;
            displayCurrentPageResults();
            updatePagination();
        }
    });

    // Populate Table
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
        headers.forEach((header) => {
            const th = document.createElement("th");
            th.textContent = header;
            headerRow.appendChild(th);
        });
        thead.appendChild(headerRow);

        // Generate table rows
        data.forEach((row) => {
            const tr = document.createElement("tr");
            headers.forEach((header) => {
                const td = document.createElement("td");
                td.textContent = row[header];
                tr.appendChild(td);
            });
            tbody.appendChild(tr);
        });
    }

    // Enable CSV Download
    function enableCsvDownload(data) {
        downloadCsvButton.style.display = "block";
        downloadCsvButton.addEventListener("click", () => {
            const headers = Object.keys(data[0]);
            const rows = data.map((row) => headers.map((header) => row[header]));

            let csvContent = headers.join(",") + "\n" + rows.map((r) => r.join(",")).join("\n");

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
