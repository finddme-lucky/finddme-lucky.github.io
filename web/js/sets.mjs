import { tierClass } from "./balls.mjs";
import { el } from "./dom.mjs";
import { formatDateTime, formatPercent, formatRound, formatWon } from "./format.mjs";
import { GAMES, gameLabel, strategyLabel } from "./labels.mjs";
import { slipGrid } from "./slip.mjs";
import { staleness } from "./staleness.mjs";

const HONESTY = "어떤 전략도 당첨 확률을 바꾸지 않는다. 비인기 조합(L1)은 1등이 됐을 때 나눠 갖는 인원을, 겹침 조절(L2)과 1~5조 몰아 사기(P2)는 당첨 분포를 바꿀 뿐이다.";
const P2_NOTE = "1~5조를 전부 사는 것(5장)을 전제한 번호다. 6자리가 모두 맞으면 1등 1장과 2등 4장을 함께 받는다. 기대값은 5장을 따로 사는 것과 같지만, 끝자리가 모두 같아 \"한 장이라도 당첨\"될 확률은 오히려 낮다 — 7등 이상 10%, 끝자리를 전부 다르게 사면 50%.";
const PENSION_RETURN_NOTE = "수익률이 이론값보다 낮은 것은 200회차 안에서 1등·2등이 거의 나오지 않기 때문이며, 전략의 차이가 아니다.";
const ML_NOTE = "학습 구간에서는 갈라내지만 평가 구간에서는 갈라내지 못한다 — 과거에만 맞는다는 뜻이다.";

const verdict = (entry) => entry.distinguishable ? "무작위와 구분됨" : "무작위와 구분되지 않음 (정상)";

// 값 막대 + 이론값 표시선. 차트 라이브러리 없이 비교만 보여준다.
function meter(value, reference, max) {
  return el("div", { class: "meter", title: `이론값 ${formatPercent(reference)}` },
    el("i", { style: `width:${Math.min(100, (value / max) * 100)}%` }),
    el("u", { style: `left:${Math.min(100, (reference / max) * 100)}%` }));
}

function lottoPerformance(entry, theory) {
  if (!entry || !theory) return el("p", { class: "fine" }, "과거 성적 기록이 아직 없습니다.");
  const max = Math.max(entry.hitRateCI[1], theory.hitRate) * 1.2;
  return el("div", { class: "perf" },
    el("p", { class: "stat" }, "5등 이상 적중률 ", el("b", {}, formatPercent(entry.hitRate))),
    meter(entry.hitRate, theory.hitRate, max),
    el("dl", { class: "facts" },
      el("dt", {}, "이론값"), el("dd", {}, formatPercent(theory.hitRate)),
      el("dt", {}, "95% 구간"), el("dd", {}, `${formatPercent(entry.hitRateCI[0])} ~ ${formatPercent(entry.hitRateCI[1])}`),
      el("dt", {}, "판정"), el("dd", {}, verdict(entry))),
    entry.inSampleSeparation === undefined ? null : el("p", { class: "fine" },
      `학습 구간 분리도 ${entry.inSampleSeparation.toFixed(5)} vs 평가 구간 ${entry.outOfSampleSeparation.toFixed(5)} — ${ML_NOTE}`));
}

function pensionPerformance(entry, theory) {
  if (!entry || !theory) return el("p", { class: "fine" }, "과거 성적 기록이 아직 없습니다.");
  const max = Math.max(entry.returnRate, theory.returnRate) * 1.2;
  return el("div", { class: "perf" },
    el("p", { class: "stat" }, "수익률 ", el("b", {}, formatPercent(entry.returnRate))),
    meter(entry.returnRate, theory.returnRate, max),
    el("dl", { class: "facts" },
      el("dt", {}, "이론값"), el("dd", {}, formatPercent(theory.returnRate)),
      el("dt", {}, "쓴 금액"), el("dd", {}, formatWon(entry.spent)),
      el("dt", {}, "받은 금액"), el("dd", {}, formatWon(entry.won)),
      el("dt", {}, "판정"), el("dd", {}, verdict(entry))),
    entry.inSampleSeparation === undefined ? null : el("p", { class: "fine" },
      `학습 구간 분리도 ${entry.inSampleSeparation.toFixed(5)} vs 평가 구간 ${entry.outOfSampleSeparation.toFixed(5)} — ${ML_NOTE}`));
}

function lottoStrategy(entry, report) {
  const label = strategyLabel(entry.strategy);
  const perf = report.strategies?.[entry.strategy];
  return el("section", { class: "block" },
    el("div", { class: "strategy" },
      el("h3", {}, label.name),
      el("code", { class: "quiet" }, entry.strategy)),
    el("p", { class: "quiet" }, `${label.score}로 점수를 매겨 뽑았다.`),
    ...entry.games.map((numbers) => el("div", { class: "game-line" },
      slipGrid(numbers, { animate: true }),
      el("div", { class: "picks" }, numbers.map((n) => el("span", { class: `pick ${tierClass(n)}` }, n))))),
    el("p", { class: "fine" }, "5게임끼리 번호가 겹치지 않는다 (L2). 인기 패턴(L1)에 걸리는 게임은 제외했다."),
    lottoPerformance(perf, report.theory));
}

function pensionStrategy(entry, report) {
  const label = strategyLabel(entry.strategy);
  const perf = report.strategies?.[entry.strategy];
  return el("section", { class: "block" },
    el("div", { class: "strategy" },
      el("h3", {}, label.name),
      el("code", { class: "quiet" }, entry.strategy)),
    el("p", { class: "quiet" }, `${label.score}로 점수를 매겨 뽑았다.`),
    el("div", { class: "digits" },
      el("em", {}, "1~5조"),
      el("b", {}, [...entry.number].join(" "))),
    pensionPerformance(perf, report.theory));
}

function sections(game, predictions, backtest, latest, now) {
  const section = predictions[game];
  const report = backtest[game];
  if (!section || !report) {
    return [el("p", { class: "error" }, `${gameLabel(game).name} 데이터가 아직 없습니다.`)];
  }
  const latestSection = latest?.games?.[game];
  const alreadyDrawn = latestSection !== undefined && section.round <= latestSection.latestRound;
  // 수집이 멈춰 있으면 이 회차도 이미 추첨됐을 수 있다 — 회차 번호만으로는 알 수 없다 (§8.3).
  const behind = !alreadyDrawn && latestSection !== undefined
    ? staleness(latestSection.latestDate, now)
    : { stale: false };
  const settled = alreadyDrawn || behind.stale;
  const head = el("section", { class: "block" },
    el("h2", { class: "game" }, `${gameLabel(game).name} ${formatRound(section.round)}`),
    el("p", { class: "quiet" },
      `${settled ? "" : "다음 추첨 회차. "}같은 회차에는 언제 봐도 같은 번호가 나온다 (다시 뽑기 없음).`),
    alreadyDrawn
      ? el("p", { class: "notice" }, "이 회차는 이미 추첨됐습니다 — 데이터 갱신이 멈췄을 수 있습니다.")
      : behind.stale
      ? el("p", { class: "notice" },
          `마지막으로 받은 추첨 결과가 ${behind.days}일 지났습니다 — 이 회차도 이미 추첨됐을 수 있습니다.`)
      : null,
    el("p", { class: "fine" }, `번호 생성 ${formatDateTime(predictions.generatedAt)}`),
    el("p", { class: "honest" }, HONESTY),
    game === "pension720" ? el("p", { class: "notice" }, P2_NOTE) : null);
  const strategies = section.sets.map((entry) =>
    game === "lotto645" ? lottoStrategy(entry, report) : pensionStrategy(entry, report));
  const tail = el("section", { class: "block" },
    el("p", { class: "fine" }, `과거 성적은 최근 ${report.evalRounds}회차를 대상으로, 각 회차 이전 자료만 써서 매긴 것이다.`),
    game === "pension720" ? el("p", { class: "fine" }, PENSION_RETURN_NOTE) : null,
    el("p", { class: "honest" }, predictions.disclaimer),
    el("p", { class: "honest" }, backtest.disclaimer));
  return [head, ...strategies, tail];
}

export function renderSets(target, predictions, backtest, latest, now = new Date()) {
  let game = "lotto645";
  const body = el("div", { class: "body" });
  const switcher = el("div", { class: "switch" });

  const paint = () => {
    let content;
    try {
      content = sections(game, predictions, backtest, latest, now);
    } catch (error) {
      content = [el("p", { class: "error" }, `데이터를 불러오지 못했습니다 — ${error.message}. 새로고침해 보세요.`)];
    }
    for (const button of switcher.querySelectorAll("button")) {
      button.classList.toggle("on", button.dataset.game === game);
    }
    body.replaceChildren(...content);
  };

  for (const id of Object.keys(GAMES)) {
    const button = el("button", { type: "button", "data-game": id }, gameLabel(id).short);
    button.addEventListener("click", () => { game = id; paint(); });
    switcher.append(button);
  }
  target.append(switcher, body);
  paint();
}
