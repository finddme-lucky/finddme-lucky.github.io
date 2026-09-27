import { test } from "node:test";
import assert from "node:assert/strict";
import { loadJson } from "../../web/js/data.mjs";

const stub = (response) => { globalThis.fetch = async () => response; };

test("서비스워커가 캐시에서 내준 응답에는 fromCache 표시가 붙는다", async () => {
  stub(new Response('{"schema":1}', { headers: { "X-From-Cache": "1" } }));
  const document = await loadJson("data/latest.json");

  assert.equal(document.fromCache, true);
  // 열거되지 않으므로 JSON 비교나 직렬화에 끼어들지 않는다.
  assert.deepEqual(Object.keys(document), ["schema"]);
  assert.equal(JSON.stringify(document), '{"schema":1}');
});

test("망에서 바로 받은 응답에는 표시가 없다", async () => {
  stub(new Response('{"schema":1}'));
  assert.equal((await loadJson("data/latest.json")).fromCache, undefined);
});

test("실패한 응답은 경로와 상태를 담아 던진다", async () => {
  stub(new Response("", { status: 404 }));
  await assert.rejects(() => loadJson("data/nope.json"), /data\/nope\.json 404/);
});
