var delete_svg = document.getElementById("icon-delete");
var revert_svg = document.getElementById("icon-revert");
var form = document.getElementById("security-form");
var new_badge = document
  .getElementById("new-role-template")
  .querySelector(".badge");

function remove_role(elem, pceen_id, role_id) {
  // elem = SVG element of the X button
  form.action.value = "remove";
  form.pceen_id.value = pceen_id;
  form.role_id.value = role_id;
  fetch("", {
    method: "POST",
    body: new FormData(form),
  }).then((response) => {
    if (response.ok) {
      var badge = elem.closest(".badge");
      badge.style.setProperty("transition", "all 0.2s");
      badge.style.setProperty("opacity", "30%");
      badge.style.setProperty("text-decoration", "line-through");
      // badge.style.setProperty("font-style", "italic");
      elem.innerHTML = revert_svg.innerHTML;
      elem.onclick = function () {
        restore_role(elem, pceen_id, role_id);
      };
    } else {
      response.text().then((text) => alert(text));
    }
  });
}

function add_role(elem, pceen_id, role_id) {
  // elem = SVG element of the + button
  form.action.value = "add";
  form.pceen_id.value = pceen_id;
  form.role_id.value = role_id;
  fetch("", {
    method: "POST",
    body: new FormData(form),
  }).then((response) => {
    if (response.ok) {
      response.json().then((data) => {
        var badge = new_badge.cloneNode(true);
        elem.closest("td").insertBefore(badge, elem.closest(".add-role"));
        var name = badge.querySelector(".role_name");
        name.textContent = data["name"];
        name.href = name.href + "#" + data["id"];
        badge.style.setProperty("background-color", "#" + data["color"]);
        badge.style.setProperty("color", data["dark"] ? "#ffffff" : "#000000", "important");
        badge.querySelector("svg").onclick = function () {
          remove_role(badge.querySelector("svg"), pceen_id, role_id);
        };
        elem.remove();
      });
    } else {
      response.text().then((text) => alert(text));
    }
  });
}

function restore_role(elem, pceen_id, role_id) {
  // elem = SVG element of the revert button
  form.action.value = "add";
  form.pceen_id.value = pceen_id;
  form.role_id.value = role_id;
  fetch("", {
    method: "POST",
    body: new FormData(form),
  }).then((response) => {
    if (response.ok) {
      var badge = elem.closest(".badge");
      badge.style.removeProperty("opacity");
      badge.style.removeProperty("text-decoration");
      // badge.style.removeProperty("font-style");
      elem.innerHTML = delete_svg.innerHTML;
      elem.onclick = function () {
        remove_role(elem, pceen_id, role_id);
      };
    } else {
      response.text().then((text) => alert(text));
    }
  });
}

// Ban modal
var moBan = document.getElementById("mo-ban");
var title = moBan.querySelector(".modal-title");
var [template_new, template_update] = title.textContent.split(" || ");
var submit = moBan.querySelector("#submit");
var [submit_text_new, submit_text_update] = submit.value.split(" || ");
moBan.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  moBan.querySelector("#pceen").value = button.dataset["pceenId"];
  moBan
    .querySelectorAll(".form-control")
    .forEach((elem) => (elem.value = null));
  moBan.querySelector("#infinite").checked = true;
  update_checkbox();
  if (button.dataset["banId"]) {
    // Update existing ban
    title.textContent = template_update.replace(
      "_name_",
      button.dataset["pceenName"]
    );
    moBan.querySelector("#ban_id").value = button.dataset["banId"];
    if (button.dataset["banEnd"]) {
      moBan.querySelector("#infinite").checked = false;
      update_checkbox();
      var end = moment.utc(new Number(button.dataset["banEnd"]) * 1000);
      var interval = moment.duration(end.diff());
      moBan.querySelector("#hours").value = interval.hours();
      moBan.querySelector("#days").value = interval.days();
      moBan.querySelector("#months").value = interval.months();
    }
    moBan.querySelector("#reason").value = button.dataset["banReason"];
    moBan.querySelector("#message").value = button.dataset["banMessage"];
    submit.value = submit_text_update;
    moBan.querySelector("#unban").hidden = false;
  } else {
    // New ban
    moBan.querySelector("#ban_id").value = null;
    title.textContent = template_new.replace(
      "_name_",
      button.dataset["pceenName"]
    );
    submit.value = submit_text_new;
    moBan.querySelector("#unban").hidden = true;
  }
});

function update_checkbox() {
  if (infiniteCheckbox.checked) {
    moBan
      .querySelectorAll(".duration-control")
      .forEach((elem) => elem.classList.add("text-muted"));
    moBan
      .querySelectorAll(".duration-input")
      .forEach((elem) => (elem.disabled = true));
  } else {
    moBan
      .querySelectorAll(".duration-control")
      .forEach((elem) => elem.classList.remove("text-muted"));
    moBan
      .querySelectorAll(".duration-input")
      .forEach((elem) => (elem.disabled = false));
  }
}

// Ban modal checkbox
var infiniteCheckbox = moBan.querySelector("#infinite");
infiniteCheckbox.addEventListener("change", update_checkbox);

function mo_add_role(elem, role_id) {
    const select = document.getElementById("roles");
    const option = select.querySelector(`option[value="${role_id}"]`);
    if (option) {
        option.selected = true;
    }
    // Create new selected role badge
    const template = document.getElementById("mo-selected-role-template").querySelector(".badge");
    const badge = template.cloneNode(true);
    badge.querySelector(".role_name").textContent = elem.textContent.trim();
    badge.style.setProperty("background-color", elem.style.backgroundColor);
    badge.style.setProperty("color", elem.style.color, "important");
    badge.dataset.roleId = role_id;
    elem.style.display = "none";
    badge.querySelector("svg").onclick = function() {
        mo_remove_role(badge, elem, role_id);
    };
    const container = document.getElementById("mo-add-pceen-roles-container");
    const addRoleDropdown = container.querySelector(".add-role");
    container.insertBefore(badge, addRoleDropdown);
}

function mo_remove_role(badge, dropdownElem, role_id) {
    const select = document.getElementById("roles");
    const option = select.querySelector(`option[value="${role_id}"]`);
    if (option) {
        option.selected = false;
    }
    // Show the option in the dropdown again
    dropdownElem.style.display = "";
    badge.remove();
}

document.addEventListener("DOMContentLoaded", function () {
  const searchForm = document.getElementById("pceen-search-form");
  const searchInput = document.getElementById("pceen-search");
  const clearBtn = document.getElementById("pceen-search-clear");
  const sortTable = document.getElementById("sort-table");
  const emptyRow = document.getElementById("pceen-search-empty");
  const paginationContainer = document.getElementById("pceen-pagination");
  const totalCountBadge = document.getElementById("pceen-total-count");
  const rezModalsContainer = document.getElementById("pceen-rez-modals");
  const tableHead = sortTable ? sortTable.closest("table")?.querySelector("thead") : null;

  if (!searchForm || !searchInput || !sortTable) return;

  let debounceTimer = null;
  let activeController = null;

  const normalize = (str) =>
    (str || "")
      .toString()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();

  function updateClearButton(val) {
    if (clearBtn) {
      clearBtn.classList.toggle("d-none", !val);
    }
  }

  function filterCurrentRows(rawQuery) {
    const q = normalize(rawQuery.trim());
    const isNumeric = /^\d+$/.test(q);
    const rows = sortTable.querySelectorAll("tr");
    rows.forEach((row) => {
      if (!q) {
        row.style.display = "";
        return;
      }
      const name = normalize(row.dataset.name);
      const promo =
        row.dataset.promo && row.dataset.promo !== "0"
          ? normalize(row.dataset.promo)
          : "";
      const email = normalize(row.dataset.email);
      const id = normalize(row.cells[0] ? row.cells[0].textContent.trim() : "");
      const room =
        row.dataset.room && row.dataset.room !== "0"
          ? normalize(row.dataset.room)
          : "";
      const roleMatch = Array.from(row.querySelectorAll(".badge a")).some((a) =>
        normalize(a.textContent).includes(q)
      );

      let match;
      if (isNumeric) {
        match =
          id === q ||
          promo === q ||
          promo === "m" + q ||
          (room !== "" && room.startsWith(q));
      } else {
        match = name.includes(q) || email.includes(q) || promo.includes(q) || roleMatch;
      }
      row.style.display = match ? "" : "none";
    });
    if (emptyRow) {
      emptyRow.style.display = !q && rows.length === 0 ? "" : "none";
    }
  }

  function updateTabLinks(qValue) {
    document
      .querySelectorAll('[name="gris_pceens_navbar"] a')
      .forEach((link) => {
        const tabUrl = new URL(link.href, window.location.origin);
        if (qValue) {
          tabUrl.searchParams.set("q", qValue);
        } else {
          tabUrl.searchParams.delete("q");
        }
        link.href = tabUrl.pathname + tabUrl.search;
      });
  }

  function buildSearchUrl(qValue) {
    const url = new URL(searchForm.action, window.location.origin);
    const sortInput = searchForm.querySelector('input[name="sort"]');
    const wayInput = searchForm.querySelector('input[name="way"]');
    if (sortInput && sortInput.value) {
      url.searchParams.set("sort", sortInput.value);
    }
    if (wayInput && wayInput.value) {
      url.searchParams.set("way", wayInput.value);
    }
    if (qValue) {
      url.searchParams.set("q", qValue);
    }
    return url;
  }

  function disposeTableTooltips() {
    if (typeof bootstrap === "undefined" || !bootstrap.Tooltip) return;
    sortTable.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      const instance = bootstrap.Tooltip.getInstance(el);
      if (instance) instance.dispose();
    });
  }

  function initTableTooltips() {
    if (typeof bootstrap === "undefined" || !bootstrap.Tooltip) return;
    sortTable.querySelectorAll('[data-bs-toggle="tooltip"]').forEach((el) => {
      bootstrap.Tooltip.getOrCreateInstance(el);
    });
  }

  async function fetchSearchResults(rawQuery) {
    const qValue = rawQuery.trim();
    const url = buildSearchUrl(qValue);

    if (activeController) {
      activeController.abort();
    }
    activeController = new AbortController();

    try {
      const response = await fetch(url.toString(), {
        headers: { "X-Requested-With": "fetch" },
        signal: activeController.signal,
      });
      if (!response.ok) return;

      const html = await response.text();
      const doc = new DOMParser().parseFromString(html, "text/html");
      const newSortTable = doc.getElementById("sort-table");
      if (!newSortTable) return;

      disposeTableTooltips();
      sortTable.innerHTML = newSortTable.innerHTML;

      const newTableHead = doc.querySelector("table thead");
      if (tableHead && newTableHead) {
        tableHead.innerHTML = newTableHead.innerHTML;
      }

      const newPagination = doc.getElementById("pceen-pagination");
      if (paginationContainer && newPagination) {
        paginationContainer.innerHTML = newPagination.innerHTML;
      }

      const newTotal = doc.getElementById("pceen-total-count");
      if (totalCountBadge && newTotal) {
        totalCountBadge.textContent = newTotal.textContent;
      }

      const newRezModals = doc.getElementById("pceen-rez-modals");
      if (rezModalsContainer && newRezModals) {
        rezModalsContainer.innerHTML = newRezModals.innerHTML;
      }

      if (emptyRow) {
        const hasRows = sortTable.querySelectorAll("tr").length > 0;
        emptyRow.style.display = hasRows ? "none" : "";
      }

      window.history.replaceState(null, "", url.pathname + url.search);
      updateTabLinks(qValue);

      if (typeof flask_moment_render_all === "function") {
        flask_moment_render_all();
      }
      initTableTooltips();
    } catch (err) {
      if (err.name !== "AbortError") {
        console.error("Live search failed:", err);
      }
    }
  }

  searchInput.addEventListener("input", function () {
    const val = searchInput.value;
    updateClearButton(val.trim());
    filterCurrentRows(val);
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(() => {
      fetchSearchResults(val);
    }, 300);
  });

  searchForm.addEventListener("submit", function (event) {
    event.preventDefault();
    clearTimeout(debounceTimer);
    fetchSearchResults(searchInput.value);
  });

  if (clearBtn) {
    clearBtn.addEventListener("click", function (event) {
      event.preventDefault();
      searchInput.value = "";
      updateClearButton("");
      filterCurrentRows("");
      clearTimeout(debounceTimer);
      fetchSearchResults("");
      searchInput.focus();
    });
  }

  window.addEventListener("pageshow", function () {
    updateClearButton(searchInput.value.trim());
  });
});
