function post_and_reload(url, form, method = "POST") {
  if (form) body = new FormData(form);
  else body = null;

  fetch(url, {
    method: method,
    body: body,
  }).then((response) => {
    if (response.ok) {
      location.reload();
    } else {
      response.json().then((data) => alert(JSON.stringify(data["error"])));
      location.reload();
    }
  });
}
