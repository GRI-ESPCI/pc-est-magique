const [collection, album] = window.location.pathname.replace("/photos/", "").split("/");

/* ----- EDIT PHOTO MODAL ----- */

const moEdit = document.getElementById("mo-edit");

function customizeEditModal(data) {
  moEdit.querySelectorAll(".form-control").forEach((elem) => (elem.value = null));
  moEdit.querySelector("#photo_name").value = data["file_name"];
  moEdit.querySelector("#caption").value = data["caption"];
  moEdit.querySelector("#author_str").value = data["author_str"];
  moEdit.querySelector("#date").value = data["date"];
  moEdit.querySelector("#time").value = data["time"];
  moEdit.querySelector("#lat").value = data["lat"];
  moEdit.querySelector("#lng").value = data["lng"];
}

// Edit button click: prepare edit modal (+ show it, handled by Bootstrap)
function preparePhotoEdit(button) {
  div = button.parentNode.parentNode;
  photo_anchor = div.getElementsByTagName("a")[0];
  customizeEditModal(photo_anchor.dataset);
}

// Edit modal submission: send request to API
const editForm = document.getElementById("edit-photo-form");
if (editForm) {
  const moEditModal = new bootstrap.Modal(moEdit);
  editForm.addEventListener("submit", (event) => {
    event.preventDefault();
    fetch("/api/photos/edit_photo", {
      method: "POST",
      body: new FormData(editForm),
    }).then((response) => {
      moEditModal.hide();
      response.text().then((text) => {
        if (response.ok) showToast(text, "success");
        else showToast(JSON.parse(text).error.message, "danger");
      });
    });
  });
}

/* ----- FAVORITE BUTTON ----- */

function favoritePhoto(button) {
  const div = button.parentNode.parentNode;
  const photo_anchor = div.getElementsByTagName("a")[0];

  const data = new FormData();
  data.append("collection", collection);
  data.append("album", album);
  data.append("photo", photo_anchor.dataset["file_name"]);

  fetch("/api/photos/star_photo", {
    method: "POST",
    body: data,
  }).then((response) => {
    if (response.ok) {
      const currentFeaturedPhoto = document.getElementsByClassName("current-feat")[0];
      [currentFeaturedPhoto.outerHTML, button.outerHTML] = [button.outerHTML, currentFeaturedPhoto.outerHTML];
      response.text().then((text) => showToast(text, "success"));
    } else {
      response.json().then((data) => showToast(data.error.message, "danger"));
    }
  });
}

/* ----- DELETE BUTTON ----- */

function deletePhoto(button) {
  const div = button.parentNode.parentNode;
  const photo_anchor = div.getElementsByTagName("a")[0];

  const data = new FormData();
  data.append("collection", collection);
  data.append("album", album);
  data.append("photo", photo_anchor.dataset["file_name"]);

  fetch("/api/photos/delete_photo", {
    method: "POST",
    body: data,
  }).then((response) => {
    if (response.ok) {
      div.classList.add("opacity-25");
      div.classList.add("pe-none");
      response.text().then((text) => showToast(text, "success"));
    } else {
      response.json().then((data) => showToast(data.error.message, "danger"));
    }
  });
}

/* ----- UPLOADER ----- */
// DEPENDENCIES: static/js/_dist/uppy/uppy.min.js, static/js/_dist/uppy/fr_FR.min.js

const uppy = new Uppy.Uppy({
  locale: Uppy.locales.fr_FR,
  restrictions: {
    maxFileSize: 100000000,
    minFileSize: 10000,
    allowedFileTypes: [".jpg", ".jpeg", ".png"],
  },
  meta: { collection, album },
})
  .use(Uppy.Dashboard, {
    trigger: "#uppy-photo-uploader",
    closeModalOnClickOutside: true,
    disablePageScrollWhenModalOpen: false,
    note: "Images .jpg / .jpeg / .png uniquement, maximum 100 MB par fichier",
    fileManagerSelectionType: "both",
    locale: Uppy.locales.fr_FR,
  })
  .use(Uppy.XHRUpload, {
    endpoint: "/api/photos/upload",
    limit: 4,
    getResponseError: (responseText, response) => {
      return new Error(`${JSON.parse(responseText).error.message} (HTTP ${JSON.parse(responseText).error.status})`);
    },
  });
