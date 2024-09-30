// Add Period moPeriodAdd
var moPeriodAdd = document.getElementById("mo-period-add");

moPeriodAdd.addEventListener("show.bs.modal", function (event) {
  document.getElementsByName("id")[0].value = null;
  document.getElementsByName("start_date")[0].value = null;
  document.getElementsByName("end_date")[0].value = null;
  document.getElementsByName("disabled_days")[0].value = null;
  document.getElementsByName("activate")[0].value = null;
});

// Edit panier bio period modal
var moPeriodEdit = document.getElementById("mo-period-edit");
var titlePE = moPeriodEdit.querySelector(".modal-title");

moPeriodEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var periodId = button.dataset["periodId"];
  var periodStartDate = button.dataset["periodStartDate"];
  var periodEndDate = button.dataset["periodEndDate"];
  var periodDisabledDays = button.dataset["periodDisabledDays"];
  var periodActive = button.dataset["periodActive"];

  titlePE.textContent = "Editer période " + periodId;


  if (button.dataset["periodActive"] == "True") {
    document.getElementsByName("activate")[1].checked = true;
  } else {
    document.getElementsByName("activate")[1].checked = false;
  }

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[1].value = periodId;
  document.getElementsByName("start_date")[1].value = periodStartDate;
  document.getElementsByName("end_date")[1].value = periodEndDate;
  document.getElementsByName("disabled_days")[1].value = periodDisabledDays;
  document.getElementsByName("activate")[1].value = periodActive;
});
