export const GAMES = {
  lotto645: { name: "로또 6/45", short: "로또" },
  pension720: { name: "연금복권720+", short: "연금복권" },
};

export const STRATEGIES = {
  hot: { name: "많이 나온 번호", score: "최근 출현 횟수" },
  cold: { name: "오래 안 나온 번호", score: "마지막 출현 이후 회차 수" },
  recent: { name: "최근 가중", score: "지수 감쇠 가중 빈도 (반감기 20회)" },
  ml: { name: "간단 ML", score: "로지스틱 회귀가 매긴 \"다음 회차 출현\" 확률" },
  random: { name: "무작위", score: "균등 — 비교 기준선" },
};

export const gameLabel = (id) => GAMES[id] ?? { name: id, short: id };
export const strategyLabel = (id) => STRATEGIES[id] ?? { name: id, score: "설명 없음" };
