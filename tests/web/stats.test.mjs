import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { statsHeaderNote as lottoHeaderNote } from "../../web/js/stats-lotto.mjs";
import { statsHeaderNote as pensionHeaderNote } from "../../web/js/stats-pension.mjs";

const read = (path) => JSON.parse(readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8"));

test("로또 통계 JSON에 화면이 쓰는 항목이 모두 있다", () => {
  const report = read("data/stats/lotto645.json");
  const stats = report.stats;
  for (const key of ["draws", "recentCountsWindow", "counts", "countsWithBonus", "recentCounts",
                     "gaps", "oddEven", "lowHigh", "sums", "decades", "series"]) {
    assert.ok(key in stats, `없는 항목: ${key}`);
  }
  assert.equal(Object.keys(stats.counts).length, 45);
  assert.equal(Object.keys(stats.gaps).length, 45);
  assert.ok(typeof report.disclaimer === "string" && report.disclaimer.length > 0);
  for (const row of stats.series.slice(-3)) {
    for (const key of ["round", "date", "sales", "firstWinners", "firstPrize"]) {
      assert.ok(key in row, `series에 없는 항목: ${key}`);
    }
  }
});

test("기대값을 겹쳐 그리는 검정에는 buckets·observed·expected가 길이가 맞게 들어 있다", () => {
  const report = read("data/stats/lotto645.json");
  for (const id of ["oddEven", "lowHigh", "adjacent", "overlap"]) {
    const entry = report.fairness.all.find((row) => row.id === id);
    assert.ok(entry, `없는 검정: ${id}`);
    assert.equal(entry.observed.length, entry.buckets.length, id);
    assert.equal(entry.expected.length, entry.buckets.length, id);
  }
});

// I2: report.disclaimer가 헤더 문구에서 빠지는 변경(§1.2 "과거 분포일 뿐" 고지)이 조용히 통과했다 —
// 헤더 문구를 순수 함수로 빼서 직접 단언한다.
test("두 게임의 통계 헤더 문구에 disclaimer가 그대로 들어간다", () => {
  const lotto = read("data/stats/lotto645.json");
  const pension = read("data/stats/pension720.json");
  assert.ok(lottoHeaderNote(lotto).includes(lotto.disclaimer), "로또 헤더에 disclaimer가 없다");
  assert.ok(pensionHeaderNote(pension).includes(pension.disclaimer), "연금복권 헤더에 disclaimer가 없다");
});

test("연금복권 통계 JSON에 화면이 쓰는 항목이 모두 있다", () => {
  const report = read("data/stats/pension720.json");
  const stats = report.stats;
  for (const key of ["draws", "recentCountsWindow", "groups", "recentGroups",
                     "firstDigits", "bonusDigits", "series"]) {
    assert.ok(key in stats, `없는 항목: ${key}`);
  }
  assert.equal(Object.keys(stats.groups).length, 5);
  assert.equal(stats.firstDigits.length, 6);
  assert.equal(stats.bonusDigits.length, 6);
  for (const position of stats.firstDigits) {
    assert.equal(Object.keys(position).length, 10);
  }
  const last = stats.series.at(-1);
  assert.ok(last.rankTotals && "1" in last.rankTotals && "bonus" in last.rankTotals);
});
