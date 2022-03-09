var delete_svg = document.getElementById("icon-delete");
var revert_svg = document.getElementById("icon-revert");
var form = document.getElementById("security-form");
var new_badge = document.getElementById("new-role-template")
                        .querySelector(".badge");

function remove_role(elem, pceen_id, role_id) {
    // elem = SVG element of the X button
    form.action.value = "remove";
    form.pceen_id.value = pceen_id;
    form.role_id.value = role_id;
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
                restore_role(elem, pceen_id, role_id);
            }
        } else {
            response.text().then(text => alert(text));
        }
    })
}

function add_role(elem, pceen_id, role_id) {
    // elem = SVG element of the + button
    form.action.value = "add";
    form.pceen_id.value = pceen_id;
    form.role_id.value = role_id;
    fetch("", {
        method: "POST",
        body: new FormData(form),
    })
    .then(response => {
        if (response.ok) {
            response.json().then(data => {
                var badge = new_badge.cloneNode(true);
                elem.closest("td").insertBefore(badge,
                                                elem.closest(".add-role"));
                var name = badge.querySelector(".role_name")
                name.textContent = data["name"];
                name.href = name.href + "#" + data["id"];
                badge.style.setProperty("background-color",
                                        "#" + data["color"]);
                name.classList.add(data["dark"] ? "text-light" : "text-dark");
                badge.querySelector("svg").onclick = function() {
                    remove_role(badge.querySelector("svg"), pceen_id, role_id);
                };
                elem.remove();
            });
        } else {
            response.text().then(text => alert(text));
        }
    })
}

function restore_role(elem, pceen_id, role_id) {
    // elem = SVG element of the revert button
    form.action.value = "add";
    form.pceen_id.value = pceen_id;
    form.role_id.value = role_id;
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
            elem.onclick = function() { remove_role(elem, pceen_id, role_id); }
        } else {
            response.text().then(text => alert(text));
        }
    })
}
