//Bekk Title page fetching
var pdfjsLib = window['pdfjs-dist/build/pdf'];
pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/js/pdf.worker.js';

//Recursive functions to avoid loading several PDF at the same time
function loadAndRenderPDF(bekk_id_list) {

  if (bekk_id_list.length === 0) {
    return;
  }
  var bekk_id = bekk_id_list.shift();

  //Render page code from https://mozilla.github.io/pdf.js/examples/

  var url = '/bekks/' + bekk_id + '.pdf';

  // Asynchronous download of PDF
  var loadingTask = pdfjsLib.getDocument(url);
  loadingTask.promise
    .then(function (pdf) {
      console.log('PDF loaded for bekk_id: ' + bekk_id);

      return pdf.getPage(1).then(function (page) {
        var scale = 0.5;
        var viewport = page.getViewport({ scale: scale });

        // Prepare canvas using PDF page dimensions
        var canvas = document.getElementById('bekk-' + bekk_id);
        var context = canvas.getContext('2d');
        canvas.height = viewport.height;
        canvas.width = viewport.width;

        // Render PDF page into canvas context
        var renderContext = {
          canvasContext: context,
          viewport: viewport,
        };
        var renderTask = page.render(renderContext);
        return renderTask.promise;
      });
    })
    .then(function () {
      // Load and render the next PDF in the queue
      loadAndRenderPDF(bekk_id_list);
    });
}
loadAndRenderPDF(bekk_id_list); 
