import http from 'node:http';
import {statSync} from 'node:fs';
import {pathToFileURL,fileURLToPath} from 'node:url';
import path from 'node:path';
const root=path.dirname(fileURLToPath(import.meta.url)),file=path.join(root,'dist/server/index.js'),port=Number(process.env.PROSPECTOR_PORT||8892);
const server=http.createServer(async(req,res)=>{
  try{const worker=(await import(pathToFileURL(file).href+'?'+statSync(file).mtimeMs)).default;
    const r=await worker.fetch(new Request('http://127.0.0.1:'+port+req.url,{method:req.method}));res.writeHead(r.status,Object.fromEntries(r.headers));res.end(Buffer.from(await r.arrayBuffer()));}
  catch(e){console.error(e.message);res.writeHead(500);res.end();}
});
server.listen(port,'127.0.0.1',()=>console.log('Prospector: http://127.0.0.1:'+port));
process.on('SIGINT',()=>server.close(()=>process.exit()));process.on('SIGTERM',()=>server.close(()=>process.exit()));
