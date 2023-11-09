document.getElementById("wysiwyg_editor").style.display = "none";

var toolbarOptions = [
  [{ size: ["small", false, "large", "huge"] }],
  [{ font: [] }],

  ["bold", "italic", "underline", "strike"],
  ["blockquote", "code-block"],

  [{ list: "ordered" }, { list: "bullet" }],
  [{ script: "sub" }, { script: "super" }],

  [{ color: [] }, { background: [] }],

  ["link", "image", "video"],
];

var quill = new Quill("#editor", {
  modules: {
    toolbar: toolbarOptions,
  },
  theme: "snow",
});

document.getElementById("edit-text").addEventListener("click", function () {
  document.getElementById("wysiwyg_editor").style.display = "block";
  document.getElementById("intro_text").style.display = "none";

  document.getElementById("save-text").addEventListener("click", function () {
    var htmlContent = quill.root.innerHTML;
    
    path = "/" + folder + "/edit_text"

    fetch("/" +   folder + "/edit_text", {
      method: "POST",
      body: new URLSearchParams({ content: htmlContent }),
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
      },
    })
    .then(function() {
      location.reload();
    })
  });
});
