// Add salle modal
const moSalleAdd = document.getElementById("mo-salle-add");
if (moSalleAdd) {
  moSalleAdd.addEventListener("show.bs.modal", function () {
    window.ClubQ.setModalFields(moSalleAdd, {
      id: "",
      nom: "",
      description: "",
      url: "",
      adresse: "",
      latitude: 0,
      longitude: 0,
    });
  });
}

// Edit salle modal
const moSalleEdit = document.getElementById("mo-salle-edit");
if (moSalleEdit) {
  const titleSaE = moSalleEdit.querySelector(".modal-title");
  moSalleEdit.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    if (!button) return;
    const { salleId, salleNom, salleDescription, salleUrl, salleAdresse, salleLatitude, salleLongitude } = button.dataset;
    if (titleSaE) titleSaE.textContent = `Editer salle ID ${salleId} - ${salleNom}`;
    window.ClubQ.setModalFields(moSalleEdit, {
      id: salleId,
      nom: salleNom,
      description: salleDescription,
      url: salleUrl,
      adresse: salleAdresse,
      latitude: salleLatitude,
      longitude: salleLongitude,
    });
  });
}

// Respo salle modal
const moRespo = document.getElementById("mo-respo-salle");
if (moRespo) {
  const form = document.getElementById("form-respo-salle");
  const contextEl = document.getElementById("respo-salle-context");
  const searchEl = document.getElementById("respo-pceen-search");
  const listEl = document.getElementById("respo-pceen-list");
  const clearBtn = document.getElementById("respo-clear-btn");

  const items = listEl
    ? Array.from(listEl.children).map((el, idx) => ({
        el,
        idx,
        cb: el.querySelector('input[type="checkbox"]'),
        norm: window.ClubQ.normalize(el.dataset.search || el.textContent),
      }))
    : [];

  function filterItems(q) {
    items.forEach((o) => {
      o.el.hidden = Boolean(q && !o.cb.checked && !o.norm.includes(q));
    });
  }

  moRespo.addEventListener("show.bs.modal", function (event) {
    const btn = event.relatedTarget;
    if (!btn) return;
    const { respoUrl, salleNom, seasonNom, currentRespoIds } = btn.dataset;
    const selected = new Set((currentRespoIds || "").split(",").filter(Boolean));
    if (form) form.action = respoUrl || "";
    if (contextEl) contextEl.textContent = `${salleNom} — ${seasonNom}`;
    if (searchEl) searchEl.value = "";
    items.forEach((o) => {
      o.cb.checked = selected.has(o.cb.value);
    });
    items
      .slice()
      .sort((a, b) => Number(b.cb.checked) - Number(a.cb.checked) || a.idx - b.idx)
      .forEach((o) => listEl.appendChild(o.el));
    filterItems("");
    if (listEl) listEl.scrollTop = 0;
  });

  clearBtn?.addEventListener("click", () => {
    items.forEach((o) => {
      o.cb.checked = false;
    });
    filterItems(window.ClubQ.normalize(searchEl?.value.trim() || ""));
  });

  searchEl?.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.isComposing) e.preventDefault();
  });

  window.ClubQ.bindFilter(searchEl, filterItems);
}
