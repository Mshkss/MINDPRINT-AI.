import { NextRequest } from 'next/server';
export const dynamic='force-dynamic';
async function proxy(request:NextRequest,{params}:{params:Promise<{path:string[]}>}) {
  const {path}=await params;
  const url=(process.env.BACKEND_URL||'http://127.0.0.1:8000')+'/api/'+path.map(encodeURIComponent).join('/')+request.nextUrl.search;
  const headers=new Headers();
  for(const name of ['content-type','cookie','origin','sec-fetch-site']) { const value=request.headers.get(name); if(value) headers.set(name,value); }
  try {
    const upstream=await fetch(url,{method:request.method,headers,body:['GET','HEAD'].includes(request.method)?undefined:await request.arrayBuffer(),cache:'no-store',signal:AbortSignal.timeout(45000)});
    const out=new Headers({'Content-Type':'application/json','Cache-Control':'no-store'});
    for(const cookie of upstream.headers.getSetCookie()) out.append('Set-Cookie',cookie);
    return new Response(upstream.body,{status:upstream.status,headers:out});
  } catch { return Response.json({detail:'Не удалось связаться с сервером. Проверьте подключение.'},{status:503}); }
}
export {proxy as GET,proxy as POST,proxy as PUT,proxy as DELETE};
