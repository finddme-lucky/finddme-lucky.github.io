import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { verdictOf } from "../../web/js/fairness.mjs";

const read = (path) => JSON.parse(readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8"));

test("건너뛴 검정을 편향 없음과 구분한다", () => {
  assert.equal(verdictOf({ p: null }), "건너뜀");
  assert.equal(verdictOf({}), "건너뜀");
  assert.equal(verdictOf({ p: 0.5, biased: false }), "편향 증거 없음");
  assert.equal(verdictOf({ p: 0.001, biased: true }), "편향 의심");
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
