import { loadJson } from "./data.mjs";
import { destroyCharts } from "./chart.mjs";
import { el } from "./dom.mjs";
import { GAMES, gameLabel } from "./labels.mjs";
import { lottoSections } from "./stats-lotto.mjs";

const SECTIONS = {
  lotto645: lottoSections,
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
      body.replaceChildren(...(await SECTIONS[picked](report, backtest)));
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
