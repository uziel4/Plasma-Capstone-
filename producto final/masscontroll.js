/* Consigna real; el estado DAC no equivale a posicion mecanica. */
(() => {
  const slider = document.getElementById('flow-slider');
  if (!slider) return;
  const valve = document.getElementById('main-valve');
  const value = document.getElementById('flow-percent');
  const meter = document.getElementById('flow-meter');
  const status = document.getElementById('mass-status');
  const apply = document.getElementById('mass-apply');
  let current = null, busy = false;
  slider.max = '81.9'; slider.step = '.1';
  function renderSelection() { value.textContent = `${Number(slider.value).toFixed(1)} %`; }
  slider.addEventListener('input', renderSelection);
  function unknown(message) {
    current = null; valve.disabled = apply.disabled = true;
    valve.dataset.unknown = 'true'; status.textContent = message;
  }
  async function request(method = 'GET', percent) {
    const response = await fetch('/api/mass-flow', {method, signal: AbortSignal.timeout(10000),
      ...(method === 'POST' ? {headers: {'Content-Type': 'application/json'}, body: JSON.stringify({percent})} : {})});
    let data;
    try { data = await response.json(); }
    catch { throw Error('Respuesta invalida: abra el GUI desde main.py, no desde Live Server.'); }
    if (!response.ok) throw Error(data.error || 'Error mass flow');
    if (!Number.isFinite(data.command_percent)) throw Error('Estado DAC invalido');
    current = data.command_percent;
    valve.dataset.unknown = 'false';
    valve.setAttribute('aria-pressed', String(current > .01));
    slider.disabled = false; valve.disabled = apply.disabled = false;
    status.textContent = `Consigna DAC: ${current.toFixed(1)} %. Limite: 81.9 %. OFF envia 0 V; no confirma cierre fisico.`;
  }
  async function send(percent) {
    if (busy) return;
    busy = true; valve.disabled = apply.disabled = true;
    try { await request('POST', percent); }
    catch (error) { unknown(error.message); }
    finally { busy = false; }
  }
  apply.addEventListener('click', () => send(Number(slider.value)));
  valve.addEventListener('click', () => send(current > .01 ? 0 : Number(slider.value)));
  window.addEventListener('adc-readings', event => {
    const reading = event.detail?.mass_flow;
    meter.textContent = reading && !reading.error && Number.isFinite(reading.percent)
      ? `${reading.percent.toFixed(1)} % FS` : 'Sin lectura';
    const message = reading?.error?.error || (reading && Number.isFinite(reading.percent) ? 'Lectura de caudal recibida.' : 'Sin lectura actual de caudal. Revise la conexión con el servidor.');
    meter.title = message;
    document.getElementById('mass-reading-status').textContent = message;
  });
  async function poll() {
    if (!busy) { busy = true; try { await request(); } catch (error) { unknown(error.message); } finally { busy = false; } }
    setTimeout(poll, 2000);
  }
  renderSelection(); poll();
})();
