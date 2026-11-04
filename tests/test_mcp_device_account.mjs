import assert from "node:assert/strict";
import test from "node:test";
import { readFileSync } from "node:fs";

// Exercise the real inline Account port body in isolation. Do not introduce
// a second copy of the validator just for tests.
const source = readFileSync(new URL("../site/assets/site.js", import.meta.url), "utf8").replace(/\r\n/g, "\n");
const start = source.indexOf("    async readMcpDevices(signal) {");
const end = source.indexOf("\n    },\n    subscribe(observer)", start);
assert.ok(start > 0 && end > start, "Account MCP device port missing");
const body = source.slice(start + "    async readMcpDevices(signal) {".length, end);

function harness(session, transport) {
  return new Function("loadJson", "initial", `let sessionView = initial;
    return { read: async function(signal) {${body}
    }, change(next) { sessionView = next; } };`)(transport, session);
}
const first = {
  device_id:"14cef8f4-3c06-4b1b-9e3a-42c74ef7dec5",
  name:"Windows OrdaX",kind:"desktop",channel:"development",
  state:"active",online:true,runtime_ready:true,last_seen_at:"2026-11-03T20:00:00Z",
};
const good = {ok:true,schema:"ordax.owner-mcp-devices/1",count:1,devices:[first]};

test("signed-in Account reads bounded same-origin device route without product tokens", async () => {
  let calls = [];
  const h = harness({status:"authenticated"},async (...args) => {calls.push(args);return good;});
  assert.deepEqual(await h.read(),good);
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],"/account/mcp/devices");
  assert.deepEqual(calls[0][2],{maxBytes:65536});
});

test("anonymous Account cannot fetch device inventory",async () => {
  const h=harness({status:"anonymous"},async () => {throw Error("should not fetch");});
  await assert.rejects(h.read(),/public-account-session-required/);
});

test("malformed inventory, other schemas and duplicate device ids fail closed",async () => {
  for(const invalid of [
    {...good,schema:"unknown"},
    {...good,count:2},
    {...good,devices:[first,first],count:2},
    {...good,devices:[{...first,online:"true"}]},
    {...good,devices:[{...first,device_id:"wrong-id"}]},
    {...good,devices:[{...first,last_seen_at:"invalid-date"}]},
  ]) {
    const h=harness({status:"authenticated"},async()=>invalid);
    await assert.rejects(h.read(),/public-account-mcp-devices-invalid/);
  }
});

test("data from a superseded account session cannot be displayed",async () => {
  let finish;
  const waiting=new Promise(resolve=>{finish=resolve;});
  const h=harness({status:"authenticated"},()=>waiting);
  const read=h.read();
  h.change({status:"authenticated"});
  finish(good);
  await assert.rejects(read,/public-account-session-changed/);
});

test("an authenticated, verified empty list is distinct from an unavailable server",async () => {
  const empty={ok:true,schema:"ordax.owner-mcp-devices/1",count:0,devices:[]};
  assert.deepEqual(await harness({status:"authenticated"},async()=>empty).read(),empty);
  await assert.rejects(harness({status:"authenticated"},async()=>{throw Error("503");}).read(),/503/);
});
