import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
// This source is intentionally dependency-free and runnable in Node for command validation.
const { createAgentLab } = await import('../js/agentLab.js');

function fakeLab({ render = () => {}, fluid = { reset() {}, update() {} } } = {}) {
  const width = 40, height = 40;
  const raw = new Uint8Array(width * height * 4);
  const memory = { buffer: raw.buffer };
  let updates = 0;
  const universe = {
    width: () => width, height: () => height, cells: () => 0,
    paint(x, y, size, id) {
      const r = size / 2;
      for (let xx = Math.max(0, Math.floor(x-r)); xx <= Math.min(width-1, Math.ceil(x+r)); xx++) {
        for (let yy = Math.max(0, Math.floor(y-r)); yy <= Math.min(height-1, Math.ceil(y+r)); yy++) {
          if (Math.hypot(xx-x, yy-y) > r) continue;
          const at = (xx * height + yy) * 4;
          if (raw[at] === 0 || id === 0) raw[at] = id;
        }
      }
    },
    tick() { updates++; }, reset() { raw.fill(0); }, flush_undos() {},
  };
  global.window = { paused: true, stopboot: false };
  return { lab: createAgentLab({ universe, memory, species: {Empty:0,Wood:1,Wall:2,Water:3}, fluid, render, mode: 'test' }), updates: () => updates };
}
test('bounded edit, inspection, revision precondition and erase', () => {
  const {lab} = fakeLab();
  let result = lab.run({op:'paint',x:8,y:8,diameter:1,material:'Wood'});
  assert.equal(result.status,'applied');
  assert.equal(result.changedCells,1);
  result = lab.run({op:'inspect',x:8,y:8,width:1,height:1,includeCells:true});
  assert.equal(result.region.cells[0].material,'Wood');
  assert.equal(lab.run({op:'paint',x:8,y:8,material:'Wall'}).changedCells,0); // empty-only paint semantics
  assert.match(lab.run({op:'paint',x:8,y:8,material:'Empty',expectedRevision:0}).reason,/stale/);
  assert.equal(lab.run({op:'paint',x:8,y:8,material:'Empty'}).changedCells,1);
  assert.equal(lab.run({op:'inspect',x:8,y:8,width:1,height:1}).region.counts.Empty,1);
});
test('refuses malformed commands and incomplete strokes without partial mutations', () => {
  const {lab} = fakeLab();
  assert.equal(lab.run({op:'paint',x:-1,y:0,material:'Wood'}).status,'refused');
  assert.equal(lab.run({op:'rect',x:0,y:0,width:999,height:2,material:'Wall'}).status,'refused');
  assert.equal(lab.run({op:'stroke',points:[{x:0,y:0},{x:1000,y:0}],material:'Wood'}).status,'refused');
  assert.equal(lab.run({op:'inspect',x:0,y:0,width:40,height:40,includeCells:true}).status,'refused');
  assert.equal(lab.run({op:'inspect',x:0,y:0,width:40,height:40}).region.counts.Empty,1600);
});
test('step requires pause and tracks ticks, exports/restores cells with explicit fidelity', () => {
  const {lab,updates} = fakeLab();
  lab.run({op:'paint',x:10,y:10,material:'Wall'});
  assert.equal(lab.run({op:'resume'}).paused,false);
  assert.equal(lab.run({op:'step',ticks:1}).status,'refused');
  lab.run({op:'pause'});
  assert.equal(lab.run({op:'step',ticks:3}).stepsApplied,3);
  assert.equal(updates(),3);
  const saved = lab.run({op:'exportCells'});
  assert.equal(saved.format,'sandspiel-cells-only/v1');
  lab.run({op:'reset'});
  assert.equal(lab.run({op:'inspect',x:10,y:10,width:1,height:1}).region.counts.Empty,1);
  assert.equal(lab.run({op:'importCells',...saved}).status,'applied');
  assert.equal(lab.run({op:'inspect',x:10,y:10,width:1,height:1}).region.counts.Wall,1);
});
test('boolean options reject invalid types without changing native cells', () => {
  const {lab} = fakeLab();
  const badRect = lab.run({op:'rect',x:1,y:1,width:10,height:10,material:'Wood',fill:'false'});
  assert.equal(badRect.status,'refused');
  assert.match(badRect.reason,/fill must be a boolean/);
  const region = lab.run({op:'inspect',x:1,y:1,width:10,height:10});
  assert.equal(region.region.counts.Empty,100);
  const badInspect = lab.run({op:'inspect',x:1,y:1,width:10,height:10,includeCells:'false'});
  assert.equal(badInspect.status,'refused');
  assert.match(badInspect.reason,/includeCells must be a boolean/);
  assert.equal(lab.run({op:'rect',x:1,y:1,width:3,height:3,material:'Wall',fill:false}).changedCells,8);
});
test('post-mutation renderer failure is not falsely classified as atomic refusal', () => {
  let failRender = false;
  const {lab} = fakeLab({render: () => { if (failRender) throw Error('renderer unavailable'); }});
  failRender = true;
  const result = lab.run({op:'paint',x:5,y:5,material:'Wood'});
  assert.equal(result.status,'failed');
  assert.equal(result.partialApplicationPossible,true);
  assert.equal(result.changedCells,1);
  assert.equal(result.revision,1);
  assert.equal(lab.run({op:'inspect',x:5,y:5,width:1,height:1}).region.counts.Wood,1);
});
test('partial native stepping preserves observed ticks and reports execution failure', () => {
  let updates = 0;
  const fluid = {reset() {},update() {if (++updates === 2) throw Error('fluid update failed');}};
  const {lab} = fakeLab({fluid});
  const result = lab.run({op:'step',ticks:3});
  assert.equal(result.status,'failed');
  assert.equal(result.nativeTicksCompleted,2);
  assert.equal(result.ticksObserved,2);
  assert.equal(result.revision,2);
  assert.equal(result.partialApplicationPossible,true);
});
test('observational commands are included in the browser command counter', () => {
  const {lab} = fakeLab();
  assert.equal(lab.run({op:'status'}).commands,1);
  assert.equal(lab.run({op:'inspect',x:0,y:0,width:1,height:1}).commands,2);
});

test('bounded native resume auto-pauses at the exact acknowledged tick', () => {
  const {lab} = fakeLab();
  assert.equal(lab.run({op:'resume', ticks:4}).status, 'applied');
  for (let i=0;i<3;i++) lab.notifyTick();
  assert.equal(lab.status().paused, false);
  lab.notifyTick();
  assert.equal(lab.status().paused, true);
  assert.equal(lab.status().ticksObserved, 4);
  assert.equal(lab.run({op:'paint',x:8,y:8,material:'Wood'}).status, 'applied');
  lab.run({op:'resume',ticks:2});
  lab.notifyTick(); lab.notifyTick();
  assert.equal(lab.status().paused, true);
  assert.equal(lab.status().ticksObserved, 6);
});
test('paced and immediate painting produce byte-identical native cells', async () => {
  const commands = [
    {op:'line',material:'Wood',diameter:3,from:{x:1,y:1},to:{x:32,y:34}},
    {op:'stroke',material:'Wall',diameter:1,points:[{x:3,y:26},{x:28,y:27},{x:33,y:32}]},
    {op:'rect',material:'Water',x:5,y:8,width:18,height:12,fill:false},
    {op:'paint',material:'Wood',x:12,y:20,diameter:9}
  ];
  const fast=fakeLab().lab, paced=fakeLab().lab;
  for (const cmd of commands) {
    assert.equal(fast.run(cmd).status,'applied');
    assert.equal((await paced.runPaced(cmd,{fps:20,stampsPerFrame:80})).status,'applied');
  }
  assert.equal(paced.run({op:'exportCells'}).cellsBase64,fast.run({op:'exportCells'}).cellsBase64);
  assert.equal(paced.status().revision,fast.status().revision);
});
test('invalid paced edit cannot apply partial stamps', async () => {
  const {lab}=fakeLab();
  assert.equal((await lab.runPaced({op:'line',material:'Wood',from:{x:1,y:1},to:{x:900,y:1}}, {fps:12})).status,'refused');
  assert.equal((await lab.runPaced({op:'paint',material:'Wood',x:5,y:5}, {fps:0})).status,'refused');
  assert.equal(lab.run({op:'inspect',x:0,y:0,width:40,height:40}).region.counts.Empty,1600);
});
