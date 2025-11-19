// Simple TabController to replace legacy showTab onclick attributes
export class TabController {
  constructor({ selector='.nav-tabs', contentSelector='.tab-content', activeClass='active' }={}){
    this.root = document.querySelector(selector);
    this.contents = Array.from(document.querySelectorAll(contentSelector));
    if (this.root){
      this.root.addEventListener('click', e=>{
        const btn = e.target.closest('[data-tab]');
        if (!btn) return;
        this.activate(btn.dataset.tab);
      });
      // activate first if none active
      const first = this.root.querySelector('[data-tab]');
      if (first && !this.root.querySelector('.active')) this.activate(first.dataset.tab, false);
    }
  }
  activate(name, focus=true){
    // buttons
    this.root.querySelectorAll('[data-tab]').forEach(b=>b.classList.toggle('active', b.dataset.tab===name));
    // contents
    this.contents.forEach(c=>c.classList.toggle('active', c.id===name+'-tab'));
    if (focus){
      const activeBtn = this.root.querySelector(`[data-tab="${name}"]`);
      activeBtn?.focus();
    }
  }
}
