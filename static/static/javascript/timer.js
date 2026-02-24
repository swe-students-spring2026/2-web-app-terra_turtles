/* timer.js
 * Rest timer:
 * - User sets minutes/seconds
 * - Start/Pause toggles countdown
 * - Reset returns to the configured time
 * - Simple completion alert + status text
 */

(function () {
  "use strict";

  const minsEl = document.getElementById("mins");
  const secsEl = document.getElementById("secs");
  const readoutEl = document.getElementById("time-readout");
  const statusEl = document.getElementById("timer-status");
  const msgEl = document.getElementById("timer-message");
  const startPauseBtn = document.getElementById("start-pause");
  const resetBtn = document.getElementById("reset");

  if (!minsEl || !secsEl || !readoutEl || !statusEl || !msgEl || !startPauseBtn || !resetBtn) return;

  let intervalId = null;
  let remainingMs = 0;
  let baseMs = 0;
  let running = false;

  function clampInt(n, min, max) {
    const x = Number(n);
    if (!Number.isFinite(x)) return min;
    const y = Math.floor(x);
    return Math.min(max, Math.max(min, y));
  }

  function formatTime(ms) {
    const totalSec = Math.max(0, Math.ceil(ms / 1000));
    const mm = Math.floor(totalSec / 60);
    const ss = totalSec % 60;
    return `${String(mm).padStart(2, "0")}:${String(ss).padStart(2, "0")}`;
  }

  function setStatus(text) {
    statusEl.textContent = text;
  }

  function setMessage(text) {
    msgEl.textContent = text || "";
  }

  function readBaseMsFromInputs() {
    const m = clampInt(minsEl.value, 0, 999);
    const s = clampInt(secsEl.value, 0, 59);
    minsEl.value = String(m);
    secsEl.value = String(s);
    return (m * 60 + s) * 1000;
  }

  function render() {
    readoutEl.textContent = formatTime(remainingMs);
  }

  function stopInterval() {
    if (intervalId) window.clearInterval(intervalId);
    intervalId = null;
  }

  function setRunning(nextRunning) {
    running = nextRunning;
    startPauseBtn.textContent = running ? "Pause" : "Start";
    setStatus(running ? "Running" : "Ready");
  }

  function finish() {
    stopInterval();
    remainingMs = 0;
    render();
    setRunning(false);
    setStatus("Done");
    setMessage("Rest complete.");

    // Simple audio beep using Web Audio API (no external files)
    try {
      const ctx = new (window.AudioContext || window.webkitAudioContext)();
      const osc = ctx.createOscillator();
      const gain = ctx.createGain();
      osc.type = "sine";
      osc.frequency.value = 880;
      gain.gain.value = 0.05;
      osc.connect(gain);
      gain.connect(ctx.destination);
      osc.start();
      setTimeout(() => {
        osc.stop();
        ctx.close();
      }, 200);
    } catch (e) {
      // Ignore audio errors (some browsers block autoplay audio)
    }

    // Visual confirmation for users
    window.alert("Rest complete!");
  }

  function tick() {
    remainingMs -= 250;
    if (remainingMs <= 0) {
      finish();
      return;
    }
    render();
  }

  function start() {
    if (running) return;

    // If remaining time is 0, reset to base time first
    if (remainingMs <= 0) {
      baseMs = readBaseMsFromInputs();
      remainingMs = baseMs;
      render();
    }

    if (remainingMs <= 0) {
      setMessage("Please set a time greater than 0.");
      return;
    }

    setMessage("");
    setRunning(true);
    stopInterval();
    intervalId = window.setInterval(tick, 250);
  }

  function pause() {
    if (!running) return;
    stopInterval();
    setRunning(false);
    setStatus("Paused");
  }

  function reset() {
    stopInterval();
    baseMs = readBaseMsFromInputs();
    remainingMs = baseMs;
    render();
    setRunning(false);
    setMessage("");
    setStatus("Ready");
  }

  // Input changes update the base time when not running
  function onInputChange() {
    if (running) return;
    baseMs = readBaseMsFromInputs();
    remainingMs = baseMs;
    render();
    setMessage("");
  }

  startPauseBtn.addEventListener("click", () => {
    if (running) pause();
    else start();
  });

  resetBtn.addEventListener("click", () => {
    reset();
  });

  minsEl.addEventListener("change", onInputChange);
  secsEl.addEventListener("change", onInputChange);

  // Initialize
  baseMs = readBaseMsFromInputs();
  remainingMs = baseMs;
  render();
  setStatus("Ready");
})();