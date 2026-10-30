
// Edit pceen discontent modal
var moDiscontentEdit = document.getElementById("mo-pceen-edit");
var titleDE = moDiscontentEdit.querySelector(".modal-title");

moDiscontentEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var pceenId = button.dataset["pceenId"];
  var pceenName = button.dataset["pceenNom"];
  var pceenDiscontent = button.dataset["pceenDiscontent"];
  
  titleDE.textContent = "Éditer le mécontentement de " + pceenName + " (ID : " + pceenId + ")";

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[0].value = pceenId;
  document.getElementsByName("discontent")[0].value = pceenDiscontent;
});

// Search bar filter for PCéens table (by name or promo)
var pceenSearch = document.getElementById("pceen-search");
if (pceenSearch) {
  const normalize = (str) =>
    (str || "")
      .toString()
      .normalize("NFD")
      .replace(/[\u0300-\u036f]/g, "")
      .toLowerCase();

  pceenSearch.addEventListener("input", function (e) {
    const q = normalize(e.target.value.trim());
    const rows = document.querySelectorAll("#sort-table tr");
    rows.forEach((row) => {
      const name = normalize(row.dataset.name);
      const promo = normalize(row.dataset.promo);
      const match = !q || name.includes(q) || promo.includes(q);
      row.style.display = match ? "" : "none";
    });
  });
}

