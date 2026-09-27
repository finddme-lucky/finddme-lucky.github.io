import { el } from "./dom.mjs";

const SKIPPED = "건너뜀";
const CLEAN = "편향 증거 없음";
const SUSPECT = "편향 의심";

// 건너뛴 검정을 "편향 없음"으로 읽히게 두면 안 된다 — 셋을 확실히 구분한다.
export function verdictOf(entry) {
  if (entry.p === null || entry.p === undefined) return SKIPPED;
  return entry.biased ? SUSPECT : CLEAN;
}

// DOM 없이도 정직성 불변식을 단언할 수 있도록 뺀 순수 함수들.
export const hasSumTest = (fairness) =>
  [...fairness.all, ...fairness.recent].some((entry) => entry.id === "sum");

export const skippedCount = (fairness) =>
  [...fairness.all, ...fairness.recent].filter((entry) => verdictOf(entry) === SKIPPED).length;

export const SUM_FOOTNOTE = "번호 합 검정은 양 끝 구간에 회차가 적어 검정력이 낮다 — 치우침이 있어도 잡아내기 어렵다.";
export const HOLM_SCOPE_NOTE = "Holm 보정은 이 표 안에서만 묶여 있다 — 다른 표의 p값과 나란히 놓고 비교하지 말 것.";

const format = (value) => (value === null || value === undefined ? "—" : value.toFixed(4));

function table(entries, title, note) {
  const rows = entries.map((entry) => {
    const verdict = verdictOf(entry);
    return el("tr", { class: verdict === SUSPECT ? "suspect" : "" },
      el("th", { scope: "row" }, entry.label,
        entry.note ? el("span", { class: "quiet" }, ` (${entry.note})`) : null),
      el("td", {}, entry.n?.toLocaleString("ko-KR") ?? "—"),
      el("td", {}, format(entry.p)),
      el("td", {}, format(entry.pAdj)),
      el("td", {}, verdict));
  });

  return el("section", { class: "panel" },
    el("h3", {}, title),
    note ? el("p", { class: "quiet" }, note) : null,
    el("p", { class: "note" }, HOLM_SCOPE_NOTE),
    el("div", { class: "scroller" },
      el("table", { class: "grid" },
        el("thead", {}, el("tr", {},
          el("th", { scope: "col" }, "검정"),
          el("th", { scope: "col" }, "n"),
          el("th", { scope: "col" }, "p"),
          el("th", { scope: "col" }, "Holm 보정 p"),
          el("th", { scope: "col" }, "판정"))),
        el("tbody", {}, rows))));
}

export function fairnessSection(report) {
  const fairness = report.fairness;
  const skipped = skippedCount(fairness);

  return el("div", {},
    el("h2", {}, "추첨 공정성 검정"),
    el("p", { class: "note" },
      "추첨기에 치우침이 있는지 모아 둔 회차로 직접 검사한 결과다. " +
      "\"편향 증거 없음\"이 정상이며, 그것이 다음 회차를 맞힐 수 있다는 뜻은 아니다."),
    table(fairness.all, "전체 회차", null),
    table(fairness.recent, `최근 ${fairness.recentWindow.toLocaleString("ko-KR")}회`, null),
    skipped > 0
      ? el("p", { class: "notice" },
          `건너뛴 검정이 ${skipped}건 있다 — 자료가 모자라 계산하지 못한 것이며, 치우침이 없다는 뜻이 아니다.`)
      : null,
    // 합 검정이 없는 게임(연금복권)에는 이 각주를 띄우지 않는다.
    hasSumTest(fairness) ? el("p", { class: "note" }, SUM_FOOTNOTE) : null,
    el("p", { class: "note" }, `유의수준 ${fairness.alpha}. 여러 검정을 한꺼번에 하므로 Holm 보정을 적용했다.`));
}
