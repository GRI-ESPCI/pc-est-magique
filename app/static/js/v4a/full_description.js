const reps = document.getElementById("representations").getElementsByTagName("li");
const del_rep_btn = document.getElementById('del-representations');
const confirm_del = new bootstrap.Modal(
    document.getElementById('confirm-del')
);
const edit_rep_btn = document.getElementById("edit-representations");
const modal_edit_ref = document.getElementById('mo-v4a-rep-edit');
const modal_edit = new bootstrap.Modal(modal_edit_ref);

var toggle_del = false;
var toggle_edit = false;

del_rep_btn.addEventListener('click', () => {
    toggle_btn('del');
});
edit_rep_btn.addEventListener('click', () => {
    toggle_btn('edit');
});

function toggle_btn(event_type) {
    for(const li of reps) {
        const del = li.getElementsByClassName("del-representation")[0];
        const edit = li.getElementsByClassName("edit-representation")[0];
        const url_del = del.dataset.url;
        const edit_data = edit.dataset;

        if(event_type == 'del') {
            if (toggle_del) {
                del.style.display = 'none';
                edit.style.display = 'none';
            } else {
                del.style.display = 'inline-block';
                edit.style.display = 'none';
                del.addEventListener('click', () => {
                    var confirm_del_btn = document.getElementById('confirm-del-btn');
                    const confirm_del_btn_new = confirm_del_btn.cloneNode(true);
                    confirm_del_btn.replaceWith(confirm_del_btn_new)
                    confirm_del_btn_new.addEventListener('click', () =>  {
                        delete_representation(url_del, li);
                    });
                    confirm_del.show();
                });
            }
        } else if (event_type == 'edit') {
            if (toggle_edit) {
                edit.style.display = 'none';
                del.style.display = 'none';
            } else {
                edit.style.display = 'inline-block';
                del.style.display = 'none';
                edit.addEventListener('click', () => {
                    modal_edit_ref.querySelector('[name="date"]').value = edit_data.date;
                    modal_edit_ref.querySelector('[name="sits"]').value = parseInt(edit_data.sits);

                    const confirm_edit_btn = document.getElementById('confirm-edit-btn');
                    const confirm_edit_btn_new = confirm_edit_btn.cloneNode(true);
                    confirm_edit_btn.replaceWith(confirm_edit_btn_new);
                    confirm_edit_btn_new.addEventListener('click', (e) => {
                        edit_representation(edit_data, li);
                    });
                    modal_edit.show();
                });
            }
        }
    }
    if (event_type == 'del') {
        toggle_del = !toggle_del;
        toggle_edit = false;
    } else if (event_type == 'edit') {
        toggle_edit = !toggle_edit;
        toggle_del = false;
    }
}

function delete_representation(url, li) {
    confirm_del.hide();
    fetch(url).then((response) => {
        if(response.ok) {
            li.remove();
        }
    });
}

function edit_representation(data, li) {
    const form = document.getElementById("edit-form");

    modal_edit.hide();
    fetch(data.url, {
        method: "POST",
        body: new FormData(form)
    }).then((response) => {
        response.json().then((r) => {
            li.getElementsByClassName('rep-time')[0].innerText = moment(r.date).format("HH:mm");
            li.getElementsByClassName('rep-date')[0].innerText = moment(r.date).format("dddd DD MMMM YYYY");
        });
    });
}