// Simple toast component (can be evolved later)
// Usage: import { Toast } from './components/toast.js'; Toast.show('Message')

export const Toast = (() => {
  let container;
  function ensure() {
    if (!container) {
      container = document.createElement('div');
      container.id = 'toastContainer';
      container.style.cssText = 'position:fixed;top:20px;right:20px;z-index:2500;display:flex;flex-direction:column;gap:8px;';
      document.body.appendChild(container);
    }
  }
  function show(message, { type='success', timeout=2000 } = {}) {
    ensure();
    const el = document.createElement('div');
    const colors = { success:'#27ae60', error:'#e74c3c', info:'#3498db', warning:'#f39c12' };
    const bg = colors[type] || colors.success;
    el.style.cssText = 'background:'+bg+';color:#fff;padding:8px 14px;border-radius:4px;font-weight:600;box-shadow:0 2px 8px rgba(0,0,0,.25);transform:translateX(120%);transition:transform .25s;';
    el.textContent = message;
    container.appendChild(el);
    requestAnimationFrame(()=> el.style.transform='translateX(0)');
    setTimeout(()=> { el.style.transform='translateX(120%)'; setTimeout(()=> el.remove(), 250); }, timeout);
  }
  return { show };
})();
