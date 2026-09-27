import { el } from "./dom.mjs";
import { formatPercent } from "./format.mjs";

const LIMITS = "규칙별 차이에는 오차 범위를 붙이지 않았고, 당첨자 수가 0으로 기록된 회차는 계산에서 빠졌다. " +
  "규칙이 통한다는 증명이 아니라, 통하는지 확인하려고 남긴 기록이다.";

const RULE_LABELS = {
  allLow: "6개 전부 31 이하 (생일 편중)",
  consecutive: "연속번호 과다",
  sameLastDigit: "같은 끝자리 과다",
  gridRow: "용지 가로줄",
  gridColumn: "용지 세로줄",
  gridDiagonal: "용지 대각선",
  multiplesOfSeven: "7의 배수 과다",
  arithmetic: "등차수열",
  sameDecade: "같은 번호대 집중",
};

const share = (group) =>
  `${formatPercent(group.flaggedRate)} (${group.rounds.toLocaleString("ko-KR")}회 중 ${group.flagged.toLocaleString("ko-KR")}회)`;

export function popularitySection(backtest) {
  const evidence = backtest?.popularity;
  if (!evidence) return null;

  const rules = Object.entries(evidence.byRule)
    .sort((a, b) => b[1].difference - a[1].difference)
    .map(([rule, rates]) => el("tr", {},
      el("th", { scope: "row" }, RULE_LABELS[rule] ?? rule),
      el("td", {}, `${formatPercent(rates.high)} (${rates.highFlagged}회)`),
      el("td", {}, `${formatPercent(rates.low)} (${rates.lowFlagged}회)`),
      el("td", {}, `${rates.difference >= 0 ? "+" : ""}${formatPercent(rates.difference)}`)));

  return el("div", { class: "fairness" },
    el("h2", {}, "인기 패턴 규칙의 근거"),
    el("p", { class: "note" },
      `5등 당첨자 수를 주변 ${evidence.window}회차 중앙값으로 정규화해, 당첨자가 많았던 회차의 당첨번호가 ` +
      "사람들이 많이 고르는 패턴에 더 자주 걸리는지 비교한 것이다. " +
      "번호 세트는 이 패턴을 피해서 만든다 — 당첨 확률이 아니라, 당첨됐을 때 나눠 갖는 인원을 줄이기 위해서다."),
    el("dl", { class: "facts" },
      el("div", {}, el("dt", {}, "당첨자 많은 회차"), el("dd", {}, share(evidence.high))),
      el("div", {}, el("dt", {}, "당첨자 적은 회차"), el("dd", {}, share(evidence.low))),
      el("div", {}, el("dt", {}, "상위 10%"), el("dd", {}, share(evidence.topDecile))),
      el("div", {}, el("dt", {}, "하위 10%"), el("dd", {}, share(evidence.bottomDecile)))),
    el("div", { class: "scroller" },
      el("table", { class: "grid" },
        el("thead", {}, el("tr", {},
          el("th", { scope: "col" }, "규칙"),
          el("th", { scope: "col" }, "당첨자 많은 회차"),
          el("th", { scope: "col" }, "적은 회차"),
          el("th", { scope: "col" }, "차이"))),
        el("tbody", {}, rules))),
    el("p", { class: "banner" }, evidence.caveat),
    el("p", { class: "note" }, LIMITS));
}
