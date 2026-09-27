import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import { installFakeDom } from "./helpers/fake-dom.mjs";
import { RULE_LABELS, excludedRounds, limitsText, popularitySection, share } from "../../web/js/popularity.mjs";

installFakeDom();

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
  // source.includes(`${rule}:`) 는 텍스트 검색이라 라벨을 빈 문자열로 비워도 통과한다 —
  // 실제로 쓰이는 RULE_LABELS 값 자체를 단언해야 라벨이 비면 테스트가 죽는다.
  for (const rule of Object.keys(backtest.popularity.byRule)) {
    assert.ok((RULE_LABELS[rule] ?? "").length > 0, `이름 없는 규칙: ${rule}`);
  }
});

// I2: 퍼센트에서 횟수를 떼어내는 것 같은 정직성 약화가 조용히 통과하면 안 된다.
test("share()는 비율뿐 아니라 회차/횟수도 문자열에 담는다", () => {
  const text = share(backtest.popularity.high);
  assert.ok(text.includes(String(backtest.popularity.high.rounds)), "회차 수가 빠졌다");
  assert.ok(text.includes(String(backtest.popularity.high.flagged)), "횟수가 빠졌다");
});

test("limitsText()는 제외된 회차 수를 실제 데이터에 맞게 말한다", () => {
  const evidence = backtest.popularity;
  const excluded = excludedRounds(evidence);
  assert.equal(excluded, evidence.rounds - (evidence.high.rounds + evidence.low.rounds));
  const text = limitsText(evidence);
  if (excluded === 0) {
    assert.ok(text.includes("해당 없음") || text.includes("없다"), "제외 0건인데 있었다고 말한다");
  } else {
    assert.ok(text.includes(String(excluded)), "제외된 회차 수가 문장에 없다");
  }
});

// I2: caveat와 LIMITS 문장을 지워도 27/27 green이었다 — 실제로 popularitySection()을 렌더해서 확인한다.
test("인기 화면에는 caveat 배너와 limits 문장이 실제로 나온다", () => {
  const section = popularitySection(backtest);
  assert.ok(section.textContent.includes(backtest.popularity.caveat), "caveat 배너가 빠졌다");
  assert.ok(section.textContent.includes(limitsText(backtest.popularity)), "limits 문장이 빠졌다");
});

test("인기 화면에 byEra 구간별 표와 반전 문장이 들어 있다", () => {
  const section = popularitySection(backtest);
  const text = section.textContent;
  assert.ok(text.includes("뒤집힌다") || text.includes("역전"), "구간 반전을 말하는 문장이 없다");
  for (const era of backtest.popularity.byEra) {
    assert.ok(text.includes(`${era.from}~`), `${era.from} 구간 표가 없다`);
  }
});
