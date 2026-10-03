// Prueba las dos instancias Node-RED: GUI original en ui-template, panel de simulación y proxy a Python.
// Ejecutar con npm start activo. Termina con Emergency enclavado.
const {io}=require('socket.io-client');
const assert=require('node:assert/strict');
const ports=[Number(process.env.SIM_VACUUM_PORT||1880),Number(process.env.SIM_DASHBOARD_PORT||1881)];
const marks=[['equipment-grid','startup-start','shutdown-start','medium-line'],['diagram','data-reading="diff_pump_a_temp"','condition']];
async function api(port,path,body){
 const r=await fetch(`http://127.0.0.1:${port}/api/${path}`,body?{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)}:{});
 assert.match(r.headers.get('content-type'),/application\/json/);
 return {status:r.status,data:await r.json()};
}
(async()=>{
 for(const [i,port] of ports.entries()){
  assert((await(await fetch(`http://127.0.0.1:${port}/`)).text()).includes('FlowFuse Dashboard'));
  const socket=io(`http://127.0.0.1:${port}`,{path:'/dashboard/socket.io'});
  try{
   const config=await new Promise((resolve,reject)=>{const t=setTimeout(()=>reject(Error('No ui-config')),8000);socket.on('ui-config',(id,c)=>{clearTimeout(t);resolve(c)})});
   const pages=Object.values(config.pages).map(p=>p.path).sort();
   assert.deepEqual(pages,['/main','/sim']);
   const formats=Object.values(config.widgets).filter(w=>w.type==='ui-template').map(w=>w.props.format).join('\n');
   for(const mark of [...marks[i],'emergency-button','/api/simulation']) assert(formats.includes(mark),`Falta ${mark} en ${port}`);
  }finally{socket.close()}
 }
 const [vac,dash]=ports;
 assert.equal((await api(dash,'simulation',{overrides:{},faults:[]})).status,200);
 assert.equal((await api(vac,'relays',{name:'Diffusion Pump A',on:true})).status,400);
 assert.equal((await api(dash,'simulation',{overrides:{medium_volts:0.6505149978},faults:[]})).status,200);
 assert.equal((await api(vac,'relays',{name:'Diffusion Pump A',on:true})).status,200);
 assert((await api(dash,'relays')).data.relays['Diffusion Pump A'].on);
 assert.equal((await api(vac,'startup',{})).status,200);
 assert((await api(dash,'startup')).data.manual_locked);
 assert((await api(dash,'emergency',{})).data.active);
 assert(Object.values((await api(vac,'relays')).data.relays).every(r=>!r.on));
 console.log('PASS: GUI original en ui-template (main + sim) en ambas instancias, proxy JSON, estado compartido, startup y Emergency');
})().catch(e=>{console.error(e);process.exitCode=1});
