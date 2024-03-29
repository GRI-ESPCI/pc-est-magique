
// turn.js code
$(function () {
  $("#magazine").turn({
    width: page_width*2,
		height: page_height,
    display: "double",
    acceleration: true,
    gradients: !$.isTouch,
    elevation: 50,
  });
});

  // Bind click events to navigation buttons
  $("#go-to-first").on( "click", function () {
    $("#magazine").turn("page", 1); // Go to the first page
  });

  $("#previous-page").on( "click", function () {
    $("#magazine").turn("previous"); // Turn to the previous page
  });

  $("#next-page").on( "click", function () {
    $("#magazine").turn("next"); // Turn to the next page
  });

  $("#go-to-last").on( "click", function () {
    $("#magazine").turn("page", nb_pages); // Go to the last page
  });


$(window).on("keydown", function (event) {
  if (event.key == "ArrowLeft") $("#magazine").turn("previous");
  else if (event.key == "ArrowRight") $("#magazine").turn("next");
});



//PDF plotting part
var pdfjsLib = window['pdfjs-dist/build/pdf'];

pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/js/pdf.worker.js';
// Asynchronous download of PDF
var loadingTask = pdfjsLib.getDocument(url);
loadingTask.promise.then(function(pdf) {
  var init = [1, 2, 3];

  
  
  for (var i in init) {
    (function (page) {
      renderPage(page);
    })(init[i]);
  }
  function renderPage(i) {
    //Render page code from https://mozilla.github.io/pdf.js/examples/
    pdf.getPage(i).then(function(page) {
  
      var scale = 1;
      var viewport = page.getViewport({scale: scale});

      // Prepare canvas using PDF page dimensions
      var canvas = document.getElementById('page-'+i);
      var context = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width = viewport.width;
  
      // Render PDF page into canvas context
      var renderContext = {
        canvasContext: context,
        viewport: viewport
      };
      var renderTask = page.render(renderContext);
      renderTask.promise;
    });
  }

  $("#magazine").on("turning", function (event, page, view) {
    
    var currentPage = $("#magazine").turn("page");

    if (page == 0) {
        renderPage(page)
        renderPage(page+1)
        renderPage(page+2)
    }
    else if (page == nb_pages) {
      renderPage(nb_pages)
      renderPage(nb_pages-1)
      renderPage(nb_pages-2)
    }
    else if (page > currentPage) {
      if (page+3 <= nb_pages) {
        renderPage(page+2)
        renderPage(page+3)
      }
      else if(i+2 <= nb_pages) {
        renderPage(page+2)
      }

    } else if (page < currentPage) {
      if (page-3 > 0)  {
        renderPage(page-2)
        renderPage(page-3)
      }
      else if(i-2 > 0) {
        renderPage(page-2)
      }
    }
  });
});
