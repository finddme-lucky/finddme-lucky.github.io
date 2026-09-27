import { barConfig, chartBlock, drawChart, guardCard, lineConfig, palette, releaseChart } from "./chart.mjs";
import { el } from "./dom.mjs";
import { fairnessSection } from "./fairness.mjs";

const DIGITS = ["0", "1", "2", "3", "4", "5", "6", "7", "8", "9"];
const RANKS = ["1", "2", "3", "4", "5", "6", "7", "bonus"];
const rankLabel = (rank) => (rank === "bonus" ? "보너스" : `${rank}등`);

// stats-lotto.mjs의 statsRoundNote와 같은 규약 — 회차 범위(메타 정보)와 disclaimer는
// 서로 다른 종류의 정보이므로 가운뎃점으로 묶지 않고 별도 줄로 나눈다.
export function statsRoundNote(report) {
  const stats = report.stats;
  return `${stats.draws.toLocaleString("ko-KR")}회 기준 (${report.latestRound.toLocaleString("ko-KR")}회까지)`;
}

// stats-lotto.mjs의 statsHeaderNote와 같은 규약 — disclaimer가 화면 첫 줄에서 빠지면 테스트가 죽어야 한다.
export function statsHeaderNote(report) {
  return report.disclaimer;
}

// 카드 안에 전환 버튼을 달고, 고를 때마다 차트를 다시 그린다.
async function switchingCard(title, note, options, build) {
  const { card, canvas } = chartBlock(title, note);
  const switcher = el("div", { class: "switch small" });
  let chart = null;
  let current = options[0].value;

  const paint = async () => {
    for (const button of switcher.querySelectorAll("button")) {
      button.classList.toggle("on", button.dataset.value === current);
    }
    releaseChart(chart);
    chart = await drawChart(canvas, build(current));
  };

  for (const option of options) {
    const button = el("button", { type: "button", "data-value": option.value }, option.label);
    button.addEventListener("click", () => { current = option.value; paint(); });
    switcher.append(button);
  }
  card.insertBefore(switcher, card.querySelector(".chart"));
  await paint();
  return card;
}

export async function pensionSections(report, backtest) {
  const stats = report.stats;
  const sections = [
    el("p", { class: "fine" }, statsRoundNote(report)),
    el("p", { class: "note" }, statsHeaderNote(report)),
  ];

  const groups = Object.keys(stats.groups);
  sections.push(await guardCard("1등 조 분포", () => switchingCard("1등 조 분포", "막대는 관측, 선은 고르게 나왔을 때의 기대값", [
    { value: "all", label: "전체" },
    { value: "recent", label: `최근 ${stats.recentCountsWindow}회` },
  ], (view) => {
    const source = view === "all" ? stats.groups : stats.recentGroups;
    const total = groups.reduce((sum, key) => sum + source[key], 0);
    return barConfig(groups.map((g) => `${g}조`), groups.map((g) => source[g]), {
      expected: groups.map(() => total / groups.length),
    });
  })));

  sections.push(await guardCard("자리별 숫자 분포", () => switchingCard("자리별 숫자 분포", "1등 번호와 보너스 번호를 나란히",
    [1, 2, 3, 4, 5, 6].map((position) => ({ value: String(position), label: `${position}번째` })),
    (value) => {
      const index = Number(value) - 1;
      const first = stats.firstDigits[index];
      const bonus = stats.bonusDigits[index];
      const colors = palette();
      const total = DIGITS.reduce((sum, digit) => sum + first[digit], 0);
      return {
        type: "bar",
        data: {
          labels: DIGITS,
          datasets: [
            { label: "1등", data: DIGITS.map((d) => first[d]), backgroundColor: colors.mark },
            { label: "보너스", data: DIGITS.map((d) => bonus[d]), backgroundColor: colors.quiet },
            { type: "line", label: "기대", data: DIGITS.map(() => total / 10),
              borderColor: colors.ink, borderWidth: 2, pointRadius: 0 },
          ],
        },
        options: {
          responsive: true, maintainAspectRatio: false, animation: false,
          scales: { x: { grid: { display: false } }, y: { beginAtZero: true } },
        },
      };
    })));

  sections.push(await guardCard("등수별 당첨 매수 추이", () => switchingCard("등수별 당첨 매수 추이", "회차별 당첨 매수",
    RANKS.map((rank) => ({ value: rank, label: rankLabel(rank) })),
    (rank) => lineConfig(
      stats.series.map((row) => row.round),
      stats.series.map((row) => row.rankTotals?.[rank] ?? null),
      { label: rankLabel(rank) },
    ))));

  sections.push(await guardCard("추첨 공정성 검정", () => fairnessSection(report)));
  return sections.filter(Boolean);
}
