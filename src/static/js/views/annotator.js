import { JWT } from '../core/jwt.js';
import { taskService } from '../services/taskService.js';
import { statsService } from '../services/statsService.js';
import { authService } from '../services/authService.js';
import { AnnotatorController } from '../controllers/annotatorController.js';
import { Toast } from '../components/toast.js';
import { StatusIndicator } from '../components/statusIndicator.js';
import { PendingList, setPendingSelectHandler } from '../components/pendingList.js';
import { StatsProgress } from '../components/statsProgress.js';

window.ModAPI = { JWT, taskService, statsService, authService };

// Estado de zoom
let zoomFactor = 1;
const ZOOM_MIN = 0.5;
const ZOOM_MAX = 4;
const ZOOM_STEP = 0.15;
let zoomHideTimer = null;
function showZoomOverlay(){
  const overlay = document.getElementById('zoomOverlay');
  if(!overlay) return;
  overlay.textContent = Math.round(zoomFactor*100)+'%';
  overlay.classList.add('show');
  if(zoomHideTimer) clearTimeout(zoomHideTimer);
  zoomHideTimer = setTimeout(()=> overlay.classList.remove('show'), 900);
}
function applyZoom() {
  const img = document.getElementById('currentImage');
  if (!img) return;
  img.style.transformOrigin = 'center top';
  img.style.transform = `scale(${zoomFactor})`;
  const display = document.getElementById('zoomDisplay');
  if (display) display.textContent = Math.round(zoomFactor * 100) + '%';
  showZoomOverlay();
}
function setZoom(z) { const prev = zoomFactor; zoomFactor = Math.min(ZOOM_MAX, Math.max(ZOOM_MIN, z)); if (Math.abs(prev-zoomFactor)>1e-4) applyZoom(); }
function zoomIn() { setZoom(zoomFactor + ZOOM_STEP); }
function zoomOut() { setZoom(zoomFactor - ZOOM_STEP); }
function zoomReset() { setZoom(1); }

// Helper: ajuste dinámico de imagen (zoom/resizing para imágenes pequeñas)
function adjustImageSize(img){
  if(!img || !img.naturalWidth || !img.naturalHeight) return;
  // Reset manual sizing (baseline antes de aplicar transform)
  img.style.width='';
  img.style.height='';
  img.style.maxWidth='100%';
  img.style.maxHeight='500px';
  const minTargetH = 200;
  const maxH = 500;
  const nh = img.naturalHeight;
  const nw = img.naturalWidth;
  if(nh < minTargetH){
    const desiredH = minTargetH;
    const desiredW = Math.round(nw * (desiredH/nh));
    img.style.height = desiredH + 'px';
    img.style.width = desiredW + 'px';
  } else if(nh > maxH){
    const desiredH = maxH;
    const desiredW = Math.round(nw * (desiredH/nh));
    img.style.height = desiredH + 'px';
    img.style.width = desiredW + 'px';
  }
  // Aplicar zoom actual
  applyZoom();
}

// UI Adapter ampliado
const uiAdapter = {
  showLoading(show) {
    const l = document.getElementById('loadingDiv');
    const w = document.getElementById('workArea');
    if (!l || !w) return;
    if (show) { l.classList.remove('hidden'); w.classList.add('hidden'); }
    else { l.classList.add('hidden'); w.classList.remove('hidden'); }
  },
  showCompletion() {
    const w = document.getElementById('workArea');
    const c = document.getElementById('completionDiv');
    if (w) w.classList.add('hidden');
    if (c) c.classList.remove('hidden');
  },
  updateTask(task) {
    // Reset zoom al cambiar de tarea
    zoomReset();
    const img = document.getElementById('currentImage');
    const noImg = document.getElementById('noImageMessage');
    if (task?.image_path && img && noImg) {
      const name = task.image_path.split('/').pop();
      // Set handler antes de cambiar src para cubrir cache race
      img.onload = () => adjustImageSize(img);
      img.src = `/images/${name}`;
      if (img.complete) adjustImageSize(img); // si viene de cache
      img.classList.remove('hidden');
      noImg.classList.add('hidden');
    } else if (img && noImg) {
      img.classList.add('hidden');
      noImg.classList.remove('hidden');
    }
    const disp = document.getElementById('transcriptionDisplay');
    if (disp) disp.textContent = task?.corrected_text || task?.initial_ocr_text || '';
    // aplicar indicador separado
    StatusIndicator.render(task, disp);
    const idEl = document.getElementById('currentImageId');
    if (idEl) idEl.textContent = task?.image_id || '-';
  },
  updateTaskStatus(task) {
    const disp = document.getElementById('transcriptionDisplay');
    StatusIndicator.render(task, disp);
  },
  updateStats(stats) {
    StatsProgress.render(stats);
  },
  updatePending(pending, currentId) {
    PendingList.render(pending, currentId);
  },
  updateHistoryNav(state) {
    const prevBtn = document.getElementById('prevBtn');
    const nextBtn = document.getElementById('nextBtn');
    if (prevBtn) prevBtn.disabled = !state.canPrev;
    if (nextBtn) nextBtn.disabled = !state.canNext;
  },
  enterEditMode(text) {
    const display = document.getElementById('transcriptionDisplay');
    const input = document.getElementById('editInput');
    if (!display || !input) return;
    display.classList.add('hidden');
    input.classList.remove('hidden');
    input.value = text;
    input.focus();
    // Seleccionar todo el texto para reemplazo rápido
    requestAnimationFrame(()=>{ try { input.select(); } catch {} });
    ['correctBtn','editBtn','discardBtn'].forEach(id=>document.getElementById(id)?.classList.add('hidden'));
    ['saveEditBtn','cancelBtn'].forEach(id=>document.getElementById(id)?.classList.remove('hidden'));
  },
  exitEditMode() {
    const display = document.getElementById('transcriptionDisplay');
    const input = document.getElementById('editInput');
    if (!display || !input) return;
    display.classList.remove('hidden');
    input.classList.add('hidden');
    ['correctBtn','editBtn','discardBtn'].forEach(id=>document.getElementById(id)?.classList.remove('hidden'));
    ['saveEditBtn','cancelBtn'].forEach(id=>document.getElementById(id)?.classList.add('hidden'));
  },
  getEditedText() { return document.getElementById('editInput')?.value.trim(); },
  disableActionButtons(disabled) {
    ['correctBtn','editBtn','discardBtn','saveEditBtn','cancelBtn'].forEach(id=>{
      const b=document.getElementById(id); if (b){ b.disabled=disabled; b.style.opacity=disabled?'0.6':'1'; }
    });
  },
  flashSuccess(msg) { Toast.show(msg, { type: 'success' }); },
  showError(msg) { Toast.show(msg, { type: 'error' }); }
};

(async function init() {
  if (!JWT.requireAuthOrRedirect()) return;
  // === NUEVO: configurar header usuario/admin sin legacy ===
  async function setupUserHeader() {
    const nameEl = document.getElementById('user-name');
    let user = JWT.getUser();
    if (nameEl && user) nameEl.textContent = `${user.username} (${user.role})`;
    // Refrescar del backend para info reciente
    try {
      const me = await authService.me();
      if (me?.user) { user = me.user; JWT.setUser(user); if (nameEl) nameEl.textContent = `${user.username} (${user.role})`; }
    } catch {}
    // Botón admin
    if (user?.role === 'admin') {
      const userInfo = document.querySelector('.user-info');
      if (userInfo && !document.getElementById('admin-panel-btn')) {
        const adminBtn = document.createElement('button');
        adminBtn.id = 'admin-panel-btn';
        adminBtn.className = 'logout-btn';
        adminBtn.style.marginRight = '1rem';
        adminBtn.textContent = '⚙️ Panel Admin';
        adminBtn.addEventListener('click', ()=> { window.location.href = '/admin'; });
        const logoutBtn = document.getElementById('logoutBtn');
        userInfo.insertBefore(adminBtn, logoutBtn || userInfo.firstChild);
      }
    }
  }
  await setupUserHeader();
  // === FIN NUEVO ===
  window.modAnnotatorController = new AnnotatorController({ ui: uiAdapter });
  await window.modAnnotatorController.bootstrap();

  const safeBind = (id, handler) => {
    const el = document.getElementById(id);
    if (!el) return;
    // evitar doble binding (marcar dataset)
    if (el.dataset.modBound) return;
    el.addEventListener('click', (e)=>{ e.stopPropagation(); handler(); });
    el.dataset.modBound = '1';
  };

  // Navegación
  safeBind('prevBtn', () => window.modAnnotatorController.navigatePrev());
  safeBind('nextBtn', () => window.modAnnotatorController.navigateNext());

  // Acciones
  safeBind('correctBtn', () => window.modAnnotatorController.approveCurrent());
  safeBind('discardBtn', () => window.modAnnotatorController.discardCurrent());
  safeBind('editBtn', () => window.modAnnotatorController.startEdit());
  safeBind('saveEditBtn', () => window.modAnnotatorController.saveEdit());
  safeBind('cancelBtn', () => window.modAnnotatorController.cancelEdit());

  // Zoom botones
  safeBind('zoomInBtn', () => zoomIn());
  safeBind('zoomOutBtn', () => zoomOut());
  safeBind('zoomResetBtn', () => zoomReset());

  // Wheel + Ctrl para zoom
  const imgContainer = document.querySelector('.image-container');
  if (imgContainer && !imgContainer.dataset.zoomWheelBound){
    imgContainer.addEventListener('wheel', (e)=>{
      if (!e.ctrlKey) return; // Solo con Ctrl para no interferir scroll normal
      e.preventDefault();
      const delta = e.deltaY;
      if (delta < 0) zoomIn(); else zoomOut();
    }, { passive:false });
    imgContainer.dataset.zoomWheelBound = '1';
  }

  // Logout (migrated modular)
  const doLogout = async () => { try { await authService.logout(); } finally { window.location.href = '/login'; } };
  safeBind('logoutBtn', doLogout);
  safeBind('logoutBtn2', doLogout);

  // Teclado (solo navegación y acciones si no editando input nativo)
  document.addEventListener('keydown', (e) => {
    if (document.activeElement && ['INPUT','TEXTAREA'].includes(document.activeElement.tagName)) {
      if (e.key === 'Escape') { window.modAnnotatorController.cancelEdit(); }
      else if (e.key === 'Enter' && window.modAnnotatorController.editMode) { e.preventDefault(); window.modAnnotatorController.saveEdit(); }
      return;
    }
    if (e.key === 'ArrowLeft') window.modAnnotatorController.navigatePrev();
    else if (e.key === 'ArrowRight') window.modAnnotatorController.navigateNext();
    else if (e.key === '1' || (e.code === 'Space' && !e.shiftKey && !e.ctrlKey && !e.altKey)) { e.preventDefault(); window.modAnnotatorController.approveCurrent(); }
    else if (e.key === '2' || e.key === 'e' || e.key === 'E') { e.preventDefault(); window.modAnnotatorController.startEdit(); }
    else if (e.key === '3' || e.key === 'Delete') { window.modAnnotatorController.discardCurrent(); }
    else if (e.key === 'l' || e.key === 'L') { doLogout(); }
    else if (e.key === '+' || e.key === '=') { e.preventDefault(); zoomIn(); }
    else if (e.key === '-') { e.preventDefault(); zoomOut(); }
    else if (e.key === '0') { e.preventDefault(); zoomReset(); }
  }, true);

  setPendingSelectHandler((id)=> window.modAnnotatorController.loadTaskFromPending(id));
  // Quitar listener manual previo para pending
  const pendingContainer = document.getElementById('pendingTasksPreview');
  if (pendingContainer && pendingContainer._legacyPendingListenerAttached) {
    // noop: indicador de posible limpieza futura
  }
})();
