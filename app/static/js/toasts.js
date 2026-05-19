var toastElList = [].slice.call(document.getElementsByClassName("show-toast"));
var toastList = toastElList.filter((toastEl) => !toastEl.hidden).map((toastEl) => new bootstrap.Toast(toastEl));
toastList.forEach((toast) => toast.show());

function showToast(text, category) {
  var toastEl = document.getElementById(`new-toast-${category}`);
  var messageSpan = toastEl.querySelector(".toast-message-text");
  if (messageSpan) {
    messageSpan.innerHTML = text;
  } else {
    toastEl.getElementsByClassName("toast-body")[0].innerHTML = text;
  }
  var toast = new bootstrap.Toast(toastEl);
  toast.show();
}
