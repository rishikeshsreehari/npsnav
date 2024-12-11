document.addEventListener("DOMContentLoaded", function () {
    const form = document.getElementById("query-form");
    const queryInput = document.getElementById("query-input");
    const resultsDisplay = document.getElementById("results-display");

    form.addEventListener("submit", async function (e) {
        e.preventDefault(); // Prevent the form from refreshing the page

        const query = queryInput.value.trim();

        if (!query) {
            resultsDisplay.textContent = "Please enter a valid SQL SELECT query.";
            return;
        }

        // Validate query format (only SELECT queries allowed)
        if (!query.toUpperCase().startsWith("SELECT")) {
            resultsDisplay.textContent = "Only SELECT queries are allowed.";
            return;
        }

        // Fetch query results from the Cloudflare Worker
        try {
            const response = await fetch(
                `https://npsnav-query.rishikeshsreehari.workers.dev/query?query=${encodeURIComponent(query)}`
            );

            if (!response.ok) {
                const errorData = await response.json();
                resultsDisplay.textContent = `Error: ${errorData.error || "Unknown error occurred"}`;
                return;
            }

            const data = await response.json();
            resultsDisplay.textContent = JSON.stringify(data, null, 2); // Pretty-print the results
        } catch (error) {
            resultsDisplay.textContent = `Error: ${error.message}`;
        }
    });
});
