// Arranca main.py (Pi-Plates) y las dos instancias Node-RED. Si uno termina, cierra todo.
// Al cerrar, main.py ejecuta su apagado de software (reles OFF); se espera a que termine.
const {spawn}=require('child_process');
const path=require('path');
const python=process.env.PYTHON||'python3';
const children=[];
let closing=false;
function close(code=0){
  if(closing)return;closing=true;
  for(const child of children)if(child.exitCode===null)child.kill('SIGTERM');
  const timer=setTimeout(()=>process.exit(code),15000);
  Promise.all(children.map(c=>c.exitCode!==null?null:new Promise(r=>c.once('exit',r)))).then(()=>{clearTimeout(timer);process.exit(code)});
}
function run(name,command,args){
  const child=spawn(command,args,{cwd:__dirname,stdio:'inherit'});children.push(child);
  child.on('error',e=>{console.error(`${name}:`,e);close(1)});
  child.on('exit',code=>{if(!closing){console.error(`${name} termino (codigo ${code}); cerrando todo.`);close(code||1)}});
}
run('main.py',python,[path.join(__dirname,'main.py'),'--port','8000','--no-browser']);
run('Node-RED vacuum',process.execPath,[path.join(__dirname,'server.js'),'vacuum']);
run('Node-RED dashboard',process.execPath,[path.join(__dirname,'server.js'),'dashboard']);
// Abrir el Vacuum Controller en el escritorio del Pi, como hacia main.py.
if(!process.env.NO_BROWSER&&(process.env.DISPLAY||process.env.WAYLAND_DISPLAY)){
  setTimeout(()=>{if(!closing)spawn('xdg-open',[`http://127.0.0.1:${process.env.VACUUM_PORT||1880}/dashboard/main`],{stdio:'ignore',detached:true}).on('error',()=>{}).unref()},8000);
}
process.on('SIGINT',()=>close());process.on('SIGTERM',()=>close());
