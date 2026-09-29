(() => {
  const start = document.querySelector('#startup-start');
  const confirm = document.querySelector('#startup-confirm');
  const status = document.querySelector('#startup-status');
  // Emergency queda fuera: nunca bloquear body, screen-content ni emergency-panel.
  const panels = ['flow-heading', 'manual-heading', 'auto-heading'].map(id => document.querySelector(`[aria-labelledby="${id}"]`)).filter(Boolean);
  const shutdownStart = document.querySelector('#shutdown-start');
  const shutdownConfirm = document.querySelector('#shutdown-confirm');
  let startupState = null, shutdownState = null;
  let busy = false;
  let revision = 0;
  function lock(locked) {
    panels.forEach(panel => { panel.inert = locked; panel.style.opacity = locked ? '.65' : ''; });
  }
  function render(data) {
    if (typeof data.manual_locked !== 'boolean' || typeof data.can_start !== 'boolean') throw Error('Estado startup invalido');
    startupState = data;
    lock(data.manual_locked || !shutdownState || shutdownState.manual_locked);
    start.disabled = busy || !data.can_start || !shutdownState || shutdownState.manual_locked;
    confirm.hidden = !data.can_confirm;
    confirm.disabled = busy || !data.can_confirm;
    const labels = {idle:'Listo para iniciar', running:'En proceso', awaiting_gas:'Esperando confirmacion manual', complete:'Completado', failed:'Detenido por error', stopped:'Interrumpido por emergencia'};
    document.querySelector('#startup-step').textContent = `Paso ${data.step} de ${data.total} — ${data.title}`;
    status.textContent = labels[data.status] || data.status;
    document.querySelector('#startup-condition').textContent = data.status === 'complete' ? 'Gas confirmado; controles manuales disponibles.' : data.condition;
    const values = Object.entries(data.readings || {}).map(([name, entry]) => `${name}: ${entry.value === null ? 'Sin lectura valida' : (entry.unit === 'Torr' ? entry.value.toExponential(3) : entry.value.toFixed(2)) + ' ' + entry.unit}`);
    if (data.remaining_seconds !== null) values.push(`Tiempo restante: ${data.remaining_seconds} s`);
    document.querySelector('#startup-readings').textContent = values.join(' | ');
    document.querySelector('#startup-error').textContent = data.error ? `Error: ${data.error}` : '';
    const list = document.querySelector('#startup-steps');
    list.replaceChildren(...data.steps.map(step => {
      const item = document.createElement('li');
      item.textContent = `${step.title} — ${step.state}`;
      if (step.state === 'actual') { item.style.fontWeight = 'bold'; item.setAttribute('aria-current','step'); }
      return item;
    }));
  }
  function renderShutdown(data) {
    shutdownState = data;
    shutdownStart.disabled = busy || !data.can_start;
    shutdownConfirm.hidden = !data.can_confirm;
    shutdownConfirm.disabled = busy || !data.can_confirm;
    document.querySelector('#shutdown-status').textContent = `Paso ${data.step} de ${data.total} — ${data.title} — ${data.status}`;
    document.querySelector('#shutdown-condition').textContent = data.status === 'complete' ? 'Shutdown normal completado.' : data.condition;
    document.querySelector('#shutdown-readings').textContent = Object.entries(data.readings || {}).map(([n,e]) => `${n}: ${e.value === null ? 'Sin lectura' : e.value.toFixed(2) + ' ' + e.unit}`).join(' | ') + (data.remaining_seconds === null ? '' : ` | Tiempo restante: ${data.remaining_seconds} s`);
    document.querySelector('#shutdown-error').textContent = data.error || '';
    document.querySelector('#shutdown-steps').replaceChildren(...data.steps.map(step => {
      const li = document.createElement('li'); li.textContent = `${step.title} — ${step.state}`; return li;
    }));
    if (startupState) render(startupState);
  }
  async function request(path, post=false) {
    const response = await fetch(path, {signal: AbortSignal.timeout(10000), ...(post ? {method:'POST', headers:{'Content-Type':'application/json'}, body:'{}'} : {})});
    if (!(response.headers.get('content-type') || '').includes('application/json')) {
      throw Error('Abra la direccion de main.py; Live Server no ejecuta el startup ni el paro');
    }
    const data = await response.json();
    if (!response.ok) throw Error(data.error || `HTTP ${response.status}`);
    return data;
  }
  function failure(error) {
    lock(true); start.disabled = confirm.disabled = shutdownStart.disabled = shutdownConfirm.disabled = true;
    document.querySelector('#startup-step').textContent = 'Startup — estado desconocido';
    ['startup-condition','startup-readings','startup-error','startup-steps'].forEach(id => document.getElementById(id).replaceChildren());
    shutdownState = null;
    document.querySelector('#shutdown-status').textContent = 'Shutdown: estado desconocido';
    ['shutdown-condition','shutdown-readings','shutdown-error','shutdown-steps'].forEach(id => document.getElementById(id).replaceChildren());
    status.textContent = `Secuencia sin confirmacion: ${error.message}. Consulte main.py; no reenvie una orden incierta.`;
  }
  async function command(path) {
    if (busy) return;
    revision += 1; busy = true; lock(true); start.disabled = confirm.disabled = shutdownStart.disabled = shutdownConfirm.disabled = true;
    try { const data = await request(path,true); busy = false; if (path.includes('/shutdown')) renderShutdown(data); else render(data); }
    catch(error) { failure(error); }
    finally { busy = false; }
  }
  start.addEventListener('click', () => command('/api/startup'));
  confirm.addEventListener('click', () => command('/api/startup/confirm-gas'));
  shutdownStart.addEventListener('click', () => command('/api/shutdown'));
  shutdownConfirm.addEventListener('click', () => command('/api/shutdown/confirm-gas'));
  async function refresh() {
    if (!busy) { const snapshot = revision; try { const [data, stop] = await Promise.all([request('/api/startup'), request('/api/shutdown')]); if (!busy && snapshot === revision) { startupState = data; renderShutdown(stop); } } catch(error) { if (!busy && snapshot === revision) failure(error); } }
    setTimeout(refresh,1000);
  }
  lock(true); refresh();
})();
