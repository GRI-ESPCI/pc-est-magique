// Add salle modalmosalleAdd
var moSpectacleAdd = document.getElementById("mo-spectacle-add");

moSpectacleAdd.addEventListener("show.bs.modal", function (event) {
  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[1].value = null;
  document.getElementsByName("salle_id")[1].value = null;
  document.getElementsByName("nom")[1].value = null;
  document.getElementsByName("categorie")[1].value = null;
  document.getElementsByName("image")[1].value = null;
  document.getElementsByName("description")[1].value = null;
  document.getElementsByName("date")[1].value = null;
  document.getElementsByName("time")[1].value = null;
  document.getElementsByName("nb_tickets")[1].value = null;
  document.getElementsByName("price")[1].value = null;



});


// Edit spectacle modal
var moSpectacleEdit = document.getElementById("mo-spectacle-edit");
var titleSeE = moSpectacleEdit.querySelector(".modal-title");

moSpectacleEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var spectacleId = button.dataset["spectacleId"];
  var spectacleNom = button.dataset["spectacleNom"];
  var saisonNom = button.dataset["saisonNom"]
  var salleId = button.dataset["salleId"];
  var salleNom = button.dataset["salleNom"]
  var spectacleNom = button.dataset["spectacleNom"];
  var spectacleCategorie = button.dataset["spectacleCategorie"];
  var spectacleDescription = button.dataset["spectacleDescription"];
  var [spectacleDate, spectacleTime] = button.dataset["spectacleDate"].split(" ");
  var spectacleTime=spectacleTime.substring(0,5)
  var spectacleNbTickets = button.dataset["spectacleNbTickets"];
  var spectaclePrice = button.dataset["spectaclePrice"];

  titleSeE.textContent = "Editer spectacle " + spectacleId + " - " + spectacleNom + " - " + salleNom + " - " + saisonNom;

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[0].value = spectacleId;
  document.getElementsByName("salle_id")[0].value = salleId;
  document.getElementsByName("nom")[0].value = spectacleNom;
  document.getElementsByName("categorie")[0].value = spectacleCategorie;
  document.getElementsByName("image")[0].value = null;
  document.getElementsByName("description")[0].value = spectacleDescription;
  document.getElementsByName("date")[0].value = spectacleDate;
  document.getElementsByName("time")[0].value = spectacleTime;
  document.getElementsByName("nb_tickets")[0].value = spectacleNbTickets;
  document.getElementsByName("price")[0].value = spectaclePrice;

});
