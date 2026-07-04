document.addEventListener("DOMContentLoaded", function() {
    const targetSelect = document.getElementById("target");
    const roleGroup = document.getElementById("role-select-group");

    if (targetSelect && roleGroup) {
        function updateVisibility() {
            if (targetSelect.value === "role") {
                roleGroup.style.display = "block";
            } else {
                roleGroup.style.display = "none";
            }
        }

        targetSelect.addEventListener("change", updateVisibility);
        updateVisibility();
    }
});

function mo_add_role(elem, role_id) {
    const select = document.getElementById("roles");
    const option = select.querySelector(`option[value="${role_id}"]`);
    if (option) {
        option.selected = true;
    }
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
    dropdownElem.style.display = "";
    badge.remove();
}
