function post_and_reload(url, form, method = "POST", keep_open_selector = null, seamless_swap_selectors = null) {
  let body;
  if (form) body = new FormData(form);
  else body = null;

  fetch(url, {
    method: method,
    body: body,
  }).then((response) => {
    if (response.ok) {
      if (seamless_swap_selectors && seamless_swap_selectors.length > 0) {
        fetch(location.href).then(res => res.text()).then(html => {
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");
          
          seamless_swap_selectors.forEach(selector => {
            const oldEls = document.querySelectorAll(selector);
            const newEls = doc.querySelectorAll(selector);
            for (let i = 0; i < oldEls.length && i < newEls.length; i++) {
              oldEls[i].innerHTML = newEls[i].innerHTML;
            }
          });
          
          const newToasts = doc.querySelectorAll('.toast-container .toast');
          const toastContainer = document.querySelector('.toast-container');
          if (toastContainer && newToasts.length > 0) {
            newToasts.forEach(t => {
              if (t.id && t.id.startsWith('new-toast-')) return;
              toastContainer.appendChild(t);
              if (typeof bootstrap !== 'undefined') {
                const bsToast = new bootstrap.Toast(t);
                bsToast.show();
              }
            });
          }
          
          if (typeof initTooltips === 'function') initTooltips();
        });
      } else {
        if (keep_open_selector) {
          sessionStorage.setItem('keep_open_selector', keep_open_selector);
        }
        location.reload();
      }
    } else {
      response.json().then((data) => alert(JSON.stringify(data["error"])));
      location.reload();
    }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  const keepOpen = sessionStorage.getItem('keep_open_selector');
  if (keepOpen) {
    sessionStorage.removeItem('keep_open_selector');
    const el = document.querySelector(keepOpen);
    if (el && typeof bootstrap !== 'undefined') {
      new bootstrap.Dropdown(el).show();
    }
  }
});
