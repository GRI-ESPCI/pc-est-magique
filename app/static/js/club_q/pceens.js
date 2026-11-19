// Edit pceen discontent modal
const moDiscontentEdit = document.getElementById("mo-pceen-edit");
if (moDiscontentEdit) {
  const titleDE = moDiscontentEdit.querySelector(".modal-title");
  moDiscontentEdit.addEventListener("show.bs.modal", function (event) {
    const { pceenId, pceenNom, pceenDiscontent } = event.relatedTarget.dataset;
    if (titleDE) {
      titleDE.textContent = `Éditer le mécontentement de ${pceenNom} (ID : ${pceenId})`;
    }
    window.ClubQ.setModalFields(moDiscontentEdit, {
      id: pceenId,
      discontent: pceenDiscontent,
    });
  });
}

// Payment status toggle
document.addEventListener("click", async function (event) {
  const btn = event.target.closest(".clubq-paid-toggle");
  if (!btn || btn.disabled) return;

  const row = btn.closest("tr");
  const targetPaid = btn.getAttribute("aria-pressed") !== "true";

  btn.disabled = true;
  try {
    const res = await fetch(btn.dataset.url, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": window.ClubQ.getCsrfToken() },
      body: JSON.stringify({ paid: targetPaid }),
    });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const { paid } = await res.json();

    const rawAmount = Number.parseFloat(btn.dataset.amount || "0") || 0;
    const remaining = paid ? 0 : rawAmount;

    if (rawAmount === 0 && !paid) {
      if (row) {
        const dash = document.createElement("span");
        dash.className = "text-body-secondary";
        dash.textContent = "—";
        btn.replaceWith(dash);
      } else {
        btn.remove();
      }
    } else {
      btn.setAttribute("aria-pressed", String(paid));
      btn.classList.toggle("btn-success", paid);
      btn.classList.toggle("btn-outline-secondary", !paid);
      btn.textContent = paid ? (btn.dataset.labelPaid || "Payé") : (btn.dataset.labelUnpaid || "Non payé");
    }

    if (row) {
      row.dataset.paid = paid ? "1" : (rawAmount === 0 ? "2" : "0");
      row.dataset.cost = String(remaining);
      const dueCell = row.querySelector(".clubq-due-cell");
      if (dueCell) {
        if (paid) {
          const zero = document.createElement("span");
          zero.className = "text-success fw-semibold";
          zero.textContent = window.ClubQ.formatEur(0);
          const orig = document.createElement("small");
          orig.className = "text-body-secondary text-decoration-line-through";
          orig.textContent = window.ClubQ.formatEur(rawAmount);
          dueCell.replaceChildren(zero, " ", orig);
        } else {
          dueCell.textContent = window.ClubQ.formatEur(rawAmount);
        }
      }
      const totalRestantEl = document.getElementById("clubq-total-restant");
      if (totalRestantEl) {
        let total = 0;
        document.querySelectorAll("#sort-table tr").forEach((tr) => {
          total += Number.parseFloat(tr.dataset.cost || "0") || 0;
        });
        totalRestantEl.textContent = window.ClubQ.formatEur(total);
      }
    }

    // Summary card on id/pceen.html
    const summaryAmount = document.getElementById("clubq-a-payer-amount");
    const summaryBadge = document.getElementById("clubq-paid-badge");
    if (summaryAmount) summaryAmount.textContent = window.ClubQ.formatEur(remaining);
    if (summaryBadge) summaryBadge.classList.toggle("d-none", !paid);
  } catch (err) {
    console.error("Failed to toggle payment status:", err);
    if (typeof showToast === "function") {
      showToast(btn.dataset.errorMsg || "Erreur lors de la mise à jour du paiement.", "danger");
    }
  } finally {
    btn.disabled = false;
  }
});

// Search filter
const pceenSearchInput = document.getElementById("pceen-search");
if (pceenSearchInput) {
  const emptyRow = document.getElementById("pceen-search-empty");
  const tableEl = document.querySelector(".clubq-table");
  const normalize = window.ClubQ.normalize;

  window.ClubQ.bindFilter(
    pceenSearchInput,
    (q) => {
      const rows = document.querySelectorAll("#sort-table tr");
      let visibleCount = 0;
      rows.forEach((row) => {
        const searchText = normalize(row.dataset.search || row.dataset.name);
        const promo = normalize(row.dataset.promo);
        const id = normalize(row.cells[0] ? row.cells[0].textContent.trim() : "");
        const match = !q || searchText.includes(q) || promo.includes(q) || id === q;
        row.style.display = match ? "" : "none";
        if (match) visibleCount++;
      });
      if (emptyRow) emptyRow.style.display = visibleCount === 0 && q ? "" : "none";
      if (tableEl) tableEl.classList.toggle("is-empty", visibleCount === 0);
    },
    { initial: true }
  );
}
