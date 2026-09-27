import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { installFakeDom } from "./helpers/fake-dom.mjs";
import { GRID_CELLS, GRID_WIDTH, NUMBERS, slipGrid } from "../../web/js/slip.mjs";

installFakeDom();

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

// I6: 위 두 테스트는 상수만 본다 — slipGrid()를 한 번도 호출하지 않아 셀 인덱스 계산이 맞는지는
// 아무것도 고정하지 못한다. 번호 n이 칸 인덱스 n-1에 칠해지는지 직접 단언한다.
test("칸 인덱스가 번호 − 1이다", () => {
  const cells = slipGrid([1, 7, 8, 45]).children;
  const on = cells
    .map((cell, index) => [cell.className, index])
    .filter(([className]) => className.includes("on"))
    .map(([, index]) => index);
  assert.deepEqual(on, [0, 6, 7, 44]);
});
