import { JWT } from '../core/jwt.js';
import { adminService } from '../services/adminService.js';
import { authService } from '../services/authService.js';
import { AdminController, defaultAdminUI } from '../controllers/adminController.js';
import { openUserStatsModal } from '../components/admin/userStatsModal.js';
import { openUserAnnotationsModal } from '../components/admin/userAnnotationsModal.js';
import { openImageViewerModal } from '../components/admin/imageViewerModal.js';
import { openTransferAnnotationsModal } from '../components/admin/transferAnnotationsModal.js';
import { openComparisonModal } from '../components/admin/comparisonModal.js';
import { Modal } from '../components/admin/modal.js';
import { TabController } from '../components/admin/tabs.js';

window.ModAPI = { ...(window.ModAPI||{}), JWT, adminService, authService };

// Segunda fase: añadir gestión modular (listeners delegados + modales)
(async function init() {
  if (!JWT.requireAdminOrRedirect()) return;
  const ui = defaultAdminUI;
  window.adminController = new AdminController({ ui });
  await window.adminController.bootstrap();

  // Inicializar controlador de pestañas (reemplaza showTab legacy)
  window.tabController = new TabController();
  // Enhance tabs with aria attributes
  document.querySelectorAll('.nav-tab[data-tab]').forEach(btn=>{
    const name = btn.dataset.tab; const panel = document.getElementById(name+'-tab');
    if (panel){
      btn.setAttribute('role','tab');
      panel.setAttribute('role','tabpanel');
      btn.setAttribute('aria-controls', panel.id);
      panel.setAttribute('aria-labelledby', btn.id || (btn.id = 'tab-btn-'+name));
    }
  });
  const updateAria = ()=>{
    document.querySelectorAll('.nav-tab[data-tab]').forEach(btn=>{
      const active = btn.classList.contains('active');
      btn.setAttribute('aria-selected', active?'true':'false');
      const panel = document.getElementById(btn.dataset.tab+'-tab');
      if(panel) panel.setAttribute('aria-hidden', active?'false':'true');
    });
  };
  updateAria();
  // Observe class changes to keep aria in sync
  const mo = new MutationObserver(updateAria);
  document.querySelectorAll('.nav-tab').forEach(el=>mo.observe(el,{attributes:true,attributeFilter:['class']}));

  // Eliminado binding directo de logout; ahora se maneja via data-action="logout"

  // Delegated top bar actions
  document.body.addEventListener('click', async (e)=>{
    const el = e.target.closest('[data-action]'); if(!el) return;
    const act = el.dataset.action;
    try {
      switch(act) {
        case 'logout': e.preventDefault(); await window.adminController.logout(); break;
        case 'go-annotator': window.location.href='/'; break;
        case 'open-create-user': document.getElementById('create-user-modal').style.display='block'; break;
        case 'modal-close': { const sel = el.dataset.target; const target = sel?document.querySelector(sel):el.closest('.modal'); if(target) target.style.display='none'; break; }
        case 'quality-refresh': await window.adminController.loadQualityControl(); break;
        case 'assign-auto': {
          const user_id = parseInt(document.getElementById('auto-user-select').value);
          const count = parseInt(document.getElementById('auto-count').value)||0;
          const priority_unannotated = document.querySelector('input[name="priority"]:checked')?.value === 'unannotated';
          if(!user_id) return ui.showError?.('Selecciona usuario');
          if(!count) return ui.showError?.('Cantidad inválida');
          if(!await Modal.confirm({ message:`Asignar automáticamente ${count} imágenes?`, acceptLabel:'Asignar'})) return;
          await window.adminController.createAutoAssignments({ user_id, count, priority_unannotated });
          document.getElementById('auto-user-select').value=''; document.getElementById('auto-count').value='10'; break; }
        // Eliminado: open-create-image (pestaña Imágenes removida)
        default: break;
      }
    } catch(err){ console.error(err); ui.showError?.('Acción falló'); }
  }, { capture:true });

  // Delegation para acciones en tablas y listas
  document.body.addEventListener('click', async (e)=>{
    const btn = e.target.closest('button'); if(!btn) return; const action = btn.dataset.action; if(!action) return;
    try {
      switch(action){
        case 'user-delete': {
          const id = parseInt(btn.dataset.user); if(!await Modal.confirm({message:'¿Eliminar usuario?', acceptLabel:'Eliminar', variant:'danger'})) return; await window.adminController.deleteUser(id); break; }
        case 'user-stats': {
          const id = parseInt(btn.dataset.user); const data = await adminService.userStats(id); openUserStatsModal({ user: data.user, stats: data.stats }); break; }
        case 'user-annotations': {
          const id = parseInt(btn.dataset.user);
          const openAnnotations = async ()=>{
            const data = await window.adminController.loadUserAnnotations(id);
            const username = data.user?.username || (data.annotations?.[0]?.username)||'Usuario';
            openUserAnnotationsModal({
              userId:id,
              username,
              annotations: data.annotations||[],
              onDelete: async (annId)=>{ if(!await Modal.confirm({message:'¿Eliminar anotación?', acceptLabel:'Eliminar', variant:'danger'})) return; await window.adminController.deleteUserAnnotation(id, annId); await openAnnotations(); },
              onBulkDelete: async (statuses)=>{ if(!await Modal.confirm({message:`¿Eliminar ${statuses.length} estados seleccionados?`, acceptLabel:'Eliminar', variant:'danger'})) return; await window.adminController.bulkDeleteUserAnnotations(id, statuses); await openAnnotations(); },
              onViewImage: (encPath, encOcr)=>{ openImageViewerModal({ imagePath: decodeURIComponent(encPath), initialOcrText: decodeURIComponent(encOcr) }); }
            });
          };
          await openAnnotations();
          break; }
        case 'user-transfer': {
          const id = parseInt(btn.dataset.user); const fromUser = window.adminController.users.find(u=>u.id===id); openTransferAnnotationsModal({ fromUser, users: window.adminController.users, onTransfer: async (opts)=>{ await window.adminController.transferAnnotations(id, opts); } }); break; }
        // Eliminadas: image-annotations, qc-view-image y qc-compare se mantienen para calidad.
        case 'qc-consolidate': {
          const ua = parseInt(btn.dataset.userAnnotation); const aa = parseInt(btn.dataset.adminAnnotation); if(!await Modal.confirm({message:'¿Consolidar anotación usando texto de usuario?', acceptLabel:'Consolidar'})) return; await window.adminController.consolidateQuality(ua, aa); break; }
        case 'qc-view-image': {
          const path = decodeURIComponent(btn.dataset.path||''); const ocr = decodeURIComponent(btn.dataset.ocr||''); openImageViewerModal({ imagePath: path, initialOcrText: ocr }); break; }
        case 'qc-compare': {
          const uTxt = decodeURIComponent(btn.dataset.userText||'');
            const aTxt = decodeURIComponent(btn.dataset.adminText||'');
            openComparisonModal({ userText:uTxt, adminText:aTxt });
            break; }
        default: break;
      }
    } catch(err){ console.error(err); ui.showError?.('Acción falló'); }
  });

  // Formularios creación usuario / asignaciones (provisional extracción)
  const createUserForm = document.getElementById('create-user-form');
  if (createUserForm && !createUserForm.dataset.modBound){
    createUserForm.addEventListener('submit', async ev => {
      ev.preventDefault();
      const username = document.getElementById('new-username').value.trim();
      const password = document.getElementById('new-password').value.trim();
      const role = document.getElementById('new-role').value;
      if(!username||!password) return ui.showError?.('Campos requeridos');
      await window.adminController.createUser({ username, password, role });
      document.getElementById('create-user-modal').style.display='none';
      createUserForm.reset();
    });
    createUserForm.dataset.modBound='1';
  }

  // User search filter & counters
  const userSearch = document.getElementById('user-search');
  if(userSearch){
    userSearch.addEventListener('input', ()=>{
      const q = userSearch.value.trim().toLowerCase();
      document.querySelectorAll('#users-table tbody tr').forEach(tr=>{
        const name = tr.children[1]?.textContent.toLowerCase()||'';
        tr.style.display = !q || name.includes(q) ? '' : 'none';
      });
    });
  }

  const updateUserCounters = ()=>{
    const rows = Array.from(document.querySelectorAll('#users-table tbody tr'));
    const total = rows.length;
    let admins=0, annotators=0;
    rows.forEach(r=>{ const role = (r.querySelector('td:nth-child(3)')?.textContent||'').trim(); if(role==='admin') admins++; else annotators++; });
    const set = (id,val)=>{ const el=document.getElementById(id); if(el) el.textContent=val; };
    set('user-count-total', total); set('user-count-annotators', annotators); set('user-count-admins', admins);
  };
  document.addEventListener('users:updated', updateUserCounters);
  const observer = new MutationObserver(updateUserCounters);
  const usersTbody = document.querySelector('#users-table tbody');
  if(usersTbody){ observer.observe(usersTbody,{ childList:true, subtree:false }); }
  updateUserCounters();

  const applyUserFilters = ()=>{
    const roleActive = document.querySelector('.filter-chip.active')?.dataset.filterRole||'all';
    const q = (document.getElementById('user-search')?.value||'').trim().toLowerCase();
    document.querySelectorAll('#users-table tbody tr').forEach(tr=>{
      const name = tr.children[1]?.textContent.toLowerCase()||'';
      const role = (tr.querySelector('td:nth-child(3)')?.textContent||'').trim();
      const matchesRole = roleActive==='all' || role===roleActive;
      const matchesQ = !q || name.includes(q);
      tr.style.display = (matchesRole && matchesQ)?'':'none';
    });
  };
  document.addEventListener('click', e=>{
    const chip = e.target.closest('.filter-chip'); if(!chip) return;
    document.querySelectorAll('.filter-chip').forEach(c=>c.classList.remove('active'));
    chip.classList.add('active');
    applyUserFilters();
  });
  if(document.getElementById('user-search')) document.getElementById('user-search').addEventListener('input', applyUserFilters);
  document.addEventListener('users:updated', applyUserFilters);

  const refreshAssignmentQuickStats = ()=>{
    const stats = window.adminController?.stats; if(!stats) return;
    const total = stats.total_images ?? '-';
    const unann = stats.unannotated_images ?? '-';
    const progress = stats.progress_percentage!=null ? stats.progress_percentage+'%' : '-';
    const set=(id,val)=>{ const el=document.getElementById(id); if(el) el.textContent=val; };
    set('a-total', total); set('a-unannotated', unann); set('a-progress', progress);
  };
  document.addEventListener('stats:updated', refreshAssignmentQuickStats);
  // Hook dentro de updateStats (adapter) emite evento; añadimos parche si aún no existe
  const origUpdateStats = window.adminController.ui.updateStats;
  window.adminController.ui.updateStats = (s)=>{ origUpdateStats.call(window.adminController.ui,s); document.dispatchEvent(new Event('stats:updated')); };
  // Inicial intento tras bootstrap diferido
  setTimeout(refreshAssignmentQuickStats,800);

  // Ejecutar al final
  refreshAssignmentQuickStats();
})();
