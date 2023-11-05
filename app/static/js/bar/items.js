// Ban modal
var modal = document.getElementById("edit-item-modal");
var title = modal.querySelector(".modal-title");
var [template_new, template_update] = title.textContent.split(" || ");

modal.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  modal.querySelector("#id").value = button.dataset["itemId"] || null;
  modal.querySelectorAll(".form-control").forEach((elem) => (elem.value = null));
  modal.querySelector("#is_quantifiable").checked = false;
  update_quantifiable_checkbox();
  modal.querySelector("#is_favorite").checked = false;
  update_favorite_checkbox();
  modal.querySelector("#is_alcohol").checked = false;
  update_alcohol_checkbox();

  if (button.dataset["itemId"]) {
    // Update existing item
    title.textContent = template_update.replace("_name_", button.dataset["itemName"]);
    modal.querySelector("#name").value = button.dataset["itemName"];
    if (button.dataset["quantity"]) {
      modal.querySelector("#is_quantifiable").checked = true;
      update_quantifiable_checkbox();
      modal.querySelector("#quantity").value = button.dataset["quantity"];
    }
    modal.querySelector("#price").value = button.dataset["price"];

    modal.querySelector("#alcohol_mass").value = button.dataset["alcoholMass"];
    if (button.dataset["alcoholMass"] == 0) {
      modal.querySelector("#alcohol_mass").value = null;
      modal.querySelector("#is_alcohol").checked = false

    }
    else {
      modal.querySelector("#is_alcohol").checked = true;
      update_alcohol_checkbox();
      modal.querySelector("#alcohol_mass").value = button.dataset["alcoholMass"];
    }

    if (button.dataset["favoriteIndex"] != "0") {
      modal.querySelector("#is_favorite").checked = true;
      update_favorite_checkbox();
      modal.querySelector("#favorite_index").value = button.dataset["favoriteIndex"];
    }
  } else {
    // New ban
    title.textContent = template_new;
  }
});

function update_favorite_checkbox() {
  if (favoriteCheckbox.checked) {
    modal.querySelector("#favoriteIndexInput").classList.remove("text-muted");
    modal.querySelector("#favorite_index").disabled = false;
  } else {
    modal.querySelector("#favoriteIndexInput").classList.add("text-muted");
    modal.querySelector("#favorite_index").disabled = true;
  }
}

function update_quantifiable_checkbox() {
  if (quantifiableCheckbox.checked) {
    modal.querySelector("#quantityInput").classList.remove("text-muted");
    modal.querySelector("#quantity").disabled = false;
  } else {
    modal.querySelector("#quantityInput").classList.add("text-muted");
    modal.querySelector("#quantity").disabled = true;
  }
}

function update_alcohol_checkbox() {
  if (isAlcoholCheckbox.checked) {
    modal.querySelector("#alcoholMassInput").classList.remove("text-muted");
    modal.querySelector("#alcohol_mass").disabled = false;
  } else {
    modal.querySelector("#alcohol_mass").value = null
    modal.querySelector("#alcoholMassInput").classList.add("text-muted");
    modal.querySelector("#alcohol_mass").disabled = true;
  }
}


favoriteCheckbox = modal.querySelector("#is_favorite");
favoriteCheckbox.addEventListener("change", update_favorite_checkbox);

quantifiableCheckbox = modal.querySelector("#is_quantifiable");
quantifiableCheckbox.addEventListener("change", update_quantifiable_checkbox);

isAlcoholCheckbox = modal.querySelector("#is_alcohol");
isAlcoholCheckbox.addEventListener("change", update_alcohol_checkbox);
