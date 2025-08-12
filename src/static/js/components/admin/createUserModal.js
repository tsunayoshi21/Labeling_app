// Component: ensureCreateUserModal
// Garantiza que el modal de creación de usuario exista y tenga sus listeners.
// Uso: import { ensureCreateUserModal } from './createUserModal.js';
//       const modal = ensureCreateUserModal(ui); modal.style.display='block';

export function ensureCreateUserModal(ui){
  // Inyectar estilos una sola vez
  if(!document.getElementById('create-user-modal-styles')){
    const st = document.createElement('style');
    st.id='create-user-modal-styles';
    st.textContent = `
    .cu-modal-card {background:#ffffff; border-radius:18px; padding:1.5rem 1.75rem 1.5rem; width:100%; max-width:520px; box-shadow:0 10px 40px -10px rgba(0,0,0,.25),0 4px 12px -2px rgba(0,0,0,.12); position:relative; font-family:system-ui,-apple-system,Segoe UI,Roboto,Ubuntu,"Helvetica Neue",Arial,sans-serif;}
    .cu-header {display:flex;align-items:center;justify-content:space-between;gap:.75rem;margin:0 0 1rem;}
    .cu-header h3 {margin:0;font-size:1.15rem;font-weight:600;letter-spacing:.3px;display:flex;align-items:center;gap:.5rem;}
    .cu-close-btn {background:transparent;border:0;cursor:pointer;font-size:1rem;line-height:1;color:#555;padding:.35rem;border-radius:6px;transition:background .2s,color .2s;}
    .cu-close-btn:hover{background:#f1f3f5;color:#111;}
    .cu-form {display:flex;flex-direction:column;gap:1rem;}
    .cu-field {display:flex;flex-direction:column;gap:.4rem;}
    .cu-field label {font-size:.72rem;letter-spacing:.5px;font-weight:600;text-transform:uppercase;color:#334155;}
    .cu-field input,.cu-field select {border:1px solid #d0d7df;border-radius:10px;padding:.6rem .75rem;font-size:.85rem;line-height:1.2;background:#fdfdfd;transition:border-color .2s, box-shadow .2s, background .2s;}
    .cu-field input:focus,.cu-field select:focus {outline:none;border-color:#2563eb;box-shadow:0 0 0 3px rgba(37,99,235,.15);background:#fff;}
    .cu-help {font-size:.62rem;color:#667085;line-height:1.3;}
    .cu-actions {display:flex;justify-content:flex-end;gap:.75rem;margin-top:.25rem;}
    .cu-actions .btn {font-size:.75rem;border-radius:8px;padding:.55rem 1rem;}
    .cu-actions .btn.btn-primary {background:linear-gradient(135deg,#2563eb,#1d4ed8);border:1px solid #1d4ed8;}
    .cu-actions .btn.btn-primary:disabled {opacity:.65;cursor:not-allowed;}
    #create-user-error {background:#fdecec;border:1px solid #f6b5b5;color:#b00020;padding:.5rem .75rem;border-radius:8px;font-weight:500;box-shadow:0 1px 2px rgba(0,0,0,.05);} 
    .cu-modal-overlay.modal {backdrop-filter:blur(3px);}
    .cu-badge-role {background:#eef4ff;color:#1d4ed8;font-size:.55rem;font-weight:600;padding:.25rem .5rem;border-radius:999px;letter-spacing:.5px;text-transform:uppercase;}
    @media (max-width:560px){ .cu-modal-card {margin-top:4vh;padding:1.25rem 1.25rem 1.25rem;border-radius:16px;} }
    `;
    document.head.appendChild(st);
  }

  let wrapper = document.getElementById('create-user-modal');
  if(!wrapper){
    wrapper = document.createElement('div');
    wrapper.id = 'create-user-modal';
    wrapper.className = 'modal cu-modal-overlay';
    wrapper.setAttribute('role','dialog');
    wrapper.setAttribute('aria-modal','true');
    wrapper.setAttribute('aria-labelledby','create-user-title');
    wrapper.innerHTML = `
      <div class="modal-content cu-modal-card" role="document">
        <header class="cu-header">
          <h3 id="create-user-title"><span style="display:inline-flex;align-items:center;justify-content:center;width:34px;height:34px;border-radius:10px;background:linear-gradient(135deg,#2563eb,#1d4ed8);color:#fff;font-size:.95rem;">👤</span> Crear Usuario <span class="cu-badge-role">Admin</span></h3>
          <button type="button" class="cu-close-btn" aria-label="Cerrar" data-action="modal-close" data-target="#create-user-modal">✕</button>
        </header>
        <form id="create-user-form" class="cu-form" novalidate>
          <div id="create-user-error" style="display:none;"></div>
          <div class="cu-field">
            <label for="new-username">Usuario</label>
            <input type="text" id="new-username" autocomplete="off" required placeholder="ej: juanperez" />
          </div>
          <div class="cu-field">
            <label for="new-password">Contraseña</label>
            <input type="password" id="new-password" required placeholder="Mínimo 8 caracteres" />
            <span class="cu-help">Debe incluir mayúscula, minúscula y número.</span>
          </div>
          <div class="cu-field">
            <label for="new-role">Rol</label>
            <select id="new-role">
              <option value="annotator">Anotador</option>
              <option value="admin">Administrador</option>
            </select>
          </div>
          <div class="cu-actions">
            <button type="button" class="btn" data-action="modal-close" data-target="#create-user-modal">Cancelar</button>
            <button type="submit" class="btn btn-primary" id="create-user-submit">Crear Usuario</button>
          </div>
        </form>
      </div>`;
    document.body.appendChild(wrapper);

    // Cerrar con ESC + focus trap
    wrapper.addEventListener('keydown', e=>{
      if(e.key==='Escape'){ wrapper.style.display='none'; }
      if(e.key==='Tab'){
        const focusables = wrapper.querySelectorAll('button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])');
        if(!focusables.length) return; const list = Array.from(focusables).filter(el=>!el.disabled && el.offsetParent!==null);
        let idx = list.indexOf(document.activeElement);
        if(e.shiftKey){ if(idx<=0){ list[list.length-1].focus(); e.preventDefault(); } }
        else { if(idx===list.length-1){ list[0].focus(); e.preventDefault(); } }
      }
    });
  }
  // (Re)Bind submit si no está aún
  const form = wrapper.querySelector('#create-user-form');
  if(form && !form.dataset.modBound){
    const errBox = form.querySelector('#create-user-error');
    const submitBtn = form.querySelector('#create-user-submit');
    const showErr = (msg)=>{ if(!errBox) return; if(!msg){ errBox.style.display='none'; errBox.textContent=''; return; } errBox.textContent=msg; errBox.style.display='block'; };
    const validatePassword = (pwd)=>{
      if(pwd.length < 8) return 'Contraseña: mínimo 8 caracteres';
      if(!/[a-z]/.test(pwd)) return 'Contraseña: falta minúscula';
      if(!/[A-Z]/.test(pwd)) return 'Contraseña: falta mayúscula';
      if(!/\d/.test(pwd)) return 'Contraseña: falta número';
      return null;
    };
    form.addEventListener('submit', async ev => {
      ev.preventDefault();
      showErr('');
      const username = document.getElementById('new-username').value.trim();
      const password = document.getElementById('new-password').value.trim();
      const role = document.getElementById('new-role').value;
      if(!username||!password){ showErr('Campos requeridos'); ui?.showError?.('Campos requeridos'); return; }
      const pwdErr = validatePassword(password); if(pwdErr){ showErr(pwdErr); ui?.showError?.(pwdErr); return; }
      submitBtn.disabled = true; submitBtn.textContent='Creando...';
      try {
        await window.adminController.createUser({ username, password, role });
        wrapper.style.display='none';
        form.reset();
      } catch(e){
        const msg = e?.message || 'Error creando usuario';
        showErr(msg); ui?.showError?.(msg);
      } finally { submitBtn.disabled=false; submitBtn.textContent='Crear Usuario'; }
    });
    // Autofocus al abrir (cuando se crea por primera vez)
    setTimeout(()=>{ const first = form.querySelector('#new-username'); if(first) first.focus(); }, 50);
    form.dataset.modBound='1';
  }
  return wrapper;
}
