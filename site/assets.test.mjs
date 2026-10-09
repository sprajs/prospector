import test from 'node:test';
import assert from 'node:assert/strict';
import {mkdtempSync,mkdirSync,copyFileSync,readFileSync,writeFileSync,rmSync} from 'node:fs';
import {spawnSync} from 'node:child_process';
import path from 'node:path';
import {fileURLToPath,pathToFileURL} from 'node:url';
import {generateAssets,renderPage,sha256} from './assets.mjs';
const source=path.dirname(fileURLToPath(import.meta.url));
const scratch=path.join(source,'../.work/asset-tests');mkdirSync(scratch,{recursive:true});
function fixture(){const root=mkdtempSync(path.join(scratch,'case-'));for(const file of ['index.template.html','logo.svg','data.json','assets.mjs','build.mjs','abstract.mjs'])copyFileSync(path.join(source,file),path.join(root,file));return root}
test('public assets preserve export bytes, hashes and interface while removing inline data/style/program',()=>{
 const root=fixture();try{
  const generated=generateAssets(root),html=renderPage(generated,'https://example.cloudfront.net');
  assert.deepEqual(Object.keys(generated.manifest.assets),['register','style','app','logo']);
  for(const [name,asset] of Object.entries(generated.manifest.assets)){
   const bytes=readFileSync(path.join(generated.directory,path.basename(asset.key)));
   assert.equal(sha256(bytes),asset.sha256);assert.equal(bytes.length,asset.bytes);
   assert.match(html,new RegExp(asset.sha256));
   if(name==='register')assert.deepEqual(JSON.parse(bytes),JSON.parse(readFileSync(path.join(root,'data.json'))));
  }
  assert.ok(Buffer.byteLength(html)<6000);assert.ok(!html.includes('REGISTER_DATA'));
  assert.ok(!html.includes('<style>'));assert.ok(!html.includes('function prospectDetail'));
  assert.ok(html.includes('inert aria-busy="true"'));assert.ok(html.includes('Retry'));
  const before=generated.manifest.assets;
  const data=generated.data;data.test_public_value='</script><script>alert(1)</script>';
  writeFileSync(path.join(root,'data.json'),JSON.stringify(data));
  const changed=generateAssets(root);
  assert.notEqual(changed.manifest.assets.register.sha256,before.register.sha256);
  for(const key of ['app','style','logo'])assert.equal(changed.manifest.assets[key].sha256,before[key].sha256);
  assert.ok(!renderPage(changed,'https://example.cloudfront.net').includes('alert(1)'));
 }finally{rmSync(root,{recursive:true,force:true})}
});
test('Worker retains registered abstract allowlist; local mode serves only four public assets',async()=>{
 const root=fixture();try{
  const built=spawnSync(process.execPath,[path.join(root,'build.mjs'),'--local-assets'],{encoding:'utf8'});
  assert.equal(built.status,0,built.stderr);
  const worker=(await import(pathToFileURL(path.join(root,'dist/server/index.js')))).default;
  const generated=generateAssets(root);
  for(const a of Object.values(generated.manifest.assets)){
   const response=await worker.fetch(new Request('http://localhost/'+a.key));
   assert.equal(response.status,200);assert.equal(sha256(Buffer.from(await response.arrayBuffer())),a.sha256);
  }
  for(const route of ['/api/abstract?id=arxiv:9999.99999v1','/data.json','/papers/example.pdf','/.work/log'])assert.equal((await worker.fetch(new Request('http://localhost'+route))).status,404);
  assert.equal((await worker.fetch(new Request('http://localhost/api/abstract?id=x',{method:'HEAD'}))).status,405);
  const data=JSON.parse(readFileSync(path.join(root,'data.json')));
  const program=readFileSync(path.join(root,'dist/server/index.js'),'utf8');
  assert.ok(program.includes(JSON.stringify(data.papers.map(({id,title})=>({id,title})))));
  const {manifest}=generateAssets(root);
  writeFileSync(path.join(root,'assets-config.json'),JSON.stringify({origin:'https://example.cloudfront.net'}));
  writeFileSync(path.join(root,'assets-release.json'),JSON.stringify({origin:'https://example.cloudfront.net',manifest}));
  assert.equal(spawnSync(process.execPath,[path.join(root,'build.mjs')]).status,0);
  const production=(await import(pathToFileURL(path.join(root,'dist/server/index.js')).href+'?production')).default;
  assert.equal((await production.fetch(new Request('http://localhost/'+manifest.assets.register.key))).status,404);
  writeFileSync(path.join(root,'data.json'),'{}');
  const stale=spawnSync(process.execPath,[path.join(root,'build.mjs')],{encoding:'utf8'});
  assert.notEqual(stale.status,0);assert.match(stale.stderr,/upload and verify/);
 }finally{rmSync(root,{recursive:true,force:true})}
});
