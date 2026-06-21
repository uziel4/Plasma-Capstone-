const $ = (selector) => document.querySelector(selector);
const chart = $("#chart");
const ctx = chart.getContext("2d");

const actionButtons = document.querySelectorAll("[data-action]");
const targetInput = $("#targetInput");
const voltageInput = $("#voltageInput");
const timerInput = $("#timerInput");

let latestState = null;

async function post(path, body = {}) {
  const response = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  const payload = await response.json();
  if (payload.state) render(payload.state);
}

async function refresh() {
  try {
    const response = await fetch("/api/state", { cache: "no-store" });
    render(await response.json());
  } catch (error) {
    $("#status").textContent = "BACKEND OFFLINE";
    document.body.classList.add("offline");
  }
}

function render(state) {
  latestState = state;
  document.body.classList.toggle("offline", Boolean(state.sensorError));

  $("#status").textContent = state.status;
  $("#mode").textContent = state.mode;
  $("#hvState").textContent = state.hvActive ? "HV ON" : "HV OFF";
  $("#roughingState").textContent = state.roughingActive ? "ON" : "OFF";
  $("#massFlowState").textContent = state.massFlowActive ? "ON" : "OFF";

  const pressureText = state.sensorError ? "SENSOR ERROR" : compactPressure(state.pressureTorr);
  $("#pressure").textContent = pressureText;
  $("#roughingPressure").textContent = pressureText;
  $("#voltageReadout").textContent = `${Number(state.voltage).toFixed(4)} V`;
  $("#sensorReadout").textContent = state.sensorError || pressureText;
  $("#relayMode").textContent = state.relaySimulated ? "Simulation" : "Hardware";

  $("#progressBar").style.width = `${Math.max(0, Math.min(100, state.progress))}%`;
  $("#progressText").textContent = state.progressText;

  $("#autoStart").classList.toggle("active", state.autoActive);
  $("#autoStop").classList.toggle("active", !state.autoActive && state.status === "SYSTEM STOPPED");
  $("#roughingBtn").classList.toggle("active", state.roughingActive);
  $("#turboBtn").classList.toggle("active", state.turboActive);
  $("#massFlowBtn").classList.toggle("active", state.massFlowActive);
  $("#hvToggle").classList.toggle("active", state.hvActive);
  $("#hvToggle").textContent = state.hvActive ? "STOP" : "START";
  $("#applyVoltage").classList.toggle("active", state.hvVoltageApplied);
  $("#applyVoltage").textContent = state.hvVoltageApplied ? "Applied" : "Apply";

  if (document.activeElement !== targetInput) targetInput.value = Number(state.targetMtorr).toFixed(3);
  if (document.activeElement !== voltageInput) voltageInput.value = Number(state.hvVoltage).toFixed(2);
  if (document.activeElement !== timerInput) timerInput.value = state.timer;

  drawChart(state.points || []);
}

function compactPressure(value) {
  const pressure = Number(value);
  if (!Number.isFinite(pressure) || pressure <= 0) return "0 Torr";

  const exponent = Math.floor(Math.log10(Math.abs(pressure)));
  const coefficient = pressure / (10 ** exponent);
  return `${coefficient.toFixed(3)}E${exponent}Torr`;
}

function drawChart(points) {
  const rect = chart.getBoundingClientRect();
  const ratio = window.devicePixelRatio || 1;
  chart.width = Math.max(320, Math.floor(rect.width * ratio));
  chart.height = Math.max(260, Math.floor(rect.height * ratio));
  ctx.setTransform(ratio, 0, 0, ratio, 0, 0);

  const width = rect.width;
  const height = rect.height;
  const pad = { left: 62, right: 22, top: 24, bottom: 44 };
  const plotW = width - pad.left - pad.right;
  const plotH = height - pad.top - pad.bottom;

  ctx.clearRect(0, 0, width, height);
  const bg = ctx.createLinearGradient(0, 0, 0, height);
  bg.addColorStop(0, "#101722");
  bg.addColorStop(1, "#070a12");
  ctx.fillStyle = bg;
  ctx.fillRect(0, 0, width, height);

  const now = points.length ? points[points.length - 1].time : 60;
  const start = Math.max(0, now - 60);
  const visible = points.filter((point) => point.time >= start);
  const pressures = visible.map((point) => Math.max(point.pressure, 1e-9));
  const minP = pressures.length ? Math.min(...pressures) * 0.55 : 1e-6;
  const maxP = pressures.length ? Math.max(...pressures) * 1.45 : 1e-1;
  const minLog = Math.log10(Math.max(minP, 1e-9));
  const maxLog = Math.log10(Math.max(maxP, minP * 10));

  const x = (time) => pad.left + ((time - start) / 60) * plotW;
  const y = (pressure) => {
    const value = Math.log10(Math.max(pressure, 1e-9));
    return pad.top + (1 - (value - minLog) / (maxLog - minLog)) * plotH;
  };

  ctx.strokeStyle = "#2d3a4f";
  ctx.lineWidth = 1;
  ctx.fillStyle = "#a7b4c7";
  ctx.font = "600 12px system-ui";
  ctx.textBaseline = "middle";

  for (let i = 0; i <= 4; i += 1) {
    const gx = pad.left + (plotW / 4) * i;
    ctx.beginPath();
    ctx.moveTo(gx, pad.top);
    ctx.lineTo(gx, pad.top + plotH);
    ctx.stroke();
    ctx.fillText(`${i * 15}s`, gx - 10, height - 20);
  }

  for (let i = 0; i <= 5; i += 1) {
    const gy = pad.top + (plotH / 5) * i;
    ctx.beginPath();
    ctx.moveTo(pad.left, gy);
    ctx.lineTo(pad.left + plotW, gy);
    ctx.stroke();

    const exponent = Math.round(maxLog - ((maxLog - minLog) / 5) * i);
    ctx.fillText(`1e${exponent}`, 14, gy);
  }

  ctx.strokeStyle = "#2d3a4f";
  ctx.lineWidth = 1.4;
  ctx.strokeRect(pad.left, pad.top, plotW, plotH);

  if (!visible.length) {
    ctx.fillStyle = "#a7b4c7";
    ctx.font = "700 14px system-ui";
    ctx.textAlign = "center";
    ctx.fillText("Waiting for live sensor data", pad.left + plotW / 2, pad.top + plotH / 2);
    ctx.textAlign = "left";
    return;
  }

  ctx.save();
  ctx.shadowColor = "rgba(45, 212, 191, 0.45)";
  ctx.shadowBlur = 14;
  ctx.strokeStyle = "#2dd4bf";
  ctx.lineWidth = 3.2;
  ctx.lineJoin = "round";
  ctx.lineCap = "round";
  ctx.beginPath();
  visible.forEach((point, index) => {
    const px = x(point.time);
    const py = y(point.pressure);
    if (index === 0) ctx.moveTo(px, py);
    else ctx.lineTo(px, py);
  });
  ctx.stroke();
  ctx.restore();

  ctx.fillStyle = "#f8fafc";
  visible.slice(-20).forEach((point) => {
    ctx.beginPath();
    ctx.arc(x(point.time), y(point.pressure), 2.5, 0, Math.PI * 2);
    ctx.fill();
  });

  const last = visible[visible.length - 1];
  ctx.fillStyle = "#f59e0b";
  ctx.beginPath();
  ctx.arc(x(last.time), y(last.pressure), 4.5, 0, Math.PI * 2);
  ctx.fill();
}

actionButtons.forEach((button) => {
  button.addEventListener("click", () => post(button.dataset.action));
});

targetInput.addEventListener("change", () => post("/api/target", { targetMtorr: targetInput.value }));
voltageInput.addEventListener("change", () => post("/api/hv/voltage", { voltage: voltageInput.value }));
timerInput.addEventListener("change", () => post("/api/hv/timer", { timer: timerInput.value }));
$("#applyVoltage").addEventListener("click", () => post("/api/hv/voltage", { voltage: voltageInput.value }));
$("#resetVoltage").addEventListener("click", () => post("/api/hv/reset-voltage"));
$("#timerReset").addEventListener("click", () => post("/api/hv/reset-timer"));

window.addEventListener("resize", () => {
  if (latestState) drawChart(latestState.points || []);
});

refresh();
setInterval(refresh, 650);
