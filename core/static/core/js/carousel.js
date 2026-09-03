// Prosta karuzela bez zewnętrznych bibliotek. Działa na każdym elemencie
// .carousel na stronie — wystarczy taka struktura HTML:
//
//   <div class="carousel">
//     <div class="carousel-track">
//       <figure class="carousel-slide"><img ...></figure>
//       ... kolejne .carousel-slide ...
//     </div>
//     <button class="carousel-btn prev">‹</button>
//     <button class="carousel-btn next">›</button>
//     <div class="carousel-dots"></div>
//   </div>
//
// Kropki w .carousel-dots są dogenerowywane automatycznie poniżej —
// nie trzeba ich ręcznie wypisywać w szablonie.

document.querySelectorAll(".carousel").forEach((carousel) => {
  const track = carousel.querySelector(".carousel-track");
  const slides = Array.from(carousel.querySelectorAll(".carousel-slide"));
  const dotsWrap = carousel.querySelector(".carousel-dots");
  const prevBtn = carousel.querySelector(".carousel-btn.prev");
  const nextBtn = carousel.querySelector(".carousel-btn.next");

  if (!track || slides.length === 0) return;

  let index = 0;

  const dots = slides.map((_, i) => {
    const dot = document.createElement("button");
    dot.type = "button";
    dot.setAttribute("aria-label", `Przejdź do zdjęcia ${i + 1}`);
    dot.addEventListener("click", () => goTo(i));
    dotsWrap.appendChild(dot);
    return dot;
  });

  function update() {
    track.style.transform = `translateX(-${index * 100}%)`;
    dots.forEach((dot, i) => dot.classList.toggle("is-active", i === index));
  }

  function goTo(i) {
    index = (i + slides.length) % slides.length;
    update();
  }

  prevBtn?.addEventListener("click", () => goTo(index - 1));
  nextBtn?.addEventListener("click", () => goTo(index + 1));

  update();
});
