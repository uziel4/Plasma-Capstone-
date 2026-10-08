(() => {
  const buttons = [...document.querySelectorAll('#equipment-grid button')];
  const status = document.querySelector('#manual-status');
  let busy = false;
  let connected = false;
  let refreshing = false;
  let revision = 0;
  let states = {};
  function lock() {
    buttons.forEach(b => {
      const disabled = busy || !connected || !states[b.querySelector('.name').textContent]?.configured || states[b.querySelector('.name').textContent]?.manual_allowed !== true;
      if (b.disabled !== disabled) b.disabled = disabled;
    });
  }
  function offline(message) {
    connected = false;
    buttons.forEach(b => { b.removeAttribute('aria-pressed'); b.dataset.unknown = 'true'; });
    status.textContent = `Sin estado confirmado: ${message}`;
    if (message !== 'Conectando…') {
      let detail = document.querySelector('#ultimo-error');
      if (!detail) {
        detail = document.createElement('details'); detail.id = 'ultimo-error';
        const summary = document.createElement('summary'); summary.textContent = 'Ultimo error';
        const text = document.createElement('p'); detail.append(summary, text); status.after(detail);
      }
      detail.querySelector('p').textContent = `${new Date().toLocaleString()} — ${message}`;
    }
    lock();
  }
  async function request(options) {
    let response;
    try {
      response = await fetch('/api/relays', {...options, signal: AbortSignal.timeout(5000)});
    } catch (e) {
      const timeout = e.name === 'TimeoutError' || e.name === 'AbortError';
      throw new Error(timeout
        ? '[NET_TIMEOUT] El servidor no respondio en 5 segundos. Revise la terminal y logs/control.log. La orden puede haberse aplicado; no se reenvia automaticamente.'
        : '[NET_CONNECTION] No se pudo contactar al servidor. Mantenga main.py abierto y acceda a su URL; no abra el HTML directamente. Si envio una orden, compruebe el rele antes de repetir.');
    }
    let data;
    try { data = await response.json(); }
    catch { throw new Error('[NET_RESPONSE] Respuesta no valida. Revise la URL y actualice juntos main.py y manual_control.js.'); }
    if (!response.ok) throw new Error(data.error || `[NET_RESPONSE] HTTP ${response.status}. Revise logs/control.log.`);
    if (!data.relays || buttons.some(b => {
      const state = data.relays[b.querySelector('.name').textContent];
      return !state || typeof state.configured !== 'boolean' || (state.configured && typeof state.on !== 'boolean');
    })) throw new Error('[NET_RESPONSE] Faltan estados validos de los reles. Actualice juntos los archivos del servidor y GUI.');
    return data;
  }
  function render(data) {
    connected = true;
    states = data.relays;
    const message = 'Reles conectados — estado confirmado por las placas.';
    if (status.textContent !== message) status.textContent = message;
    buttons.forEach(b => {
      const state = states[b.querySelector('.name').textContent];
      b.title = state?.manual_reason || (state?.manual_allowed === true ? 'Control manual disponible' : 'Bloqueado en la etapa inicial de control manual');
      const unknown = String(!state?.configured);
      if (b.dataset.unknown !== unknown) b.dataset.unknown = unknown;
      if (state?.configured) {
        const pressed = String(state.on);
        if (b.getAttribute('aria-pressed') !== pressed) b.setAttribute('aria-pressed', pressed);
      }
      else b.removeAttribute('aria-pressed');
    });
    lock();
  }
  async function refresh() {
    if (busy || refreshing) return;
    refreshing = true;
    const snapshot = revision;
    try {
      const data = await request();
      if (!busy && snapshot === revision) render(data);
    } catch (e) {
      if (!busy && snapshot === revision) offline(e.message);
    } finally { refreshing = false; }
  }
  buttons.forEach(button => {
    button.addEventListener('click', async () => {
      if (busy || !connected) return;
      const name = button.querySelector('.name').textContent;
      if (states[name]?.manual_allowed !== true) return;
      revision += 1;
      busy = true; lock();
      status.textContent = 'Esperando confirmacion de la placa…';
      try {
        render(await request({method: 'POST', headers: {'Content-Type': 'application/json'},
          body: JSON.stringify({name, on: !states[name].on})}));
      } catch (e) { offline(e.message); }
      finally { busy = false; lock(); }
    });
  });
  offline('Conectando…');
  refresh();
  setInterval(refresh, 2000);
})();
