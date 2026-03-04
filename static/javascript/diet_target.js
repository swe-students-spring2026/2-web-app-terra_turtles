function renderTargetMessage(target, today) {
  const msg = document.getElementById("targetMsg");
  if (!msg) return;

  const diff = target - today;

  if (diff > 0) {
    msg.textContent = `You have ${diff} calories left today.`;
    msg.className = "target-box__msg target-box__msg--ok";
  } else if (diff < 0) {
    msg.textContent = `You are over by ${Math.abs(diff)} calories today.`;
    msg.className = "target-box__msg target-box__msg--over";
  } else {
    msg.textContent = "You hit your target exactly.";
    msg.className = "target-box__msg target-box__msg--ok";
  }
}

document.addEventListener("DOMContentLoaded", () => {
  const box = document.querySelector(".target-box");
  if (!box) return;

  const dayCalories = parseInt(box.dataset.dayCalories || "0", 10);
  const input = document.getElementById("targetCalories");
  const btn = document.getElementById("targetApply");

  const saved = localStorage.getItem("fitflow_target_calories");
  if (saved && input) {
    input.value = saved;
    renderTargetMessage(parseInt(saved, 10), dayCalories);
  }

  if (btn) {
    btn.addEventListener("click", () => {
      const v = parseInt((input && input.value) || "0", 10);
      if (!v || v < 0) return;

      localStorage.setItem("fitflow_target_calories", String(v));
      renderTargetMessage(v, dayCalories);
    });
  }
});