

// Edit add modal
var moVoeuAdd = document.getElementById("mo-voeu-add");




// Edit voeu modal
var moVoeuEdit = document.getElementById("mo-voeu-edit");
var titleVE = moVoeuEdit.querySelector(".modal-title");

moVoeuEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var voeuId = button.dataset["voeuId"];
  var spectacleName = button.dataset["voeuSpectacle"];
  var pceenName = button.dataset["voeuPceen"];
  var priorite = button.dataset["voeuPriorite"];
  var placesDemandees = button.dataset["voeuPlacesDemandees"];
  var placesMinimum = button.dataset["voeuPlacesMinimum"];
  var placesAttribuees = button.dataset["voeuPlacesAttribuees"];


  titleVE.textContent = "Editer voeu " + voeuId + " - " + spectacleName + " - " + pceenName;

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id_edit")[0].value = voeuId;
  document.getElementsByName("priorite_edit")[0].value = priorite;
  document.getElementsByName("places_demandees_edit")[0].value = placesDemandees;
  document.getElementsByName("places_minimum_edit")[0].value = placesMinimum;
  document.getElementsByName("places_attribuees_edit")[0].value = placesAttribuees;

});




/*
// Edit spectacle modal
var moSpectacleEdit = document.getElementById("mo-spectacle-edit");
var titleSE = moVoeuEdit.querySelector(".modal-title");

moSpectacleEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var id = button.dataset["id"];
  var name = button.dataset["name"];
  var season = button.dataset["season"];
  var salle = button.dataset["salle"];
  var category = button.dataset["category"];
  var image = button.dataset["image"];
  var description = button.dataset["description"];
  var date = button.dataset["date"];
  var tickets = button.dataset["tickets"];
  var price = button.dataset["price"];


  titleSE.textContent = "Editer spectacle " + name + " - " + salle;

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[0].value = id;
  document.getElementsByName("season")[0].value = season;
  document.getElementsByName("salle")[0].value = salle;
  document.getElementsByName("category")[0].value = category;
  document.getElementsByName("image")[0].value = image;
  document.getElementsByName("description")[0].value = description;
  document.getElementsByName("date")[0].value = date;
  document.getElementsByName("tickets")[0].value = tickets;
  document.getElementsByName("price")[0].value = price;

  // Delete voeu button click event
  var deleteButton = moSpectacleEdit.querySelector("#delete-spectacle-btn");
  deleteButton.addEventListener("click", function () {
    // Construct the URL with the voeu ID
    var deleteUrl = `/club_q/delete_spectacle/${spectacleId}`;
    // Redirect to the delete URL
    window.location.href = deleteUrl;
  });
});
  
*/