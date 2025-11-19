import { http } from '../core/http.js';

export const statsService = {
  myStats() { return http('/stats'); },
};
