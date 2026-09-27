import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";

const backtest = JSON.parse(
  readFileSync(new URL("../../data/backtest.json", import.meta.url), "utf-8"));

test("인기 규칙 근거가 화면이 쓰는 모양으로 들어 있다", () => {
  const evidence = backtest.popularity;
  assert.ok(evidence, "popularity 구간이 없다");
  assert.ok(typeof evidence.caveat === "string" && evidence.caveat.length > 0, "caveat 문장이 없다");
  for (const key of ["high", "low", "topDecile", "bottomDecile"]) {
    for (const field of ["rounds", "flagged", "flaggedRate"]) {
      assert.ok(field in evidence[key], `${key}.${field} 없음`);
    }
  }
  for (const [rule, rates] of Object.entries(evidence.byRule)) {
    for (const field of ["high", "low", "difference", "highFlagged", "lowFlagged"]) {
      assert.ok(field in rates, `${rule}.${field} 없음`);
    }
  }
});

test("모든 규칙 id에 사람이 읽는 이름이 있다", async () => {
  const source = readFileSync(new URL("../../web/js/popularity.mjs", import.meta.url), "utf-8");
  for (const rule of Object.keys(backtest.popularity.byRule)) {
    assert.ok(source.includes(`${rule}:`), `이름 없는 규칙: ${rule}`);
  }
});
