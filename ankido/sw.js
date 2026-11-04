// Ankidō service worker: keeps the app and its data working offline.
// App files and data: fetched fresh when online (so updates arrive), saved copy as fallback.
// Stroke-order files and fonts: kept once loaded.
const CACHE = "ak-v1";
const SHELL = ["./", "./index.html", "./manifest.webmanifest", "./data/kanji.json", "./data/dict.json", "./icon-192.png", "./apple-touch-icon.png"];
self.addEventListener("install", e => { e.waitUntil(caches.open(CACHE).then(c => c.addAll(SHELL))); self.skipWaiting(); });
self.addEventListener("activate", e => {
  e.waitUntil(caches.keys().then(ks => Promise.all(ks.filter(k => k !== CACHE && k !== "ak-keep").map(k => caches.delete(k)))).then(() => self.clients.claim()));
});
function withTimeout(p, ms) { return new Promise((res, rej) => { const t = setTimeout(() => rej(new Error("timeout")), ms); p.then(v => { clearTimeout(t); res(v); }, e => { clearTimeout(t); rej(e); }); }); }
const keep = r => caches.open("ak-keep").then(c => c.match(r).then(m => m || fetch(r).then(res => { if (res.ok || res.type === "opaque") c.put(r, res.clone()); return res; })));
self.addEventListener("fetch", e => {
  const r = e.request; if (r.method !== "GET") return;
  const u = new URL(r.url);
  if (u.origin === location.origin && u.pathname.includes("/data/strokes/")) e.respondWith(keep(r));
  else if (u.origin === location.origin) {
    const big = u.pathname.endsWith("dict.json");
    e.respondWith(withTimeout(fetch(r, {cache: "no-cache"}), big ? 20000 : 5000).then(res => {
      if (res.ok) { const cp = res.clone(); caches.open(CACHE).then(c => c.put(r, cp)); }
      return res;
    }).catch(() => caches.match(r, {ignoreSearch: true}).then(m => m || caches.match("./index.html"))));
  } else if (u.hostname === "fonts.googleapis.com" || u.hostname === "fonts.gstatic.com") e.respondWith(keep(r));
});
