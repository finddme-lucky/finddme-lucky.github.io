const VERSION = "v1";
const SHELL = `shell-${VERSION}`;
const DATA = `data-${VERSION}`;

// 셸 파일이 늘어나면 여기에 추가한다 (내용만 바뀔 때는 손댈 필요 없다).
const ASSETS = [
  "./",
  "index.html",
  "app.css",
  "manifest.webmanifest",
  "icons/icon-192.png",
  "icons/icon-512.png",
  "js/app.mjs",
  "js/balls.mjs",
  "js/data.mjs",
  "js/dom.mjs",
  "js/format.mjs",
  "js/home.mjs",
  "js/labels.mjs",
  "js/sets.mjs",
  "js/staleness.mjs",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL).then((cache) => cache.addAll(ASSETS)).then(() => self.skipWaiting()),
  );
});

self.addEventListener("activate", (event) => {
  event.waitUntil(
    caches.keys()
      .then((names) => Promise.all(
        names.filter((name) => name !== SHELL && name !== DATA).map((name) => caches.delete(name)),
      ))
      .then(() => self.clients.claim()),
  );
});

self.addEventListener("fetch", (event) => {
  const { request } = event;
  if (request.method !== "GET") return;
  const url = new URL(request.url);
  if (url.origin !== location.origin) return;
  event.respondWith(
    url.pathname.includes("/data/") ? dataFirst(event, request) : shellFirst(event, request),
  );
});

// 데이터는 항상 새 것을 먼저 시도하고, 못 받으면 마지막으로 받은 것을 쓴다.
async function dataFirst(event, request) {
  const cache = await caches.open(DATA);
  try {
    const response = await fetch(request);
    if (response.ok) event.waitUntil(cache.put(request, response.clone()));
    return response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return cached;
    throw error;
  }
}

// 셸은 캐시로 즉시 띄우고 뒤에서 새 버전을 받아 둔다 (다음에 열 때 반영).
async function shellFirst(event, request) {
  const cache = await caches.open(SHELL);
  const cached = await cache.match(request);
  const fresh = fetch(request)
    .then((response) => {
      if (response.ok) return cache.put(request, response.clone()).then(() => response);
      return response;
    })
    .catch(() => null);
  if (cached) {
    event.waitUntil(fresh);
    return cached;
  }
  const response = await fresh;
  return response ?? Response.error();
}
