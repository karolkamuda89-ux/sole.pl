// Lightbox do galerii zdjęć. Działa z jednym elementem #gallery-lightbox
// na stronie i dowolną liczbą siatek ze zdjęciami oznaczonych klasą
// .airbnb-gallery-grid — slajdy budowane są automatycznie z <img> w środku
// (kolejność w DOM = kolejność w lightboksie), więc dodanie/podmiana
// zdjęcia w szablonie nie wymaga żadnych zmian tutaj.

const lightbox = document.getElementById("gallery-lightbox");
const grid = document.querySelector(".airbnb-gallery-grid");

if (lightbox && grid) {
  const thumbs = Array.from(grid.querySelectorAll("img"));
  const slides = thumbs.map((img) => ({ src: img.currentSrc || img.src, alt: img.alt }));

  const lightboxImg = lightbox.querySelector(".lightbox-img");
  const counter = lightbox.querySelector(".lightbox-counter");
  const closeBtn = lightbox.querySelector(".lightbox-close");
  const prevBtn = lightbox.querySelector(".lightbox-btn.prev");
  const nextBtn = lightbox.querySelector(".lightbox-btn.next");

  let index = 0;

  function show(i) {
    index = (i + slides.length) % slides.length;
    const slide = slides[index];
    lightboxImg.src = slide.src;
    lightboxImg.alt = slide.alt;
    counter.textContent = `${index + 1} / ${slides.length}`;
  }

  function open(i) {
    show(i);
    lightbox.hidden = false;
    document.body.style.overflow = "hidden";
  }

  function close() {
    lightbox.hidden = true;
    document.body.style.overflow = "";
  }

  grid.querySelectorAll(".airbnb-gallery-item").forEach((link, i) => {
    link.addEventListener("click", (event) => {
      event.preventDefault();
      open(i);
    });
  });

  closeBtn.addEventListener("click", close);
  prevBtn.addEventListener("click", () => show(index - 1));
  nextBtn.addEventListener("click", () => show(index + 1));

  // Klik na ciemne tło (poza samym zdjęciem) też zamyka.
  lightbox.addEventListener("click", (event) => {
    if (event.target === lightbox) close();
  });

  document.addEventListener("keydown", (event) => {
    if (lightbox.hidden) return;
    if (event.key === "Escape") close();
    if (event.key === "ArrowLeft") show(index - 1);
    if (event.key === "ArrowRight") show(index + 1);
  });
}
