(function () {
    function pageRange(current, total) {
        if (total <= 7) return Array.from({ length: total }, (_, index) => index + 1);
        if (current <= 4) return [1, 2, 3, 4, 5, '…', total];
        if (current >= total - 3) return [1, '…', total - 4, total - 3, total - 2, total - 1, total];
        return [1, '…', current - 1, current, current + 1, '…', total];
    }

    function attach(bar) {
        const table = document.getElementById(bar.dataset.paginationFor);
        const info = bar.querySelector('.pagination-info');
        const controls = bar.querySelector('.pagination-controls');
        const pageSize = Number.parseInt(bar.dataset.pageSize, 10);
        if (!table || !info || !controls || !Number.isInteger(pageSize) || pageSize < 1) return;

        let currentPage = 1;
        const allRows = () => Array.from(table.tBodies).flatMap(body => Array.from(body.rows));
        const eligibleRows = () => allRows().filter(row =>
            !row.hidden &&
            row.dataset.paginationFiltered !== 'true' &&
            !row.matches('.empty-row, [data-empty-state], [data-search-empty]')
        );

        function renderControls(totalPages) {
            controls.replaceChildren();
            if (totalPages < 2) return;

            const addButton = (label, page, className, disabled, ariaLabel) => {
                const button = document.createElement('button');
                button.type = 'button';
                button.className = `page-btn ${className || ''}`.trim();
                button.textContent = label;
                button.disabled = disabled;
                if (ariaLabel) button.setAttribute('aria-label', ariaLabel);
                button.addEventListener('click', () => render(page));
                controls.appendChild(button);
            };

            addButton('‹', currentPage - 1, 'page-arrow', currentPage === 1, 'Previous page');
            pageRange(currentPage, totalPages).forEach(page => {
                if (page === '…') {
                    const ellipsis = document.createElement('span');
                    ellipsis.className = 'page-ellipsis';
                    ellipsis.textContent = page;
                    controls.appendChild(ellipsis);
                } else {
                    addButton(String(page), page, page === currentPage ? 'active' : '', false, `Page ${page}`);
                }
            });
            addButton('›', currentPage + 1, 'page-arrow', currentPage === totalPages, 'Next page');
        }

        function render(page) {
            const rows = eligibleRows();
            const total = rows.length;
            const totalPages = Math.ceil(total / pageSize);
            currentPage = totalPages ? Math.max(1, Math.min(page, totalPages)) : 1;
            const start = (currentPage - 1) * pageSize;
            const end = Math.min(start + pageSize, total);
            const visibleRows = new Set(rows.slice(start, end));

            allRows().forEach(row => {
                if (row.matches('.empty-row, [data-empty-state], [data-search-empty]')) return;
                const visible = visibleRows.has(row);
                row.dataset.paginationPageHidden = visible ? 'false' : 'true';
                row.style.display = visible ? '' : 'none';
            });

            info.textContent = total
                ? `Showing ${start + 1}–${end} of ${total} results`
                : 'No results';
            renderControls(totalPages);
        }

        bar.refresh = () => render(1);
        render(1);
    }

    function initialize() {
        document.querySelectorAll('.pagination-bar[data-pagination-for]').forEach(attach);
    }

    window.GWSTablePagination = { initialize };
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initialize);
    } else {
        initialize();
    }
})();
