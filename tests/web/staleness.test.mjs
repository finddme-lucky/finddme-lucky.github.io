import { test } from "node:test";
import assert from "node:assert/strict";
import { STALE_DAYS, daysSince, staleness } from "../../web/js/staleness.mjs";

const at = (iso) => new Date(iso);

test("추첨일로부터 며칠 지났는지 KST 날짜로 센다", () => {
  assert.equal(daysSince("2026-09-19", at("2026-09-19T23:00:00+09:00")), 0);
  assert.equal(daysSince("2026-09-19", at("2026-09-20T00:30:00+09:00")), 1);
  assert.equal(daysSince("2026-09-19", at("2026-09-28T09:00:00+09:00")), 9);
});

test("9일까지는 정상, 넘으면 갱신 지연", () => {
  assert.equal(STALE_DAYS, 9);
  assert.deepEqual(staleness("2026-09-19", at("2026-09-28T09:00:00+09:00")), { days: 9, stale: false });
  assert.deepEqual(staleness("2026-09-19", at("2026-09-29T09:00:00+09:00")), { days: 10, stale: true });
});

test("기기 시간대가 달라도 같은 판정", () => {
  const tz = process.env.TZ;
  process.env.TZ = "America/Los_Angeles";
  assert.equal(staleness("2026-09-19", at("2026-09-29T09:00:00+09:00")).stale, true);
  if (tz === undefined) delete process.env.TZ; else process.env.TZ = tz;  // 원래 없던 값을 "undefined" 문자열로 남기지 않는다
});
