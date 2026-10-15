// Tarjeta centrada de la alarma High room temperature (Room > 29 °C). Igual en ambos GUI.
// Aparece mientras la alarma esta activa y nadie la apago; "Apagar alarma" apaga el Buzzer
// (POST /api/room-alarm/silence) y la cierra en las dos pantallas hasta que Room baje a <= 28 °C.
(() => {
  const overlay = document.getElementById('room-alarm-overlay');
  if (!overlay) return;
  const temp = document.getElementById('room-alarm-temp');
  const limit = document.getElementById('room-alarm-limit');
  const clear = document.getElementById('room-alarm-clear');
  const buzz = document.getElementById('room-alarm-buzz');
  const buzzText = document.getElementById('room-alarm-buzz-text');
  const button = document.getElementById('room-alarm-silence');
  const error = document.getElementById('room-alarm-error');
  let busy = false;

  function show(alarm) {
    const visible = alarm?.active === true && alarm.silenced !== true;
    const opening = visible && overlay.hidden;
    overlay.hidden = !visible;
    if (!visible) { error.hidden = true; return; }
    temp.textContent = Number.isFinite(alarm.celsius) ? alarm.celsius.toFixed(1) : '—';
    limit.textContent = alarm.limit_c;
    clear.textContent = alarm.clear_c;
    buzzText.textContent = alarm.buzzer ? 'Buzzer sonando' : 'Buzzer apagado';
    buzz.classList.toggle('room-alarm-quiet', !alarm.buzzer);
    if (opening) button.focus();
  }

  async function poll() {
    if (!busy) {
      try {
        const response = await fetch('/api/temperatures', {signal: AbortSignal.timeout(10000)});
        if (response.ok) show((await response.json()).room_alarm);
      } catch { /* Sin conexion: se conserva lo mostrado; temperaturas.js informa el error. */ }
    }
    setTimeout(poll, 2000);
  }

  button.addEventListener('click', async () => {
    if (busy) return;
    busy = true; button.disabled = true; button.textContent = 'Apagando…'; error.hidden = true;
    try {
      const response = await fetch('/api/room-alarm/silence', {method: 'POST', signal: AbortSignal.timeout(10000),
        headers: {'Content-Type': 'application/json'}, body: '{}'});
      const data = await response.json().catch(() => null);
      if (!response.ok) throw Error(data?.error || `HTTP ${response.status}`);
      show(data);
    } catch (exc) {
      error.textContent = `No se pudo apagar la alarma: ${exc.message}. Apague el Buzzer desde Manual Control.`;
      error.hidden = false;
    } finally {
      busy = false; button.disabled = false; button.textContent = 'Apagar alarma';
    }
  });
  poll();
})();
