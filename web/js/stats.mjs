import { loadJson } from "./data.mjs";
import { destroyCharts } from "./chart.mjs";
import { el } from "./dom.mjs";
import { GAMES, gameLabel } from "./labels.mjs";
import { lottoSections } from "./stats-lotto.mjs";
import { pensionSections } from "./stats-pension.mjs";

const SECTIONS = {
  lotto645: lottoSections,
  pension720: pensionSections,
};

export function renderStats(target, backtest) {
  let game = "lotto645";
  const cache = new Map();
  const body = el("div", { class: "body" });
  const switcher = el("div", { class: "switch" });

  async function paint() {
    for (const button of switcher.querySelectorAll("button")) {
      button.classList.toggle("on", button.dataset.game === game);
    }
    const picked = game;
    destroyCharts();
    body.replaceChildren(el("p", { class: "note" }, "불러오는 중…"));
    try {
      if (!cache.has(picked)) cache.set(picked, await loadJson(`data/stats/${picked}.json`));
      if (picked !== game) return;  // 기다리는 사이에 다른 게임으로 바꿨으면 버린다
      const report = cache.get(picked);
      const sections = await SECTIONS[picked](report, backtest);
      // SECTIONS[picked]는 차트를 여러 개 그리며 그때마다 await 한다 (첫 진입이면 208KB Chart.js
      // 번들 로드까지 기다린다) — 그 사이에 사용자가 다른 게임을 골랐으면 이 렌더는 버린다.
      if (picked !== game) return;
      body.replaceChildren(...sections);
    } catch (error) {
      if (picked !== game) return;
      body.replaceChildren(el("p", { class: "error" },
        `통계를 불러오지 못했습니다 — ${error.message}`));
    }
  }

  for (const id of Object.keys(GAMES)) {
    if (!SECTIONS[id]) continue;
    const button = el("button", { type: "button", "data-game": id }, gameLabel(id).short);
    button.addEventListener("click", () => { game = id; paint(); });
    switcher.append(button);
  }
  target.append(switcher, body);

  // 라이트/다크가 바뀌면 차트 색을 다시 잡아야 한다 (Chart.js는 스스로 따라가지 않는다).
  matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => { paint(); });

  paint();
}
