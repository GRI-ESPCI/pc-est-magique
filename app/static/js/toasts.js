var toastElList = [].slice.call(document.getElementsByClassName("show-toast"));
var toastList = toastElList.filter((toastEl) => !toastEl.hidden).map((toastEl) => new bootstrap.Toast(toastEl));
toastList.forEach((toast) => toast.show());

function showToast(text, category) {
  var toastEl = document.getElementById(`new-toast-${category}`);
  toastEl.getElementsByClassName("toast-body")[0].innerHTML = text;
  var toast = new bootstrap.Toast(toastEl);
  toast.show();
}
