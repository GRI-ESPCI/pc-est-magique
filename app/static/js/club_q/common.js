// Shared Club Q client helpers
window.ClubQ = {
  normalize(str) {
    return window.PEM.normalize(str);
  },

  getCsrfToken() {
    return window.PEM.getCsrfToken();
  },

  formatEur(amount) {
    if (!this._eurFmt) {
      this._eurFmt = new Intl.NumberFormat(document.documentElement.lang || "fr-FR", {
        style: "currency",
        currency: "EUR",
      });
    }
    return this._eurFmt.format(amount);
  },

  setModalFields(modal, values) {
    if (!modal) return;
    Object.entries(values).forEach(([name, val]) => {
      const el = modal.querySelector(`[name="${name}"]`);
      if (el) el.value = val ?? "";
    });
  },

  bindFilter(input, onFilter, { initial = false } = {}) {
    if (!input) return;
    const run = () => onFilter(this.normalize(input.value.trim()));
    input.addEventListener("input", run);
    window.addEventListener("pageshow", run);
    if (initial) run();
  },
};
