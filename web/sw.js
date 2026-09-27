const VERSION = "v4";  // 올리면 낡은 셸 캐시가 activate에서 지워진다 (데이터 캐시는 유지)
const SHELL = `shell-${VERSION}`;
const DATA = "data"; // 버전과 분리한다 — 셸 버전을 올려도 마지막으로 받은 데이터는 지우지 않는다.

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
  "js/chart.mjs",
  "js/data.mjs",
  "js/dom.mjs",
  "js/format.mjs",
  "js/home.mjs",
  "js/labels.mjs",
  "js/sets.mjs",
  "js/staleness.mjs",
  "js/stats.mjs",
  "js/stats-lotto.mjs",
  "vendor/chart.umd.js",
];

// 첫 방문은 이 서비스워커가 제어하기 전에 데이터를 받아 가므로, 그 요청은 캐시를 거치지 않는다.
// 설치할 때 한 번 받아 둬야 "설치하자마자 오프라인"에서도 마지막 데이터가 보인다.
const DATA_ASSETS = [
  "data/latest.json",
  "data/predictions.json",
  "data/backtest.json",
  "data/stats/lotto645.json",
  "data/stats/pension720.json",
];

self.addEventListener("install", (event) => {
  event.waitUntil(
    caches.open(SHELL)
      .then((cache) => cache.addAll(ASSETS))
      // 데이터는 받아두면 좋지만 없다고 설치를 실패시키지는 않는다 (셸은 이미 캐시됐다).
      .then(() => caches.open(DATA))
      .then((cache) => Promise.all(DATA_ASSETS.map((path) => cache.add(path).catch(() => {}))))
      .then(() => self.skipWaiting()),
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
    if (response.ok) {
      event.waitUntil(cache.put(request, response.clone()));
      return response;
    }
    const stale = await cache.match(request);
    return stale ? markFromCache(stale) : response;
  } catch (error) {
    const cached = await cache.match(request);
    if (cached) return markFromCache(cached);
    throw error;
  }
}

// 화면이 "지금 보는 건 마지막으로 받은 값"이라고 말할 수 있게 표시를 남긴다.
// navigator.onLine은 DevTools 오프라인이나 서버만 죽은 경우 true로 남아 믿을 수 없다.
async function markFromCache(cached) {
  const headers = new Headers(cached.headers);
  headers.set("X-From-Cache", "1");
  return new Response(await cached.blob(), {
    status: cached.status,
    statusText: cached.statusText,
    headers,
  });
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
