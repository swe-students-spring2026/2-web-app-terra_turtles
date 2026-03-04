function clamp(n, min, max) {
  return Math.max(min, Math.min(max, n));
}

function bmiStatus(bmi) {
  if (bmi < 18.5) return { text: "Underweight", cls: "bmi-tag--under" };
  if (bmi < 25) return { text: "Normal", cls: "bmi-tag--normal" };
  if (bmi < 30) return { text: "Overweight", cls: "bmi-tag--over" };
  return { text: "Obese", cls: "bmi-tag--obese" };
}

document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("bmiForm");
  const resetBtn = document.getElementById("bmiReset");

  const result = document.getElementById("bmiResult");
  const valueEl = document.getElementById("bmiValue");
  const tagEl = document.getElementById("bmiTag");
  const marker = document.getElementById("bmiMarker");

  form.addEventListener("submit", (e) => {
    e.preventDefault();

    const h = parseFloat(document.getElementById("heightCm").value);
    const w = parseFloat(document.getElementById("weightKg").value);

    if (!h || !w) return;

    const hm = h / 100.0;
    const bmi = w / (hm * hm);

    const rounded = Math.round(bmi * 10) / 10;
    valueEl.textContent = rounded.toFixed(1);

    const st = bmiStatus(rounded);
    tagEl.textContent = st.text;
    tagEl.className = "bmi-tag " + st.cls;

    // Map BMI 10~40 to 0~100% for marker position
    const pos = ((clamp(rounded, 10, 40) - 10) / (40 - 10)) * 100;
    marker.style.left = pos + "%";

    result.style.display = "block";
  });

  resetBtn.addEventListener("click", () => {
    form.reset();
    result.style.display = "none";
    valueEl.textContent = "--";
    tagEl.textContent = "--";
    tagEl.className = "bmi-tag";
    marker.style.left = "0%";
  });
});