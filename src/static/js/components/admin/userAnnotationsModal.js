import { Modal } from './modal.js';
import { adminService } from '../../services/adminService.js';

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
  <thead><tr><th style="min-width:50px;">ID</th><th>Imagen</th><th style="min-width:80px;">Imagen ID</th><th style="min-width:220px;text-align:center;">Texto</th><th>Estado</th><th>Actualización</th><th>Acciones</th></tr></thead>
        <tbody>
          ${annotations.map(a=>row(a)).join('')||'<tr><td colspan="7" style="text-align:center;padding:1rem;">Sin anotaciones</td></tr>'}
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
    } else if (btn.dataset.editAnn){
      const annId = parseInt(btn.dataset.editAnn);
      const currentStatus = (btn.dataset.status || 'pending');
      const currentText = decodeURIComponent(btn.dataset.text || '');
      openEditAnnotationModal(annId, currentStatus, currentText);
    }
  });
}

function row(a){
  const correctedText = a.corrected_text || a.annotation_text || '';
  const displayText = correctedText.length>60? correctedText.slice(0,60)+'…':correctedText;
  return `<tr data-ann-id="${a.annotation_id}">
    <td>${a.annotation_id}</td>
    <td><button class="btn btn-secondary btn-sm" data-view-image="${encodeURIComponent(a.image_path)}" data-ocr="${encodeURIComponent(a.initial_ocr_text||'')}">👁️</button></td>
    <td>${a.image_id ?? '-'}</td>
  <td title="${escapeHtml(correctedText)}" style="font-family:monospace;font-size:.7rem;text-align:center;">${escapeHtml(displayText)||'N/A'}</td>
    <td><span class="status-badge status-${a.status}">${a.status}</span></td>
    <td>${a.updated_at? new Date(a.updated_at).toLocaleString():'N/A'}</td>
    <td>
      <button class="btn btn-primary btn-sm" data-edit-ann="${a.annotation_id}" data-status="${a.status}" data-text="${encodeURIComponent(correctedText)}">✏️</button>
      <button class="btn btn-danger btn-sm" data-delete-ann="${a.annotation_id}">🗑️</button>
    </td>
  </tr>`;
}

function escapeHtml(str){
  return str.replace(/[&<>"]/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
}

function openEditAnnotationModal(annotationId, currentStatus, currentText){
  const statuses = ['pending','corrected','approved','discarded'];
  const selectId = `edit-status-${annotationId}`;
  const textId = `edit-text-${annotationId}`;
  const content = `
    <div style="display:flex;flex-direction:column;gap:.75rem;">
      <label for="${selectId}" style="font-weight:600;">Estado</label>
      <select id="${selectId}" style="padding:.4rem .5rem;border:1px solid #e1e5e9;border-radius:6px;">
        ${statuses.map(s=>`<option value="${s}" ${s===currentStatus?'selected':''}>${s}</option>`).join('')}
      </select>
      <label for="${textId}" style="font-weight:600;">Texto corregido</label>
      <textarea id="${textId}" rows="6" style="width:100%;padding:.5rem;border:1px solid #e1e5e9;border-radius:6px;resize:vertical;">${escapeHtml(currentText)}</textarea>
    </div>`;
  const m = Modal.open({ id:`edit-annotation-${annotationId}`, title:`✏️ Editar Anotación ${annotationId}`, content, width:'600px', actions:[
    { label:'Cancelar', variant:'secondary', onClick:({close})=>close() },
    { label:'Guardar', variant:'primary', onClick: async ({close})=>{
        const sel = document.getElementById(selectId);
        const txt = document.getElementById(textId);
        if(!sel || !txt) return;
        const newStatus = sel.value;
        const newText = txt.value;
        try {
          await adminService.updateAnnotation(annotationId, { status: newStatus, corrected_text: newText });
          // Actualizar fila en la tabla
          const tr = document.querySelector(`tr[data-ann-id="${annotationId}"]`);
          if (tr){
            // Texto
            const textCell = tr.querySelector('td:nth-child(4)');
            if (textCell){
              const display = (newText||'').length>60 ? (newText||'').slice(0,60)+'…' : (newText||'');
              textCell.textContent = display || 'N/A';
              textCell.title = newText || '';
              textCell.style.fontFamily='monospace';
              textCell.style.fontSize='.7rem';
              textCell.style.textAlign='center';
            }
            // Estado
            const badge = tr.querySelector('td:nth-child(5) .status-badge');
            if (badge){
              badge.textContent = newStatus;
              badge.className = `status-badge status-${newStatus}`;
            }
            // Fecha
            const dateCell = tr.querySelector('td:nth-child(6)');
            if (dateCell){ dateCell.textContent = new Date().toLocaleString(); }
          }
          close();
        } catch (err) {
          console.error('Admin update annotation failed', err);
          alert('No se pudo actualizar la anotación');
        }
      }
    }
  ]});
  return m;
}
