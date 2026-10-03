// Run with: node --test 'producto final/tests/test_manual_polling.cjs'
const {test} = require('node:test');
const assert = require('node:assert/strict');
const vm = require('node:vm');
const fs = require('node:fs');
const path = require('node:path');
test('polling keeps controls stable and ignores a read overtaken by a command', async () => {
  let click, poll;
  const pending = [];
  const button = {disabled: false, dataset: {}, attrs: {},
    querySelector: () => ({textContent: 'Pump'}),
    getAttribute(k) {return this.attrs[k];}, setAttribute(k,v) {this.attrs[k]=v;}, removeAttribute(k) {delete this.attrs[k];},
    addEventListener(_,fn) {click=fn;}};
  const status = {textContent: ''};
  vm.runInNewContext(fs.readFileSync(path.join(__dirname,'../manual_control.js'),'utf8'), {
    document: {querySelectorAll:()=>[button], querySelector:()=>status},
    fetch: (_,options) => new Promise(resolve=>pending.push({resolve, options})),
    AbortSignal, setInterval: fn=>{poll=fn;}, Date,
  });
  const answer = (request,on) => request.resolve({ok:true,json:async()=>({relays:{Pump:{configured:true,manual_allowed:true,on}}})});
  const settle = () => new Promise(resolve=>setImmediate(resolve));
  answer(pending.shift(),false); await settle();
  assert.equal(button.disabled,false);
  const read = poll();
  assert.equal(button.disabled,false, 'background GET must not dim buttons');
  const stale = pending.shift();
  const command = click();
  assert.equal(button.disabled,true, 'command must lock buttons');
  const write = pending.shift();
  assert.equal(write.options.method,'POST');
  answer(write,true); await command;
  answer(stale,false); await read;
  assert.equal(button.attrs['aria-pressed'],'true','stale GET cannot undo confirmed command');
  assert.equal(button.disabled,false);
});
