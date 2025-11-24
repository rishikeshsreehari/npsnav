document.addEventListener("DOMContentLoaded", function () {
    const fundTable = document.getElementById("fundTableBody");
    const headers = document.querySelectorAll("#fundTable th");
    const showAllButton = document.getElementById("showAllButton");
    const filterInput = document.getElementById("filterInput");
    const pfmFilter = document.getElementById("pfmFilter");
    const tierFilter = document.getElementById("tierFilter");
    const schemeTypeFilter = document.getElementById("schemeTypeFilter");
    let rows = Array.from(fundTable.rows);

    let numFundsToShow = 10; // Number of funds to show initially
    let allFundsShown = false;
    let filterText = ''; // Variable to store the filter text
    let selectedPfm = ''; // Variable to store selected PFM
    let selectedTier = ''; // Variable to store selected Tier
    let selectedSchemeType = ''; // Variable to store selected Scheme Type

    // Auto-focus by default on search box in Desktop only ---
    // This prevents the keyboard from popping up automatically on mobile devices
    if (window.innerWidth > 768 && filterInput) {
        filterInput.focus();
    }

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

        // Trim the filter text
        const trimmedFilterText = filterText.trim();

        let filteredRows = rows;

        // Apply PFM filter
        if (selectedPfm) {
            filteredRows = filteredRows.filter(row => {
                return row.getAttribute('data-pfm') === selectedPfm;
            });
        }

        // Apply Tier filter
        if (selectedTier) {
            filteredRows = filteredRows.filter(row => {
                return row.getAttribute('data-tier') === selectedTier;
            });
        }

        // Apply Scheme Type filter
        if (selectedSchemeType) {
            filteredRows = filteredRows.filter(row => {
                return row.getAttribute('data-scheme-type') === selectedSchemeType;
            });
        }

        // Apply search filter
        if (trimmedFilterText !== '') {
            filteredRows = filteredRows.filter(row => {
                const fundName = row.cells[0].innerText.trim();
                return fuzzyMatch(fundName, trimmedFilterText);
            });
        }

        // Get the rows to display (limit to numFundsToShow unless showing all)
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
        header.addEventListener("click", function () {
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
    showAllButton.addEventListener("click", function () {
        allFundsShown = true;
        renderTable();
    });

    // Add event listener for filter input
    filterInput.addEventListener("input", function () {
        filterText = this.value;
        allFundsShown = false; // Reset to show limited rows when filtering
        renderTable();
    });

    // Add event listener for PFM filter
    if (pfmFilter) {
        pfmFilter.addEventListener("change", function () {
            selectedPfm = this.value;
            allFundsShown = false;
            renderTable();
        });
    }

    // Add event listener for Tier filter
    if (tierFilter) {
        tierFilter.addEventListener("change", function () {
            selectedTier = this.value;
            allFundsShown = false;
            renderTable();
        });
    }

    // Add event listener for Scheme Type filter
    if (schemeTypeFilter) {
        schemeTypeFilter.addEventListener("change", function () {
            selectedSchemeType = this.value;
            allFundsShown = false;
            renderTable();
        });
    }

    // Hover effect for scheme names
    document.addEventListener('mouseover', function (e) {
        if (e.target.classList.contains('scheme-link')) {
            e.target.textContent = e.target.dataset.fullName;
        }
    });

    document.addEventListener('mouseout', function (e) {
        if (e.target.classList.contains('scheme-link')) {
            e.target.textContent = e.target.dataset.shortName;
        }
    });

    // Default sort by 5Y column (index 9) in descending order
    // Ensure index 9 exists before trying to sort it
    if (headers[9]) {
        const fiveYearHeader = headers[9];
        fiveYearHeader.classList.add("sorted-desc");
        sortTable(9, true, false);
    } else {
        // Fallback: Just render the table if 5Y column doesn't exist
        renderTable();
    }
});