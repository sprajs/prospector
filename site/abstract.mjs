// arXiv descriptive metadata is fetched on demand, never bundled with the site.
export function decodeEntities(value) {
  const named={amp:'&',lt:'<',gt:'>',quot:'"',apos:"'",nbsp:' '};
  return value.replace(/&(#x[\da-f]+|#\d+|amp|lt|gt|quot|apos|nbsp);/gi,(whole,key)=>{
    if(!key.startsWith('#'))return named[key.toLowerCase()]||whole;
    const n=key[1].toLowerCase()==='x'?parseInt(key.slice(2),16):parseInt(key.slice(1),10);
    return n>0&&n<=0x10ffff&&!(n>=0xd800&&n<=0xdfff)?String.fromCodePoint(n):whole;
  });
}
export function metadataFromPage(html,paper) {
  const title=decodeEntities(html.match(/<title\b[^>]*>([\s\S]*?)<\/title\s*>/i)?.[1]||'');
  const version=paper.id.replace(/^arxiv:/,'');
  if(!title.startsWith(`[${version}]`))throw new Error('Source version mismatch');
  const values={};
  for(const tag of html.match(/<meta\b[^>]*>/gi)||[]) {
    const attrs={};
    for(const m of tag.matchAll(/([\w:-]+)\s*=\s*(?:"([^"]*)"|'([^']*)')/g))attrs[m[1].toLowerCase()]=decodeEntities(m[2]??m[3]);
    if(attrs.name)values[attrs.name]=attrs.content;
  }
  const normalize=s=>s.normalize('NFKC').toLowerCase().replace(/[^\p{L}\p{N}]/gu,'');
  if(!values.citation_title||normalize(values.citation_title)!==normalize(paper.title))throw new Error('Source title mismatch');
  const abstract=values.citation_abstract?.trim();
  if(!abstract||abstract.length>32000)throw new Error('Missing or oversized abstract');
  return {id:paper.id,abstract};
}
export async function readBounded(response,limit=262144) {
  const reader=response.body?.getReader();if(!reader)throw new Error('Missing response body');
  const chunks=[];let size=0;
  try{while(true){const {value,done}=await reader.read();if(done)break;size+=value.byteLength;if(size>limit)throw new Error('Response too large');chunks.push(value)}}
  catch(e){await reader.cancel().catch(()=>{});throw e}
  const bytes=new Uint8Array(size);let offset=0;for(const c of chunks){bytes.set(c,offset);offset+=c.byteLength}return new TextDecoder().decode(bytes);
}
export function abstractService(papers,{fetchPage=fetch,now=Date.now,wait=ms=>new Promise(r=>setTimeout(r,ms))}={}) {
  const admitted=new Map(papers.map(p=>[p.id,p])),cache=new Map(),pending=new Map();
  let tail=Promise.resolve(),nextAt=0,stoppedUntil=0;
  const json=(value,status=200,headers={})=>Response.json(value,{status,headers});
  async function acquire(paper) {
    await wait(Math.max(0,nextAt-now()));
    if(now()<stoppedUntil)return json({error:'unavailable'},503,{'Retry-After':'60'});
    const signal=AbortSignal.timeout(20000),url='https://export.arxiv.org/abs/'+paper.id.replace(/^arxiv:/,'');
    let response;
    try{
      response=await fetchPage(url,{redirect:'manual',signal,headers:{'User-Agent':'Prospector/1.0 (https://github.com/sprajs/prospector)','Accept':'text/html'},cf:{cacheTtl:86400,cacheEverything:true}});
      if(response.status===429){const raw=response.headers.get('Retry-After'),seconds=Number(raw),date=Date.parse(raw||'');const until=Number.isFinite(seconds)&&seconds>0?now()+seconds*1000:Number.isFinite(date)?date:now()+60000;stoppedUntil=Math.max(now()+60000,until);return json({error:'unavailable'},503,{'Retry-After':String(Math.ceil((stoppedUntil-now())/1000))})}
      if(!response.ok||!response.headers.get('content-type')?.includes('text/html'))throw new Error('Source unavailable');
      const body=await readBounded(response),value=metadataFromPage(body,paper);cache.set(paper.id,{value,expires:now()+86400000});
      return json(value,200,{'Cache-Control':'public, max-age=86400'});
    }catch{return json({error:'unavailable'},503,{'Retry-After':'60'})}
    finally{await response?.body?.cancel().catch(()=>{});nextAt=now()+3100}
  }
  return async id=>{
    if(!admitted.has(id))return json({error:'not_found'},404);
    const hit=cache.get(id);if(hit&&hit.expires>now())return json(hit.value,200,{'Cache-Control':'public, max-age=86400'});
    if(pending.has(id))return (await pending.get(id)).clone();
    if(pending.size>=3||now()<stoppedUntil)return json({error:'unavailable'},503,{'Retry-After':'60'});
    const job=tail.catch(()=>{}).then(()=>acquire(admitted.get(id)));tail=job;
    pending.set(id,job);
    try{return (await job).clone()}finally{pending.delete(id)}
  };
}
