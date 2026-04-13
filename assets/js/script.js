document.addEventListener("DOMContentLoaded", function () {
    const fundTable = document.getElementById("fundTableBody");
    const headers = document.querySelectorAll("#fundTable th");
    const showAllButton = document.getElementById("showAllButton");
    const filterInput = document.getElementById("filterInput");
    const pfmFilter = document.getElementById("pfmFilter");
    const tierFilter = document.getElementById("tierFilter");
    const schemeTypeFilter = document.getElementById("schemeTypeFilter");
    const variantFilter = document.getElementById("variantFilter");
    let rows = Array.from(fundTable.rows);

    let numFundsToShow = 50; // Increased from 10 for better initial display
    let allFundsShown = false;
    let filterText = '';
    let selectedPfm = '';
    let selectedTier = '';
    let selectedSchemeType = '';
    let selectedVariant = '';

    // --- FEATURE #6: KEYBOARD SHORTCUTS ---
    document.addEventListener('keydown', function(e) {
        // Press "/" to focus search (like GitHub, Reddit, etc.)
        if (e.key === '/' && !e.ctrlKey && !e.metaKey && document.activeElement !== filterInput) {
            e.preventDefault();
            filterInput.focus();
            filterInput.select();
        }

        // Press "Esc" to clear search and unfocus
        if (e.key === 'Escape' && document.activeElement === filterInput) {
            filterInput.value = '';
            filterText = '';
            filterInput.blur();
            renderTable();
            updateURL();
        }
    });

    // --- URL Sync Functions ---
    function updateURL() {
        const params = new URLSearchParams();
        if (filterText) params.set('q', filterText);
        if (selectedPfm) params.set('pfm', selectedPfm);
        if (selectedTier) params.set('tier', selectedTier);
        if (selectedSchemeType) params.set('scheme', selectedSchemeType);
        if (selectedVariant) params.set('variant', selectedVariant); // FEATURE #1

        const newUrl = params.toString() ? `?${params.toString()}` : window.location.pathname;
        window.history.pushState({}, '', newUrl);
    }

    function applyFiltersFromURL() {
        const params = new URLSearchParams(window.location.search);

        filterText = params.get('q') || '';
        selectedPfm = params.get('pfm') || '';
        selectedTier = params.get('tier') || '';
        selectedSchemeType = params.get('scheme') || '';
        selectedVariant = params.get('variant') || ''; // FEATURE #1

        // Update the UI elements to match the URL
        if (filterInput) filterInput.value = filterText;
        if (pfmFilter) pfmFilter.value = selectedPfm;
        if (tierFilter) tierFilter.value = selectedTier;
        if (schemeTypeFilter) schemeTypeFilter.value = selectedSchemeType;
        if (variantFilter) variantFilter.value = selectedVariant; // FEATURE #1

        renderTable();
    }

    // Handle back/forward navigation
    window.addEventListener('popstate', applyFiltersFromURL);

    // Auto-focus search on desktop (but not on mobile)
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

    // --- FEATURE #5: PROGRESSIVE LOADING ---
    let renderTimeout = null;
    function renderTable() {
        // Clear any pending render
        if (renderTimeout) {
            clearTimeout(renderTimeout);
        }

        // Show loading state for large datasets
        const shouldShowLoading = rows.length > 100;

        if (shouldShowLoading) {
            fundTable.innerHTML = '<tr><td colspan="10" style="text-align: center; padding: 20px;">Loading...</td></tr>';
        }

        // Use setTimeout to allow UI to update
        renderTimeout = setTimeout(() => {
            fundTable.innerHTML = '';
            const trimmedFilterText = filterText.trim();
            let filteredRows = rows;

            // Apply all filters
            if (selectedPfm) {
                filteredRows = filteredRows.filter(row => row.getAttribute('data-pfm') === selectedPfm);
            }
            if (selectedTier) {
                filteredRows = filteredRows.filter(row => row.getAttribute('data-tier') === selectedTier);
            }
            if (selectedSchemeType) {
                filteredRows = filteredRows.filter(row => row.getAttribute('data-scheme-type') === selectedSchemeType);
            }
            // FEATURE #1: VARIANT FILTER
            if (selectedVariant) {
                filteredRows = filteredRows.filter(row => row.getAttribute('data-variant') === selectedVariant);
            }
            if (trimmedFilterText !== '') {
                filteredRows = filteredRows.filter(row => {
                    const fundName = row.cells[0].innerText.trim();
                    return fuzzyMatch(fundName, trimmedFilterText);
                });
            }

            const rowsToDisplay = allFundsShown ? filteredRows : filteredRows.slice(0, numFundsToShow);

            // FEATURE #5: Progressive rendering for better perceived performance
            const batchSize = 25;
            let currentIndex = 0;

            function renderBatch() {
                const endIndex = Math.min(currentIndex + batchSize, rowsToDisplay.length);
                for (let i = currentIndex; i < endIndex; i++) {
                    fundTable.appendChild(rowsToDisplay[i]);
                }
                currentIndex = endIndex;

                if (currentIndex < rowsToDisplay.length) {
                    requestAnimationFrame(renderBatch);
                }
            }

            // Start rendering
            if (rowsToDisplay.length > 0) {
                renderBatch();
            }

            // Update "Show All" button
            if (filteredRows.length > numFundsToShow && !allFundsShown) {
                showAllButton.style.display = 'block';
                showAllButton.textContent = `Show All ${filteredRows.length} Funds`;
            } else {
                showAllButton.style.display = 'none';
            }

            // Show "no results" message
            if (filteredRows.length === 0) {
                const noResultsRow = document.createElement('tr');
                const noResultsCell = document.createElement('td');
                noResultsCell.colSpan = headers.length;
                noResultsCell.textContent = 'No matching funds found.';
                noResultsCell.style.textAlign = 'center';
                noResultsRow.appendChild(noResultsCell);
                fundTable.appendChild(noResultsRow);
            }

            // Update result count display
            updateResultCount(filteredRows.length, rowsToDisplay.length);
        }, shouldShowLoading ? 50 : 0);
    }

    // Show result count
    function updateResultCount(total, showing) {
        const existingCount = document.querySelector('.result-count');
        if (existingCount) {
            existingCount.remove();
        }

        if (total > 0) {
            const countDiv = document.createElement('div');
            countDiv.className = 'result-count';
            countDiv.style.cssText = 'margin: 10px 0; font-size: 14px; color: #666;';
            countDiv.textContent = `Showing ${showing} of ${total} funds`;

            const tableContainer = document.querySelector('.table-container');
            tableContainer.insertBefore(countDiv, tableContainer.firstChild);
        }
    }

    // --- FEATURE #7: COLUMN SORTING VISUAL FEEDBACK ---
    // (Already implemented with sorted-asc/sorted-desc classes, enhanced below)

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

            // FEATURE #7: Enhanced visual feedback
            headers.forEach(h => {
                h.classList.remove("sorted-asc", "sorted-desc");
                // Update sort icons
                const icon = h.querySelector('.sort-icon');
                if (icon) icon.textContent = '';
            });

            this.classList.add(isAscending ? "sorted-asc" : "sorted-desc");

            // Update sort icon for active column
            const icon = this.querySelector('.sort-icon');
            if (icon) {
                icon.textContent = isAscending ? ' ▲' : ' ▼';
            }

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
        updateURL();
    });

    if (pfmFilter) {
        pfmFilter.addEventListener("change", function () {
            selectedPfm = this.value;
            allFundsShown = false;
            renderTable();
            updateURL();
        });
    }

    if (tierFilter) {
        tierFilter.addEventListener("change", function () {
            selectedTier = this.value;
            allFundsShown = false;
            renderTable();
            updateURL();
        });
    }

    if (schemeTypeFilter) {
        schemeTypeFilter.addEventListener("change", function () {
            selectedSchemeType = this.value;
            allFundsShown = false;
            renderTable();
            updateURL();
        });
    }

    // FEATURE #1: VARIANT FILTER EVENT LISTENER
    if (variantFilter) {
        variantFilter.addEventListener("change", function () {
            selectedVariant = this.value;
            allFundsShown = false;
            renderTable();
            updateURL();
        });
    }

    // Default Sort: 5Y column descending
    if (headers[9]) {
        const fiveYearHeader = headers[9];
        fiveYearHeader.classList.add("sorted-desc");
        const icon = fiveYearHeader.querySelector('.sort-icon');
        if (icon) icon.textContent = ' ▼';
        sortTable(9, true, false);
    } else {
        renderTable();
    }

    // Initialize filters from URL on page load
    applyFiltersFromURL();

    // --- FEATURE #6: Show keyboard shortcut hint ---
    console.log('💡 Keyboard shortcuts: Press "/" to search, "Esc" to clear');
});
