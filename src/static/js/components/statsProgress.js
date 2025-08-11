// Stats & Progress component
// Usage: StatsProgress.render(stats)
// Expects elements with ids: totalTasks, pendingTasks, correctedTasks, approvedTasks, discardedTasks, progressBar

export const StatsProgress = {
  previous: {},
  render(stats = {}) {
    const map = [
      ['totalTasks','total'],
      ['pendingTasks','pending'],
      ['correctedTasks','corrected'],
      ['approvedTasks','approved'],
      ['discardedTasks','discarded']
    ];
    map.forEach(([elId, key]) => {
      const el = document.getElementById(elId);
      if (!el) return;
      const val = stats[key] ?? '-';
      if (this.previous[key] !== undefined && this.previous[key] !== val && el.closest) {
        const statContainer = el.closest('.stat');
        if (statContainer) {
          statContainer.classList.remove('highlight');
          // force reflow
            // eslint-disable-next-line no-unused-expressions
          statContainer.offsetHeight;
          statContainer.classList.add('highlight');
          setTimeout(()=> statContainer.classList.remove('highlight'), 1000);
        }
      }
      el.textContent = val;
    });
    this.previous = { ...stats };

    const progressBar = document.getElementById('progressBar');
    if (progressBar) {
      const total = stats.total || 0;
      const completed = (stats.corrected||0)+(stats.approved||0)+(stats.discarded||0);
      const pct = total ? Math.round(completed/total*100) : 0;
      progressBar.style.width = pct + '%';
      progressBar.textContent = pct + '%';
    }
  }
};
