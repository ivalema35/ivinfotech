/* ===== IV Infotech — Preloader Injector =====
 * This script injects the preloader immediately so it appears
 * before any async content (header, footer, animations) loads.
 * Include as the FIRST script inside <body> on every page.
 * ================================================= */

document.write(`
<div id="preloader">
    <lottie-player
        src="assets/animations/loader.json"
        background="transparent"
        speed="1"
        style="width: 200px; height: 200px;"
        loop
        autoplay>
    </lottie-player>
</div>
`);

window.addEventListener("load", function () {
    setTimeout(function () {
        var preloader = document.getElementById("preloader");
        if (preloader) {
            document.body.classList.add("loaded");
        }
    }, 800);
});
