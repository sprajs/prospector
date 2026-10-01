import {readFileSync,mkdirSync,writeFileSync} from 'node:fs';
import {fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url));
const data=JSON.parse(readFileSync(path.join(root,'data.json'),'utf8'));
const escaped=JSON.stringify(data).replaceAll('<','\\u003c').replaceAll('>','\\u003e').replaceAll('&','\\u0026');
const html=readFileSync(path.join(root,'index.template.html'),'utf8').replace('/* REGISTER_DATA */ null',escaped).replace('/* LOGO_DATA */','data:image/svg+xml;base64,'+readFileSync(path.join(root,'logo.svg')).toString('base64'));
const abstract=readFileSync(path.join(root,'abstract.mjs'),'utf8').replace(/^export /gm,'');
const dist=path.join(root,'dist/server');mkdirSync(dist,{recursive:true});
writeFileSync(path.join(dist,'index.js'),abstract+`\nconst page=${JSON.stringify(html)};\nconst abstracts=abstractService(${JSON.stringify(data.papers)});\nexport default {async fetch(request){
 const url=new URL(request.url);
 if(request.method!=='GET'&&request.method!=='HEAD')return new Response(null,{status:405,headers:{Allow:'GET, HEAD'}});
 if(url.pathname==='/api/abstract'){
   if(request.method==='HEAD')return new Response(null,{status:405,headers:{Allow:'GET'}});
   return abstracts(url.searchParams.get('id'));
 }
 if(!['/','/index.html','/map.html'].includes(url.pathname))return new Response(null,{status:404});
 return new Response(request.method==='HEAD'?null:page,{headers:{'Content-Type':'text/html; charset=utf-8','Cache-Control':'no-cache','X-Content-Type-Options':'nosniff','Referrer-Policy':'strict-origin-when-cross-origin'}});
}};\n`);
console.log('Built '+path.join(dist,'index.js'));
