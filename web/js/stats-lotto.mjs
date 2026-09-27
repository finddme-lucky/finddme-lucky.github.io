import { barConfig, chartCard, drawChart } from "./chart.mjs";
import { el } from "./dom.mjs";

// 이 단계에서는 "번호별 출현" 하나만. 나머지는 Task 2에서 붙인다.
export async function lottoSections(report, backtest) {
  const stats = report.stats;
  const sections = [];

  sections.push(el("p", { class: "note" },
    `${stats.draws.toLocaleString("ko-KR")}회 기준 · ${report.disclaimer}`));

  const numbers = Object.keys(stats.counts);
  const counts = chartCard("번호별 출현 (본번호)", "전체 회차");
  sections.push(counts.card);
  await drawChart(counts.canvas, barConfig(numbers, numbers.map((n) => stats.counts[n])));

  return sections;
}
