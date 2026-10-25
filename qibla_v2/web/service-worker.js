'use strict';
const VERSION='qibla-v2-2026-10-25';
const STATIC_CACHE=VERSION+'-static';
const TILE_CACHE=VERSION+'-tiles';
const STATIC=['/','/index.html','/qibla-engine.js','/manifest.webmanifest','/qibla-icon.svg'];
self.addEventListener('install',event=>event.waitUntil(caches.open(STATIC_CACHE).then(c=>c.addAll(STATIC)).then(()=>self.skipWaiting())));
self.addEventListener('activate',event=>event.waitUntil((async()=>{for(const key of await caches.keys())if(key.startsWith('qibla-v2-')&&key!==STATIC_CACHE&&key!==TILE_CACHE)await caches.delete(key);await self.clients.claim()})()));
self.addEventListener('message',event=>{if(event.data&&event.data.type==='CACHE_MAP_VIEW'&&event.source)event.source.postMessage({type:'MAP_CACHE_NOTE',message:'Map tiles cache as they are viewed. Pan and zoom through an area while online to prepare it for offline use.'})});
self.addEventListener('fetch',event=>{
 const req=event.request;if(req.method!=='GET')return;const url=new URL(req.url);
 if(url.origin===self.location.origin){event.respondWith((async()=>{const cache=await caches.open(STATIC_CACHE),cached=await cache.match(req);if(cached)return cached;try{const response=await fetch(req);if(response.ok&&['document','script','style','manifest'].includes(req.destination))cache.put(req,response.clone());return response}catch(e){if(req.mode==='navigate')return cache.match('/index.html');throw e}})());return}
 const tile=/^https?:$/.test(url.protocol)&&/(^|\.)tile\.openstreetmap\.org$/.test(url.hostname)&&/\/(\d+)\/(\d+)\/(\d+)\.png$/.test(url.pathname);
 const leaflet=/^https?:$/.test(url.protocol)&&/(^|\.)unpkg\.com$/.test(url.hostname)&&url.pathname.includes('/leaflet@1.9.4/');
 if(!tile&&!leaflet)return;
 event.respondWith((async()=>{const cache=await caches.open(tile?TILE_CACHE:STATIC_CACHE),cached=await cache.match(req);if(cached)return cached;try{const response=await fetch(req);if(response.ok||response.type==='opaque'){if(tile){const keys=await cache.keys();if(keys.length>350)await cache.delete(keys[0])}cache.put(req,response.clone())}return response}catch(e){return cached||Response.error()}})())
});