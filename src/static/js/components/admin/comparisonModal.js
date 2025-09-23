import { Modal } from './modal.js';

export function openComparisonModal({ imageId, username, userText='', adminText='', initialOcrText='', imagePath='' }) {
  const fileName = imagePath ? decodeURIComponent(imagePath).split('/').pop() : '';
  const ocrBlock = `
    <div style="background:#f8fafc;border:1px solid #e5e7eb;border-radius:8px;padding:.5rem .75rem;">
      <div style="display:flex;align-items:center;gap:.5rem;color:#0b5ed7;font-weight:600;margin-bottom:.35rem;">🅾️ OCR inicial
        <small style="color:#6b7280;font-weight:400;">(${(initialOcrText||'').length} caracteres)<\/small>
      <\/div>
  <div style="background:#fff;padding:.5rem;border-radius:6px;font-family:monospace;white-space:pre-wrap;max-height:100px;overflow:auto;font-size:.7rem;color:#374151;border:1px dashed #e5e7eb;">${escapeHtml(initialOcrText)||'N/A'}<\/div>
    <\/div>`;

  const imageBlock = fileName ? `
    <div style="margin-top:.5rem;">
      <div id="cmp-zoom-controls" style="display:flex;justify-content:center;gap:.5rem;align-items:center;margin:.25rem 0 .5rem 0;">
        <button type="button" id="cmp-zoom-out" style="padding:.25rem .5rem;border:1px solid #d1d5db;border-radius:6px;background:#fff;">–<\/button>
        <span id="cmp-zoom-label" style="min-width:3ch;text-align:center;color:#374151;font-size:.8rem;">90%<\/span>
        <button type="button" id="cmp-zoom-in" style="padding:.25rem .5rem;border:1px solid #d1d5db;border-radius:6px;background:#fff;">+<\/button>
        <button type="button" id="cmp-zoom-reset" title="Ajuste" style="padding:.25rem .5rem;border:1px solid #d1d5db;border-radius:6px;background:#fff;">100%<\/button>
        <button type="button" id="cmp-zoom-fit" style="padding:.25rem .5rem;border:1px solid #d1d5db;border-radius:6px;background:#fff;">Ajustar<\/button>
      <\/div>
  <div id="cmp-img-container" style="text-align:center;height:20vh;max-height:60vh;border:1px solid #e5e7eb;border-radius:6px;box-shadow:0 1px 6px rgba(0,0,0,.06) inset;overflow:auto;background:#fff;display:flex;align-items:center;justify-content:center;">
        <img id="cmp-img" src="/images/${fileName}" alt="Imagen ${imageId||''}" style="display:block;max-width:none;max-height:none;width:auto;height:auto;transform-origin:center center;object-fit:contain;" onerror="this.style.display='none';this.nextElementSibling.style.display='block';" />
        <div style="display:none;color:#666;font-size:.8rem;margin-top:.5rem;">❌ No se pudo cargar la imagen<\/div>
      <\/div>
    <\/div>` : '';

  const content = `
    <div style="display:flex;flex-direction:column;gap:1rem;">
      ${ocrBlock}
      <div style="display:grid;grid-template-columns:1fr 1fr;gap:1rem;align-items:start;">
        <div>
          <h5 style="margin:.1rem 0 .35rem 0;color:#16a34a;font-weight:600;font-size:.9rem;">👤 Usuario${username? ' · '+escapeHtml(username):''}<\/h5>
          <div style="background:#f9fafb;padding:.6rem;border-radius:6px;border:1px solid #e5e7eb;font-family:monospace;white-space:pre-wrap;max-height:180px;overflow:auto;font-size:.78rem;">${escapeHtml(userText)||'N/A'}<\/div>
          <small style="display:block;margin-top:.25rem;color:#6b7280;font-size:.65rem;">${(userText||'').length} caracteres<\/small>
        <\/div>
        <div>
          <h5 style="margin:.1rem 0 .35rem 0;color:#dc2626;font-weight:600;font-size:.9rem;">👨‍💼 Admin<\/h5>
          <div style="background:#f9fafb;padding:.6rem;border-radius:6px;border:1px solid #e5e7eb;font-family:monospace;white-space:pre-wrap;max-height:180px;overflow:auto;font-size:.78rem;">${escapeHtml(adminText)||'N/A'}<\/div>
          <small style="display:block;margin-top:.25rem;color:#6b7280;font-size:.65rem;">${(adminText||'').length} caracteres<\/small>
        <\/div>
      <\/div>
      <div style="background:#fffbea;border:1px solid #fef3c7;border-left:4px solid #f59e0b;padding:.5rem .75rem;border-radius:6px;font-size:.75rem;color:#92400e;">
        Revisa diferencias y consolida sólo si el texto del usuario es más preciso.
      <\/div>
      ${imageBlock}
      ${fileName?`<div style=\"text-align:center;margin-top:-.25rem;\"><a href=\"/images/${fileName}\" target=\"_blank\" style=\"color:#2563eb;font-size:.8rem;\">Abrir imagen en pestaña nueva ↗︎<\/a><\/div>`:''}
    <\/div>`;
  Modal.open({ id:'comparison-modal', title:`🔍 Comparación Detallada ${imageId? ' · Img '+imageId:''}`, content, width:'50vw', actions:[{label:'Cerrar', variant:'primary', onClick:({close})=>close()}] });

  // Zoom controls wiring (fit to container with adjustable scale)
  setTimeout(()=>{
    const modal = document.getElementById('comparison-modal');
    if(!modal) return;
    const img = modal.querySelector('#cmp-img');
    const cont = modal.querySelector('#cmp-img-container');
    const lbl = modal.querySelector('#cmp-zoom-label');
    const btnIn = modal.querySelector('#cmp-zoom-in');
    const btnOut = modal.querySelector('#cmp-zoom-out');
    const btnReset = modal.querySelector('#cmp-zoom-reset');
    const btnFit = modal.querySelector('#cmp-zoom-fit');
    if(!img || !cont) return;
    let fit = 1;
    let scale = 1;
  const clamp = v => Math.min(fit*4, Math.max(fit*0.05, v));
    const updateLabel = ()=>{ if(lbl) lbl.textContent = Math.round((scale/fit)*100)+'%'; };
    const apply = ()=>{ img.style.transform = `scale(${scale})`; updateLabel(); };
    const computeFit = ()=>{
      const cw = cont.clientWidth || 1; const ch = cont.clientHeight || 1;
      const iw = img.naturalWidth || 1; const ih = img.naturalHeight || 1;
      fit = Math.max(0.01, Math.min(cw/iw, ch/ih));
    };
    const init = ()=>{ computeFit(); scale = clamp(fit*0.9); apply(); };
    if(img.complete) init(); else img.addEventListener('load', init, { once:true });
    btnIn && btnIn.addEventListener('click', ()=>{ scale = clamp(scale + fit*0.1); apply(); });
    btnOut && btnOut.addEventListener('click', ()=>{ scale = clamp(scale - fit*0.1); apply(); });
    btnReset && btnReset.addEventListener('click', ()=>{ scale = clamp(fit); apply(); });
    btnFit && btnFit.addEventListener('click', ()=>{ computeFit(); scale = clamp(fit); apply(); });
    // Keyboard +/- shortcuts
    const keyHandler = (ev)=>{
      const key = ev.key;
      if(key === '+' || key === '=') { ev.preventDefault(); scale = clamp(scale + fit*0.1); apply(); }
      else if(key === '-' || key === '_') { ev.preventDefault(); scale = clamp(scale - fit*0.1); apply(); }
    };
    document.addEventListener('keydown', keyHandler);
    // Recompute on resize
    const onResize = ()=>{ const pct = scale/fit; computeFit(); scale = clamp(fit*pct); apply(); };
    window.addEventListener('resize', onResize);
    // Cleanup on close
    const cleanup = ()=>{ document.removeEventListener('keydown', keyHandler); window.removeEventListener('resize', onResize); };
    // Try to hook into modal close button or general overlay close
    modal.addEventListener('close', cleanup, { once:true });
  }, 0);
}

function escapeHtml(str){
  return (str||'').replace(/[&<>"]/g, c=>({ '&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;' }[c]));
}
