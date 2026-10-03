// Una instancia Node-RED por pantalla; proxy local al backend simulado fijo.
const express = require('express');
const http = require('http');
const path = require('path');
const RED = require('node-red');
const fs = require('fs');
const role = process.argv[2];
if (!['vacuum','dashboard'].includes(role)) throw Error('Use vacuum o dashboard');
const port = Number(role === 'vacuum' ? (process.env.SIM_VACUUM_PORT || 1880) : (process.env.SIM_DASHBOARD_PORT || 1881));
const app = express();
const server = http.createServer(app);
const userDir = path.join(__dirname,'.runtime',role);
fs.mkdirSync(userDir,{recursive:true});
RED.init(server,{httpAdminRoot:'/red',httpNodeRoot:'/',userDir,flowFile:path.join(__dirname,`flows-${role}.json`),credentialSecret:false,uiHost:'127.0.0.1'});
app.use('/red',RED.httpAdmin);
app.use(RED.httpNode);
app.get('/',(req,res)=>res.redirect('/dashboard/main'));
server.listen(port,'127.0.0.1',async()=>{await RED.start();console.log(`SIMULACION ${role}: http://127.0.0.1:${port}/ | Editor /red`)});
async function stop(){await RED.stop();server.close(()=>process.exit(0))}
process.on('SIGTERM',stop);process.on('SIGINT',stop);
