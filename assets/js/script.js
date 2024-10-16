document.addEventListener("DOMContentLoaded", function() {
    const fundTable = document.getElementById("fundTableBody");
    const headers = document.querySelectorAll("#fundTable th");
    const showAllButton = document.getElementById("showAllButton");
    const filterInput = document.getElementById("filterInput");
    let rows = Array.from(fundTable.rows);

    let numFundsToShow = 10; // Number of funds to show initially
    let allFundsShown = false;
    let filterText = ''; // Variable to store the filter text

    // List of priority words
    const priorityWords = ['HDFC', 'LIC', 'AXIS', 'BIRLA', 'ADITYA', 'UTI', 'ICICI', 'TATA', 'MAX', 'KOTAK'];

    // Simple fuzzy match function
    function fuzzyMatch(fundName, filterText) {
        fundName = fundName.toLowerCase();
        filterText = filterText.toLowerCase();

        let fundIndex = 0;
        let filterIndex = 0;

        while (fundIndex < fundName.length && filterIndex < filterText.length) {
            if (fundName[fundIndex] === filterText[filterIndex]) {
                filterIndex++;
            }
            fundIndex++;
        }

        return filterIndex === filterText.length;
    }

    // Function to render the table based on the number of funds to show and filter text
    function renderTable() {
        // Clear the table first
        fundTable.innerHTML = '';

        // Trim and uppercase the filter text
        const trimmedFilterText = filterText.trim().toUpperCase();

        // Check if the filter text matches any priority word
        const matchedPriorityWords = priorityWords.filter(word => word.includes(trimmedFilterText));

        let filteredRows;

        if (trimmedFilterText === '') {
            // No filter text; display funds containing any priority word
            filteredRows = rows.filter(row => {
                const fundName = row.cells[0].innerText.trim().toUpperCase();
                return priorityWords.some(word => fundName.includes(word));
            });
        } else if (matchedPriorityWords.length > 0) {
            // Filter funds containing the matched priority word(s)
            filteredRows = rows.filter(row => {
                const fundName = row.cells[0].innerText.trim().toUpperCase();
                return matchedPriorityWords.some(word => fundName.includes(word));
            }).filter(row => {
                // Apply fuzzy search on the filtered funds
                const fundName = row.cells[0].innerText.trim();
                return fuzzyMatch(fundName, filterText.trim());
            });
        } else {
            // If filter text doesn't match any priority word, apply fuzzy search to all priority funds
            filteredRows = rows.filter(row => {
                const fundName = row.cells[0].innerText.trim().toUpperCase();
                return priorityWords.some(word => fundName.includes(word));
            }).filter(row => {
                const fundName = row.cells[0].innerText.trim();
                return fuzzyMatch(fundName, filterText.trim());
            });
        }

        // Get the rows to display
        const rowsToDisplay = allFundsShown
            ? filteredRows
            : filteredRows.slice(0, numFundsToShow);

        // Append the rows to the table
        rowsToDisplay.forEach(row => fundTable.appendChild(row));

        // Toggle the "Show All" button visibility
        if (filteredRows.length > numFundsToShow && !allFundsShown) {
            showAllButton.style.display = 'block';
        } else {
            showAllButton.style.display = 'none';
        }

        // If no rows match, display a message
        if (filteredRows.length === 0) {
            const noResultsRow = document.createElement('tr');
            const noResultsCell = document.createElement('td');
            noResultsCell.colSpan = headers.length;
            noResultsCell.textContent = 'No matching funds found.';
            noResultsCell.style.textAlign = 'center';
            noResultsRow.appendChild(noResultsCell);
            fundTable.appendChild(noResultsRow);
        }
    }

    // Function to sort table
    function sortTable(columnIndex, isNumeric, ascending) {
        rows.sort((a, b) => {
            let aText = a.cells[columnIndex].innerText.trim();
            let bText = b.cells[columnIndex].innerText.trim();

            // Handle "-" values explicitly: treat them as a special case
            if (aText === '-') aText = ascending ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;
            if (bText === '-') bText = ascending ? Number.POSITIVE_INFINITY : Number.NEGATIVE_INFINITY;

            if (isNumeric) {
                aText = parseFloat(aText);
                bText = parseFloat(bText);
                return ascending ? aText - bText : bText - aText;
            } else {
                return ascending ? aText.localeCompare(bText) : bText.localeCompare(aText);
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

    // Add event listener for filter input
    filterInput.addEventListener("input", function() {
        filterText = this.value;
        allFundsShown = false; // Reset to show limited rows when filtering
        renderTable();
    });

    // Default sort by 5Y column (index 9) in descending order
    const fiveYearHeader = headers[9]; // Adjust the index if needed
    fiveYearHeader.classList.add("sorted-desc");
    sortTable(9, true, false);

    // Initial rendering of the table
    renderTable();
});
