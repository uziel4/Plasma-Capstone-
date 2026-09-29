(() => {
  const cells = [...document.querySelectorAll('[data-temperature]')];
  const status = document.querySelector('#temperature-status');
  function unavailable(message) {
    cells.forEach(cell => { cell.textContent = 'Sin lectura'; cell.title = message; });
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
          cell.title = `THERMOplate address 2, canal ${entry.channel}`;
        }
      }
      status.textContent = errors.length ? errors.join('\n') : `Actualizado: ${new Date(data.timestamp*1000).toLocaleTimeString()}`;
    } catch (error) {
      unavailable(`[TEMP_CONNECTION] ${error.message}. Revise main.py y logs/control.log.`);
    } finally { setTimeout(update, 1500); }
  }
  update();
})();
