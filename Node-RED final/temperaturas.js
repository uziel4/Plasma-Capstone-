(() => {
  const cells = [...document.querySelectorAll('[data-temperature]')];
  const status = document.querySelector('#temperature-status');
  function unavailable(message) {
    cells.forEach(cell => { cell.textContent = 'Sin lectura'; cell.title = message; cell.closest('.metric').classList.remove('room-alarm'); });
    status.textContent = message;
  }
  async function update() {
    try {
      const response = await fetch('/api/temperatures', {signal: AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!data.temperatures || !Number.isFinite(data.timestamp) || Math.abs(Date.now()/1000-data.timestamp)>15) {
        throw new Error('Respuesta incompleta o lectura vencida');
      }
      const errors = [];
      for (const cell of cells) {
        const entry = data.temperatures[cell.dataset.temperature];
        if (!entry || entry.error || !Number.isFinite(entry.celsius)) {
          const message = entry?.error?.error || 'Lectura no valida';
          cell.textContent = 'Sin lectura'; cell.title = message;
          errors.push(`${cell.dataset.temperature}: ${message}`);
        } else {
          cell.textContent = `${entry.celsius.toFixed(1)} °C`;
          cell.title = `THERMOplate address 2, ${entry.channel === 9 ? 'puerto 9 (DS18B20)' : 'canal ' + entry.channel}`;
        }
      }
      const alarm = data.room_alarm, room = cells.find(cell => cell.dataset.temperature === 'Room');
      const high = alarm?.active === true;
      if (room) {
        room.closest('.metric').classList.toggle('room-alarm', high);
        if (high) { room.textContent += ' — HIGH ROOM TEMPERATURE'; room.title = `Alarma: se activo con Room mayor de ${alarm.limit_c} °C; se desactiva a ${alarm.clear_c} °C o menos. Buzzer ${alarm.buzzer ? 'activado' : 'no activado'}.`; }
      }
      if (high) errors.unshift(`ALARMA High room temperature: activa con Room > ${alarm.limit_c} °C; se desactiva a <= ${alarm.clear_c} °C`);
      if (alarm?.error) errors.push(`Alarma Room: ${alarm.error}`);
      status.textContent = errors.length ? errors.join('\n') : `Actualizado: ${new Date(data.timestamp*1000).toLocaleTimeString()}`;
    } catch (error) {
      unavailable(`[TEMP_CONNECTION] ${error.message}. Revise main.py y logs/control.log.`);
    } finally { setTimeout(update, 1500); }
  }
  update();
})();
