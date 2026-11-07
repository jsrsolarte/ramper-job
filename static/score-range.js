document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("input[data-score-slider]").forEach((slider) => {
    const output = document.querySelector(`output[for="${slider.id}"]`);
    if (!output) return;
    const updateScoreLabel = () => {
      const stars = (Number(slider.value) / 2).toFixed(1).replace(".", ",");
      const starThreshold = stars.endsWith(",0") ? stars.slice(0, -2) : stars;
      const label = `${starThreshold} ${starThreshold === "1" ? "estrella" : "estrellas"} o más`;
      const labelContent = output.querySelector("[data-score-label]");
      const starContent = output.querySelector("[data-score-stars]");
      if (labelContent) labelContent.textContent = label;
      else output.textContent = label;
      if (starContent) starContent.style.setProperty("--score-fill", `${Number(slider.value) * 10}%`);
      output.value = label;
      slider.setAttribute("aria-valuetext", label);
    };
    slider.addEventListener("input", updateScoreLabel);
    if (slider.hasAttribute("data-auto-submit")) {
      slider.addEventListener("change", () => slider.form?.requestSubmit());
    }
    updateScoreLabel();
  });
});
