// Log Pose service worker: keeps the app and card list working offline.
// App files: fetched fresh when online (so updates arrive), saved copy as fallback.
// Card pictures from the official site: kept once loaded.
const CACHE = "lp-v6";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./data/cards.json", "./icon-192.png", "./icon-512.png", "./apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k !== "lp-cards").map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
function withTimeout(p, ms){ return new Promise((res, rej) => { const t = setTimeout(() => rej(new Error("timeout")), ms); p.then(v => { clearTimeout(t); res(v); }, e => { clearTimeout(t); rej(e); }); }); }
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin === location.origin && u.pathname.includes("/img/")) {
    // card pictures: never change, keep forever once loaded
    e.respondWith(caches.open("lp-cards").then(c => c.match(r).then(m => m || fetch(r).then(res => { if (res.ok) c.put(r, res.clone()); return res; }))));
  } else if (u.origin === location.origin) {
    e.respondWith(withTimeout(fetch(r, {cache: "no-cache"}), 5000).then(res => {
      if (res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(r, cp)); }
      return res;
    }).catch(() => caches.match(r, {ignoreSearch: true}).then(m => m || caches.match("./index.html"))));
  } else if (u.hostname === "storage.googleapis.com" && u.pathname.includes("images.pricecharting.com")) {
    // DON!! card pictures: keep once loaded
    e.respondWith(caches.open("lp-cards").then(c => c.match(r.url).then(m => m || fetch(r).then(res => { if (res.ok || res.type === "opaque") c.put(r.url, res.clone()); return res; }))));
  } else if (u.hostname.endsWith("onepiece-cardgame.com")) {
    e.respondWith(caches.open("lp-cards").then(c => c.match(r.url).then(m => m || fetch(r).then(res => { if (res.ok || res.type === "opaque") c.put(r.url, res.clone()); return res; }))));
  } else if (u.hostname === "fonts.googleapis.com" || u.hostname === "fonts.gstatic.com") {
    e.respondWith(caches.match(r).then(m => m || fetch(r).then(res => { const cp = res.clone(); caches.open(CACHE).then(c => c.put(r, cp)); return res; })));
  }
});
