(() => {
  const cells = [...document.querySelectorAll('[data-pressure]')];
  const status = document.querySelector('#pressure-status');
  const water = document.querySelector('#water-temperature-current');
  // Vencida si la marca de tiempo de main.py deja de avanzar; no se compara con el reloj de
  // este navegador (por SSH desde otra PC el reloj del Pi puede no coincidir).
  let lastStamp = null, lastChange = 0;
  async function update() {
    try {
      const response = await fetch('/api/pressures', {signal: AbortSignal.timeout(10000)});
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!data.pressures || !Number.isFinite(data.timestamp)) throw new Error('Respuesta incompleta');
      if (data.timestamp !== lastStamp) { lastStamp = data.timestamp; lastChange = Date.now(); }
      if (Date.now() - lastChange > 15000) throw new Error('Lectura vencida: main.py no actualiza');
      window.dispatchEvent(new CustomEvent('adc-readings', {detail: data}));
      const details = [];
      for (const cell of cells) {
        const name = cell.dataset.pressure;
        const entry = data.pressures[name];
        const rangeWarning = entry?.error?.code === 'PRESS_RANGE';
        const valid = entry && Number.isFinite(entry.psi) && Number.isFinite(entry.ma) && (!entry.error || rangeWarning);
        cell.textContent = valid ? `${entry.psi.toFixed(2)} PSI${rangeWarning ? ' ⚠' : ''}` : 'Sin lectura';
        cell.style.color = rangeWarning ? '#ffd28a' : '';
        const text = entry?.error?.error || (valid ? `${entry.channel}: ${entry.ma.toFixed(3)} mA` : 'Lectura invalida');
        cell.title = text;
        details.push(`${name}: ${text}`);
      }
      const waterData = data.water_temperature;
      if (water) {
      if (waterData && !waterData.error && Number.isFinite(waterData.celsius)) {
        water.textContent = `${waterData.celsius.toFixed(2)} °C`;
        water.title = `ADCplate 3, I0: ${waterData.ma.toFixed(3)} mA; °C = (mA - 4) × 6.25`;
      } else {
        water.textContent = 'Sin lectura';
        water.title = waterData?.error?.error || 'Corriente de temperatura del agua no disponible';
        details.push(water.title);
      }
      }
      status.textContent = details.join('\n');
    } catch (error) {
      window.dispatchEvent(new CustomEvent('adc-readings', {detail: null}));
      if (water) { water.textContent = 'Sin lectura'; water.title = error.message; }
      cells.forEach(cell => { cell.textContent = 'Sin lectura'; cell.title = error.message; cell.style.color = ''; });
      status.textContent = `[PRESS_CONNECTION] ${error.message}. Revise main.py y logs/control.log.`;
    } finally { setTimeout(update, 1500); }
  }
  update();
})();
