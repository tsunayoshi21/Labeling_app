// Pending list component: renders and handles selection events
// Usage: import { PendingList, setPendingSelectHandler } from './components/pendingList.js'
// setPendingSelectHandler(fn) where fn(annotationId)

let onSelect = null;
export function setPendingSelectHandler(fn) { onSelect = fn; }

export const PendingList = {
  render(pending = [], currentId = null) {
    const container = document.getElementById('pendingTasksPreview');
    if (!container) return;
    if (!pending.length) {
      container.innerHTML = '<div class="pending-item">No hay tareas pendientes</div>';
    } else {
      container.innerHTML = pending.map(t => {
        const isCurrent = t.annotation_id === currentId;
        let statusClass = '';
        if (t.status === 'corrected') statusClass = 'corrected';
        else if (t.status === 'approved') statusClass = 'approved';
        else if (t.status === 'discarded') statusClass = 'discarded';
        const icon = t.status === 'discarded' ? '🗑️' : (t.status === 'approved' || t.status === 'corrected') ? '✓' : '';
        return `<div class="pending-item ${isCurrent ? 'current' : ''} ${statusClass}" data-anno-id="${t.annotation_id}" title="Clic para cargar">${icon} ID: ${t.image_id}</div>`;
      }).join('');
    }
    if (!container.dataset.plBound) {
      container.addEventListener('click', (e) => {
        const item = e.target.closest('.pending-item');
        if (!item) return;
        const id = parseInt(item.getAttribute('data-anno-id'));
        if (id && onSelect) onSelect(id);
      });
      container.dataset.plBound = '1';
    }
  }
};
