import { test } from "node:test";
import assert from "node:assert/strict";
import { readFileSync, readdirSync, statSync } from "node:fs";
import { fileURLToPath } from "node:url";
import path from "node:path";

const webDir = fileURLToPath(new URL("../../web/", import.meta.url));
const swSource = readFileSync(path.join(webDir, "sw.js"), "utf-8");

// sw.js는 classic worker라 import할 수 없으므로, ASSETS 배열 리터럴을 텍스트에서 뽑아 평가한다.
function parseAssets(source) {
  const match = source.match(/const ASSETS = \[([\s\S]*?)\];/);
  if (!match) throw new Error("sw.js에서 ASSETS 배열을 찾을 수 없다");
  const body = match[1].replace(/\/\/.*$/gm, "");
  return new Function(`return [${body}]`)();
}

function listFiles(dir, base = dir) {
  const out = [];
  for (const name of readdirSync(dir)) {
    const full = path.join(dir, name);
    if (statSync(full).isDirectory()) out.push(...listFiles(full, base));
    else out.push(path.relative(base, full).split(path.sep).join("/"));
  }
  return out;
}

test("web/ 아래 모든 파일(sw.js 제외)이 ASSETS에 있고, ASSETS의 모든 항목이 실재한다", () => {
  const assets = parseAssets(swSource);
  const files = listFiles(webDir).filter((file) => file !== "sw.js");
  const assetSet = new Set(assets.filter((asset) => asset !== "./"));

  for (const file of files) {
    assert.ok(assetSet.has(file), `ASSETS에 없는 파일: ${file}`);
  }
  for (const asset of assetSet) {
    assert.ok(files.includes(asset), `실재하지 않는 ASSETS 항목: ${asset}`);
  }
});

test("predictions.json의 전략은 모두 backtest.json의 전략에 있다 (게임별)", () => {
  const predictions = JSON.parse(
    readFileSync(new URL("../../data/predictions.json", import.meta.url), "utf-8"),
  );
  const backtest = JSON.parse(
    readFileSync(new URL("../../data/backtest.json", import.meta.url), "utf-8"),
  );

  for (const [game, section] of Object.entries(predictions)) {
    if (!section || !Array.isArray(section.sets)) continue; // generatedAt/disclaimer 등 게임이 아닌 키는 건너뛴다
    const strategies = new Set(Object.keys(backtest[game]?.strategies ?? {}));
    for (const entry of section.sets) {
      assert.ok(strategies.has(entry.strategy), `${game}의 "${entry.strategy}" 전략이 backtest.json에 없다`);
    }
  }
});
