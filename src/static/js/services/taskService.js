import { http } from '../core/http.js';

export const taskService = {
  async getNextTask() {
    const data = await http('/task/next');
    if (data === null) return { completed: true };
    return data;
  },
  getHistory(limit = 10) { return http(`/task/history?limit=${encodeURIComponent(limit)}`); },
  getPendingPreview(limit = 10) { return http(`/task/pending-preview?limit=${encodeURIComponent(limit)}`); },
  loadTask(annotationId) { return http(`/task/load/${annotationId}`); },
  submitAction(annotationId, action, correctedText = null) {
    const body = { status: action };
    if (correctedText !== null) body.corrected_text = correctedText;
    return http(`/annotations/${annotationId}`, { method: 'PUT', body: JSON.stringify(body) });
  },
  getAnnotation(annotationId) { return http(`/annotations/${annotationId}`); },
};
