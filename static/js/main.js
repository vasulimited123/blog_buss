// ---------------------------------------------------------------------------
// Mobile navigation toggle
// ---------------------------------------------------------------------------
document.addEventListener("DOMContentLoaded", function () {
    var toggle = document.querySelector(".nav-toggle");
    var nav = document.querySelector(".site-nav");
    if (toggle && nav) {
        toggle.addEventListener("click", function () {
            var open = nav.classList.toggle("is-open");
            toggle.setAttribute("aria-expanded", open ? "true" : "false");
        });
    }

    // -----------------------------------------------------------------------
    // Reading progress bar (only present on article pages)
    // -----------------------------------------------------------------------
    var bar = document.querySelector(".reading-progress span");
    if (bar) {
        var update = function () {
            var scrollTop = window.scrollY || document.documentElement.scrollTop;
            var height = document.documentElement.scrollHeight - window.innerHeight;
            var pct = height > 0 ? (scrollTop / height) * 100 : 0;
            bar.style.width = pct + "%";
        };
        window.addEventListener("scroll", update, { passive: true });
        window.addEventListener("resize", update);
        update();
    }

    // -----------------------------------------------------------------------
    // Copy-link share button
    // -----------------------------------------------------------------------
    document.querySelectorAll(".share-copy").forEach(function (btn) {
        btn.addEventListener("click", function () {
            var url = btn.getAttribute("data-url");
            var done = function () {
                var original = btn.textContent;
                btn.textContent = "Copied!";
                setTimeout(function () { btn.textContent = original; }, 1500);
            };
            if (navigator.clipboard && navigator.clipboard.writeText) {
                navigator.clipboard.writeText(url).then(done).catch(done);
            } else {
                // Fallback for older browsers
                var tmp = document.createElement("input");
                tmp.value = url;
                document.body.appendChild(tmp);
                tmp.select();
                try { document.execCommand("copy"); } catch (e) {}
                document.body.removeChild(tmp);
                done();
            }
        });
    });

    // -----------------------------------------------------------------------
    // Cookie consent banner
    // -----------------------------------------------------------------------
    var banner = document.querySelector(".cookie-consent");
    if (banner) {
        if (localStorage.getItem("cookieConsent") === "accepted") {
            banner.remove();
        } else {
            banner.classList.add("is-visible");
            var accept = banner.querySelector(".cookie-accept");
            if (accept) {
                accept.addEventListener("click", function () {
                    localStorage.setItem("cookieConsent", "accepted");
                    banner.remove();
                });
            }
        }
    }
});
