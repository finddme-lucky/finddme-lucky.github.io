import { barConfig, bucketLabel, chartCard, drawChart, lineConfig } from "./chart.mjs";
import { el } from "./dom.mjs";
import { fairnessSection } from "./fairness.mjs";
import { popularitySection } from "./popularity.mjs";
import { formatWonShort } from "./format.mjs";

const test = (report, id) => report.fairness.all.find((entry) => entry.id === id);

// 관측과 기대를 같은 그림에 놓는다 — 검정이 하는 말과 같은 내용이다.
async function observedVsExpected(report, id, title, note) {
  const entry = test(report, id);
  if (!entry || !entry.observed) return null;
  const { card, canvas } = chartCard(title, note);
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
  const { card, canvas } = chartCard("번호별 출현", null);
  const switcher = el("div", { class: "switch small" });
  let chart = null;
  let current = "all";

  const paint = async () => {
    for (const button of switcher.querySelectorAll("button")) {
      button.classList.toggle("on", button.dataset.view === current);
    }
    chart?.destroy();
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

async function seriesChart(series, key, title, note, { tickFormat = null } = {}) {
  const { card, canvas } = chartCard(title, note);
  await drawChart(canvas, lineConfig(series.map((row) => row.round), series.map((row) => row[key]), {
    tickFormat: tickFormat ? (value) => tickFormat(value) : null,
  }));
  return card;
}

export async function lottoSections(report, backtest) {
  const stats = report.stats;
  const sections = [
    el("p", { class: "note" },
      `${stats.draws.toLocaleString("ko-KR")}회 기준 (${report.latestRound.toLocaleString("ko-KR")}회까지) · ${report.disclaimer}`),
    await numberCounts(stats),
  ];

  const gaps = Object.keys(stats.gaps);
  const gapCard = chartCard("번호별 미출현 간격", "마지막으로 나온 뒤 지난 회차 수");
  await drawChart(gapCard.canvas, barConfig(gaps, gaps.map((n) => stats.gaps[n])));
  sections.push(gapCard.card);

  sections.push(
    await observedVsExpected(report, "oddEven", "홀수 개수 분포", "막대는 관측, 선은 이론 기대값"),
    await observedVsExpected(report, "lowHigh", "저번호(1~22) 개수 분포", "막대는 관측, 선은 이론 기대값"),
  );

  const sums = Object.keys(stats.sums).map(Number).sort((a, b) => a - b);
  const sumCard = chartCard("번호 합 분포", "6개 번호를 더한 값");
  await drawChart(sumCard.canvas, lineConfig(sums, sums.map((value) => stats.sums[String(value)])));
  sections.push(sumCard.card);

  const decades = Object.keys(stats.decades);
  const decadeCard = chartCard("번호대 분포", "구간마다 번호 개수가 달라 높이 차이는 당연하다 (41~45는 5개뿐)");
  await drawChart(decadeCard.canvas, barConfig(decades, decades.map((k) => stats.decades[k])));
  sections.push(decadeCard.card);

  sections.push(
    await observedVsExpected(report, "adjacent", "연속번호 쌍 개수", "막대는 관측, 선은 이론 기대값"),
    await observedVsExpected(report, "overlap", "직전 회차와 겹치는 번호 개수", "막대는 관측, 선은 이론 기대값"),
    await seriesChart(stats.series, "sales", "회차별 판매액", "원", { tickFormat: formatWonShort }),
    await seriesChart(stats.series, "firstWinners", "1등 당첨자 수", "명"),
    await seriesChart(stats.series, "firstPrize", "1등 1인당 당첨금", "원", { tickFormat: formatWonShort }),
  );
  sections.push(fairnessSection(report));
  sections.push(popularitySection(backtest));

  return sections.filter(Boolean);
}
