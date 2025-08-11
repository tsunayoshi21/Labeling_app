import { http } from '../core/http.js';

const API_BASE = '/api/v2/admin';

export const adminService = {
  // users
  listUsers() { return http(`${API_BASE}/users`); },
  createUser({ username, password, role = 'annotator' }) {
    return http(`${API_BASE}/users`, { method: 'POST', body: JSON.stringify({ username, password, role }) });
  },
  deleteUser(userId) { return http(`${API_BASE}/users/${userId}`, { method: 'DELETE' }); },
  userStats(userId) { return http(`${API_BASE}/users/${userId}/stats`); },
  userAnnotations(userId) { return http(`${API_BASE}/users/${userId}/annotations`); },
  deleteUserAnnotation(userId, annotationId) {
    return http(`${API_BASE}/users/${userId}/annotations/${annotationId}`, { method: 'DELETE' });
  },
  bulkDeleteUserAnnotations(userId, statuses) {
    return http(`${API_BASE}/users/${userId}/annotations/bulk-delete`, { method: 'POST', body: JSON.stringify({ statuses }) });
  },
  transferAnnotations(fromUserId, { to_user_id, include_pending, include_reviewed }) {
    return http(`${API_BASE}/users/${fromUserId}/transfer-annotations`, { method: 'POST', body: JSON.stringify({ to_user_id, include_pending, include_reviewed }) });
  },
  agreementStats() { return http(`${API_BASE}/users/agreement-stats`); },

  // assignments
  createAssignments({ user_ids, image_ids }) {
    return http(`${API_BASE}/assignments`, { method: 'POST', body: JSON.stringify({ user_ids, image_ids }) });
  },
  createAutoAssignments({ count, priority_unannotated, user_id }) {
    return http(`${API_BASE}/assignments/auto`, { method: 'POST', body: JSON.stringify({ count, priority_unannotated, user_id }) });
  },

  // stats and activity
  generalStats() { return http(`${API_BASE}/stats`); },
  recentActivity(limit = 6) { return http(`${API_BASE}/recent-activity?limit=${limit}`); },
  qualityControl() { return http(`${API_BASE}/quality-control`); },
  consolidateQuality({ user_annotation_id, admin_annotation_id }) {
    return http(`${API_BASE}/quality-control/consolidate`, { method: 'POST', body: JSON.stringify({ user_annotation_id, admin_annotation_id }) });
  }
};
