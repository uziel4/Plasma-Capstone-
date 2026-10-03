/* Consigna real; el estado DAC no equivale a posicion mecanica. */
(() => {
  const slider = document.getElementById('flow-slider');
  // Manual Gas Flow Control comentado en HTML: reservado para grupos futuros.
  const valve = document.getElementById('main-valve');
  const value = document.getElementById('flow-percent');
  const meter = document.getElementById('flow-meter');
  const status = document.getElementById('mass-status');
  const apply = document.getElementById('mass-apply');
  window.addEventListener('adc-readings', event => {
    const reading = event.detail?.mass_flow;
    meter.textContent = reading && !reading.error && Number.isFinite(reading.percent)
      ? `${(reading.percent * 50).toFixed(0)} SCCM` : 'Sin lectura';
    const message = reading?.error?.error || (reading && Number.isFinite(reading.percent) ? 'Lectura de caudal recibida.' : 'Sin lectura actual de caudal. Revise la conexión con el servidor.');
    meter.title = message;
    document.getElementById('mass-reading-status').textContent = message;
  });
  if (!slider) return; // Solo lectura del meter; no consultar ni mandar consignas.
  let current = null, busy = false;
  slider.min = '10'; slider.max = '5000'; slider.step = '1';
  function renderSelection() { value.textContent = `${Number(slider.value).toFixed(0)} SCCM`; }
  slider.addEventListener('input', renderSelection);
  function unknown(message) {
    current = null; valve.disabled = apply.disabled = true;
    valve.dataset.unknown = 'true'; status.textContent = message;
  }
  async function request(method = 'GET', sccm) {
    const response = await fetch('/api/mass-flow', {method, signal: AbortSignal.timeout(10000),
      ...(method === 'POST' ? {headers: {'Content-Type': 'application/json'}, body: JSON.stringify({sccm})} : {})});
    let data;
    try { data = await response.json(); }
    catch { throw Error('Respuesta invalida: abra el GUI desde main.py, no desde Live Server.'); }
    if (!response.ok) throw Error(data.error || 'Error mass flow');
    if (!Number.isFinite(data.command_percent)) throw Error('Estado DAC invalido');
    current = data.command_percent;
    valve.dataset.unknown = 'false';
    valve.setAttribute('aria-pressed', String(current > .01));
    slider.disabled = false; valve.disabled = apply.disabled = false;
    status.textContent = `Consigna DAC: ${(current * 50).toFixed(0)} SCCM. Maximo aplicable: 4095 SCCM. OFF envia 0 V; no confirma cierre fisico.`;
  }
  async function send(sccm) {
    if (busy) return;
    if (sccm > 4095) { status.textContent = 'Seleccion superior al limite de salida: maximo aplicable 4095 SCCM. No se envio la orden.'; return; }
    busy = true; valve.disabled = apply.disabled = true;
    try { await request('POST', sccm); }
    catch (error) { unknown(error.message); }
    finally { busy = false; }
  }
  apply.addEventListener('click', () => send(Number(slider.value)));
  valve.addEventListener('click', () => send(current > .01 ? 0 : Number(slider.value)));
  async function poll() {
    if (!busy) { busy = true; try { await request(); } catch (error) { unknown(error.message); } finally { busy = false; } }
    setTimeout(poll, 2000);
  }
  renderSelection(); poll();
})();
