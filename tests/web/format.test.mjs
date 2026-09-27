import { test } from "node:test";
import assert from "node:assert/strict";
import {
  formatDate, formatDateTime, formatRound, formatCount, formatWon, formatWonShort, formatPercent,
} from "../../web/js/format.mjs";

test("날짜는 한국어 요일까지 붙인다", () => {
  assert.equal(formatDate("2026-09-19"), "2026년 9월 19일 (토)");
  assert.equal(formatDate("2026-09-17"), "2026년 9월 17일 (목)");
});

test("날짜 계산은 기기 시간대에 흔들리지 않는다", () => {
  const tz = process.env.TZ;
  process.env.TZ = "America/Los_Angeles";
  assert.equal(formatDate("2026-09-19"), "2026년 9월 19일 (토)");
  process.env.TZ = tz;
});

test("갱신 시각은 KST로 고정해 보여준다", () => {
  // data/*.json의 generatedAt·updatedAt은 이미 +09:00이지만, 다른 오프셋이 와도 KST로 바꿔 쓴다.
  assert.equal(formatDateTime("2026-09-27T09:05:00+09:00"), "2026-09-27 09:05 KST");
  assert.equal(formatDateTime("2026-09-27T00:05:00+00:00"), "2026-09-27 09:05 KST");
  assert.throws(() => formatDateTime("어제"), /시각/);
});

test("읽을 수 없는 날짜는 던진다", () => {
  assert.throws(() => formatDate("2026-13-99"), /날짜/);
});

test("회차와 사람 수에는 천 단위 구분", () => {
  assert.equal(formatRound(1243), "1,243회");
  assert.equal(formatCount(2729145), "2,729,145명");
});

test("금액은 전체 표기와 짧은 표기 두 가지", () => {
  assert.equal(formatWon(5000), "5,000원");
  assert.equal(formatWonShort(3281029250), "32억 8,102만원");
  assert.equal(formatWonShort(1680000000), "16억 8,000만원");
  assert.equal(formatWonShort(120000000), "1억 2,000만원");
  assert.equal(formatWonShort(1000000), "100만원");
  assert.equal(formatWonShort(5000), "5,000원");
  assert.equal(formatWonShort(0), "0원");
});

test("확률은 소수점 둘째 자리 백분율", () => {
  assert.equal(formatPercent(0.028), "2.80%");
  assert.equal(formatPercent(0.023834), "2.38%");
  assert.equal(formatPercent(0), "0.00%");
});
