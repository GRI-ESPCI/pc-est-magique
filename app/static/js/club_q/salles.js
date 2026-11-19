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
  const selectEl = document.getElementById("respo-pceen-select");

  const allOptions = selectEl
    ? Array.from(selectEl.options).map((el) => ({
        el,
        norm: window.ClubQ.normalize(el.dataset.search || el.textContent),
      }))
    : [];

  function renderOptions(q, selectedVal) {
    if (!selectEl) return;
    selectEl.replaceChildren(
      ...allOptions
        .filter((o) => !q || o.el.value === "" || o.el.value === selectedVal || o.norm.includes(q))
        .map((o) => o.el)
    );
    selectEl.value = selectedVal;
  }

  moRespo.addEventListener("show.bs.modal", function (event) {
    const btn = event.relatedTarget;
    if (!btn) return;
    const { respoUrl, salleNom, seasonNom, currentRespoId } = btn.dataset;
    if (form) form.action = respoUrl || "";
    if (contextEl) contextEl.textContent = `${salleNom} — ${seasonNom}`;
    if (searchEl) searchEl.value = "";
    renderOptions("", currentRespoId || "");
  });

  window.ClubQ.bindFilter(searchEl, (q) => renderOptions(q, selectEl?.value || ""));
}
