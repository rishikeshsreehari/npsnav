document.addEventListener("DOMContentLoaded", function () {
    const fundTable = document.getElementById("fundTableBody");
    const headers = document.querySelectorAll("#fundTable th");
    const showAllButton = document.getElementById("showAllButton");
    const filterInput = document.getElementById("filterInput");
    const pfmFilter = document.getElementById("pfmFilter");
    const tierFilter = document.getElementById("tierFilter");
    const schemeTypeFilter = document.getElementById("schemeTypeFilter");
    let rows = Array.from(fundTable.rows);

    let numFundsToShow = 10;
    let allFundsShown = false;
    let filterText = '';
    let selectedPfm = '';
    let selectedTier = '';
    let selectedSchemeType = '';

    // --- NEW: URL Sync Functions ---

    // Function to update the browser URL based on current filter variables
    function updateURL() {
        const params = new URLSearchParams();
        if (filterText) params.set('q', filterText);
        if (selectedPfm) params.set('pfm', selectedPfm);
        if (selectedTier) params.set('tier', selectedTier);
        if (selectedSchemeType) params.set('scheme', selectedSchemeType);

        const newUrl = params.toString() ? `?${params.toString()}` : window.location.pathname;
        window.history.pushState({}, '', newUrl);
    }

    // Function to load filters from the URL query parameters
    function applyFiltersFromURL() {
        const params = new URLSearchParams(window.location.search);
        
        filterText = params.get('q') || '';
        selectedPfm = params.get('pfm') || '';
        selectedTier = params.get('tier') || '';
        selectedSchemeType = params.get('scheme') || '';

        // Update the UI elements to match the URL
        if (filterInput) filterInput.value = filterText;
        if (pfmFilter) pfmFilter.value = selectedPfm;
        if (tierFilter) tierFilter.value = selectedTier;
        if (schemeTypeFilter) schemeTypeFilter.value = selectedSchemeType;

        renderTable();
    }

    // Handle back/forward navigation
    window.addEventListener('popstate', applyFiltersFromURL);

    // --- END NEW Logic ---

    if (window.innerWidth > 768 && filterInput) {
        filterInput.focus();
    }

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

    function renderTable() {
        fundTable.innerHTML = '';
        const trimmedFilterText = filterText.trim();
        let filteredRows = rows;

        if (selectedPfm) {
            filteredRows = filteredRows.filter(row => row.getAttribute('data-pfm') === selectedPfm);
        }
        if (selectedTier) {
            filteredRows = filteredRows.filter(row => row.getAttribute('data-tier') === selectedTier);
        }
        if (selectedSchemeType) {
            filteredRows = filteredRows.filter(row => row.getAttribute('data-scheme-type') === selectedSchemeType);
        }
        if (trimmedFilterText !== '') {
            filteredRows = filteredRows.filter(row => {
                const fundName = row.cells[0].innerText.trim();
                return fuzzyMatch(fundName, trimmedFilterText);
            });
        }

        const rowsToDisplay = allFundsShown ? filteredRows : filteredRows.slice(0, numFundsToShow);
        rowsToDisplay.forEach(row => fundTable.appendChild(row));

        if (filteredRows.length > numFundsToShow && !allFundsShown) {
            showAllButton.style.display = 'block';
        } else {
            showAllButton.style.display = 'none';
        }

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

    function sortTable(columnIndex, isNumeric, ascending) {
        rows.sort((a, b) => {
            let aText = a.cells[columnIndex].innerText.trim();
            let bText = b.cells[columnIndex].innerText.trim();
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
        renderTable();
    }

    headers.forEach((header, index) => {
        header.classList.add('sortable');
        header.addEventListener("click", function () {
            const isNumeric = index !== 0;
            const isAscending = !this.classList.contains("sorted-asc");
            headers.forEach(h => h.classList.remove("sorted-asc", "sorted-desc"));
            this.classList.add(isAscending ? "sorted-asc" : "sorted-desc");
            sortTable(index, isNumeric, isAscending);
        });
    });

    showAllButton.addEventListener("click", function () {
        allFundsShown = true;
        renderTable();
    });

    filterInput.addEventListener("input", function () {
        filterText = this.value;
        allFundsShown = false;
        renderTable();
        updateURL(); // Sync to URL
    });

    if (pfmFilter) {
        pfmFilter.addEventListener("change", function () {
            selectedPfm = this.value;
            allFundsShown = false;
            renderTable();
            updateURL(); // Sync to URL
        });
    }

    if (tierFilter) {
        tierFilter.addEventListener("change", function () {
            selectedTier = this.value;
            allFundsShown = false;
            renderTable();
            updateURL(); // Sync to URL
        });
    }

    if (schemeTypeFilter) {
        schemeTypeFilter.addEventListener("change", function () {
            selectedSchemeType = this.value;
            allFundsShown = false;
            renderTable();
            updateURL(); // Sync to URL
        });
    }

    // Default Sort and Initial Render
    if (headers[9]) {
        const fiveYearHeader = headers[9];
        fiveYearHeader.classList.add("sorted-desc");
        sortTable(9, true, false);
    } else {
        renderTable();
    }

    // Initialize filters from URL on page load
    applyFiltersFromURL();
});