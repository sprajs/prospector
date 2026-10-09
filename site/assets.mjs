// One public-only asset projection shared by the upload and Worker builds.
import {readFileSync,mkdirSync,writeFileSync,rmSync} from 'node:fs';
import {createHash} from 'node:crypto';
import path from 'node:path';
export const sha256=bytes=>createHash('sha256').update(bytes).digest('hex');
export const integrity=bytes=>'sha384-'+createHash('sha384').update(bytes).digest('base64');
export function generateAssets(root) {
  const template=readFileSync(path.join(root,'index.template.html'),'utf8');
  const data=JSON.parse(readFileSync(path.join(root,'data.json'),'utf8'));
  const css=template.match(/<style>([\s\S]*?)<\/style>/)?.[1];
  const program=template.match(/<script>\n([\s\S]*?)<\/script>/)?.[1];
  if(!css||!program?.includes("const data=JSON.parse(document.getElementById('prospector-data').textContent), $="))throw Error('Unexpected interface template');
  const start=program.replace("const data=JSON.parse(document.getElementById('prospector-data').textContent), $=",'const $=');
  const loader=`
(async()=>{
 try {
  const config=JSON.parse(document.getElementById('prospector-assets').textContent);
  const response=await fetch(config.register.url,{credentials:'same-origin',mode:'cors',signal:AbortSignal.timeout(20000)});
  if(!response.ok)throw Error('Register unavailable');
  const bytes=await response.arrayBuffer();
  const digest=Array.from(new Uint8Array(await crypto.subtle.digest('SHA-256',bytes)),x=>x.toString(16).padStart(2,'0')).join('');
  if(digest!==config.register.sha256)throw Error('Register integrity mismatch');
  if(!document.querySelector('link[rel=stylesheet]').sheet)throw Error('Styles unavailable');
  const data=JSON.parse(new TextDecoder().decode(bytes));
  start(data);
  document.querySelector('.shell').inert=false;
  document.querySelector('.shell').removeAttribute('aria-busy');
  document.getElementById('asset-status').remove();
  clearTimeout(window.prospectorLoadTimer);
  performance.mark('prospector-ready');
  if(new URLSearchParams(location.search).has('performance')){
   const measure=()=>{document.documentElement.dataset.prospectorPerformance=JSON.stringify({ready_ms:performance.getEntriesByName('prospector-ready')[0].startTime,navigation:performance.getEntriesByType('navigation').map(e=>({transfer_bytes:e.transferSize,encoded_bytes:e.encodedBodySize,decoded_bytes:e.decodedBodySize,response_end_ms:e.responseEnd,dom_content_loaded_ms:e.domContentLoadedEventEnd})),assets:performance.getEntriesByType('resource').filter(e=>e.name.includes('/assets/')).map(e=>({url:e.name,duration_ms:e.duration,transfer_bytes:e.transferSize,encoded_bytes:e.encodedBodySize,decoded_bytes:e.decodedBodySize}))})};
   measure();window.addEventListener('load',measure,{once:true});
  }
 }catch{window.prospectorLoadFailed()}
})();`;
  const directory=path.join(root,'.work/public-assets');
  rmSync(directory,{recursive:true,force:true});mkdirSync(directory,{recursive:true});
  const assets={};
  function add(name,extension,content,type) {
    const bytes=Buffer.from(content),hash=sha256(bytes),key=`assets/${name}.${hash}.${extension}`;
    writeFileSync(path.join(directory,path.basename(key)),bytes);
    assets[name]={key,sha256:hash,integrity:integrity(bytes),bytes:bytes.length,content_type:type};
  }
  add('register','json',JSON.stringify(data),'application/json; charset=utf-8');
  add('style','css',css,'text/css; charset=utf-8');
  add('app','js',`'use strict';\nfunction start(data){\n${start}\n}\n${loader}`,'text/javascript; charset=utf-8');
  add('logo','svg',readFileSync(path.join(root,'logo.svg')),'image/svg+xml');
  const manifest={schema:'prospector-public-assets/v1',assets};
  writeFileSync(path.join(root,'.work/assets-manifest.json'),JSON.stringify(manifest,null,2)+'\n');
  return {template,data,manifest,directory};
}
export function renderPage({template,manifest},origin) {
  const url=name=>origin+'/'+manifest.assets[name].key;
  const {style,app,register}=manifest.assets;
  const config=JSON.stringify({register:{url:url('register'),sha256:register.sha256}}).replaceAll('<','\\u003c');
  const status=`<div id="asset-status" role="status" aria-live="polite" style="padding:1rem"><span id="asset-message">Loading register…</span> <button id="asset-retry" hidden>Retry</button></div>`;
  const bootstrap=`<script>
window.prospectorLoadFailed=()=>{clearTimeout(window.prospectorLoadTimer);document.getElementById('asset-message').textContent='The register could not be loaded. Please retry.';document.getElementById('asset-retry').hidden=false};
document.getElementById('asset-retry').onclick=()=>location.reload();
window.prospectorLoadTimer=setTimeout(window.prospectorLoadFailed,25000);
</script>`;
  return template.replace(/<link rel="icon"[^>]*>/,`<link rel="icon" href="${url('logo')}">`).replace(/<style>[\s\S]*?<\/style>/,`<link rel="preconnect" href="${origin}" crossorigin>\n<link rel="preload" as="fetch" href="${url('register')}" crossorigin>\n<link rel="stylesheet" href="${url('style')}" integrity="${style.integrity}" crossorigin="anonymous" onerror="window.prospectorLoadFailed?.()">`)
    .replace('/* LOGO_DATA */',url('logo'))
    .replace('<div class="shell">',status+'<div class="shell" inert aria-busy="true">')
    .replace(/<script id="prospector-data"[\s\S]*?<\/script>/,`<script id="prospector-assets" type="application/json">${config}</script>`)
    .replace(/<script>\n[\s\S]*?<\/script>/,bootstrap+`<script src="${url('app')}" integrity="${app.integrity}" crossorigin="anonymous" defer onerror="window.prospectorLoadFailed()"></script>`);
}
