// AnnotatorController (Phase 3 initial extraction)
// Handles business logic separate from legacy global script.
// This is a simplified, incremental version; we'll migrate more pieces gradually.

import { taskService } from '../services/taskService.js';
import { statsService } from '../services/statsService.js';
import { JWT } from '../core/jwt.js';

export class AnnotatorController {
  constructor({ ui }) {
    this.ui = ui; // expect an object with methods: showLoading, showCompletion, updateImage, updateStats, showError
    this.currentTask = null;
    this.currentAnnotationId = null;
    this.history = [];
    this.pending = [];
    this.historyIndex = -1;
    this.editMode = false; // nuevo estado de edición
  }

  async bootstrap() {
    if (!JWT.requireAuthOrRedirect()) return;
    await Promise.all([
      this.refreshStats(),
      this.loadHistory(),
    ]);
    await this.loadCurrentTask();
    await this.loadPending();
  }

  async loadCurrentTask() {
    try {
      this.ui.showLoading(true);
      const data = await taskService.getNextTask();
      if (data?.completed) {
        this.currentTask = null;
        this.currentAnnotationId = null;
        this.ui.showCompletion();
        return;
      }
      this.currentTask = data;
      this.currentAnnotationId = data.annotation_id;
      this.historyIndex = -1;
      this.ui.updateTask?.(data);
      this.ui.updateTaskStatus?.(data); // asegurar estado visual
    } catch (e) {
      this.ui.showError('Error cargando tarea');
      console.error(e);
    } finally {
      this.ui.showLoading(false);
    }
  }

  async refreshStats() {
    try {
      const stats = await statsService.myStats();
      this.ui.updateStats?.(stats);
    } catch (e) { console.warn('stats error', e); }
  }

  async loadHistory() {
    try {
      const h = await taskService.getHistory(10);
      this.history = h.history || [];
      this.ui.updateHistoryNav?.(this.navState());
    } catch (e) { console.warn('history error', e); }
  }

  async loadPending() {
    try {
      const p = await taskService.getPendingPreview(10);
      this.pending = p.pending || [];
      this.ui.updatePending?.(this.pending, this.currentTask?.annotation_id);
    } catch (e) { console.warn('pending error', e); }
  }

  navState() {
    return {
      historyIndex: this.historyIndex,
      historyLength: this.history.length,
      canPrev: (this.historyIndex === -1 && this.history.length > 0) || (this.historyIndex >= 0 && this.historyIndex < this.history.length - 1),
      canNext: this.historyIndex >= 0,
    };
  }

  // === Navigation & Pending Migration ===
  async navigatePrev() {
    if (this.historyIndex === -1) {
      if (this.history.length === 0) return;
      this.historyIndex = 0;
      this._loadHistoryTask(this.history[0]);
    } else if (this.historyIndex < this.history.length - 1) {
      this.historyIndex += 1;
      this._loadHistoryTask(this.history[this.historyIndex]);
    }
    this._updateNavUI();
  }

  async navigateNext() {
    if (this.historyIndex > 0) {
      this.historyIndex -= 1;
      this._loadHistoryTask(this.history[this.historyIndex]);
    } else if (this.historyIndex === 0) {
      this.historyIndex = -1; // Return to current
      await this.loadCurrentTask();
      await this.loadPending();
    }
    this._updateNavUI();
  }

  async loadTaskFromPending(annotationId) {
    try {
      this.ui.showLoading(true);
      const data = await taskService.loadTask(annotationId);
      this.currentTask = data;
      this.currentAnnotationId = data.annotation_id;
      this.historyIndex = -1; // treat as current context
      this.ui.updateTask?.(data);
      this.ui.updateTaskStatus?.(data);
      await this.loadPending();
      this._updateNavUI();
    } catch (e) {
      this.ui.showError('Error cargando tarea');
      console.error(e);
    } finally {
      this.ui.showLoading(false);
    }
  }

  // === Action Methods (Phase 4) ===
  _inHistory() { return this.historyIndex >= 0; }

  startEdit() {
    // Permitir edición también en historial (undo/corrección)
    if (!this.currentTask) return;
    if (this.editMode) return; // ya activo
    const text = this.currentTask.corrected_text || this.currentTask.initial_ocr_text || '';
    this.editMode = true;
    this.ui.enterEditMode?.(text);
  }

  cancelEdit() {
    if (!this.editMode) return;
    this.editMode = false;
    this.ui.exitEditMode?.();
  }

  async saveEdit() {
    if (!this.currentAnnotationId) return;
    const newText = this.ui.getEditedText?.();
    if (!newText) { this.ui.showError('Texto vacío'); return; }
    const fromHistory = this._inHistory();
    try {
      this.ui.disableActionButtons?.(true);
      await taskService.submitAction(this.currentAnnotationId, 'corrected', newText);
      if (this.currentTask) {
        this.currentTask.corrected_text = newText;
        this.currentTask.status = 'corrected';
        this.ui.updateTaskStatus?.(this.currentTask);
      }
      this.editMode = false;
      this.ui.exitEditMode?.();
      this.ui.flashSuccess?.('✓ Corrección guardada');
      await this.afterActionRefresh({ fromHistory, annotationId: this.currentAnnotationId });
    } catch (e) {
      console.error(e);
      this.ui.showError('Error guardando');
    } finally {
      this.ui.disableActionButtons?.(false);
    }
  }

  async approveCurrent() {
    if (!this.currentAnnotationId) return;
    const fromHistory = this._inHistory();
    try {
      this.ui.disableActionButtons?.(true);
      await taskService.submitAction(this.currentAnnotationId, 'approved');
      if (this.currentTask) {
        this.currentTask.status = 'approved';
        this.ui.updateTaskStatus?.(this.currentTask);
      }
      this.ui.flashSuccess?.('✓ Imagen aprobada');
      await this.afterActionRefresh({ fromHistory, annotationId: this.currentAnnotationId });
    } catch (e) {
      console.error(e);
      this.ui.showError('Error aprobando');
    } finally {
      this.ui.disableActionButtons?.(false);
    }
  }

  async discardCurrent() {
    if (!this.currentAnnotationId) return;
    const fromHistory = this._inHistory();
    try {
      this.ui.disableActionButtons?.(true);
      await taskService.submitAction(this.currentAnnotationId, 'discarded');
      if (this.currentTask) {
        this.currentTask.status = 'discarded';
        this.ui.updateTaskStatus?.(this.currentTask);
      }
      this.ui.flashSuccess?.('🗑️ Imagen descartada');
      await this.afterActionRefresh({ fromHistory, annotationId: this.currentAnnotationId });
    } catch (e) {
      console.error(e);
      this.ui.showError('Error descartando');
    } finally {
      this.ui.disableActionButtons?.(false);
    }
  }

  async afterActionRefresh(ctx = {}) {
    // NUEVO: si la acción viene del historial, regresar al flujo de tarea actual
    if (ctx.fromHistory) {
      this.historyIndex = -1; // asegurar estado navegación principal
      await this.loadCurrentTask();
      await Promise.all([
        this.refreshStats(),
        this.loadHistory(), // incluye cambios hechos en historial
        this.loadPending(),
      ]);
      this._updateNavUI();
      return;
    }
    // Flujo original para tarea actual
    await this.loadCurrentTask();
    await Promise.all([
      this.refreshStats(),
      this.loadHistory(),
      this.loadPending(),
    ]);
  }

  _loadHistoryTask(task) {
    this.currentTask = task;
    this.currentAnnotationId = task.annotation_id;
    this.ui.updateTask?.(task, { history: true });
    this.ui.updateTaskStatus?.(task);
    if (this.editMode) this.cancelEdit();
  }

  _updateNavUI() {
    this.ui.updateHistoryNav?.(this.navState());
    if (this.historyIndex === -1) {
      this.ui.updatePending?.(this.pending, this.currentTask?.annotation_id);
    }
  }
}
