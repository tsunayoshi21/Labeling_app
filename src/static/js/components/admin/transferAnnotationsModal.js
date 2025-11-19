import { Modal } from './modal.js';

export function openTransferAnnotationsModal({ fromUser, users = [], onTransfer }) {
  const options = users.filter(u=>u.id!==fromUser.id).map(u=>`<option value="${u.id}">${u.username} (${u.total_assigned} asignadas)</option>`).join('') || '<option value="">Sin destinos</option>';
  const content = `
    <p style="margin:.25rem 0 1rem;">Transferir anotaciones de <strong>${fromUser.username}</strong> a:</p>
    <div class="form-group" style="margin-bottom:1rem;">
      <label style="display:block;font-weight:600;font-size:.75rem;letter-spacing:.5px;">Usuario destino</label>
      <select id="transfer-target-user" style="width:100%;padding:.5rem;border:1px solid #e1e5e9;border-radius:6px;">${options}</select>
    </div>
    <div class="form-group" style="margin-bottom:1rem;">
      <label style="display:block;font-weight:600;font-size:.75rem;letter-spacing:.5px;">Tipos</label>
      <label style="display:flex;align-items:center;gap:.4rem;font-size:.8rem;">
        <input type="checkbox" id="transfer-include-pending" checked> Pendientes
      </label>
      <label style="display:flex;align-items:center;gap:.4rem;font-size:.8rem;margin-top:.25rem;">
        <input type="checkbox" id="transfer-include-reviewed"> Revisadas (corregidas/aprobadas/descartadas)
      </label>
    </div>`;
  Modal.open({ id:'transfer-annotations-modal', title:'↔️ Transferir Anotaciones', content, width:'520px', actions:[
    { label:'Cancelar', variant:'secondary', onClick:({close})=>close() },
    { label:'Transferir', variant:'primary', onClick:({close})=>{
        const to_user_id = parseInt(document.getElementById('transfer-target-user').value);
        const include_pending = document.getElementById('transfer-include-pending').checked;
        const include_reviewed = document.getElementById('transfer-include-reviewed').checked;
        if(!to_user_id) return;
        if(!include_pending && !include_reviewed) return;
        onTransfer?.({ to_user_id, include_pending, include_reviewed });
        close();
    }}
  ]});
}
