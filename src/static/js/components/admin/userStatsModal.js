import { Modal } from './modal.js';

export function openUserStatsModal({ user, stats }) {
  const completionRate = stats.total > 0 ? ((stats.corrected + stats.approved + stats.discarded) / stats.total * 100).toFixed(1) : 0;
  const content = `
    <div class="user-info-section" style="background:#f8f9fa;padding:.75rem 1rem;border-radius:8px;margin:.5rem 0 1rem;">
      <p style="margin:.25rem 0;"><strong>Usuario:</strong> ${user.username}</p>
      <p style="margin:.25rem 0;"><strong>Rol:</strong> <span class="status-badge ${user.role === 'admin' ? 'status-approved' : 'status-pending'}">${user.role}</span></p>
    </div>
    <div class="stats-grid" style="display:grid;grid-template-columns:repeat(auto-fit,minmax(120px,1fr));gap:.75rem;">
      ${gridStat(stats.total,'Total Asignadas')}
      ${gridStat(stats.pending,'Pendientes')}
      ${gridStat(stats.corrected,'Corregidas')}
      ${gridStat(stats.approved,'Aprobadas')}
      ${gridStat(stats.discarded,'Descartadas')}
      ${gridStat(completionRate+'%','Completado')}
    </div>
  `;
  Modal.open({ id:'user-stats-modal', title:'📊 Estadísticas de '+user.username, content, width:'680px', actions:[{label:'Cerrar', variant:'primary', onClick:({close})=>close()}] });
}

function gridStat(value, label){
  return `<div class="stat-card" style="background:linear-gradient(135deg,#667eea,#764ba2);color:#fff;padding:.75rem;border-radius:10px;text-align:center;display:flex;flex-direction:column;justify-content:center;min-height:90px;">
    <div class="stat-number" style="font-size:1.4rem;font-weight:700;">${value}</div>
    <div class="stat-label" style="font-size:.65rem;letter-spacing:.5px;text-transform:uppercase;margin-top:.25rem;">${label}</div>
  </div>`;
}
