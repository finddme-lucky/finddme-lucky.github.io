import { barConfig, bucketLabel, chartBlock, drawChart, guardCard, lineConfig, releaseChart } from "./chart.mjs";
import { el } from "./dom.mjs";
import { fairnessSection } from "./fairness.mjs";
import { popularitySection } from "./popularity.mjs";
import { formatWonShort } from "./format.mjs";

const test = (report, id) => report.fairness.all.find((entry) => entry.id === id);

// 회차 범위(메타 정보)와 disclaimer(정직성 문구)는 서로 다른 종류의 정보이므로 가운뎃점으로
// 묶지 않고 별도 줄로 나눈다. disclaimer 문장 자체는 그대로다.
export function statsRoundNote(report) {
  const stats = report.stats;
  return `${stats.draws.toLocaleString("ko-KR")}회 기준 (${report.latestRound.toLocaleString("ko-KR")}회까지)`;
}

// "과거 분포이며 다음 회차 확률과 무관하다"는 매 게임 화면 첫 줄에 반드시 나와야 한다 (§1.2) —
// 순수 함수로 빼 두면 disclaimer가 조용히 빠지는 변경을 DOM 없이도 테스트로 잡을 수 있다.
export function statsHeaderNote(report) {
  return report.disclaimer;
}

// 관측과 기대를 같은 그림에 놓는다 — 검정이 하는 말과 같은 내용이다.
async function observedVsExpected(report, id, title, note) {
  const entry = test(report, id);
  if (!entry || !entry.observed) return null;
  const { card, canvas } = chartBlock(title, note);
  await drawChart(canvas, barConfig(entry.buckets.map(bucketLabel), entry.observed, {
    expected: entry.expected,
  }));
  return card;
}

async function numberCounts(stats) {
  const numbers = Object.keys(stats.counts);
  const views = {
    all: { label: "전체", data: stats.counts },
    recent: { label: `최근 ${stats.recentCountsWindow}회`, data: stats.recentCounts },
    bonus: { label: "보너스 포함", data: stats.countsWithBonus },
  };
  const { card, canvas } = chartBlock("번호별 출현", null);
  const switcher = el("div", { class: "switch small" });
  let chart = null;
  let current = "all";

  const paint = async () => {
    for (const button of switcher.querySelectorAll("button")) {
      button.classList.toggle("on", button.dataset.view === current);
    }
    releaseChart(chart);
    chart = await drawChart(canvas, barConfig(numbers, numbers.map((n) => views[current].data[n])));
  };

  for (const [view, { label }] of Object.entries(views)) {
    const button = el("button", { type: "button", "data-view": view }, label);
    button.addEventListener("click", () => { current = view; paint(); });
    switcher.append(button);
  }
  card.insertBefore(switcher, card.querySelector(".chart"));
  await paint();
  return card;
}

async function seriesChart(series, key, title, note, { tickFormat = null, value = (row) => row[key] } = {}) {
  const { card, canvas } = chartBlock(title, note);
  await drawChart(canvas, lineConfig(series.map((row) => row.round), series.map(value), {
    tickFormat: tickFormat ? (value) => tickFormat(value) : null,
  }));
  return card;
}

export async function lottoSections(report, backtest) {
  const stats = report.stats;
  const sections = [
    el("p", { class: "fine" }, statsRoundNote(report)),
    el("p", { class: "note" }, statsHeaderNote(report)),
    await guardCard("번호별 출현", () => numberCounts(stats)),
  ];

  sections.push(await guardCard("번호별 미출현 간격", async () => {
    const gaps = Object.keys(stats.gaps);
    const gapCard = chartBlock("번호별 미출현 간격", "마지막으로 나온 뒤 지난 회차 수");
    await drawChart(gapCard.canvas, barConfig(gaps, gaps.map((n) => stats.gaps[n])));
    return gapCard.card;
  }));

  sections.push(
    await guardCard("홀수 개수 분포", () => observedVsExpected(report, "oddEven", "홀수 개수 분포", "막대는 관측, 선은 이론 기대값")),
    await guardCard("저번호(1~22) 개수 분포", () => observedVsExpected(report, "lowHigh", "저번호(1~22) 개수 분포", "막대는 관측, 선은 이론 기대값")),
  );

  sections.push(await guardCard("번호 합 분포", async () => {
    const sums = Object.keys(stats.sums).map(Number).sort((a, b) => a - b);
    const sumCard = chartBlock("번호 합 분포", "6개 번호를 더한 값");
    await drawChart(sumCard.canvas, lineConfig(sums, sums.map((value) => stats.sums[String(value)])));
    return sumCard.card;
  }));

  sections.push(await guardCard("번호대 분포", async () => {
    const decades = Object.keys(stats.decades);
    const decadeCard = chartBlock("번호대 분포", "구간마다 번호 개수가 달라 높이 차이는 당연하다 (41~45는 5개뿐)");
    await drawChart(decadeCard.canvas, barConfig(decades, decades.map((k) => stats.decades[k])));
    return decadeCard.card;
  }));

  sections.push(
    await guardCard("연속번호 쌍 개수", () => observedVsExpected(report, "adjacent", "연속번호 쌍 개수", "막대는 관측, 선은 이론 기대값")),
    await guardCard("직전 회차와 겹치는 번호 개수", () => observedVsExpected(report, "overlap", "직전 회차와 겹치는 번호 개수", "막대는 관측, 선은 이론 기대값")),
    await guardCard("회차별 판매액", () => seriesChart(stats.series, "sales", "회차별 판매액", "원", { tickFormat: formatWonShort })),
    await guardCard("1등 당첨자 수", () => seriesChart(stats.series, "firstWinners", "1등 당첨자 수", "명")),
    await guardCard("1등 1인당 당첨금", () => seriesChart(stats.series, "firstPrize", "1등 1인당 당첨금",
      "단위는 원이다. 1등 당첨자가 없던 회차는 0원이 아니라 끊어서 표시한다", {
        tickFormat: formatWonShort,
        value: (row) => (row.firstWinners ? row.firstPrize : null),
      })),
  );
  sections.push(await guardCard("추첨 공정성 검정", () => fairnessSection(report)));
  sections.push(await guardCard("인기 패턴 규칙의 근거", () => popularitySection(backtest)));

  return sections.filter(Boolean);
}
