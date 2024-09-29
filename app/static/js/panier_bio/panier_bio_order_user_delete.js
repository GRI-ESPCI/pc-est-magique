// Delete panier bio order modal
var moOrderDelete = document.getElementById("mo-order-delete");
var titleOD = moOrderDelete.querySelector(".modal-title");

moOrderDelete.addEventListener("show.bs.modal", function (event) {
    // Button that triggered the modal
    var button = event.relatedTarget;
    // Update the modal's content.
    var orderId = button.dataset["orderId"];
    var orderDate = button.dataset["orderDate"];
    var formVisibility = button.dataset["formVisibility"];

    titleOD.textContent =
        "Supprimer commande " +
        orderDate

    document.getElementsByName("id")[formVisibility].value = orderId;
    
});

