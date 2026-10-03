const {spawn}=require('child_process');
const path=require('path');
const children=[];
let closing=false;
function close(code=0){if(closing)return;closing=true;for(const child of children)child.kill('SIGTERM');setTimeout(()=>process.exit(code),1500)}
function run(command,args){const child=spawn(command,args,{cwd:__dirname,stdio:'inherit'});children.push(child);child.on('error',e=>{console.error(e);close(1)});child.on('exit',code=>{if(!closing)close(code||1)});}
run('python3',[path.join(__dirname,'main_sim.py')]);
run(process.execPath,[path.join(__dirname,'server.js'),'vacuum']);
run(process.execPath,[path.join(__dirname,'server.js'),'dashboard']);
process.on('SIGINT',()=>close());process.on('SIGTERM',()=>close());
