import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
import {generateAssets,renderPage} from './assets.mjs';
const root=path.dirname(fileURLToPath(import.meta.url));
const generated=generateAssets(root),{data,manifest}=generated;
if(process.argv.includes('--assets-only')){console.log('Generated '+Object.keys(manifest.assets).length+' public assets');process.exit(0)}
const local=process.argv.includes('--local-assets');
let origin='';
if(!local){
 const config=JSON.parse(readFileSync(path.join(root,'assets-config.json'),'utf8'));
 origin=config.origin;
 if(!/^https:\/\/[a-z0-9-]+\.cloudfront\.net$/.test(origin))throw Error('Expected an HTTPS CloudFront origin');
 const release=JSON.parse(readFileSync(path.join(root,'assets-release.json'),'utf8'));
 if(release.origin!==origin||JSON.stringify(release.manifest)!==JSON.stringify(manifest))throw Error('Public assets changed: upload and verify them before building the Site');
}
const html=renderPage(generated,origin);
const abstract=readFileSync(path.join(root,'abstract.mjs'),'utf8').replace(/^export /gm,'');
const dist=path.join(root,'dist/server');mkdirSync(dist,{recursive:true});
const localAssets=local?Object.fromEntries(Object.values(manifest.assets).map(a=>['/'+a.key,{body:readFileSync(path.join(generated.directory,path.basename(a.key))).toString('base64'),type:a.content_type}])):{};
writeFileSync(path.join(root,'.work/index.html'),html);
writeFileSync(path.join(dist,'index.js'),abstract+`\nconst page=${JSON.stringify(html)};\nconst assets=${JSON.stringify(localAssets)};\nconst abstracts=abstractService(${JSON.stringify(data.papers.map(({id,title})=>({id,title})))});\nexport default {async fetch(request){
 const url=new URL(request.url);
 if(request.method!=='GET'&&request.method!=='HEAD')return new Response(null,{status:405,headers:{Allow:'GET, HEAD'}});
 if(url.pathname==='/api/abstract'){
   if(request.method==='HEAD')return new Response(null,{status:405,headers:{Allow:'GET'}});
   return abstracts(url.searchParams.get('id'));
 }
 if(assets[url.pathname]){const a=assets[url.pathname];return new Response(request.method==='HEAD'?null:Uint8Array.from(atob(a.body),c=>c.charCodeAt(0)),{headers:{'Content-Type':a.type,'Cache-Control':'public, max-age=31536000, immutable','X-Content-Type-Options':'nosniff'}})}
 if(!['/','/index.html','/map.html'].includes(url.pathname))return new Response(null,{status:404});
 return new Response(request.method==='HEAD'?null:page,{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Referrer-Policy':'strict-origin-when-cross-origin'}});
}};\n`);
console.log('Built '+path.join(dist,'index.js')+'; HTML '+Buffer.byteLength(html)+' bytes');
