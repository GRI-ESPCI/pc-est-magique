// Add Order moOrderAdd
var moOrderAdd = document.getElementById("mo-order-add");

moOrderAdd.addEventListener("show.bs.modal", function (event) {
  document.getElementsByName("id")[0].value = null;
  document.getElementsByName("date")[0].value = null;
  document.getElementsByName("prenom")[0].value = null;
  document.getElementsByName("nom")[0].value = null;
  document.getElementsByName("service")[0].value = null;
  document.getElementsByName("payment_method")[0].value = null;
  document.getElementsByName("phone")[0].value = null;
  document.getElementsByName("payed")[0].value = null;
  document.getElementsByName("pceen_id")[0].value = null;
  document.getElementsByName("comment")[0].value = null;
});

// Edit panier bio order modal
var moOrderEdit = document.getElementById("mo-order-edit");
var titleOE = moOrderEdit.querySelector(".modal-title");

moOrderEdit.addEventListener("show.bs.modal", function (event) {
  // Button that triggered the modal
  var button = event.relatedTarget;
  // Update the modal's content.
  var orderId = button.dataset["orderId"];
  var orderName = button.dataset["orderName"];
  var orderService = button.dataset["orderService"];
  var orderDate = button.dataset["orderDate"];
  var orderPaymentMethod = button.dataset["orderPaymentMethod"];
  var orderComment = button.dataset["orderComment"];
  var orderPhone = button.dataset["orderPhone"];
  var orderPceenId = button.dataset["orderPceenId"];

  titleOE.textContent =
    "Editer commande " +
    orderId +
    " - " +
    orderDate +
    " - " +
    orderName +
    " - " +
    orderService;

  if (orderPceenId == "None") {
    document.getElementsByName("prenom")[1].disabled = false;
    document.getElementsByName("nom")[1].disabled = false;
    document.getElementsByName("service")[1].disabled = false;
  } else {
    document.getElementsByName("prenom")[1].disabled = true;
    document.getElementsByName("nom")[1].disabled = true;
    document.getElementsByName("service")[1].disabled = true;
  }

  if (button.dataset["orderPaymentMade"] == "True") {
    document.getElementsByName("payed")[1].checked = true;
  } else {
    document.getElementsByName("payed")[1].checked = false;
  }

  if (button.dataset["orderTreasurerValidate"] == "True") {
    document.getElementsByName("treasurer_validate")[1].checked = true;
  } else {
    document.getElementsByName("treasurer_validate")[1].checked = false;
  }

  if (button.dataset["orderTaken"] == "True") {
    document.getElementsByName("taken")[1].checked = true;
  } else {
    document.getElementsByName("taken")[1].checked = false;
  }

  // Set the form field values using Flask-WTF's API
  document.getElementsByName("id")[1].value = orderId;
  document.getElementsByName("date")[1].value = orderDate;
  document.getElementsByName("prenom")[1].value = orderName.split(/[ ]+/)[0];
  document.getElementsByName("nom")[1].value = orderName.split(/[ ]+/).slice(1);
  document.getElementsByName("service")[1].value = orderService;
  document.getElementsByName("payment_method")[1].value = orderPaymentMethod;
  document.getElementsByName("phone")[1].value = orderPhone;
  document.getElementsByName("pceen_id")[1].value = orderPceenId;
  document.getElementsByName("comment")[1].value = orderComment;
});

