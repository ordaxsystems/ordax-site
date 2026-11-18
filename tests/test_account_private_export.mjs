import test from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const src=readFileSync(new URL("../site/assets/site.js",import.meta.url),"utf8");
const portal=readFileSync(new URL("../site/assets/account-portal.js",import.meta.url),"utf8");
const start=src.indexOf("    async readPrivateDataExport(signal) {");
const end=src.indexOf("\n    },\n    // Read-only account data",start);
assert.ok(start>0&&end>start,"canonical data-export port is required");
const body=src.slice(start+"    async readPrivateDataExport(signal) {".length,end);
function harness(session,transport){
  return new Function("loadJson","initial",
    "let sessionView=initial;return {read:async function(signal){"+body+"},"+
    "change(next){sessionView=next;}};")(transport,session);
}
const subject="8bce09bf-963b-4ccb-8f67-e1b02e44a873";
const archive={
  $schema:"prototype-ordax.account-export/1",
  subject,exported_at:"2026-11-18T09:00:00.000Z",
  account:{user_id:subject,display_name:"A",created_at:"2026-11-18T09:00:00Z",updated_at:"2026-11-18T09:00:00Z"},
  spaces:[],memberships:[],space_profile_packs:[],entitlements:[],
  projects:[],devices:[],project_connections:[],memory_items:[],sync_objects:[],
};
test("only activated authenticated session may request a sensitive export",async()=>{
  let called=0;
  for(const session of [
    {status:"anonymous",dataExportEnabled:true},
    {status:"authenticated",dataExportEnabled:false},
    {status:"checking",dataExportEnabled:false},
  ]){
    await assert.rejects(harness(session,async()=>{called++;return archive;}).read(),/account-export-not-authorized/);
  }
  assert.equal(called,0);
});
test("reads only exact owner endpoint with bounded no-store JSON transport",async()=>{
  const calls=[];
  const h=harness({status:"authenticated",dataExportEnabled:true},async (...args)=>{
    calls.push(args);return archive;
  });
  assert.deepEqual(await h.read(),archive);
  assert.equal(calls.length,1);
  assert.equal(calls[0][0],"/account/export");
  assert.deepEqual(calls[0][2],{maxBytes:4194304});
});
test("untrusted export contract and foreign account identifiers fail closed",async()=>{
  for(const forged of [
    {...archive,$schema:"unknown"},{...archive,subject:"not-a-subject"},
    {...archive,account:{user_id:"33f58c01-65f2-4e2f-b3cd-179b76a5469b"}},
    {...archive,spaces:"fake"}, {...archive,memory_items:null},
    {...archive,exported_at:"not-a-date"},
    {...archive,providerToken:"sensitive"},
  ]){
    await assert.rejects(harness({status:"authenticated",dataExportEnabled:true},
      async()=>forged).read(),/account-export-contract-invalid/);
  }
});
test("superseded session cannot receive an in-flight private archive",async()=>{
  let resolve;
  const waiting=new Promise(r=>resolve=r);
  const h=harness({status:"authenticated",dataExportEnabled:true},()=>waiting);
  const pending=h.read();
  h.change({status:"authenticated",dataExportEnabled:true});
  resolve(archive);
  await assert.rejects(pending,/public-account-session-changed/);
});
test("privacy interface only offers an explicit action and never auto-fetches",()=>{
  assert.match(portal,/if \(!signedIn\(\) \|\| session\.dataExportEnabled !== true \|\| accountExportBusy\) return/);
  assert.match(portal,/account\.readPrivateDataExport\(\)/);
  assert.match(portal,/control\.matches\("\[data-account-export\]"\)/);
  assert.match(portal,/new Blob\(\[serialized\], \{ type: "application\/json;charset=utf-8" \}\)/);
  assert.match(portal,/URL\.revokeObjectURL/);
  assert.doesNotMatch(portal,/localStorage\.setItem\([^)]*export/);
});
