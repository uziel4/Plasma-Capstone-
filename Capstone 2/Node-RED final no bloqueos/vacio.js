(() => {
  const status = document.querySelector('#vacuum-status');
  const history = {medium: [], high: []};
  let timestamp = null;
  const format = value => `${value.toExponential(3)} Torr`;
  function chart(id, entry, fresh) {
    const value = document.querySelector(`#${id}-value`);
    const line = document.querySelector(`#${id}-line`);
    const dot = document.querySelector(`#${id}-dot`);
    const diagnostic = document.querySelector(`#${id}-diagnostic`);
    const valid = entry && !entry.error && Number.isFinite(entry.torr) && entry.torr > 0;
    if (!valid) {
      value.textContent = Number.isFinite(entry?.volts) ? `${entry.volts.toFixed(4)} V` : 'ADC sin datos';
      const volts = Number.isFinite(entry?.volts) ? `${entry.channel}: ${entry.volts.toFixed(4)} V. ` : '';
      const reason = entry?.error?.error || 'No hay datos validos del ADC. Revise la conexion con main.py.';
      value.title = volts + reason;
      diagnostic.textContent = `${volts}${reason} Linea punteada: sin datos, no representa cero Torr.`;
      line.setAttribute('points', '0,80 500,80');
      line.setAttribute('stroke-dasharray', '8 6');
      line.closest('svg').setAttribute('aria-label', 'Sin datos de presion: linea horizontal de referencia, no es una medicion');
      dot.setAttribute('r', '0'); history[id] = [];
      return;
    }
    line.removeAttribute('stroke-dasharray');
    diagnostic.textContent = Number.isFinite(entry.volts) ? `${entry.channel}: ${entry.volts.toFixed(4)} V` : '';
    value.textContent = format(entry.torr);
    value.title = `${entry.channel}: ${entry.volts.toFixed(4)} V`;
    if (fresh || history[id].length === 0) { history[id].push(Math.log10(entry.torr)); if (history[id].length > 60) history[id].shift(); }
    const list = history[id];
    const low = Math.min(...list) - 0.5, high = Math.max(...list) + 0.5;
    const points = list.map((v, i) => [i * 500 / Math.max(1, list.length - 1), 150 - (v-low)/(high-low)*140]);
    line.setAttribute('points', points.map(p => p.join(',')).join(' '));
    if (points.length) {
      dot.setAttribute('cx', points.at(-1)[0]); dot.setAttribute('cy', points.at(-1)[1]); dot.setAttribute('r', '4');
    }
    line.closest('svg').setAttribute('aria-label', `Historial logaritmico, ultimas ${list.length} muestras; escala ${low.toFixed(1)} a ${high.toFixed(1)} log10(Torr)`);
  }
  chart('medium', null, false);
  chart('high', null, false);
  // Roughing Vacuum Gauges A/B (S4/S5): solo voltaje 0-10 V como barra; no se convierte a Torr.
  function rough(id, entry) {
    const bar = document.querySelector(`#rough-bar-${id}`), fill = bar.querySelector('.bargraph-fill');
    const percent = document.querySelector(`#rough-percent-${id}`), volts = document.querySelector(`#rough-${id}`);
    const valid = entry && !entry.error && Number.isFinite(entry.volts) && Number.isFinite(entry.percent);
    fill.style.width = valid ? `${entry.percent}%` : '0%';
    percent.textContent = valid ? `${entry.percent.toFixed(1)} %` : '—';
    volts.textContent = valid ? `${entry.volts.toFixed(2)} V` : 'Sin lectura';
    bar.setAttribute('aria-valuenow', valid ? entry.percent.toFixed(1) : '0');
    bar.setAttribute('aria-valuetext', valid ? `${entry.volts.toFixed(2)} V, ${entry.percent.toFixed(1)} %` : 'Sin lectura');
    bar.title = valid ? `${entry.channel}: ${entry.volts.toFixed(3)} V` : entry?.error?.error || 'Sin lectura';
    return valid ? null : `Rough ${id.toUpperCase()}: ${entry?.error?.error || 'Sin lectura'}`;
  }
  window.addEventListener('adc-readings', event => {
    const data = event.detail;
    const readings = data?.vacuum || {};
    const fresh = data && data.timestamp !== timestamp;
    chart('medium', readings['Medium Vacuum'], fresh);
    chart('high', readings['High Vacuum'], fresh);

    const roughErrors = [rough('a', data?.rough?.['Rough Manifold A']), rough('b', data?.rough?.['Rough Manifold B'])].filter(Boolean);
    document.querySelector('#rough-status').textContent = !data ? 'Sin comunicacion con ADCplate.' : roughErrors.length ? roughErrors.join('\n') : 'S4 (A) y S5 (B): 0–10 V.';
    timestamp = data?.timestamp ?? null;
    const errors = Object.values(readings).filter(e => e.error).map(e => e.error.error);
    status.textContent = !data ? 'Sin comunicacion con ADCplate. Revise main.py y Estado de presiones.'
      : errors.length ? errors.join('\n') : 'Medium: Terranova 906A; High: GP270. Graficas: ultimas 60 muestras, escala logaritmica automatica. Objetivo solo de referencia; control automatico pendiente.';
  });
})();
