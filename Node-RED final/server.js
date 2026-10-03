// Una instancia Node-RED por pantalla; proxy local hacia main.py (127.0.0.1:8000).
const express = require('express');
const http = require('http');
const path = require('path');
const RED = require('node-red');
const fs = require('fs');
const role = process.argv[2];
if (!['vacuum','dashboard'].includes(role)) throw Error('Use vacuum o dashboard');
const port = Number(role === 'vacuum' ? (process.env.VACUUM_PORT || 1880) : (process.env.DASHBOARD_PORT || 1881));
const app = express();
const server = http.createServer(app);
const userDir = path.join(__dirname,'.runtime',role);
fs.mkdirSync(userDir,{recursive:true});
RED.init(server,{httpAdminRoot:'/red',httpNodeRoot:'/',userDir,flowFile:path.join(__dirname,`flows-${role}.json`),credentialSecret:false,uiHost:'127.0.0.1'});
app.use('/red',RED.httpAdmin);
app.use(RED.httpNode);
app.get('/',(req,res)=>res.redirect('/dashboard/main'));
server.listen(port,'127.0.0.1',async()=>{await RED.start();console.log(`NODE-RED ${role}: http://127.0.0.1:${port}/dashboard/main | Editor http://127.0.0.1:${port}/red`)});
async function stop(){await RED.stop();server.close(()=>process.exit(0))}
process.on('SIGTERM',stop);process.on('SIGINT',stop);
