document.addEventListener("DOMContentLoaded", function() {
    const fundTable = document.getElementById("fundTableBody");
    const headers = document.querySelectorAll("th");

    // Function to sort table
    function sortTable(columnIndex, isNumeric, ascending) {
        const rows = Array.from(fundTable.rows);
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

        // Append sorted rows back to the table
        rows.forEach(row => fundTable.appendChild(row));
    }

    // Add click event to each header for sorting
    headers.forEach((header, index) => {
        header.classList.add('sortable');
        const sortIcon = header.querySelector('.sort-icon');
        if (!sortIcon) {
            const icon = document.createElement('span');
            icon.classList.add('sort-icon');
            header.appendChild(icon);
        }

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

    // Default sort by 5Y column (index 8) in descending order
    const fiveYearHeader = headers[8]; // 5Y column
    fiveYearHeader.classList.add("sorted-desc");
    sortTable(8, true, false);

    // Set the last updated date
    const lastUpdatedElement = document.getElementById("lastUpdated");
    const now = new Date();
    lastUpdatedElement.textContent = now.toLocaleString();
});