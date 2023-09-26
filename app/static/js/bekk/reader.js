
$(window).ready(function () {
  $("#magazine").turn({
    display: "double",
    acceleration: true,
    gradients: !$.isTouch,
    elevation: 50,
    when: {
      turned: function (e, page) {
        /*console.log('Current view: ', $(this).turn('view'));*/
      },
    },
  });
});

  // Bind click events to navigation buttons
  $("#go-to-first").click(function () {
    $("#magazine").turn("page", 1); // Go to the first page
  });

  $("#previous-page").click(function () {
    $("#magazine").turn("previous"); // Turn to the previous page
  });

  $("#next-page").click(function () {
    $("#magazine").turn("next"); // Turn to the next page
  });

  $("#go-to-last").click(function () {
    $("#magazine").turn("page", $("#magazine").turn("pages")); // Go to the last page
  });


$(window).bind("keydown", function (e) {
  if (e.keyCode == 37) $("#magazine").turn("previous");
  else if (e.keyCode == 39) $("#magazine").turn("next");
});