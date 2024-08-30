document.addEventListener("DOMContentLoaded", function() {
    const fundTable = document.getElementById("fundTableBody");
    const headers = document.querySelectorAll("#fundTable th");
    const showAllButton = document.getElementById("showAllButton");
    const rows = Array.from(fundTable.rows);

    let numFundsToShow = 10; // Variable for home page table pagination, sort works irrespective
    let allFundsShown = false;

    // Function to render the table based on the number of funds to show
    function renderTable() {
        // Clear the table first
        fundTable.innerHTML = '';

        // Get the rows to display
        const rowsToDisplay = allFundsShown ? rows : rows.slice(0, numFundsToShow);

        // Append the rows to the table
        rowsToDisplay.forEach(row => fundTable.appendChild(row));
        
        // Toggle the "Show All" button visibility
        showAllButton.style.display = allFundsShown ? 'none' : 'block';
    }

    // Function to sort table
    function sortTable(columnIndex, isNumeric, ascending) {
        rows.sort((a, b) => {
            const aText = a.cells[columnIndex].innerText;
            const bText = b.cells[columnIndex].innerText;

            if (isNumeric) {
                return ascending
                    ? parseFloat(aText) - parseFloat(bText)
                    : parseFloat(bText) - parseFloat(aText);
            } else {
                return ascending
                    ? aText.localeCompare(bText)
                    : bText.localeCompare(aText);
            }
        });

        // Re-render the table after sorting
        renderTable();
    }

    // Add click event to each header for sorting
    headers.forEach((header, index) => {
        header.classList.add('sortable');
        header.addEventListener("click", function() {
            const isNumeric = index !== 0; // Assume all columns except the first are numeric
            const isAscending = !this.classList.contains("sorted-asc");

            // Remove sorting classes from all headers
            headers.forEach(h => h.classList.remove("sorted-asc", "sorted-desc"));

            // Add appropriate sorting class to clicked header
            this.classList.add(isAscending ? "sorted-asc" : "sorted-desc");

            sortTable(index, isNumeric, isAscending);
        });
    });

    // Add event listener for "Show All" button
    showAllButton.addEventListener("click", function() {
        allFundsShown = true;
        renderTable();
    });

    // Default sort by 5Y column (index 8) in descending order
    const fiveYearHeader = headers[8]; // 5Y column
    fiveYearHeader.classList.add("sorted-desc");
    sortTable(8, true, false);

    // Set the last updated date
    const lastUpdatedElement = document.getElementById("lastUpdated");
    const now = new Date();
    lastUpdatedElement.textContent = now.toLocaleString();

    // Initial rendering of the table
    renderTable();
});
