

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
