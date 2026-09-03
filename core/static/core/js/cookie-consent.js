// Baner zgody na cookies + warunkowe ładowanie Meta Pixel.
//
// Zasada: cookies niezbędne (sesja, CSRF) działają zawsze — to nie one
// wymagają zgody. Meta Pixel to cookie MARKETINGOWE, więc ładuje się
// dopiero po kliknięciu "Akceptuję" (nigdy automatycznie), zgodnie z tym,
// co obiecuje core/templates/core/polityka-prywatnosci.html (sekcja 11).
//
// Wybór użytkownika trzyma się w localStorage (per przeglądarka, nie per
// konto) — "accepted" albo "rejected". Brak wpisu = baner jeszcze nie
// pokazany, więc go wyświetlamy.
//
// window.METAPIXEL_ID jest wstrzykiwane w base.html z ustawienia Django
// META_PIXEL_ID (settings.py) — dopóki jest puste (brak ID od Meta),
// loadMetaPixel() nic nie robi, nawet po zaakceptowaniu bannera.

(function () {
  const STORAGE_KEY = "cookie-consent";
  const banner = document.getElementById("cookie-banner");
  if (!banner) return;

  const acceptBtn = document.getElementById("cookie-accept");
  const rejectBtn = document.getElementById("cookie-reject");

  function loadMetaPixel() {
    const pixelId = window.METAPIXEL_ID;
    if (!pixelId || window.fbq) return;

    // Standardowy fragment startowy Meta Pixel (z Events Managera) —
    // ładuje fbevents.js asynchronicznie i inicjalizuje śledzenie.
    !function (f, b, e, v, n, t, s) {
      if (f.fbq) return;
      n = f.fbq = function () {
        n.callMethod ? n.callMethod.apply(n, arguments) : n.queue.push(arguments);
      };
      if (!f._fbq) f._fbq = n;
      n.push = n;
      n.loaded = true;
      n.version = "2.0";
      n.queue = [];
      t = b.createElement(e);
      t.async = true;
      t.src = v;
      s = b.getElementsByTagName(e)[0];
      s.parentNode.insertBefore(t, s);
    }(window, document, "script", "https://connect.facebook.net/en_US/fbevents.js");

    fbq("init", pixelId);
    fbq("track", "PageView");
  }

  function hideBanner() {
    banner.hidden = true;
  }

  const existingChoice = localStorage.getItem(STORAGE_KEY);
  if (existingChoice === "accepted") {
    loadMetaPixel();
  } else if (existingChoice !== "rejected") {
    banner.hidden = false;
  }

  acceptBtn?.addEventListener("click", () => {
    localStorage.setItem(STORAGE_KEY, "accepted");
    loadMetaPixel();
    hideBanner();
  });

  rejectBtn?.addEventListener("click", () => {
    localStorage.setItem(STORAGE_KEY, "rejected");
    hideBanner();
  });
})();
