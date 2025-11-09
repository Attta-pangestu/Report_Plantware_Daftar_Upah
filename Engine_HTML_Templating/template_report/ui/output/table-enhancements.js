// Tooltip and truncation detection for payroll table
// - Adds 'truncated' class and a title/data-tooltip for cells whose content overflows
// - Displays a floating tooltip near the cursor when hovering truncated cells

(function () {
  function initTooltip() {
    let tooltip = document.getElementById('cell-tooltip');
    if (!tooltip) {
      tooltip = document.createElement('div');
      tooltip.id = 'cell-tooltip';
      document.body.appendChild(tooltip);
    }
    return tooltip;
  }

  function scanAndMarkTruncation(table) {
    const cells = table.querySelectorAll('th, td');
    cells.forEach((cell) => {
      // force a reflow read then mark if overflowing
      const isOverflowing = cell.scrollWidth > cell.clientWidth;
      if (isOverflowing) {
        const text = (cell.getAttribute('data-tooltip') || cell.textContent || '').trim();
        cell.classList.add('truncated');
        if (!cell.getAttribute('title')) cell.setAttribute('title', text);
        cell.setAttribute('data-tooltip', text);
      } else {
        cell.classList.remove('truncated');
      }
    });
  }

  function attachHoverHandlers(table, tooltip) {
    const cells = table.querySelectorAll('th, td');
    cells.forEach((cell) => {
      cell.addEventListener('mouseenter', (e) => {
        if (!cell.classList.contains('truncated')) return;
        tooltip.textContent = cell.getAttribute('data-tooltip') || cell.textContent.trim();
        tooltip.style.display = 'block';
      });
      cell.addEventListener('mousemove', (e) => {
        if (tooltip.style.display !== 'block') return;
        const x = e.clientX + 14;
        const y = e.clientY + 14;
        tooltip.style.left = x + 'px';
        tooltip.style.top = y + 'px';
      });
      cell.addEventListener('mouseleave', () => {
        tooltip.style.display = 'none';
      });
    });
  }

  function init() {
    const table = document.querySelector('table.payroll-table');
    if (!table) return;
    const tooltip = initTooltip();
    scanAndMarkTruncation(table);
    attachHoverHandlers(table, tooltip);

    // Re-scan after window resize to reflect new truncation states
    let resizeTimer;
    window.addEventListener('resize', () => {
      clearTimeout(resizeTimer);
      resizeTimer = setTimeout(() => scanAndMarkTruncation(table), 120);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', init);
  } else {
    init();
  }
})();

