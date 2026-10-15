(() => {
  const thermal = {coil_a_temp:'Field Magnet A', coil_b_temp:'Field Magnet B', trap_a_temp:'Cool Trap A', trap_b_temp:'Cool Trap B', diff_pump_a_temp:'Diffusion Pump A', diff_pump_b_temp:'Diffusion Pump B'};
  const analogKeys = ['water_temp','water_pressure','air_pressure','medium_vacuum','high_vacuum'];
  const states = [...document.querySelectorAll('.state')];
  states.forEach(el => { el.dataset.equipment = el.getAttribute('aria-label'); });
  const diagnostics = {};
  function report(group, errors) {
    diagnostics[group] = errors;
    const all = Object.entries(diagnostics).flatMap(([key, messages]) => messages.map(m => `${key}: ${m}`));
    const alarm = all.find(m => m.includes('ALARMA High room temperature'));
    document.querySelector('#status').textContent = alarm ? 'ALARMA: HIGH ROOM TEMPERATURE' : all.length ? 'Atencion: lecturas o estados pendientes' : 'Monitor conectado';
    document.querySelector('#condition').textContent = Object.entries(diagnostics).map(([k,v]) => `${k}: ${v.length ? 'revisar diagnosticos' : 'conectado'}`).join(' | ');
    document.querySelector('#result').textContent = all.length ? all.join('\n') : 'Sin errores de comunicacion.';
  }
  function reading(key, value, unit, detail='', warning=false) {
    const el = document.querySelector(`[data-reading="${key}"]`);
    el.querySelector('.value').textContent = value;
    el.querySelector('.unit').textContent = unit;
    el.classList.toggle('warning', warning);
    el.title = detail;
    el.setAttribute('aria-label', `${key.replaceAll('_',' ')}: ${value} ${unit}. ${detail}`);
  }
  // Vencida si la marca de tiempo de main.py deja de avanzar; no se compara con el reloj de
  // este navegador (por SSH desde otra PC el reloj del Pi puede no coincidir).
  const stamps = {};
  async function poll(group, url, render, clear) {
    try {
      const response = await fetch(url,{signal:AbortSignal.timeout(10000)});
      const data = await response.json();
      if (!response.ok) throw Error(data.error || `HTTP ${response.status}`);
      if (url !== '/api/relays') {
        if (!Number.isFinite(data.timestamp)) throw Error('Lectura sin fecha');
        if (stamps[url]?.value !== data.timestamp) stamps[url] = {value: data.timestamp, at: Date.now()};
        if (Date.now() - stamps[url].at > 15000) throw Error('Lectura vencida: main.py no actualiza');
      }
      report(group, render(data));
    } catch (error) {
      clear(); report(group,[`[DASH_CONNECTION] ${error.message}. Revise main.py, la URL y logs/control.log.`]);
    } finally { setTimeout(() => poll(group,url,render,clear),1500); }
  }
  function clearRelays() {
    states.forEach(el => {el.classList.remove('on');el.classList.add('unknown');el.title='Estado no confirmado';el.setAttribute('aria-label',`${el.dataset.equipment}: desconocido`);});
  }
  poll('Reles','/api/relays',data => {
    if (!data.relays) throw Error('Respuesta de reles invalida');
    const errors=[];
    states.forEach(el => {
      const name=el.dataset.equipment, state=data.relays[name];
      const known = state?.configured && typeof state.on==='boolean';
      el.classList.toggle('unknown',!known);el.classList.toggle('on',known && state.on);
      const label=known ? (state.on?'ON':'OFF') : 'desconocido';
      el.title=`${name}: ${label}`;el.setAttribute('aria-label',el.title);
      if(!known) errors.push(`${name}: estado no confirmado`);
    });
    return errors;
  },clearRelays);
  poll('Temperaturas','/api/temperatures',data => {
    const errors=[];
    for(const [key,name] of Object.entries(thermal)) {
      const entry=data.temperatures?.[name];
      const valid=entry && !entry.error && Number.isFinite(entry.celsius);
      const detail=entry?.error?.error || (valid?`THERMOplate 2, canal ${entry.channel}`:'Sin lectura');
      reading(key,valid?entry.celsius.toFixed(1):'—','°C',detail);
      if(!valid) errors.push(`${name}: ${detail}`);
    }
    const alarm=data.room_alarm, room=data.temperatures?.Room;
    if(alarm?.active) errors.unshift(`ALARMA High room temperature: Room ${Number.isFinite(alarm.celsius)?alarm.celsius.toFixed(1):'—'} °C (activa > ${alarm.limit_c} °C; se desactiva a <= ${alarm.clear_c} °C)`);
    else if(!room || room.error || !Number.isFinite(room.celsius)) errors.push(`Room: ${room?.error?.error || 'Sin lectura'}`);
    return errors;
  },() => {
    Object.keys(thermal).forEach(k=>reading(k,'—','°C','Sin conexion'));
  });
  poll('ADC','/api/pressures',data => {
    const errors=[];
    for(const [key,name] of [['water_pressure','Water'],['air_pressure','Air']]) {
      const e=data.pressures?.[name], warning=e?.error?.code==='PRESS_RANGE';
      const valid=e && Number.isFinite(e.psi) && Number.isFinite(e.ma) && (!e.error || warning);
      const detail=e?.error?.error || (valid?`${e.channel}: ${e.ma.toFixed(3)} mA`:'Sin lectura');
      reading(key,valid?(e.psi / 14.5037738).toFixed(2):'—','bar',detail,warning);
      if(!valid || warning)errors.push(`${name}: ${detail}`);
    }
    const water=data.water_temperature;
    const valid=water && !water.error && Number.isFinite(water.celsius);
    reading('water_temp',valid?water.celsius.toFixed(2):'—','°C',water?.error?.error || 'I0: °C = (mA - 4) × 6.25');
    if(!valid)errors.push(water?.error?.error || 'Sin corriente de temperatura Water');
    for(const [key,name] of [['medium_vacuum','Medium Vacuum'],['high_vacuum','High Vacuum']]) {
      const e=data.vacuum?.[name],ok=e && !e.error && Number.isFinite(e.torr) && e.torr>0;
      const detail=e?.error?.error || (ok?`${e.channel}: ${e.volts} V`:'Sin lectura');
      reading(key,ok?(e.torr * 1.333223874).toExponential(2):'—','mbar',detail);
      if(!ok)errors.push(`${name}: ${detail}`);
    }
    return errors;
  },() => analogKeys.forEach(k=>reading(k,'—',k==='water_temp'?'°C':k.includes('vacuum')?'mbar':'bar','Sin conexion')));
})();
