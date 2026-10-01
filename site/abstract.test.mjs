import {test} from 'node:test';
import assert from 'node:assert/strict';
import {abstractService,metadataFromPage,readBounded} from './abstract.mjs';
const p={id:'arxiv:1811.04083v2',title:'Early Dark Energy & Cosmology'};
const page=(id=p.id.slice(6),title='Early Dark Energy &amp; Cosmology',abstract='An &quot;early&quot; component &lt; rho. &#945;')=>`<title>[${id}] ${title}</title><meta name="citation_title" content="${title}"><meta name="citation_abstract" content="${abstract}">`;
const response=()=>new Response(page(),{headers:{'Content-Type':'text/html; charset=utf-8'}});
test('extracts metadata and decodes entities as plain text',()=>assert.deepEqual(metadataFromPage(page(),p),{id:p.id,abstract:'An "early" component < rho. α'}));
test('rejects changed version, wrong title and absent abstract',()=>{
 for(const html of [page('1811.04083v3'),page(undefined,'Unrelated'),page(undefined,undefined,'')])assert.throws(()=>metadataFromPage(html,p));
});
test('rejects oversized response while streaming',async()=>{
 await assert.rejects(readBounded(new Response('x'.repeat(100)),20),/too large/);
});
test('only admitted pinned IDs can cause network requests',async()=>{
 let calls=0;const service=abstractService([p],{fetchPage:async()=>{calls++;return response()},wait:async()=>{}});
 for(const id of ['arxiv:1811.04083','arxiv:1811.04083v9','https://localhost/','../../env',null])assert.equal((await service(id)).status,404);
 assert.equal(calls,0);
});
test('coalesces concurrent requests and caches a successful abstract',async()=>{
 let calls=0,clock=0;const service=abstractService([p],{fetchPage:async(url,options)=>{calls++;assert.equal(url,'https://export.arxiv.org/abs/1811.04083v2');assert.equal(options.redirect,'manual');return response()},now:()=>clock,wait:async ms=>{clock+=ms}});
 const results=await Promise.all([service(p.id),service(p.id),service(p.id)]);assert.equal(calls,1);
 for(const r of results)assert.equal((await r.json()).abstract,'An "early" component < rho. α');
 await service(p.id);assert.equal(calls,1);clock+=86400001;await service(p.id);assert.equal(calls,2);
});
test('serializes upstream requests and spaces completions by three seconds',async()=>{
 let clock=0,active=0,maximum=0;const starts=[];
 const all=[p,{...p,id:'arxiv:1910.10739v5'}];const service=abstractService(all,{now:()=>clock,wait:async ms=>{clock+=ms},fetchPage:async url=>{starts.push(clock);active++;maximum=Math.max(maximum,active);await Promise.resolve();active--;return new Response(page(url.split('/').at(-1)),{headers:{'Content-Type':'text/html'}})}});
 await Promise.all(all.map(x=>service(x.id)));assert.equal(maximum,1);assert.ok(starts[1]-starts[0]>=3100);
});
test('rate limit stops pending requests without an automatic retry',async()=>{
 let calls=0,clock=0;const all=[p,{...p,id:'arxiv:1910.10739v5'}];const service=abstractService(all,{now:()=>clock,wait:async ms=>{clock+=ms},fetchPage:async()=>{calls++;return new Response('',{status:429,headers:{'Retry-After':'120'}})}});
 const rs=await Promise.all(all.map(x=>service(x.id)));assert.ok(rs.every(r=>r.status===503));assert.equal(calls,1);assert.equal((await service(p.id)).status,503);assert.equal(calls,1);
});
test('wrong source metadata is unavailable and never cached',async()=>{
 let calls=0;const service=abstractService([p],{wait:async()=>{},fetchPage:async()=>{calls++;return new Response(page('1811.04083v3'),{headers:{'Content-Type':'text/html'}})}});
 assert.equal((await service(p.id)).status,503);assert.equal((await service(p.id)).status,503);assert.equal(calls,2);
});
