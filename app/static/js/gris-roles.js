var delete_svg = document.getElementById("icon-delete");
var revert_svg = document.getElementById("icon-revert");
var form = document.getElementById("security-form");
var new_badge = document.getElementById("new-perm-template")
                        .querySelector(".badge");
var addPermissionModal = document.getElementById('addPermissionModal')
var add_perm_form = document.getElementById("add-perm-form")
add_perm_form.addEventListener("submit", add_perm);


function remove_perm(elem, role_id, perm_id) {
    // elem = SVG element of the X button
    form.action.value = "remove";
    form.role_id.value = role_id;
    form.perm_id.value = perm_id;
    fetch("", {
        method: "POST",
        body: new FormData(form),
    })
    .then(response => {
        if (response.ok) {
            var badge = elem.closest(".badge");
            badge.style.setProperty("transition", "all 0.2s");
            badge.style.setProperty("opacity", "30%");
            badge.style.setProperty("text-decoration", "line-through");
            // badge.style.setProperty("font-style", "italic");
            elem.innerHTML = revert_svg.innerHTML;
            elem.onclick = function() {
                restore_perm(elem, role_id, perm_id);
            }
        } else {
            response.text().then(text => alert(text));
        }
    })
}


function add_perm(event) {
    event.preventDefault();
    form.action.value = "add";
    form.role_id.value = event.target.querySelector("input[name='role_id']").value;
    form.type_name.value = event.target.querySelector("input[name='type_name']:checked").value;
    form.scope_name.value = event.target.querySelector("input[name='scope_name']:checked").value;
    form.ref_id.value = event.target.querySelector("select[name='ref_id']").value;
    fetch("", {
        method: "POST",
        body: new FormData(form),
    })
    .then(response => {
        if (response.ok) {
            location.reload();
        } else {
            response.text().then(text => alert(text));
        }
    })
}


function restore_perm(elem, role_id, perm_id) {
    // elem = SVG element of the revert button
    form.action.value = "add";
    form.role_id.value = role_id;
    form.perm_id.value = perm_id;
    fetch("", {
        method: "POST",
        body: new FormData(form),
    })
    .then(response => {
        if (response.ok) {
            var badge = elem.closest(".badge");
            badge.style.removeProperty("opacity");
            badge.style.removeProperty("text-decoration");
            // badge.style.removeProperty("font-style");
            elem.innerHTML = delete_svg.innerHTML;
            elem.onclick = function() { remove_role(elem, role_id, perm_id); }
        } else {
            response.text().then(text => alert(text));
        }
    })
}


function create_option(select, value, name) {
    option = document.createElement("option");
    option.value = value;
    option.innerHTML = name;
    select.appendChild(option)
}

function get_elements(elem, scope_name) {
    // elem = SVG element of the revert button
    console.log(scope_name)
    if (!elem.checked)  return;
    select = elem.closest(".modal-body").querySelector("select");
    select.disabled = true;
    select.innerHTML = "";      // remove all options
    create_option(select, "", "Loading...");

    form.action.value = "get_elements";
    form.scope_name.value = scope_name;
    fetch("", {
        method: "POST",
        body: new FormData(form),
    })
    .then(response => {
        if (response.ok) {
            response.json().then(data => {
                console.log(data);
                select.innerHTML = "";  // remove "Loading..."
                if (data["allow_elem"]) {
                    if (!data["need_elem"]) {
                        create_option(select, "", "(all)");
                    }
                    data["items"].forEach(
                        item => create_option(select, item[0], item[1])
                    );
                    select.disabled = false;
                } else {
                    create_option(select, "", "N/A");
                }
            });
        } else {
            response.text().then(text => alert(text));
        }
    })
}


addPermissionModal.addEventListener("show.bs.modal", function (event) {
    var button = event.relatedTarget;
    var id = button.getAttribute("data-role-id");
    addPermissionModal.querySelector(".pem-role-id").value = id;
    var name = button.getAttribute("data-role-name");
    addPermissionModal.querySelector(".pem-role-name").innerHTML = name;
})
