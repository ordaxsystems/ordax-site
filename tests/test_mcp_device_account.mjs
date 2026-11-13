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
const gateStart = source.indexOf('  function sameOriginPath(value, method = "GET") {');
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
  assert.match(source,/if \(!sameOriginPath\(path, method\)\) throw new Error\("api-path-invalid"\)/);
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
const revokeEnd = source.indexOf("\n    },\n    async readMcpCentralTargets(clientId, signal) {", revokeStart);
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

const centralTargetsStart=source.indexOf("    async readMcpCentralTargets(clientId, signal) {");
const centralTargetsEnd=source.indexOf("\n    },\n    async readMcpCentralSelections(clientId, signal) {",
  centralTargetsStart);
const centralTicketsStart=source.indexOf("    async readMcpCentralSelections(clientId, signal) {");
const centralTicketsEnd=source.indexOf("\n    },\n    async selectMcpCentralDevice(input, signal) {",
  centralTicketsStart);
const centralSelectStart=source.indexOf("    async selectMcpCentralDevice(input, signal) {");
const centralSelectEnd=source.indexOf("\n    },\n    // Reuse Account's authenticated",
  centralSelectStart);
assert.ok(centralTargetsStart>0&&centralTargetsEnd>centralTargetsStart);
assert.ok(centralTicketsStart>0&&centralTicketsEnd>centralTicketsStart);
assert.ok(centralSelectStart>0&&centralSelectEnd>centralSelectStart);
const centralBody=(start,end,head)=>source.slice(start+head.length,end);
function centralHarness(session,fetcher){
  return new Function("loadJson","initial",`let sessionView=initial;
    return {
      targets: async function(clientId,signal) {${centralBody(
        centralTargetsStart,centralTargetsEnd,"    async readMcpCentralTargets(clientId, signal) {")}
      },
      tickets: async function(clientId,signal) {${centralBody(
        centralTicketsStart,centralTicketsEnd,"    async readMcpCentralSelections(clientId, signal) {")}
      },
      select: async function(input,signal) {${centralBody(
        centralSelectStart,centralSelectEnd,"    async selectMcpCentralDevice(input, signal) {")}
      },
      change(next){sessionView=next}
    };`)(fetcher,session);
}
const challenge="99999999-9999-4999-8999-999999999999";
const expiry=new Date(Date.now()+100000).toISOString();
const centralTargets={ok:true,schema:"ordax.owner-central-targets/1",client_id:client,
  eligible_device_count:1,targets:[{device_id:first.device_id,
    reported_online:true,runtime_ready:true}],attested:false,dispatch_authorized:false};
const centralTickets={ok:true,schema:"ordax.owner-central-selections/1",client_id:client,
  count:1,pending_selections:[{challenge_id:challenge,
    created_at:new Date(Date.now()-1000).toISOString(),expires_at:expiry}],
  attested:false,dispatch_authorized:false};
const centralChoice={client_id:client,challenge_id:challenge,
  device_id:first.device_id,confirm:"selecionar"};

test("Account central MCP routes admit only exact client UUID and one POST",async()=>{
  for(const route of ["targets","selections"]){
    const path="/account/mcp/central-"+route+"?client_id="+client;
    assert.equal(sameOriginPath(path),true);
    for(const invalid of ["/account/mcp/central-"+route,
      path+"&client_id="+client,path+"&owner_id="+other,path+"#fragment",
      path.replace(client,"invalid"),path.replace(client,"%32"+client.slice(1))])
      assert.equal(sameOriginPath(invalid),false,invalid);
  }
  assert.equal(sameOriginPath("/account/mcp/central-selections"),false);
  assert.equal(sameOriginPath("/account/mcp/central-selections","GET"),false);
  assert.equal(sameOriginPath("/account/mcp/central-selections","POST"),true);
  assert.equal(sameOriginPath("/account/mcp/central-targets","POST"),false);
  const calls=[];
  const h=centralHarness({status:"authenticated"},async (...args)=>{
    calls.push(args);
    return args[0].includes("central-targets")?centralTargets:
      args[0].includes("?")?centralTickets:
      {ok:true,schema:"ordax.owner-central-device-selection/1",status:"pending",
        client_id:client,device_id:first.device_id,challenge_id:challenge,
        expires_at:expiry,attested:false,dispatch_authorized:false};
  });
  assert.equal((await h.targets(client)).eligible_device_count,1);
  assert.equal((await h.tickets(client)).count,1);
  assert.equal((await h.select(centralChoice)).status,"pending");
  assert.deepEqual(calls.map(c=>c[0]),[
    "/account/mcp/central-targets?client_id="+client,
    "/account/mcp/central-selections?client_id="+client,
    "/account/mcp/central-selections",
  ]);
  assert.equal(calls[2][2].method,"POST");
  assert.deepEqual(calls[2][2].jsonBody,centralChoice);
});

test("Account central results never imply attestation and reject session changes",async()=>{
  for(const invalid of [{...centralTargets,attested:true},
    {...centralTargets,targets:[{...centralTargets.targets[0],runtime_ready:"yes"}]},
    {...centralTargets,client_id:other}]){
    await assert.rejects(centralHarness({status:"authenticated"},async()=>invalid).targets(client));
  }
  for(const invalid of [{...centralTickets,count:2},
    {...centralTickets,pending_selections:[{...centralTickets.pending_selections[0],
      challenge_id:"bad"}]}, {...centralTickets,dispatch_authorized:true}]){
    await assert.rejects(centralHarness({status:"authenticated"},async()=>invalid).tickets(client));
  }
  await assert.rejects(centralHarness({status:"authenticated"},async()=>({
    ok:true,schema:"ordax.owner-central-device-selection/1",status:"bound",
    client_id:client,challenge_id:challenge,device_id:first.device_id,
    expires_at:expiry,attested:true,dispatch_authorized:true,
  })).select(centralChoice));
  await assert.rejects(centralHarness({status:"anonymous"},async()=>{
    throw Error("must not fetch");
  }).select(centralChoice),/session-required/);
  let release;
  const waiting=new Promise(resolve=>{release=resolve});
  const h=centralHarness({status:"authenticated"},()=>waiting);
  const request=h.targets(client);
  h.change({status:"authenticated"});
  release(centralTargets);
  await assert.rejects(request,/session-changed/);
  const portal=readFileSync(new URL("../site/assets/account-portal.js",import.meta.url),"utf8");
  assert.match(portal,/data-mcp-central-select/);
  assert.match(portal,/mcpCentralSelections\?\.count === 1/);
  assert.match(portal,/window\.confirm\(/);
  assert.match(portal,/mcpCentralNotice = "Vínculo solicitado/);
  assert.match(portal,/expires_at belongs only to this pending Owner challenge/);
  assert.match(portal,/conversation -> device binding is persistent in Platform/);
  assert.match(portal,/offline, heartbeat atrasado ou reinício não escolhem outro computador/);
  assert.doesNotMatch(portal,/Selecionar sessão MCP/);
});

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
  assert.match(source,/method !== "POST" \|\| !\[/);
  assert.match(source,/"\/account\/mcp\/revoke", "\/account\/mcp\/central-selections"/);
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
    'let mcpCentralSelecting=false;const resetMcpCentral=()=>{};',
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

test("MCP device presentation never marks offline Runtime as verified or exposes busy controls",()=>{
  // Exercise the real Account renderer; readiness alone never proves online state.
  const portal=readFileSync(new URL("../site/assets/account-portal.js",import.meta.url),"utf8");
  const start=portal.indexOf("  function mcpDeviceRecords() {");
  const end=portal.indexOf("\n  function mcpAuthorityPanel() {",start);
  assert.ok(start>0 && end>start,"real MCP device renderer missing");
  const render=new Function("devices","selecting","revoking",[
    'const mcpDevicesStatus="ready",mcpDevices=devices;',
    'const mcpRevoking=revoking,mcpCentralSelecting=selecting;',
    'const i18n={getLocale:()=>"pt-BR"};',
    'const esc=value=>String(value??""),tx=value=>String(value);',
    'const icon=()=>"",pendingRecords=()=>"",empty=()=>"";',
    'const action=(label,_icon,options)=>"<button"+(options.disabled?" disabled":"")+">"+label+"</button>";',
    portal.slice(start,end),
    "return mcpDeviceRecords();",
  ].join("\n"));
  const target={device_id:first.device_id,name:"Product",
    last_seen_at:"2026-11-12T06:00:00Z",online:false,runtime_ready:true};
  const offline=render([target],false,false);
  assert.match(offline,/Offline/);
  assert.doesNotMatch(offline,/status-tag is-verified/,"offline is not attested");
  assert.match(offline,/<button>Autorizações<\/button>/);
  const online=render([{...target,online:true}],false,false);
  assert.match(online,/status-tag is-verified/);
  assert.match(render([{...target,online:true,runtime_ready:false}],false,false),
    /Runtime não confirmado/);
  assert.doesNotMatch(render([{...target,online:true,runtime_ready:false}],false,false),
    /status-tag is-verified/);
  assert.match(render([target],true,false),/<button disabled>Autorizações<\/button>/);
  assert.match(render([target],false,true),/<button disabled>Autorizações<\/button>/);
  const panel=portal.slice(portal.indexOf("  function mcpAuthorityPanel() {"),
    portal.indexOf("\n  function field(",portal.indexOf("  function mcpAuthorityPanel() {")));
  assert.match(panel,/disabled:mcpRevoking \|\| mcpCentralSelecting, small:true/);
});

test("re-entering devices refreshes Owner data without interrupting a revocation",()=>{
  // Run the actual router with injected navigation/document stubs.
  const portal=readFileSync(new URL("../site/assets/account-portal.js",import.meta.url),"utf8");
  const start=portal.indexOf("  function route({ initial = false } = {}) {");
  const end=portal.indexOf("\n  const dialog = document.getElementById(\"account-dialog\");",start);
  assert.ok(start>0 && end>start,"real Account router missing");
  const realRoute=portal.slice(start,end);
  const harness=new Function("revoking","selecting",[
    'let state={section:"visao-geral"};',
    'const byId=new Map([["visao-geral",{}],["dispositivos",{}]]);',
    'const location={hash:"#dispositivos"};',
    'const window={scrollTo:()=>{}};',
    'const document={getElementById:()=>({focus:()=>{}})};',
    'const dialog={open:false,close:()=>{}};',
    'const closeMore=()=>{},renderNavigation=()=>{},renderContent=()=>{};',
    'let mcpRevoking=revoking,mcpCentralSelecting=selecting,mcpDevicesRevision=3,mcpAuthorityRevision=5;',
    'let mcpDevices=[{device_id:"old"}],mcpDevicesStatus="ready";',
    'let mcpAuthority={grant_groups:[{grant_group_id:"old"}]},mcpAuthorityDevice="old",',
    '    mcpAuthorityStatus="ready",mcpRevocationNotice="old";',
    'const signedIn=()=>true;',
    'let centralResets=0;const resetMcpCentral=()=>{centralResets++};',
    'let loads=0;',
    'async function loadMcpDevices(){loads++;mcpDevicesStatus="loading";}',
    realRoute,
    'return {run:route, setHash:v=>{location.hash=v}, resets:()=>centralResets,',
    '  view:()=>({loads,deviceRev:mcpDevicesRevision,authRev:mcpAuthorityRevision,',
    '  devices:mcpDevices,authority:mcpAuthority,chosen:mcpAuthorityDevice,',
    '  deviceStatus:mcpDevicesStatus,notice:mcpRevocationNotice})};',
  ].join("\n"));

  const normal=harness(false,false);
  normal.run();
  assert.deepEqual(normal.view(),{
    loads:1,deviceRev:4,authRev:6,devices:null,authority:null,
    chosen:null,deviceStatus:"loading",notice:"",
  });
  normal.run();
  assert.equal(normal.view().loads,1,"hash revisit during fetch must not duplicate calls");
  normal.setHash("#visao-geral");normal.run();
  normal.setHash("#dispositivos");normal.run();
  assert.equal(normal.view().loads,2,"new visit refreshes instead of showing stale grants");

  const pending=harness(true,false);
  pending.run();
  assert.equal(pending.view().loads,0,"do not start a new fetch during revoke");
  assert.equal(pending.view().authRev,5,"do not cancel in-flight revocation receipt");
  assert.equal(pending.view().authority.grant_groups[0].grant_group_id,"old");

  // A user may navigate away and back after confirming the Owner choice
  // while the single POST is still in flight. Never invalidate its receipt
  // or permit a fresh selection while the original outcome is uncertain.
  const selecting=harness(false,true);
  selecting.run();
  assert.equal(selecting.view().loads,0,"do not refresh while selecting");
  assert.equal(selecting.view().authRev,5);
  assert.equal(selecting.view().deviceRev,3);
  selecting.setHash("#visao-geral");
  selecting.run();
  selecting.setHash("#dispositivos");
  selecting.run();
  assert.equal(selecting.view().loads,0,"revisit cannot restart inventory during POST");
  assert.equal(selecting.view().authRev,5,"revisit preserves the Owner selection receipt");
  assert.equal(selecting.view().deviceRev,3,"revisit preserves current device scope");
  assert.equal(selecting.view().chosen,"old");
  assert.equal(selecting.resets(),0,"revisit must not cancel the pending selection");
});
