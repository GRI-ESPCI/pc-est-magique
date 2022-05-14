
function show_edit_form () {
    var header = document.getElementById("header");
    var form = document.getElementById("modify-form");
    header.hidden = true;
    form.hidden = false;
    window.history.pushState({}, document.title, "?edit");
}

function hide_edit_form () {
    var header = document.getElementById("header");
    var form = document.getElementById("modify-form");
    header.hidden = false;
    form.hidden = true;
    window.history.pushState({}, document.title, window.location.pathname);
}
