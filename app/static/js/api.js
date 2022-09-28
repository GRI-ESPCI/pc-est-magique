function post_and_reload(url, form) {
  // event.preventDefault();
  // form.role_id.value = event.target.querySelector("input[name='role_id']").value;
  // form.type_name.value = event.target.querySelector("input[name='type_name']:checked").value;
  // form.scope_name.value = event.target.querySelector("input[name='scope_name']:checked").value;
  // form.ref_id.value = event.target.querySelector("select[name='ref_id']").value;
  console.log(url);
  if (form) body = new FormData(form);
  else body = null;

  fetch(url, {
    method: "POST",
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
