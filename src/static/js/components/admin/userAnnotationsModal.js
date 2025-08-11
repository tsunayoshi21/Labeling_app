import { Modal } from './modal.js';

export function openUserAnnotationsModal({ userId, username, annotations = [], onDelete, onBulkDelete, onViewImage }) {
  const counts = {
    pending: annotations.filter(a=>a.status==='pending').length,
    reviewed: annotations.filter(a=>['corrected','approved','discarded'].includes(a.status)).length
  };
  const content = `
    <div class="management-actions" style="border-left:4px solid #667eea;background:#f8f9fa;padding:.75rem 1rem;border-radius:8px;margin:0 0 1rem;">
      <h4 style="margin:.25rem 0 .5rem;">Acciones Masivas</h4>
      <div style="display:flex;flex-wrap:wrap;gap:.5rem;">
        <button class="btn btn-warning btn-sm" data-ann-bulk="pending">🗑️ Pendientes (${counts.pending})</button>
        <button class="btn btn-danger btn-sm" data-ann-bulk="reviewed">🗑️ Revisadas (${counts.reviewed})</button>
        <button class="btn btn-danger btn-sm" data-ann-bulk="all">🗑️ Todas (${annotations.length})</button>
      </div>
    </div>
    <div class="annotations-list" style="border:1px solid #e1e5e9;border-radius:8px;max-height:360px;overflow:auto;">
      <table class="table" style="margin:0;">
        <thead><tr><th style="min-width:50px;">ID</th><th>Imagen</th><th style="min-width:220px;">Texto</th><th>Estado</th><th>Actualización</th><th>Acciones</th></tr></thead>
        <tbody>
          ${annotations.map(a=>row(a)).join('')||'<tr><td colspan="6" style="text-align:center;padding:1rem;">Sin anotaciones</td></tr>'}
        </tbody>
      </table>
    </div>
  `;
  const modal = Modal.open({ id:'annotations-management-modal', title:'📝 Anotaciones - '+username, content, width:'960px', actions:[{label:'Cerrar', variant:'primary', onClick:({close})=>close()}] });

  modal.addEventListener('click', e=>{
    const btn = e.target.closest('button');
    if (!btn) return;
    if (btn.dataset.viewImage){
      onViewImage?.(btn.dataset.viewImage, btn.dataset.ocr || '');
    } else if (btn.dataset.deleteAnn){
      onDelete?.(parseInt(btn.dataset.deleteAnn));
    } else if (btn.dataset.annBulk){
      const type = btn.dataset.annBulk;
      if (type==='pending') onBulkDelete?.(['pending']);
      else if (type==='reviewed') onBulkDelete?.(['corrected','approved','discarded']);
      else onBulkDelete?.(['pending','corrected','approved','discarded']);
    }
  });
}

function row(a){
  const correctedText = a.corrected_text || a.annotation_text || '';
  const displayText = correctedText.length>60? correctedText.slice(0,60)+'…':correctedText;
  return `<tr data-ann-id="${a.annotation_id}">
    <td>${a.annotation_id}</td>
    <td><button class="btn btn-secondary btn-sm" data-view-image="${encodeURIComponent(a.image_path)}" data-ocr="${encodeURIComponent(a.initial_ocr_text||'')}">👁️</button></td>
    <td title="${escapeHtml(correctedText)}" style="font-family:monospace;font-size:.7rem;">${escapeHtml(displayText)||'N/A'}</td>
    <td><span class="status-badge status-${a.status}">${a.status}</span></td>
    <td>${a.updated_at? new Date(a.updated_at).toLocaleString():'N/A'}</td>
    <td><button class="btn btn-danger btn-sm" data-delete-ann="${a.annotation_id}">🗑️</button></td>
  </tr>`;
}

function escapeHtml(str){
  return str.replace(/[&<>"]/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
}
