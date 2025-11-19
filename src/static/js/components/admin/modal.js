// Simple modal factory to standardize creation & lifecycle
// Usage: Modal.open({ id, title, content, actions: [{label, variant, onClick}], width })
// Provides promise-based helpers for confirm dialogs later.

export const Modal = {
  open({ id, title, content, actions = [], width = '600px', onClose } = {}) {
    // If already open with same id remove first
    if (id) {
      const existing = document.getElementById(id);
      if (existing) existing.remove();
    }
    const modal = document.createElement('div');
    modal.className = 'modal mod-modal';
    if (id) modal.id = id;
    modal.style.cssText = 'position:fixed;inset:0;display:flex;align-items:flex-start;justify-content:center;padding:4vh 1rem;z-index:2500;background:rgba(0,0,0,.45);overflow:auto;';

    const card = document.createElement('div');
    card.className = 'modal-content mod-modal-card';
    card.style.cssText = `background:#fff;border-radius:12px;padding:1.25rem 1.5rem;box-shadow:0 10px 35px -10px rgba(0,0,0,.35);width:100%;max-width:${width};position:relative;animation:modFade .25s ease;`;

    card.innerHTML = `
      <div class="mod-modal-header" style="display:flex;align-items:center;justify-content:space-between;gap:1rem;">
        <h3 style="margin:.25rem 0;font-size:1.1rem;">${title || ''}</h3>
        <button class="btn btn-secondary" data-mod-close style="padding:.25rem .5rem;font-size:.8rem;">✕</button>
      </div>
      <div class="mod-modal-body" style="margin-top:.75rem;">${content || ''}</div>
      <div class="mod-modal-footer" style="margin-top:1rem;display:${actions.length?'flex':'none'};gap:.5rem;justify-content:flex-end;flex-wrap:wrap;"></div>
    `;

    modal.appendChild(card);
    document.body.appendChild(modal);
    document.documentElement.style.overflow = 'hidden';

    const footer = card.querySelector('.mod-modal-footer');
    actions.forEach(a => {
      const b = document.createElement('button');
      b.textContent = a.label;
      b.className = `btn ${a.variant?`btn-${a.variant}`:'btn-primary'}`;
      b.addEventListener('click', async () => {
        try { await a.onClick?.({ close: () => Modal.close(modal, onClose) }); } catch(e){ console.error(e); }
      });
      footer.appendChild(b);
    });

    const closeBtn = card.querySelector('[data-mod-close]');
    closeBtn.addEventListener('click', ()=>Modal.close(modal, onClose));

    modal.addEventListener('click', e => { if (e.target === modal) Modal.close(modal, onClose); });
    return modal;
  },
  close(modalElOrId, onClose){
    const el = typeof modalElOrId === 'string' ? document.getElementById(modalElOrId) : modalElOrId;
    if (!el) return;
    el.remove();
    if (!document.querySelector('.mod-modal')) {
      document.documentElement.style.overflow='';
    }
    onClose?.();
  },
  confirm({ title='Confirmación', message='¿Continuar?', acceptLabel='Aceptar', cancelLabel='Cancelar', variant='primary'} = {}){
    return new Promise(resolve => {
      const id = 'mod-confirm-'+Date.now();
      Modal.open({
        id,
        title,
        content:`<p style="line-height:1.4;">${message}</p>`,
        actions:[
          { label: cancelLabel, variant: 'secondary', onClick: ({close}) => { close(); resolve(false);} },
          { label: acceptLabel, variant, onClick: ({close}) => { close(); resolve(true);} }
        ]
      });
    });
  }
};

// Minimal keyframe (only define once)
if (!document.getElementById('mod-modal-styles')){
  const st = document.createElement('style');
  st.id='mod-modal-styles';
  st.textContent = `@keyframes modFade{from{opacity:0;transform:translateY(-8px)}to{opacity:1;transform:translateY(0)}}`;
  document.head.appendChild(st);
}
