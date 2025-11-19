// AdminController - primera fase de migración modular del panel admin
// Objetivo: ir sacando lógica de carga de datos y logout del script legacy enorme.
// Incremental: stats generales, actividad reciente y (fase 2) gestión usuarios / asignaciones / control calidad.

import { adminService } from '../services/adminService.js';
import { authService } from '../services/authService.js';
import { JWT } from '../core/jwt.js';

export class AdminController {
  constructor({ ui }) {
    this.ui = ui;
    this.stats = null;
    this.activity = [];
    this.agreement = null;
    this.users = [];
    this.userSort = { field: 'id', direction: 'asc' };
    // Eliminado: this.images (pestaña Imágenes removida)
    this.quality = [];
  }

  async bootstrap() {
    if (!JWT.requireAdminOrRedirect()) return;
    await Promise.all([
      this.loadStats(),
      this.loadRecentActivity(),
      this.loadAgreementStats().catch(()=>{}),
    ]);
    // Fase 2: cargar modulos extra de forma diferida para no bloquear primer paint
    setTimeout(()=>{
      this.safeLoadUsers();
      // Eliminado: this.safeLoadImages();
      this.safeLoadQualityControl();
    }, 0);
  }

  // Helpers seguros para evitar errores si endpoints no están listos
  async safeLoadUsers(){ try { await this.loadUsers(); } catch(e){ console.warn('Users load (mod) fallo', e);} }
  // Eliminado: safeLoadImages
  async safeLoadQualityControl(){ try { await this.loadQualityControl(); } catch(e){ console.warn('Quality load (mod) fallo', e);} }

  // ============== STATS & ACTIVITY ==============
  async loadStats() {
    try {
      const data = await adminService.generalStats();
      this.stats = data;
      this.ui.updateStats?.(data);
    } catch (e) { this.ui.showError?.('Error cargando stats'); console.error(e); }
  }

  async loadRecentActivity() {
    try {
      const data = await adminService.recentActivity();
      this.activity = data.recent_activity || [];
      this.ui.updateRecentActivity?.(this.activity);
    } catch (e) { this.ui.showError?.('Error actividad'); console.error(e); }
  }

  async loadAgreementStats() {
    try {
      const data = await adminService.agreementStats();
      this.agreement = data.agreement_stats || {};
      this.ui.updateAgreement?.(this.agreement);
      // si ya tenemos usuarios, actualizar celdas
      if (this.users.length) {
        if (['agreement','comparisons'].includes(this.userSort?.field)) {
          this.applyUserSort();
          this.ui.updateUsers?.(this.users, this.agreement);
          this.ui.updateAssignmentUsers?.(this.users);
        } else {
          this.ui.updateUsersAgreement?.(this.agreement);
        }
      }
    } catch (e) { console.warn('Agreement stats no disponibles aún'); }
  }

  // ============== USERS MANAGEMENT ==============
  async loadUsers() {
    const data = await adminService.listUsers();
    this.users = data.users || [];
    this.applyUserSort();
    this.ui.updateUsers?.(this.users, this.agreement);
    this.ui.updateAssignmentUsers?.(this.users);
  }

  async createUser({ username, password, role }) {
    await adminService.createUser({ username, password, role });
    await this.loadUsers();
    this.ui.toast?.('Usuario creado');
  }

  async deleteUser(userId) {
    await adminService.deleteUser(userId);
    this.users = this.users.filter(u=>u.id!==userId);
    this.applyUserSort();
    this.ui.updateUsers?.(this.users, this.agreement);
    await this.loadStats();
    this.ui.toast?.('Usuario eliminado');
  }

  async transferAnnotations(fromUserId, opts){
    await adminService.transferAnnotations(fromUserId, opts);
    await this.loadUsers();
    this.ui.toast?.('Transferencia completada');
  }

  async loadUserAnnotations(userId){
    return adminService.userAnnotations(userId); // UI abre modal
  }

  async bulkDeleteUserAnnotations(userId, statuses){
    await adminService.bulkDeleteUserAnnotations(userId, statuses);
    await this.loadUsers();
    this.ui.toast?.('Anotaciones eliminadas');
  }

  async deleteUserAnnotation(userId, annotationId){
    await adminService.deleteUserAnnotation(userId, annotationId);
    await this.loadUsers();
    this.ui.toast?.('Anotación eliminada');
  }

  applyUserSort(){
    if (!Array.isArray(this.users) || !this.users.length || !this.userSort) return;
    const { field, direction } = this.userSort;
    const dir = direction === 'desc' ? -1 : 1;
    const agreementStats = this.agreement || {};
    const compareNumbers = (a,b)=>{
      if (a === b) return 0;
      return a > b ? 1 : -1;
    };
    this.users.sort((userA, userB)=>{
      switch(field){
        case 'username': {
          const nameA = (userA.username || '').toLocaleLowerCase('es-ES');
          const nameB = (userB.username || '').toLocaleLowerCase('es-ES');
          return nameA.localeCompare(nameB, 'es-ES') * dir;
        }
        case 'agreement': {
          const pctA = agreementStats[userA.id]?.agreement_percentage ?? -1;
          const pctB = agreementStats[userB.id]?.agreement_percentage ?? -1;
          return compareNumbers(pctA, pctB) * dir;
        }
        case 'comparisons': {
          const compA = agreementStats[userA.id]?.total_comparisons ?? -1;
          const compB = agreementStats[userB.id]?.total_comparisons ?? -1;
          return compareNumbers(compA, compB) * dir;
        }
        case 'id':
        default: {
          const idA = Number(userA.id) || 0;
          const idB = Number(userB.id) || 0;
          return compareNumbers(idA, idB) * dir;
        }
      }
    });
  }

  sortUsers(field){
    if (!field) return;
    if (!this.userSort) this.userSort = { field: 'id', direction: 'asc' };
    if (this.userSort.field === field) {
      this.userSort.direction = this.userSort.direction === 'asc' ? 'desc' : 'asc';
    } else {
      const defaultDir = (field === 'agreement' || field === 'comparisons') ? 'desc' : 'asc';
      this.userSort = { field, direction: defaultDir };
    }
    this.applyUserSort();
    this.ui.updateUsers?.(this.users, this.agreement);
    this.ui.updateAssignmentUsers?.(this.users);
  }

  // ============== IMAGES (eliminado) ==============
  // loadImages, createImage e imageAnnotations fueron eliminados junto con la pestaña Imágenes.

  // ============== ASSIGNMENTS ==============
  async createAssignments({ user_ids, image_ids }){
    await adminService.createAssignments({ user_ids, image_ids });
    await Promise.all([this.loadUsers(), this.loadStats()]);
    this.ui.toast?.('Asignaciones creadas');
  }

  async createAutoAssignments(opts){
    await adminService.createAutoAssignments(opts);
    await Promise.all([this.loadUsers(), this.loadStats()]);
    this.ui.toast?.('Asignaciones automáticas creadas');
  }

  // ============== QUALITY CONTROL ==============
  async loadQualityControl(filters){
    const data = await adminService.qualityControl(filters);
    this.quality = data.quality_control_data || [];
    this.ui.updateQualityControl?.(this.quality);
  }

  async consolidateQuality(user_annotation_id, admin_annotation_id){
    try {
      await adminService.consolidateQuality({ user_annotation_id, admin_annotation_id });
      await this.loadQualityControl();
      this.ui.toast?.('Consolidado');
    } catch (e) { this.ui.showError?.('Error consolidando'); }
  }

  // ============== AUTH ==============
  async logout() {
    try { await authService.logout(); } finally { window.location.href = '/login'; }
  }
  // Navegación a vista de anotación (reemplaza goToAnnotation legacy)
  goToAnnotator(){ window.location.href = '/'; }
  // Método placeholder (tabs ahora gestionadas por TabController)
  legacyShowTab(){ /* noop */ }
}

// UI Adapter de referencia rápida (se puede extraer a /components pronto)
export const defaultAdminUI = {
  updateStats(stats) {
    const c = document.getElementById('general-stats');
    if (!c || !stats) return;
    const progressPct = stats.progress_percentage ?? 0;
    const totalTasks = (stats.completed_tasks||0) + (stats.pending_tasks||0);
    const taskCompletionRate = totalTasks? Math.round((stats.completed_tasks||0)*100/totalTasks):0;
    const annotatedImages = stats.annotated_images ?? (stats.total_images && stats.unannotated_images!=null ? (stats.total_images - stats.unannotated_images) : 0);
    const annotatedPct = stats.total_images? Math.round(annotatedImages*100/(stats.total_images||1)):0;
    const avgAnnotationsPerUser = (stats.total_annotations && stats.total_users) ? (stats.total_annotations / (stats.total_users||1)) : 0;

    const metrics = [
      { key:'total_users', label:'Usuarios', value: stats.total_users, cls:'users', icon:'👥' },
      { key:'total_images', label:'Imágenes Totales', value: stats.total_images, cls:'images', icon:'🖼️' },
      { key:'annotated_images', label:'Imágenes Anotadas', value: annotatedImages, cls:'annotated', icon:'✅', extra:`${annotatedPct}%` },
      { key:'unannotated_images', label:'Sin Anotar', value: stats.unannotated_images, cls:'unannotated', icon:'🕒' },
      { key:'total_annotations', label:'Anotaciones Asignadas', value: stats.total_annotations, cls:'assigned', icon:'📝' },
      { key:'pending_tasks', label:'Tareas Pendientes', value: stats.pending_tasks, cls:'pending', icon:'⌛' },
      { key:'completed_tasks', label:'Tareas Completadas', value: stats.completed_tasks, cls:'completed', icon:'🏁' },
      { key:'progress_percentage', label:'Progreso Global', value: progressPct+'%', cls:'progress', icon:'📈' },
      { key:'task_completion_rate', label:'% Tareas Completadas', value: taskCompletionRate+'%', cls:'rate', icon:'⚙️' },
      { key:'avg_annotations_per_user', label:'Prom. Anotaciones / Usuario', value: avgAnnotationsPerUser.toFixed(1), cls:'avg', icon:'📊' }
    ];

    const cardHTML = m=>`<div class="stat-card stat-card--${m.cls}" data-metric="${m.key}">
        <div class="stat-card__icon" aria-hidden="true">${m.icon}</div>
        <div class="stat-card__value">${m.value ?? '-'}</div>
        <div class="stat-card__label">${m.label}${m.extra?` <span class='stat-card__extra'>${m.extra}</span>`:''}</div>
      </div>`;

    c.innerHTML = `
      <section class="stats-dashboard" aria-label="Estadísticas Generales">
        <div class="stats-grid stats-grid--all">${metrics.map(cardHTML).join('')}</div>
        <div class="progress-composite" aria-label="Progreso de anotación">
          <div class="progress-composite__header">
            <h3>Progreso de Anotación</h3>
            <span class="progress-text">${annotatedImages} de ${stats.total_images ?? 0} imágenes (${progressPct}%)</span>
          </div>
          <div class="progress-bar" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${progressPct}">
            <div class="progress-fill" style="width:${progressPct}%">${progressPct}%</div>
          </div>
        </div>
      </section>`;
  },
  updateRecentActivity(activity) {
    const container = document.getElementById('recent-activity');
    if (!container) return;
    if (!activity || activity.length === 0) {
      container.innerHTML = '<div class="activity-empty"><p>No hay actividad reciente<\/p><\/div>';
      return;
    }
    const card = a => {
      const totalAssigned = a.total_assigned || 0;
      const completed = a.completed || 0; // campo correcto para "Revisadas"
      const approved = a.approved || 0;
      const corrected = a.corrected || 0;
      const discarded = a.discarded || 0;
      const completionRate = totalAssigned > 0 ? Math.round((completed / totalAssigned) * 100) : 0;
      const approvedPct = a.approved_pct != null ? a.approved_pct : (completed > 0 ? Math.round(approved * 100 / completed) : 0);
      const correctedPct = a.corrected_pct != null ? a.corrected_pct : (completed > 0 ? Math.round(corrected * 100 / completed) : 0);
      const discardedPct = a.discarded_pct != null ? a.discarded_pct : (completed > 0 ? Math.round(discarded * 100 / completed) : 0);
      const progressColor = completionRate>=100? 'var(--color-success)': completionRate>=60? 'var(--color-primary)': '#ffc107';
      let lastActivityTxt = '';
      if (a.last_activity) {
        const d = new Date(a.last_activity);
        const fecha = d.toLocaleDateString('es-ES',{ day:'2-digit', month:'2-digit', year:'numeric'});
        const hora = d.toLocaleTimeString('es-ES',{ hour:'2-digit', minute:'2-digit'});
        lastActivityTxt = `${fecha} · ${hora}`;
      }
      return `<article class="user-activity-card" data-user-card="${a.user_id}">
        <header class="user-activity-card__header">
          <div class="user-identity"><span class="user-name">${a.username}<\/span>${lastActivityTxt?`<small class="last-activity" aria-label="Última actividad"><span class="last-activity__icon" aria-hidden="true">🕒<\/span>${lastActivityTxt}<\/small>`:''}<\/div>
          <div class="user-progress-badge" style="--pct:${completionRate};"><span>${completionRate}%<\/span><\/div>
        <\/header>
        <div class="metrics-row">
          <div class="metric"><span class="metric__value">${totalAssigned}<\/span><span class="metric__label">Asignadas<\/span></div>
          <div class="metric"><span class="metric__value">${completed}<\/span><span class="metric__label">Revisadas (${completionRate}%)<\/span></div>
          <div class="metric"><span class="metric__value metric--approved">${approved}<\/span><span class="metric__label">Aprobadas (${approvedPct}%)<\/span></div>
          <div class="metric"><span class="metric__value metric--corrected">${corrected}<\/span><span class="metric__label">Corregidas (${correctedPct}%)<\/span></div>
          <div class="metric"><span class="metric__value metric--discarded">${discarded}<\/span><span class="metric__label">Descartadas (${discardedPct}%)<\/span></div>
        <\/div>
        <div class="mini-progress" role="progressbar" aria-valuemin="0" aria-valuemax="100" aria-valuenow="${completionRate}" aria-label="Progreso del usuario" aria-valuetext="${completionRate}% completado"><div class="mini-progress__fill" style="width:${completionRate}%;background:${progressColor}"></div></div>
      <\/article>`;
    };
    container.classList.add('user-activity-grid');
    container.innerHTML = activity.map(card).join('');
  },
  updateUsers(users, agreementStats){
    const tbody = document.querySelector('#users-table tbody');
    if (!tbody) return;
    // Inject styling once for agreement + comparisons + sortable headers
    if(!document.getElementById('agreement-metric-style')){
      const style = document.createElement('style');
      style.id='agreement-metric-style';
  style.textContent = `.users-table-modern thead th[data-sort]{cursor:pointer;user-select:none;position:relative;}
.users-table-modern thead th[data-sort]:after{content:'\\25B4';opacity:0;position:absolute;right:.4rem;font-size:.65rem;transition:opacity .2s, transform .2s;}
.users-table-modern thead th[data-sort][data-direction="desc"]:after{transform:rotate(180deg);}
.users-table-modern thead th[data-sort].is-sorted:after{opacity:.55;}
.users-table-modern td.agreement-cell,.users-table-modern td.comparisons-cell{text-align:center;}
.agreement-metric{display:inline-flex;align-items:center;justify-content:center;font-size:.9rem;font-weight:700;padding:.2rem .65rem;border-radius:999px;min-width:3.1rem;letter-spacing:.3px;transition:background-color .3s,color .3s,border-color .3s;}
.agreement-metric--low{color:#c1121f;background:rgba(220,53,69,.12);border:1px solid rgba(220,53,69,.4);}
.agreement-metric--mid{color:#0a3d62;background:rgba(30,144,255,.12);border:1px solid rgba(30,144,255,.4);}
.agreement-metric--high{color:#0b6b41;background:rgba(25,135,84,.15);border:1px solid rgba(25,135,84,.38);}
.agreement-loading{font-size:.75rem;color:#777;}
.comparisons-metric{display:flex;align-items:center;justify-content:center;font-size:.8rem;font-weight:600;color:#455060;}
@media (prefers-color-scheme: dark){
  .agreement-metric{border-color:transparent;}
  .agreement-metric--low{color:#ff6b81;background:rgba(220,53,69,.28);}
  .agreement-metric--mid{color:#8abaff;background:rgba(30,144,255,.24);}
  .agreement-metric--high{color:#8dffc2;background:rgba(25,135,84,.28);}
  .agreement-loading{color:#9aa8ff;}
  .comparisons-metric{color:#c5cce0;}
}`;
      document.head.appendChild(style);
    }
    const getAgreementTier = pct => {
      if (typeof pct !== 'number' || Number.isNaN(pct)) return '';
      if (pct > 95) return 'agreement-metric--high';
      if (pct >= 90) return 'agreement-metric--mid';
      return 'agreement-metric--low';
    };
    const renderAgreement = (u,aStats)=>{
      if(!aStats){
        return (u.role==='admin') ? 'N/A' : '<span class="agreement-loading" aria-label="Calculando agreement…">…<\/span>';
      }
      const pct = aStats.agreement_percentage;
      const tierClass = getAgreementTier(pct);
      return `<span class="agreement-metric ${tierClass}" aria-label="Agreement ${pct}%">${pct}%<\/span>`;
    };
    const renderComparisons = (u,aStats)=>{
      if(!aStats){
        return (u.role==='admin') ? 'N/A' : '<span class="agreement-loading" aria-label="Calculando comparaciones…">…<\/span>';
      }
      const total = aStats.total_comparisons;
      const agreements = aStats.agreements;
      return `<span class="comparisons-metric" title="Acuerdos / Comparaciones: ${agreements}/${total}" aria-label="${agreements} acuerdos de ${total}">${total}<\/span>`;
    };
    tbody.innerHTML = users.map(u => {
      const aStats = agreementStats && agreementStats[u.id];
      const agreementCellText = renderAgreement(u,aStats);
      const comparisonsCellText = renderComparisons(u,aStats);
      const agreementTitle = aStats
        ? `Agreement: ${aStats.agreement_percentage}% (${aStats.agreements}/${aStats.total_comparisons})`
        : (u.role==='admin' ? 'Usuario admin (no aplica agreement)' : 'Calculando agreement...');
      const comparisonsTitle = aStats
        ? `Comparaciones totales: ${aStats.total_comparisons} (acuerdos: ${aStats.agreements})`
        : (u.role==='admin' ? 'Usuario admin (no aplica comparaciones)' : 'Calculando comparaciones...');
      return `<tr data-user-id="${u.id}">
        <td>${u.id}<\/td>
        <td>${u.username}<\/td>
        <td><span class="status-badge ${u.role==='admin'?'status-approved':'status-pending'}">${u.role}<\/span><\/td>
        <td class="agreement-cell" data-agreement-user="${u.id}" title="${agreementTitle}" aria-label="${agreementTitle}">${agreementCellText}<\/td>
        <td class="comparisons-cell" data-comparisons-user="${u.id}" title="${comparisonsTitle}" aria-label="${comparisonsTitle}">${comparisonsCellText}<\/td>
        <td>
          <div class="action-buttons">
            <button class="btn btn-primary btn-sm" data-action="user-stats" data-user="${u.id}">📊 Stats<\/button>
            <button class="btn btn-secondary btn-sm" data-action="user-annotations" data-user="${u.id}" ${u.role==='admin'?'disabled':''}>📝 Anotaciones<\/button>
            <button class="btn btn-warning btn-sm" data-action="user-transfer" data-user="${u.id}" ${u.role==='admin'?'disabled':''}>↔️ Transferir<\/button>
            <button class="btn btn-danger btn-sm" data-action="user-delete" data-user="${u.id}" ${u.role==='admin'?'disabled':''}>🗑️ Eliminar<\/button>
          <\/div>
        <\/td>
      <\/tr>`; }).join('');
    // update counters if helper exists
    const evt = new CustomEvent('users:updated');
    document.dispatchEvent(evt);
  },
  updateUsersAgreement(agreementStats){
    Object.entries(agreementStats||{}).forEach(([id, st])=>{
      const cell = document.querySelector(`[data-agreement-user="${id}"]`);
      if (cell) {
        const pct = st.agreement_percentage;
        const t = `Agreement: ${pct}% (${st.agreements}/${st.total_comparisons})`;
        const tierClass = (typeof pct === 'number' && !Number.isNaN(pct))
          ? (pct > 95 ? 'agreement-metric--high' : (pct >= 90 ? 'agreement-metric--mid' : 'agreement-metric--low'))
          : '';
        cell.innerHTML = `<span class="agreement-metric ${tierClass}" aria-label="Agreement ${pct}%">${pct}%<\/span>`;
        cell.title = t;
        cell.setAttribute('aria-label', t);
        cell.removeAttribute('data-loading-agreement');
      }
      const compCell = document.querySelector(`[data-comparisons-user="${id}"]`);
      if (compCell) {
        const total = st.total_comparisons;
        const agreements = st.agreements;
        const title = `Comparaciones totales: ${total} (acuerdos: ${agreements})`;
        compCell.innerHTML = `<span class="comparisons-metric" title="Acuerdos / Comparaciones: ${agreements}/${total}" aria-label="${agreements} acuerdos de ${total}">${total}<\/span>`;
        compCell.title = title;
        compCell.setAttribute('aria-label', title);
        compCell.removeAttribute('data-loading-agreement');
      }
    });
  },
  updateAssignmentUsers(users){
    const container = document.getElementById('assignment-users'); // (opcional, fue removido en nuevo diseño)
    const autoSelect = document.getElementById('auto-user-select');
    const annotators = (users||[]).filter(u=>u.role==='annotator');
    if (container) {
      container.innerHTML = annotators.map(u=>`<div class="checkbox-item"><input type="checkbox" id="user-${u.id}" value="${u.id}"><label for="user-${u.id}">${u.username} (${u.total_assigned||0} asignadas, ${u.completed||0} completadas)<\/label><\/div>`).join('');
    }
    if (autoSelect) {
      const prev = autoSelect.value;
      autoSelect.innerHTML = '<option value="">Seleccionar usuario...</option>' + annotators.map(u=>`<option value="${u.id}">${u.username} · ${u.total_assigned||0}/${u.completed||0}<\/option>`).join('');
      if (prev && autoSelect.querySelector(`option[value="${prev}"]`)) autoSelect.value = prev; // mantener selección si existe
    }
  },
  // Eliminados: updateImages, updateAssignmentImages (pestaña Imágenes removida)
  updateQualityControl(items){
    const list = document.getElementById('quality-control-list');
    if (!list) return;
    if (!items.length){
      list.innerHTML = `<div class="message success"><h4>🎉 ¡Excelente!<\/h4><p>No hay discrepancias encontradas.<\/p><\/div>`;
      return;
    }
    list.innerHTML = items.map(it=>{
      const userTxt = encodeURIComponent(it.user_annotation_text||'');
      const adminTxt = encodeURIComponent(it.admin_annotation_text||'');
      const encUser = encodeURIComponent(it.username||'');
      const encPath = encodeURIComponent(it.image_path||'');
      const encOcr = encodeURIComponent(it.initial_ocr_text||'');
      return `<div class="quality-item" data-quality-id="${it.annotation_id}" style="border:1px solid #e1e5e9;border-radius:8px;padding:1rem;margin-bottom:.75rem;background:#fff;">
      <div style="display:grid;grid-template-columns:1fr 2fr 1fr;gap:1rem;align-items:start;">
        <div><h4>📷 Img ${it.image_id}<\/h4><p style=\"font-size:.75rem;color:#555;\"><strong>Anotación ID:<\/strong> ${it.annotation_id}<\/p><button class=\"btn btn-secondary btn-sm\" data-action=\"qc-view-image\" data-path=\"${encodeURIComponent(it.image_path)}\" data-ocr=\"${encodeURIComponent(it.initial_ocr_text||'')}\">👁️ Ver Imagen<\/button><\/div>
        <div style=\"display:grid;grid-template-columns:1fr 1fr;gap:.75rem;\">
          <div><h5 style=\"margin:.25rem 0;color:#28a745;\">👤 ${it.username}<\/h5><div style=\"background:#f8f9fa;padding:.5rem;border-left:4px solid #28a745;font-family:monospace;max-height:120px;overflow:auto;\">${it.user_annotation_text||'N/A'}<\/div><small class=\"status-badge status-${it.user_status}\">${it.user_status}<\/small></div>
            <div><h5 style=\"margin:.25rem 0;color:#dc3545;\">👨‍💼 Admin<\/h5><div style=\"background:#f8f9fa;padding:.5rem;border-left:4px solid #dc3545;font-family:monospace;max-height:120px;overflow:auto;\">${it.admin_annotation_text||'N/A'}<\/div><small class=\"status-badge status-${it.admin_status}\">${it.admin_status}<\/small><small style=\"display:block;font-size:.7rem;color:#6c757d;margin-top:.25rem;\">ID admin: ${it.admin_annotation_id}<\/small><\/div>
        </div>
        <div style=\"text-align:center;display:flex;flex-direction:column;gap:.5rem;\">
          <button class=\"btn btn-success btn-sm\" data-action=\"qc-consolidate\" data-user-annotation=\"${it.annotation_id}\" data-admin-annotation=\"${it.admin_annotation_id}\">✅ Consolidar<\/button>
          <button class=\"btn btn-secondary btn-sm\" data-action=\"qc-compare\"
            data-user-text=\"${userTxt}\"
            data-admin-text=\"${adminTxt}\"
            data-image-id=\"${it.image_id}\"
            data-username=\"${encUser}\"
            data-image-path=\"${encPath}\"
            data-ocr=\"${encOcr}\"
          >🔍 Comparar<\/button>
        </div>
      <\/div>
    <\/div>`;}).join('');
  },
  toast(msg){
    if (!msg) return;
    let box = document.getElementById('toast-box');
    if (!box){
      box = document.createElement('div');
      box.id='toast-box';
      box.style.cssText='position:fixed;top:1rem;right:1rem;z-index:3000;display:flex;flex-direction:column;gap:.5rem;';
      document.body.appendChild(box);
    }
    const el = document.createElement('div');
    el.textContent = msg;
    el.style.cssText='background:#333;color:#fff;padding:.5rem 1rem;border-radius:4px;font-size:.85rem;box-shadow:0 2px 6px rgba(0,0,0,.2);opacity:0;transform:translateY(-5px);transition:all .3s';
    box.appendChild(el);
    requestAnimationFrame(()=>{ el.style.opacity='1'; el.style.transform='translateY(0)'; });
    setTimeout(()=>{ el.style.opacity='0'; el.style.transform='translateY(-5px)'; setTimeout(()=>el.remove(),300); }, 3000);
  },
  showError(msg) { console.error(msg); this.toast?.(msg); }
};
