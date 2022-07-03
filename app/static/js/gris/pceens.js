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
        name.classList.add(data["dark"] ? "text-light" : "text-dark");
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
