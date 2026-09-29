(() => {
  const status = document.querySelector('#vacuum-status');
  const history = {medium: [], high: []};
  let timestamp = null;
  let lastReadings = {};
  const format = value => `${value.toExponential(3)} Torr`;
  function chart(id, entry, fresh) {
    const value = document.querySelector(`#${id}-value`);
    const line = document.querySelector(`#${id}-line`);
    const dot = document.querySelector(`#${id}-dot`);
    const valid = entry && !entry.error && Number.isFinite(entry.torr) && entry.torr > 0;
    if (!valid) {
      value.textContent = 'Sin lectura'; line.setAttribute('points', ''); dot.setAttribute('r', '0'); history[id] = [];
      return;
    }
    value.textContent = format(entry.torr);
    value.title = `${entry.channel}: ${entry.volts.toFixed(4)} V`;
    if (fresh) { history[id].push(Math.log10(entry.torr)); if (history[id].length > 60) history[id].shift(); }
    const list = history[id];
    const low = Math.min(...list) - 0.5, high = Math.max(...list) + 0.5;
    const points = list.map((v, i) => [i * 500 / Math.max(1, list.length - 1), 150 - (v-low)/(high-low)*140]);
    line.setAttribute('points', points.map(p => p.join(',')).join(' '));
    if (points.length) {
      dot.setAttribute('cx', points.at(-1)[0]); dot.setAttribute('cy', points.at(-1)[1]); dot.setAttribute('r', '4');
    }
    line.closest('svg').setAttribute('aria-label', `Historial logaritmico, ultimas ${list.length} muestras; escala ${low.toFixed(1)} a ${high.toFixed(1)} log10(Torr)`);
  }
  window.addEventListener('adc-readings', event => {
    const data = event.detail;
    const readings = data?.vacuum || {};
    lastReadings = readings;
    const fresh = data && data.timestamp !== timestamp;
    chart('medium', readings['Medium Vacuum'], fresh);
    chart('high', readings['High Vacuum'], fresh);

    timestamp = data?.timestamp ?? null;
    const errors = Object.values(readings).filter(e => e.error).map(e => e.error.error);
    status.textContent = !data ? 'Sin comunicacion con ADCplate. Revise main.py y Estado de presiones.'
      : errors.length ? errors.join('\n') : 'Medium: Terranova 906A; High: GP270. Graficas: ultimas 60 muestras, escala logaritmica automatica. Objetivo solo de referencia; control automatico pendiente.';
  });
})();
