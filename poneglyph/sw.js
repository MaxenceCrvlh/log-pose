// Poneglyph moved to ../ankido/. This worker clears the old offline copy and removes itself.
self.addEventListener("install", () => self.skipWaiting());
self.addEventListener("activate", e => e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k.startsWith("pg-")).map(k => caches.delete(k)))).then(() => self.registration.unregister())));
