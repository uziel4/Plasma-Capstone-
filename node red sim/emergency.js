(() => {
  const button = document.getElementById('emergency-button');
  const status = document.getElementById('emergency-status');
  let busy = false;
  async function request(stop) {
    const response = await fetch('/api/emergency', {method: stop ? 'POST' : 'GET', signal: AbortSignal.timeout(15000),
      ...(stop ? {headers: {'Content-Type': 'application/json'}, body: '{}'} : {})});
    if (!response.ok) throw Error(`HTTP ${response.status}`);
    const data = await response.json();
    if (typeof data.active !== 'boolean') throw Error('Respuesta invalida');
    if (data.active) {
      const result = data.result;
      status.textContent = result?.confirmed
        ? 'PARO ACTIVADO. Relés OFF y consigna cero confirmados en las placas. Mandos bloqueados hasta reiniciar main.py.'
        : `PARO ACTIVADO: hay salidas sin confirmar. Mandos bloqueados.\n${Object.entries(result?.errors || {}).map(([k,v])=>`${k}: ${v}`).join('\n')}`;
      button.textContent = 'REINTENTAR APAGADO';
    }
  }
  button.addEventListener('click', async () => {
    if (busy) return;
    busy = true; button.disabled = true;
    status.textContent = 'Solicitando apagado…';
    try { await request(true); }
    catch { status.textContent = 'NO SE PUDO CONFIRMAR EL PARO. Compruebe el equipo y use el paro físico. La orden pudo llegar al servidor.'; }
    finally { busy = false; button.disabled = false; }
  });
  async function poll() {
    if (!busy) { try { await request(false); } catch { if (button.textContent === 'EMERGENCY SHUTDOWN') status.textContent = 'Sin conexión con el paro. Abra main.py y use su dirección; Live Server no controla el hardware.'; } }
    setTimeout(poll, 2000);
  }
  poll();
})();
