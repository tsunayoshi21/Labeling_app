import { Modal } from './modal.js';

export function openImageViewerModal({ imagePath, initialOcrText='' }) {
  const name = decodeURIComponent(imagePath).split('/').pop();
  const content = `
    <div style="display:flex;flex-direction:column;gap:1rem;">
      <div>
        <h4 style="margin:.25rem 0;font-size:.9rem;">Archivo</h4>
        <code style="background:#f8f9fa;padding:.25rem .5rem;border-radius:4px;display:inline-block;max-width:100%;overflow:hidden;text-overflow:ellipsis;">${name}</code>
      </div>
      <div>
        <h4 style="margin:.25rem 0;font-size:.9rem;">Texto OCR Inicial</h4>
        <div style="background:#f8f9fa;padding:.5rem;border-radius:6px;font-family:monospace;max-height:140px;overflow:auto;font-size:.7rem;">${escapeHtml(initialOcrText)||'N/A'}</div>
      </div>
      <div style="text-align:center;">
        <img src="/images/${name}" alt="Imagen" style="max-width:100%;max-height:420px;border:1px solid #ddd;border-radius:6px;object-fit:contain;" onerror="this.style.display='none';this.nextElementSibling.style.display='block';" />
        <div style="display:none;color:#666;font-size:.8rem;margin-top:.5rem;">❌ No se pudo cargar la imagen</div>
      </div>
    </div>`;
  Modal.open({ id:'image-viewer-modal', title:'🖼️ Visualización', content, width:'780px', actions:[{label:'Cerrar', variant:'primary', onClick:({close})=>close()}] });
}

function escapeHtml(str){
  return (str||'').replace(/[&<>"]/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
}
