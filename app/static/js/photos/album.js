/* ----- GALLERY ----- */

const lg = document.getElementById("lightgallery");

// On gallery init
lg.addEventListener("lgInit", (event) => {
  // Append custom toolbar buttons
  const toolbar = document.getElementById("lg-toolbar-1");
  toolbar.appendChild(document.getElementById("report-button"));
  // Show requested slide if anchor in URL
  if (window.location.hash) {
    const index = new Number(window.location.hash.slice(1)) - 1;
    if (!isNaN(index) && 0 <= index < event.detail.instance.items.length) {
      event.detail.instance.openGallery(index);
    }
  }
  // Once gallery is init and shown if necessary, we can load thumbnails
  const thumbs = lg.querySelectorAll("div > a > img");
  const thumbs_in_thumb = document.querySelectorAll(".lg-thumb > div > img");
  for (let i = 0; i < thumbs.length; i++) {
    let src = thumbs[i].dataset["src"];
    thumbs[i].src = src;
    thumbs_in_thumb[i].src = src;
  }
});

// Init gallery
const gallery = lightGallery(lg, {
  plugins: [lgZoom, lgThumbnail, lgFullscreen],
  selector: "a",
  licenseKey: "1234-1234-567-1234",
  startAnimationDuration: 200,
  hideControlOnEnd: true,
  loop: false,
  thumbHeight: 80,
  thumbWidth: 80,
  toggleThumb: true,
});

// On slide change
const report = document.getElementById("send-report-button");
const report_template = report.href;
lg.addEventListener("lgAfterSlide", (event) => {
  // Update slide number in URL hash
  window.history.replaceState({}, document.title, "#" + (event.detail.index + 1));
  // Update photo link in report URL
  report.href = report_template.replace("__photo__", data["file_name"]);
});

// On URL hash change: close / switch slide
window.addEventListener("hashchange", () => {
  if (window.location.hash && window.location.hash != "#") {
    const index = new Number(window.location.hash.slice(1)) - 1;
    if (!isNaN(index) && 0 <= index < gallery.items.length) {
      if (gallery.lgOpened) {
        gallery.slide(index);
      } else {
        gallery.openGallery(index);
      }
    }
  } else if (gallery.lgOpened) {
    gallery.closeGallery();
  }
});

// On gallery close: remove slide number from URL
lg.addEventListener("lgAfterClose", () => {
  window.history.replaceState({}, document.title, window.location.pathname);
});
