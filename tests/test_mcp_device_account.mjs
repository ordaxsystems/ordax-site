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
// Execute the original path gate from site.js. Tests of the Account port
// alone would mock loadJson and miss a GET rejected before network dispatch.
const gateStart = source.indexOf("  function sameOriginPath(value) {");
const gateEnd = source.indexOf("\n  // Eligibility is shared", gateStart);
assert.ok(gateStart >= 0 && gateEnd > gateStart, "canonical same-origin gate missing");
const sameOriginPath = new Function(source.slice(gateStart,gateEnd) +
  "\nreturn sameOriginPath;")();

test("real same-origin gate permits only a single exact MCP authority UUID query",()=>{
  const deviceId="14cef8f4-3c06-4b1b-9e3a-42c74ef7dec5";
  const valid="/account/mcp/authority?device_id="+deviceId;
  assert.equal(sameOriginPath(valid),true);
  assert.equal(sameOriginPath("/account/mcp/devices"),true);
  assert.equal(sameOriginPath("/account/mcp/revoke"),true);
  for(const bad of [
    "/account/mcp/authority", "/account/mcp/authority?device_id=bad",
    valid+"&device_id="+deviceId, valid+"&owner_id="+deviceId,
    "/account/mcp/authority?owner_id="+deviceId,
    "/account/mcp/authority?device_id="+deviceId.toUpperCase(),
    "/account/mcp/authority?device_id=%31"+deviceId.slice(1),
    valid+"#fragment", "/auth/session?device_id="+deviceId,
    "/account/usage/mcp?device_id="+deviceId,
    "/account/mcp/authority?device_id="+deviceId+"/../../auth/session",
    "//evil.example/account/mcp/authority?device_id="+deviceId,
    "https://evil.example/account/mcp/authority?device_id="+deviceId,
  ]) assert.equal(sameOriginPath(bad),false,bad);
});

test("Account JSON transport always invokes the real same-origin URL gate",()=>{
  assert.match(source,/if \(!sameOriginPath\(path\)\) throw new Error\("api-path-invalid"\)/);
});

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

const authorityStart = source.indexOf("    async readMcpAuthority(deviceId, signal) {");
const authorityEnd = source.indexOf("\n    },\n    async revokeMcpGrant(input, signal) {", authorityStart);
const revokeStart = source.indexOf("    async revokeMcpGrant(input, signal) {");
const revokeEnd = source.indexOf("\n    },\n    // Reuse Account's authenticated", revokeStart);
assert.ok(authorityStart > 0 && authorityEnd > authorityStart, "Owner authority read port missing");
assert.ok(revokeStart > 0 && revokeEnd > revokeStart, "Owner revoke port missing");

function ownerHarness(session, loadJson) {
  const authorityBody = source.slice(authorityStart + "    async readMcpAuthority(deviceId, signal) {".length, authorityEnd);
  const revokeBody = source.slice(revokeStart + "    async revokeMcpGrant(input, signal) {".length, revokeEnd);
  return new Function("loadJson", "initial", `let sessionView=initial;
    return {
      authority: async function(deviceId,signal) {${authorityBody}
      },
      revoke: async function(input,signal) {${revokeBody}
      },
      change(next) {sessionView=next}
    };`)(loadJson,session);
}
const other = "44444444-4444-4444-8444-444444444444";
const client = "22222222-2222-4222-8222-222222222222";
const group = "33333333-3333-4333-8333-333333333333";
const groupItem = {grant_group_id:group,client_id:client,profile_key:"full-computer-control",valid_until:null,client_consent_active:true};
const authority = {ok:true,schema:"ordax.owner-mcp-authority-view/1",device_id:first.device_id,
  clients:[{client_id:client,client_name:"ChatGPT"}],grant_groups:[groupItem]};

test("Account grant inspection is scoped to one UUID, rejects forgery and duplicate grants", async () => {
  const calls = [];
  const h = ownerHarness({status:"authenticated"},async (...args) => {calls.push(args);return authority;});
  assert.deepEqual(await h.authority(first.device_id),authority);
  assert.equal(calls[0][0],"/account/mcp/authority?device_id="+first.device_id);
  await assert.rejects(h.authority("evil-device"),/mcp-owner-device-invalid/);
  await assert.rejects(ownerHarness({status:"authenticated"},async()=>({...authority,device_id:other})).authority(first.device_id),/mcp-owner-authority-invalid/);
  await assert.rejects(ownerHarness({status:"authenticated"},async()=>({...authority,grant_groups:[groupItem,groupItem]})).authority(first.device_id),/mcp-owner-authority-invalid/);
});

test("Revocation is an explicit same-origin POST and rejects unconfirmed outcomes", async () => {
  const input={device_id:first.device_id,client_id:client,grant_group_id:group,confirm:"revogar"};
  let calls=[];
  const h=ownerHarness({status:"authenticated"},async (...args)=>{
    calls.push(args);
    return {ok:true,schema:"ordax.owner-mcp-revocation/1",revoked:true,
      device_id:first.device_id,client_id:client,grant_group_id:group};
  });
  assert.equal((await h.revoke(input)).revoked,true);
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],"/account/mcp/revoke");
  assert.equal(calls[0][2].method,"POST");
  assert.deepEqual(calls[0][2].jsonBody,input);
  await assert.rejects(h.revoke({...input,confirm:"yes"}),/mcp-owner-revoke-invalid/);
  await assert.rejects(ownerHarness({status:"authenticated"},async()=>({ok:true})).revoke(input),/mcp-owner-revoke-unconfirmed/);
  await assert.rejects(ownerHarness({status:"anonymous"},async()=>{throw Error("unexpected");}).revoke(input),/public-account-session-required/);
});

test("Late grant/revocation responses cannot authorize a superseded Account session", async () => {
  let resolve;
  const waiting=new Promise(r=>{resolve=r});
  const h=ownerHarness({status:"authenticated"},()=>waiting);
  const pending=h.authority(first.device_id);
  h.change({status:"authenticated"});
  resolve(authority);
  await assert.rejects(pending,/public-account-session-changed/);
});

test("Revoke UI requires exact group and Owner confirmation; no optimistic removal",()=>{
  const portal=readFileSync(new URL("../site/assets/account-portal.js",import.meta.url),"utf8");
  assert.match(portal,/window\.confirm\(/);
  assert.match(portal,/mcpAuthority\.grant_groups\.some\(/);
  assert.match(portal,/await account\.revokeMcpGrant\(/);
  assert.match(portal,/await account\.readMcpAuthority\(deviceId\)/);
  assert.match(portal,/mcp-owner-revoke-not-reflected/);
  assert.match(source,/method !== "POST" \|\| path !== "\/account\/mcp\/revoke"/);
});

test("denied MCP device selection cannot invalidate an active grant revocation",async()=>{
  // Exercise the actual portal controller, not a duplicate implementation.
  const portal=readFileSync(new URL("../site/assets/account-portal.js",import.meta.url),"utf8");
  const start=portal.indexOf("  async function loadMcpAuthority(deviceId) {");
  const end=portal.indexOf("\n  async function revokeMcpDeviceGrant(control) {",start);
  assert.ok(start>=0 && end>start);
  const realFunction=portal.slice(start,end);
  const run=new Function("deviceId","answer",[
    'let mcpRevoking=true, mcpAuthorityRevision=7, mcpAuthority=null;',
    'let mcpAuthorityDevice=null, mcpAuthorityStatus="unavailable";',
    'let mcpRevocationNotice="", mcpDevicesStatus="ready";',
    'let mcpDevices=[{device_id:deviceId}], calls=0;',
    'const state={section:"dispositivos"};',
    'const signedIn=()=>true, renderContent=()=>{};',
    'const account={readMcpAuthority:async()=>{calls+=1;return answer}};',
    realFunction,
    'return {open:loadMcpAuthority, revision:()=>mcpAuthorityRevision,',
    '  calls:()=>calls, release:()=>{mcpRevoking=false}};',
  ].join("\n"))(first.device_id,authority);
  await run.open(first.device_id);
  assert.equal(run.revision(),7,"stale click must not cancel pending POST");
  assert.equal(run.calls(),0,"stale click cannot query while revoking");
  run.release();
  await run.open(first.device_id);
  assert.equal(run.revision(),8);
  assert.equal(run.calls(),1);
});
