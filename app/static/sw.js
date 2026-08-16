const CACHE='vinoth-os-v2';
const ASSETS=['/','/static/style.css','/static/app.js'];
self.addEventListener('install',e=>{self.skipWaiting();e.waitUntil(caches.open(CACHE).then(c=>c.addAll(ASSETS)))});
self.addEventListener('activate',e=>e.waitUntil(self.clients.claim()));
self.addEventListener('fetch',e=>{if(e.request.method==='GET')e.respondWith(fetch(e.request).catch(()=>caches.match(e.request)))});
self.addEventListener('push',e=>{let d={title:'Vinoth OS',body:'Reminder',url:'/'};try{d={...d,...e.data.json()}}catch(_){};e.waitUntil(self.registration.showNotification(d.title,{body:d.body,icon:'/static/icon.svg',badge:'/static/icon.svg',data:{url:d.url}}))});
self.addEventListener('notificationclick',e=>{e.notification.close();const u=e.notification.data?.url||'/';e.waitUntil(clients.matchAll({type:'window',includeUncontrolled:true}).then(cs=>{for(const c of cs){if('focus'in c){c.navigate(u);return c.focus()}}return clients.openWindow(u)}))});
