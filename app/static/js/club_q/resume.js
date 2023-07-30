/*
var moUser = document.getElementById("mo-user");
var title = moUser.querySelector(".modal-title");
title.textContent = "Bannir _name_";
moUser.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal

  var button = event.relatedTarget;

  // Update the modal's content.
  // moUser.querySelector("#pceen").value = button.dataset["pceenId"];

  title.textContent = title.textContent.replace(
    "_name_",
    button.dataset["pceenName"]
  );
});
*/
var pceenId = 0;
var moUser = document.getElementById("mo-user");
moUser.addEventListener("show.bs.modal", function (event) {
  var pceenIdElement = moUser.querySelector("#pceenId");
  var pceenNameElement = moUser.querySelector("#pceenName");
  var button = event.relatedTarget;
  pceenId = parseInt(button.dataset["pceenId"]);
  var pceenName = button.dataset["pceenName"];
  console.log(pceenId);
  console.log(typeof pceenId);
  // Set the data in the modal
  pceenIdElement.textContent = pceenId;
  pceenNameElement.textContent = pceenName;
});
