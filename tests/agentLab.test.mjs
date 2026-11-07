import assert from 'node:assert/strict';
import { test } from 'node:test';
import { createRequire } from 'node:module';
const require = createRequire(import.meta.url);
// This source is intentionally dependency-free and runnable in Node for command validation.
const { createAgentLab } = await import('../js/agentLab.js');

function fakeLab() {
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
  return { lab: createAgentLab({ universe, memory, species: {Empty:0,Wood:1,Wall:2,Water:3}, fluid: { reset() {}, update() {} }, render() {}, mode: 'test' }), updates: () => updates };
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