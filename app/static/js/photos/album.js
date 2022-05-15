
var lg = document.getElementById('lightgallery');

// On gallery init
lg.addEventListener('lgInit', (event) => {
    // Append custom toolbar buttons
    var toolbar = document.getElementById('lg-toolbar-1')
    toolbar.appendChild(document.getElementById('edit-button'))
    toolbar.appendChild(document.getElementById('follow-button'))
    toolbar.appendChild(document.getElementById('followed-button'))
    toolbar.appendChild(document.getElementById('report-button'))
    // Show requested slide if anchor in URL
    if (window.location.hash) {
        var index = new Number(window.location.hash.slice(1)) - 1;
        if (!isNaN(index) && 0 <= index < event.detail.instance.items.length) {
            event.detail.instance.openGallery(index);
        }
    }
    // Once gallery is init and shown if necessary, we can load thumbnails
    var thumbs = lg.querySelectorAll("div > a > img");
    var thumbs_in_thumb = document.querySelectorAll(".lg-thumb > div > img");
    for (let i = 0; i < thumbs.length; i++) {
        let src = thumbs[i].dataset["src"];
        thumbs[i].src = src;
        thumbs_in_thumb[i].src = src;
    }
});

// Init gallery
var gallery = lightGallery(lg, {
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
var moEdit = document.getElementById("mo-edit")
var follow = document.getElementById("follow-button")
var followed = document.getElementById("followed-button")
var report = document.getElementById("send-report-button")
var report_template = report.href;
console.log(report_template);
lg.addEventListener('lgAfterSlide', (event) => {
    // Update slide number in URL hash
    window.history.replaceState(
        {}, document.title, "#" + (event.detail.index + 1)
    );
    // Update infos modifications form (in modal)
    moEdit.querySelectorAll(".form-control").forEach(elem => elem.value = null)
    var data = gallery.items[event.detail.index].dataset;
    moEdit.querySelector('#photo_name').value = data["file_name"];
    moEdit.querySelector('#caption').value = data["caption"];
    moEdit.querySelector('#author_str').value = data["author_str"];
    moEdit.querySelector('#date').value = data["date"];
    moEdit.querySelector('#time').value = data["time"];
    moEdit.querySelector('#lat').value = data["lat"];
    moEdit.querySelector('#lng').value = data["lng"];
    // Fill / unfill feature button
    if (data["featured"]) {
        follow.classList.replace("d-flex", "d-none");
        followed.classList.replace("d-none", "d-flex");
    } else {
        followed.classList.replace("d-flex", "d-none");
        follow.classList.replace("d-none", "d-flex");
    }
    // Update photo link in report URL
    report.href = report_template.replace("__photo__", data["file_name"]);
});

// On URL hash change: close / switch slide
window.addEventListener('hashchange', () => {
    if (window.location.hash && window.location.hash != "#") {
        var index = new Number(window.location.hash.slice(1)) - 1;
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
})

// On gallery close: remove slide number from URL
lg.addEventListener('lgAfterClose', () => {
    window.history.replaceState({}, document.title, window.location.pathname);
});
