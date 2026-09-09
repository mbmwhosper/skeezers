const CACHE='skeezers-v3';
const ASSETS=['./','index.html','styles.css','app.js','catalog.json','icon.svg','manifest.webmanifest','third-party.html'];
const CACHEABLE=new Set(ASSETS.map(path=>new URL(path,self.registration.scope).href));
self.addEventListener('install',event=>event.waitUntil(caches.open(CACHE).then(cache=>cache.addAll(ASSETS)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(key=>key!==CACHE).map(key=>caches.delete(key)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',event=>{
  if(event.request.method!=='GET') return;
  event.respondWith(fetch(event.request).then(response=>{
    if(response.ok && CACHEABLE.has(event.request.url)){
      const copy=response.clone();
      caches.open(CACHE).then(cache=>cache.put(event.request,copy));
    }
    return response;
  }).catch(async()=>{
    const cached=await caches.match(event.request);
    if(cached) return cached;
    if(event.request.mode==='navigate' && event.request.destination==='document') return caches.match('index.html');
    return Response.error();
  }));
});
