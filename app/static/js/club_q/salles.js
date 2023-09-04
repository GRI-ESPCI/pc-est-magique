// Add salle modalmosalleAdd
var moSalleAdd = document.getElementById("mo-salle-add");

moSalleAdd.addEventListener("show.bs.modal", function (event) {
  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[1].value = null;
  document.getElementsByName("nom")[1].value = null;
  document.getElementsByName("description")[1].value = null;
  document.getElementsByName("url")[1].value =  null;
  document.getElementsByName("adresse")[1].value = null;
  document.getElementsByName("latitude")[1].value = 0;
  document.getElementsByName("longitude")[1].value = 0;



});

// Edit salle modal
var moSalleEdit = document.getElementById("mo-salle-edit");
var titleSaE = moSalleEdit.querySelector(".modal-title");

moSalleEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var salleId = button.dataset["salleId"];
  var salleNom = button.dataset["salleNom"];
  var salleDescription = button.dataset["salleDescription"];
  var salleUrl = button.dataset["salleUrl"];
  var salleAdresse = button.dataset["salleAdresse"];
  var salleLatitude = button.dataset["salleLatitude"];
  var salleLongitude = button.dataset["salleLongitude"];

  titleSaE.textContent = "Editer salle ID " + salleId + " - " + salleNom;

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[0].value = salleId;
  document.getElementsByName("nom")[0].value = salleNom;
  document.getElementsByName("description")[0].value = salleDescription;
  document.getElementsByName("url")[0].value = salleUrl;
  document.getElementsByName("adresse")[0].value = salleAdresse;
  document.getElementsByName("latitude")[0].value = salleLatitude;
  document.getElementsByName("longitude")[0].value = salleLongitude;



});

