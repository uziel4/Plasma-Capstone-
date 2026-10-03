// Prueba SOLO LECTURA de las dos instancias Node-RED con npm start activo.
// No envía órdenes (ningún POST): segura con el reactor conectado.
const {io}=require('socket.io-client');
const assert=require('node:assert/strict');
const ports=[Number(process.env.VACUUM_PORT||1880),Number(process.env.DASHBOARD_PORT||1881)];
const marks=[['equipment-grid','startup-start','shutdown-start','medium-line','data-temperature="Room"'],['diagram','data-reading="diff_pump_a_temp"','condition']];
(async()=>{
 for(const [i,port] of ports.entries()){
  assert((await(await fetch(`http://127.0.0.1:${port}/`)).text()).includes('FlowFuse Dashboard'));
  const socket=io(`http://127.0.0.1:${port}`,{path:'/dashboard/socket.io'});
  try{
   const config=await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('No ui-config')),8000);socket.on('ui-config',(id,c)=>{clearTimeout(t);resolve(c)})});
   assert.deepEqual(Object.values(config.pages).map(p=>p.path),['/main']);
   const formats=Object.values(config.widgets).filter(w=>w.type==='ui-template').map(w=>w.props.format).join('\n');
   for(const mark of [...marks[i],'emergency-button']) assert(formats.includes(mark),`Falta ${mark} en ${port}`);
   assert(!/SIMULACI|\/api\/simulation/.test(formats),'La GUI final no debe tener simulación');
  }finally{socket.close()}
  for(const path of ['relays','temperatures','pressures','startup','shutdown','emergency']){
   const r=await fetch(`http://127.0.0.1:${port}/api/${path}`);
   assert.match(r.headers.get('content-type'),/application\/json/);
   const data=await r.json();
   assert.equal(r.status,200,`${port}/api/${path}: ${JSON.stringify(data)}`);
  }
 }
 const temps=await(await fetch(`http://127.0.0.1:${ports[0]}/api/temperatures`)).json();
 assert.equal(temps.temperatures.Room.channel,9);
 assert.equal(temps.room_alarm.limit_c,29);
 console.log('PASS: dos instancias Node-RED con la GUI final (sin simulación) y API de main.py por proxy; sin enviar órdenes');
})().catch(e=>{console.error(e);process.exitCode=1});
