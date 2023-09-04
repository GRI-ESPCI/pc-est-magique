
// Edit pceen discontent modal
var moDiscontentEdit = document.getElementById("mo-pceen-edit");
var titleDE = moDiscontentEdit.querySelector(".modal-title");

moDiscontentEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var pceenId = button.dataset["pceenId"];
  var pceenName = button.dataset["pceenName"];
  var pceenDiscontent = button.dataset["pceenDiscontent"];
  
  titleDE.textContent = "Editer le mécontement de " + pceenName + " ID : " + pceenId;

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[0].value = pceenId;
  document.getElementsByName("discontent")[0].value = pceenDiscontent;


});
