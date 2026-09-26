import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { GAMES, STRATEGIES, gameLabel, strategyLabel } from "../../web/js/labels.mjs";

const read = (path) => JSON.parse(readFileSync(new URL(`../../${path}`, import.meta.url), "utf-8"));

test("실제 데이터의 전략 id가 모두 라벨을 갖는다", () => {
  const predictions = read("data/predictions.json");
  const backtest = read("data/backtest.json");
  const ids = new Set();
  for (const game of Object.keys(GAMES)) {
    for (const entry of predictions[game].sets) ids.add(entry.strategy);
    for (const id of Object.keys(backtest[game].strategies)) ids.add(id);
  }
  assert.ok(ids.size >= 5);
  for (const id of ids) assert.ok(id in STRATEGIES, `라벨 없는 전략: ${id}`);
});

test("두 게임 이름이 있다", () => {
  assert.equal(gameLabel("lotto645").name, "로또 6/45");
  assert.equal(gameLabel("pension720").name, "연금복권720+");
});

test("모르는 id는 id를 그대로 보여주고 죽지 않는다", () => {
  assert.equal(strategyLabel("nope").name, "nope");
});
