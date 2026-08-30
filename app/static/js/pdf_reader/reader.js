var MOBILE_BREAKPOINT = 1024; // px

function availableWidth() {
  var container = document.querySelector('.container');
  return container ? container.clientWidth : window.innerWidth;
}

function computeLayout() {
  var isSingle  = window.innerWidth < MOBILE_BREAKPOINT;
  var avail     = availableWidth();
  var natural   = isSingle ? page_width : page_width * 2;
  var scale     = Math.min(1, avail / natural);
  return {
    isSingle   : isSingle,
    scale      : scale,
    magWidth   : Math.floor(natural * scale),
    magHeight  : Math.floor(page_height * scale),
  };
}

function updatePageIndicator() {
  var current = $('#magazine').turn('page');
  $('#page-indicator').text(current + ' / ' + nb_pages);
}

var _layout = null;

function initTurn(layout, startPage) {
  _layout = layout;

  $('#magazine').turn({
    width       : layout.magWidth,
    height      : layout.magHeight,
    display     : layout.isSingle ? 'single' : 'double',
    acceleration: true,
    gradients   : !$.isTouch,
    elevation   : 50,
  });

  if (startPage && startPage > 1) {
    try { $('#magazine').turn('page', startPage); } catch(e) {}
  }

  updatePageIndicator();
  $('#magazine').on('turned', updatePageIndicator);
}

var _pdf         = null;
var _donePage    = {}; 
var _inFlight    = {}; 

function renderPage(i, scale) {
  if (!_pdf || !i || i < 1 || i > nb_pages) return;
  var key = i + '@' + scale.toFixed(4);
  if (_donePage[key] || _inFlight[key]) return;
  _inFlight[key] = true;

  _pdf.getPage(i).then(function(page) {
    var viewport = page.getViewport({ scale: scale });

    function tryDraw() {
      var canvas = document.getElementById('page-' + i);
      if (!canvas) {
        setTimeout(tryDraw, 100);
        return;
      }
      _donePage[key] = true;
      delete _inFlight[key];
      var ctx = canvas.getContext('2d');
      canvas.height = viewport.height;
      canvas.width  = viewport.width;
      page.render({ canvasContext: ctx, viewport: viewport });
    }

    tryDraw();
  }).catch(function(err) {
    delete _inFlight[key];
    console.warn('PDF page ' + i + ' failed to load:', err);
  });
}

function renderSpread(page, scale) {
  for (var d = -2; d <= 3; d++) {
    renderPage(page + d, scale);
  }
}

var pdfjsLib = window['pdfjs-dist/build/pdf'];
pdfjsLib.GlobalWorkerOptions.workerSrc = '/static/js/pdf.worker.js';

$(function() {
  var layout = computeLayout();
  initTurn(layout);

  pdfjsLib.getDocument(url).promise.then(function(pdf) {
    _pdf = pdf;
    renderSpread(1, layout.scale);

    $('#magazine').on('turning', function(event, page) {
      renderSpread(page, _layout.scale);
    });
  });

  // Navigation buttons
  $('#go-to-first').on('click',   function() { $('#magazine').turn('page', 1); });
  $('#previous-page').on('click', function() { $('#magazine').turn('previous'); });
  $('#next-page').on('click',     function() { $('#magazine').turn('next'); });
  $('#go-to-last').on('click',    function() { $('#magazine').turn('page', nb_pages); });
});

$(window).on('keydown', function(event) {
  if (event.key === 'ArrowLeft')       $('#magazine').turn('previous');
  else if (event.key === 'ArrowRight') $('#magazine').turn('next');
});

(function() {
  var touchStartX   = null;
  var SWIPE_MIN     = 40; // px

  var wrapper = document.getElementById('magazine-wrapper');

  wrapper.addEventListener('touchstart', function(e) {
    touchStartX = e.changedTouches[0].clientX;
  }, { passive: true });

  wrapper.addEventListener('touchend', function(e) {
    if (touchStartX === null) return;
    var dx = e.changedTouches[0].clientX - touchStartX;
    touchStartX = null;
    if (Math.abs(dx) < SWIPE_MIN) return;
    if (dx < 0) $('#magazine').turn('next');
    else        $('#magazine').turn('previous');
  }, { passive: true });
})();

var _resizeTimer;
$(window).on('resize orientationchange', function() {
  clearTimeout(_resizeTimer);
  _resizeTimer = setTimeout(function() {
    if (!_pdf) return;

    var newLayout   = computeLayout();
    var currentPage = $('#magazine').turn('page');
    _donePage = {};
    _inFlight = {};
    try { $('#magazine').turn('destroy'); } catch(e) {}

    initTurn(newLayout, currentPage);
    renderSpread(currentPage, newLayout.scale);
  }, 150);
});
