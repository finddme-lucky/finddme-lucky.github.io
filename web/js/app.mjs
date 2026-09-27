import { loadJson } from "./data.mjs";
import { el } from "./dom.mjs";
import { renderHome } from "./home.mjs";
import { renderSets } from "./sets.mjs";

// 이 줄까지 왔다는 것은 모듈 그래프가 정상적으로 로드됐다는 뜻이다 — 정적 대체 문구를 지운다.
document.getElementById("boot")?.remove();

const TABS = {
  home: { sources: ["data/latest.json"], render: renderHome },
  sets: { sources: ["data/predictions.json", "data/backtest.json", "data/latest.json"], render: renderSets },
};
const DEFAULT_TAB = "home";
const drawn = new Set();

const currentTab = () => {
  const name = location.hash.replace(/^#/, "");
  return name in TABS ? name : DEFAULT_TAB;
};

async function show(name) {
  for (const id of Object.keys(TABS)) {
    document.getElementById(`tab-${id}`).hidden = id !== name;
  }
  for (const link of document.querySelectorAll(".tabbar a")) {
    link.classList.toggle("on", link.dataset.tab === name);
  }
  if (drawn.has(name)) return;

  const target = document.getElementById(`tab-${name}`);
  target.replaceChildren(el("p", { class: "note" }, "불러오는 중…"));
  try {
    const documents = await Promise.all(TABS[name].sources.map(loadJson));
    target.replaceChildren();
    TABS[name].render(target, ...documents);
    drawn.add(name);
  } catch (error) {
    target.replaceChildren(el("p", { class: "error" },
      `데이터를 불러오지 못했습니다 — ${error.message}`));
  }
}

addEventListener("hashchange", () => show(currentTab()));
show(currentTab());

if ("serviceWorker" in navigator) {
  addEventListener("load", () => {
    navigator.serviceWorker.register("sw.js").catch((error) => {
      console.warn("서비스워커 등록 실패", error);
    });
  });
}
