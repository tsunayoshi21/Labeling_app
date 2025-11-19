// Componente para manejar indicador de estado de transcripción
// Usage: import { StatusIndicator } from './components/statusIndicator.js';
// StatusIndicator.render(task, transcriptionDisplayElement)

export const StatusIndicator = {
  render(task, displayEl) {
    if (!displayEl) return;
    const container = displayEl.parentElement;
    if (!container) return;
    container.querySelectorAll('.status-indicator').forEach(el => el.remove());
    displayEl.style.color=''; displayEl.style.fontWeight=''; displayEl.style.textDecoration='';
    if (!task?.status) return;
    const map = {
      discarded: { text: '🗑️ Imagen Descartada', color:'#e74c3c', deco:'line-through' },
      corrected: { text: '✓ Texto Corregido', color:'#27ae60' },
      approved: { text: '✓ Texto Aprobado', color:'#3498db' }
    };
    const cfg = map[task.status];
    if (!cfg) return;
    const indicator = document.createElement('div');
    indicator.className = `status-indicator ${task.status}-indicator`;
    indicator.style.cssText = `color:${cfg.color};font-size:.8rem;font-weight:bold;margin-bottom:5px;`;
    indicator.textContent = cfg.text;
    container.insertBefore(indicator, displayEl);
    displayEl.style.color = cfg.color;
    displayEl.style.fontWeight = 'bold';
    if (cfg.deco) displayEl.style.textDecoration = cfg.deco;
  }
};
