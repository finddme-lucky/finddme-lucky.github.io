import { balls } from "./balls.mjs";
import { el } from "./dom.mjs";
import { formatCount, formatDate, formatDateTime, formatRound, formatWonShort } from "./format.mjs";
import { GAMES, gameLabel } from "./labels.mjs";
import { STALE_DAYS, staleness } from "./staleness.mjs";

const firstRank = (draw) => draw.ranks.find((rank) => rank.rank === 1);

const fact = (term, value) => el("div", {}, el("dt", {}, term), el("dd", {}, value));

function lottoDraw(draw) {
  const rank = firstRank(draw);
  return el("div", { class: "draw" },
    balls(draw.numbers, draw.bonus),
    el("dl", { class: "facts" },
      fact("1등", `${formatCount(rank.winners)} · ${formatWonShort(rank.prize)}`),
      fact("판매액", formatWonShort(draw.sales))));
}

function pensionDraw(draw) {
  const rank = firstRank(draw);
  return el("div", { class: "draw" },
    el("div", { class: "digits" },
      el("span", { class: "group" }, `${draw.group}조`),
      [...draw.first].map((digit) => el("span", { class: "digit" }, digit))),
    el("dl", { class: "facts" },
      fact("보너스", [...draw.bonus].join(" ")),
      fact("1등 (총액)", `${formatCount(rank.total)} · ${formatWonShort(rank.prize)}`)));
}

function pastRounds(game, draws) {
  if (draws.length === 0) return null;
  const line = (draw) => game === "lotto645"
    ? `${formatRound(draw.round)} ${draw.numbers.join(", ")} + ${draw.bonus}`
    : `${formatRound(draw.round)} ${draw.group}조 ${draw.first}`;
  return el("details", { class: "past" },
    el("summary", {}, `지난 ${draws.length}회차`),
    el("ul", {}, [...draws].reverse().map((draw) => el("li", {}, line(draw)))));
}

export function renderHome(target, latest, now = new Date()) {
  // 캐시에서 나온 데이터인지가 가장 확실한 신호다. navigator.onLine은 DevTools 오프라인이나
  // 서버만 죽은 경우 true로 남으므로 보조로만 쓴다.
  const servedFromCache = latest?.fromCache === true;
  const offlineBanner = el("p", { class: "banner" },
    "네트워크에 연결되지 않아 마지막으로 받은 데이터를 보여줍니다.");
  offlineBanner.hidden = !servedFromCache && navigator.onLine !== false;
  addEventListener("online", () => { offlineBanner.hidden = !servedFromCache; });
  addEventListener("offline", () => { offlineBanner.hidden = false; });
  target.append(offlineBanner);
  target.append(el("p", { class: "note" }, `데이터 변경 ${formatDateTime(latest.updatedAt)}`));
  for (const game of Object.keys(GAMES)) {
    const section = latest.games[game];
    if (!section) continue;
    const { days, stale } = staleness(section.latestDate, now);
    const draws = section.draws;
    target.append(el("section", { class: "card" },
      el("h2", {}, gameLabel(game).name),
      el("p", { class: "sub" }, `${formatRound(section.latestRound)} · ${formatDate(section.latestDate)}`),
      stale ? el("p", { class: "banner" },
        `마지막 추첨일로부터 ${days}일이 지났는데 새 회차가 없습니다 — 데이터 갱신이 멈췄을 수 있습니다 (기준 ${STALE_DAYS}일).`) : null,
      game === "lotto645" ? lottoDraw(draws.at(-1)) : pensionDraw(draws.at(-1)),
      pastRounds(game, draws.slice(0, -1))));
  }
}
