import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { installFakeDom } from "./helpers/fake-dom.mjs";
import { verdictOf, hasSumTest, skippedCount, fairnessSection, SUM_FOOTNOTE, HOLM_SCOPE_NOTE } from "../../web/js/fairness.mjs";

installFakeDom();

const read = (path) => JSON.parse(readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8"));

test("건너뛴 검정을 편향 없음과 구분한다", () => {
  assert.equal(verdictOf({ p: null }), "건너뜀");
  assert.equal(verdictOf({}), "건너뜀");
  assert.equal(verdictOf({ p: 0.5, biased: false }), "편향 증거 없음");
  assert.equal(verdictOf({ p: 0.001, biased: true }), "편향 의심");
});

test("hasSumTest는 합 검정이 있는 로또와 없는 연금복권을 구분한다", () => {
  const lotto = read("data/stats/lotto645.json").fairness;
  const pension = read("data/stats/pension720.json").fairness;
  assert.equal(hasSumTest(lotto), true);
  assert.equal(hasSumTest(pension), false);
});

test("skippedCount는 건너뛴 검정 수를 센다 (현재 자료는 0건)", () => {
  const lotto = read("data/stats/lotto645.json").fairness;
  assert.equal(skippedCount(lotto), 0);
  assert.equal(
    skippedCount({ all: [{ p: null }, { p: 0.5, biased: false }], recent: [{ p: null }] }),
    2,
  );
});

// I2: 표별 Holm 경고를 지우거나, 합 각주를 두 게임 모두에 다시 보여주는 회귀(1a6b3ff에서 이미 한 번 고친
// 결함)가 조용히 통과했던 것이 리뷰의 지적이다 — 실제로 fairnessSection()을 렌더해 문구를 확인한다.
test("전체·최근 두 표 모두에 Holm 범위 경고가 붙는다", () => {
  const report = read("data/stats/lotto645.json");
  const section = fairnessSection(report);
  const occurrences = section.textContent.split(HOLM_SCOPE_NOTE).length - 1;
  assert.equal(occurrences, 2, "표 두 개 모두에 Holm 경고가 있어야 한다");
});

test("합 각주는 합 검정이 있는 게임에만 나온다", () => {
  const lotto = fairnessSection(read("data/stats/lotto645.json"));
  const pension = fairnessSection(read("data/stats/pension720.json"));
  assert.ok(lotto.textContent.includes(SUM_FOOTNOTE), "로또 화면에 합 각주가 없다");
  assert.ok(!pension.textContent.includes(SUM_FOOTNOTE), "연금복권 화면에 합 각주가 나오면 안 된다");
});

test("실제 데이터의 모든 검정 항목이 표가 쓰는 필드를 갖는다", () => {
  for (const game of ["lotto645", "pension720"]) {
    const fairness = read(`data/stats/${game}.json`).fairness;
    assert.ok(typeof fairness.alpha === "number");
    assert.ok(typeof fairness.recentWindow === "number");
    for (const period of ["all", "recent"]) {
      assert.ok(fairness[period].length > 0, `${game} ${period}`);
      for (const entry of fairness[period]) {
        for (const key of ["id", "label", "biased"]) {
          assert.ok(key in entry, `${game} ${period} ${entry.id}: ${key} 없음`);
        }
        assert.ok("p" in entry && "pAdj" in entry);
      }
    }
  }
});
