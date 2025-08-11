import { Modal } from './modal.js';

export function openComparisonModal({ imageId, username, userText='', adminText='' }) {
  const content = `
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;">
      <div>
        <h5 style="margin:.25rem 0;color:#28a745;">👤 Usuario ${username? ' ('+username+')':''}</h5>
        <div style="background:#f8f9fa;padding:.6rem;border-radius:6px;border-left:4px solid #28a745;font-family:monospace;white-space:pre-wrap;max-height:260px;overflow:auto;font-size:.7rem;">${escapeHtml(userText)||'N/A'}</div>
        <small style="display:block;margin-top:.25rem;color:#666;font-size:.65rem;">Caracteres: ${(userText||'').length}</small>
      </div>
      <div>
        <h5 style="margin:.25rem 0;color:#dc3545;">👨‍💼 Admin</h5>
        <div style="background:#f8f9fa;padding:.6rem;border-radius:6px;border-left:4px solid #dc3545;font-family:monospace;white-space:pre-wrap;max-height:260px;overflow:auto;font-size:.7rem;">${escapeHtml(adminText)||'N/A'}</div>
        <small style="display:block;margin-top:.25rem;color:#666;font-size:.65rem;">Caracteres: ${(adminText||'').length}</small>
      </div>
    </div>
    <div style="margin-top:1rem;background:#fff3cd;border-left:4px solid #ffc107;padding:.5rem .75rem;border-radius:6px;font-size:.7rem;color:#856404;">
      Revisa diferencias y consolida sólo si el texto del usuario es más preciso.
    </div>`;
  Modal.open({ id:'comparison-modal', title:`🔍 Comparación Detallada ${imageId? ' - Img '+imageId:''}`, content, width:'880px', actions:[{label:'Cerrar', variant:'primary', onClick:({close})=>close()}] });
}

function escapeHtml(str){
  return (str||'').replace(/[&<>"]/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
}
