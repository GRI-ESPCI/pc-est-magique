// Add saison modal
var moSaisonAdd = document.getElementById("mo-saison-add");

moSaisonAdd.addEventListener("show.bs.modal", function (event) {
  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[1].value = null;
  document.getElementsByName("nom")[1].value = null;
  document.getElementsByName("promo")[1].value = null;
  document.getElementsByName("debut")[1].value =  null;
  document.getElementsByName("fin")[1].value = null;
  document.getElementsByName("fin_inscription")[1].value = null;


});

// Edit saison modal
var moSaisonEdit = document.getElementById("mo-saison-edit");
var titleSE = moSaisonEdit.querySelector(".modal-title");

moSaisonEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var saisonId = button.dataset["saisonId"];
  var saisonNom = button.dataset["saisonNom"];
  var saisonPromo = button.dataset["saisonPromo"];
  var saisonDebut = button.dataset["saisonDebut"];
  var saisonFin = button.dataset["saisonFin"];
  var saisonFinInscription = button.dataset["saisonFinInscription"];

  titleSE.textContent = "Editer saison ID " + saisonId + " - " + saisonNom + " - " + saisonPromo;

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[0].value = saisonId;
  document.getElementsByName("nom")[0].value = saisonNom;
  document.getElementsByName("promo")[0].value = saisonPromo;
  document.getElementsByName("debut")[0].value = saisonDebut;
  document.getElementsByName("fin")[0].value = saisonFin;
  document.getElementsByName("fin_inscription")[0].value = saisonFinInscription;


});

