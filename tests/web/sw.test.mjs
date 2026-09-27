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

function parseList(source, name) {
  const match = source.match(new RegExp(`const ${name} = \\[([\\s\\S]*?)\\];`));
  if (!match) throw new Error(`sw.js에서 ${name} 배열을 찾을 수 없다`);
  return new Function(`return [${match[1].replace(/\/\/.*$/gm, "")}]`)();
}

// 설치할 때 미리 받아 두는 데이터 파일 — 하나라도 이름이 틀리면 "설치 직후 오프라인"에서 데이터가 빈다.
test("DATA_ASSETS의 모든 항목이 data/에 실재한다", () => {
  const dataDir = fileURLToPath(new URL("../../data/", import.meta.url));
  const assets = parseList(swSource, "DATA_ASSETS");
  assert.ok(assets.length >= 3, "미리 받아 둘 데이터 파일이 비어 있다");
  for (const asset of assets) {
    assert.ok(asset.startsWith("data/"), `data/ 밖의 항목: ${asset}`);
    assert.ok(
      statSync(path.join(dataDir, asset.slice("data/".length)), { throwIfNoEntry: false }),
      `실재하지 않는 DATA_ASSETS 항목: ${asset}`,
    );
  }
});

test("web/ 아래 모든 파일(sw.js 제외)이 ASSETS에 있고, ASSETS의 모든 항목이 실재한다", () => {
  const assets = parseAssets(swSource);
  // sw.js 자신과 마찬가지로 vendor/README.md도 페이지가 fetch하는 자원이 아니므로 제외한다
  // (사람이 라이선스·출처를 확인할 때만 읽는 문서다).
  const files = listFiles(webDir).filter((file) => file !== "sw.js" && file !== "vendor/README.md");
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
