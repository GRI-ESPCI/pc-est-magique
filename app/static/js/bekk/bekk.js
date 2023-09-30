// Add bekk moBekkAdd
var moBekkAdd = document.getElementById("mo-bekk-add");

moBekkAdd.addEventListener("show.bs.modal", function (event) {
  // Set the form field values using Flask-WTF's API

  var today = new Date();
  var dd = String(today.getDate()).padStart(2, '0');
  var mm = String(today.getMonth() + 1).padStart(2, '0'); //January is 0!
  var yyyy = today.getFullYear();

  today = yyyy + '-' + mm + '-' + dd;


  document.getElementsByName("id")[1].value = null;
  document.getElementsByName("bekk_name")[1].value = null;
  document.getElementsByName("promo")[1].value = null;
  document.getElementsByName("date")[1].value =  today;
  document.getElementsByName("pdf_file")[1].value =  null;
});

// Edit bekk modal
var moBekkEdit = document.getElementById("mo-bekk-edit");
var titleBekk = moBekkEdit.querySelector(".modal-title");

moBekkEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var bekkId = button.dataset["bekkId"];
  var bekkName = button.dataset["bekkName"];
  var bekkPromo = button.dataset["bekkPromo"];
  var bekkDate = button.dataset["bekkDate"];


  titleBekk.textContent = "Editer Bekk ID " + bekkId + " - " + bekkName;

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[0].value = bekkId;
  document.getElementsByName("bekk_name")[0].value = bekkName;
  document.getElementsByName("promo")[0].value = bekkPromo;
  document.getElementsByName("date")[0].value = bekkDate;
  document.getElementsByName("pdf_file")[0].value =  null;
});






