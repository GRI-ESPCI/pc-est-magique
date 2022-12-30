var editModeElements = document.getElementsByClassName("edit-mode-only");
var viewModeElements = document.getElementsByClassName("view-mode-only");

function enable_edit_mode() {
  for (const element of viewModeElements) element.classList.add("d-none");
  for (const element of editModeElements) element.classList.remove("d-none");
  window.history.replaceState({}, document.title, "?edit");
}

function disable_edit_mode() {
  for (const element of editModeElements) element.classList.add("d-none");
  for (const element of viewModeElements) element.classList.remove("d-none");
  window.history.replaceState({}, document.title, window.location.pathname);
}
