import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { GRID_CELLS, GRID_WIDTH, NUMBERS } from "../../web/js/slip.mjs";

const rules = JSON.parse(
  readFileSync(new URL("../../rules/lotto645-unpopular.json", import.meta.url), "utf-8"));

// 격자가 어긋나면 화면이 보여주는 "용지 패턴"이 규칙이 판정하는 패턴과 달라진다.
test("용지 격자 폭이 인기 규칙의 격자와 같다", () => {
  assert.equal(GRID_WIDTH, rules.gridWidth);
});

test("45개 번호가 모두 들어가고 남는 칸만 비어 있다", () => {
  assert.equal(NUMBERS, 45);
  assert.ok(GRID_CELLS >= NUMBERS);
  assert.equal(GRID_CELLS, GRID_WIDTH * Math.ceil(NUMBERS / GRID_WIDTH));
});
