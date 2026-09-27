# finddme-lucky.github.io

로또 6/45 · 연금복권720+ 추첨 결과 수집·분석 앱 (개인용).

## 개발 환경

테스트와 실행은 dev 컨테이너 `finddme-lucky` 안에서 한다. 호스트에는 개발 도구를 설치하지 않는다.

## 데이터 수집

```bash
docker exec finddme-lucky python -m lucky collect                    # 두 게임의 신규 회차
docker exec finddme-lucky python -m lucky collect --game lotto645    # 한 게임만
docker exec finddme-lucky python -m lucky collect --full             # 전 회차 재수집 → 저장값 변경 여부 확인
```

- 산출물: `data/lotto645.json`, `data/pension720.json`, `data/meta.json`
- 동행복권 사이트의 내부 JSON 엔드포인트를 사용한다 (공식 API 아님).
- 네트워크 오류로 중간에 실패하면 같은 명령을 다시 실행하면 저장된 곳부터 이어서 받는다.
- 실패하면 종료 코드 1, 원인은 stderr에 출력된다. 검증을 통과하지 못한 데이터는 저장하지 않는다.

### 실패했을 때

stderr 메시지로 대응이 갈린다.

- `N회 시도 실패` — 네트워크 오류. 같은 명령을 다시 실행하면 저장된 페이지부터 이어받는다.
- `리다이렉트됨` / `JSON이 아닌 응답` / `형식 변경` / `불일치` — 동행복권 사이트가 바뀐 것이다. 결과 페이지가 호출하는 새 주소를 찾아 `lucky/sources/`를 고쳐야 한다. 재실행해도 똑같이 실패한다.
- `고정 당첨금과 다름` — 연금복권 당첨금 제도가 바뀐 것이다. `lucky/validate.py`의 `PENSION_PRIZES`를 갱신하기 전까지 새 회차가 저장되지 않는다.
- 그 밖의 `이상` / `불연속` — 받은 값이 검증 규칙을 위반했다. 저장하지 않았으니 메시지에 나온 회차를 직접 확인한다.

## 통계 · 추첨 공정성 검정

```bash
docker exec finddme-lucky python -m lucky analyze      # 통계·검정 계산 → data/stats/
docker exec finddme-lucky python -m lucky fairness     # 검정 결과만 출력 (저장 안 함)
```

- 산출물: `data/stats/lotto645.json`, `data/stats/pension720.json`
- 검정은 관측 분포를 이론 분포(정확한 조합 계산)와 카이제곱으로 비교하고, 여러 검정을 한꺼번에 하므로 Holm 보정을 적용한다.
- "편향 증거 없음"이 정상적인 결과다. 과거 분포일 뿐 다음 회차 확률과는 무관하다.

## 번호 세트

```bash
docker exec finddme-lucky python -m lucky sets                       # 다음 회차 세트 → data/predictions.json
docker exec finddme-lucky python -m lucky sets --strategy hot        # 점검용: 한 전략만 계산 (저장 안 함)
docker exec finddme-lucky python -m lucky sets --round 1200          # 점검용: 그 회차 기준으로 계산만 (저장 안 함)
```

- 산출물: `data/predictions.json`
- 로또는 전략별로 5게임을 만들고, 게임끼리 번호가 겹치지 않으며, 사람들이 많이 고르는 패턴(`rules/lotto645-unpopular.json`)을 피한다.
- 연금복권은 6자리 하나를 만든다. **1~5조를 전부 사는 것**을 전제한 번호다. 6자리가 맞으면 1등 1장과 2등 4장을 함께 받는 "몰아서 받기"이고, 기대값은 5장을 따로 사는 것과 같다. 대신 다섯 장의 끝자리가 같아 "한 장이라도 당첨"될 확률은 오히려 낮다 (7등 이상 10%, 끝자리를 전부 다르게 사면 50%).
- 같은 회차에는 언제 실행해도 같은 번호가 나온다. 다시 뽑기는 없다.
- **어떤 전략도 당첨 확률을 바꾸지 않는다.** 비인기 조합은 1등이 됐을 때 나눠 갖는 인원을, 겹침 조절은 당첨 분포를 바꿀 뿐이다.

## 백테스트 · 인기 규칙 근거

```bash
docker exec finddme-lucky python -m lucky backtest                    # 전략별 과거 성적 → data/backtest.json (2~3분)
docker exec finddme-lucky python -m lucky backtest --rounds 50        # 점검용: 짧게 계산만 (저장 안 함)
docker exec finddme-lucky python -m lucky backtest --strategy hot     # 점검용: 한 전략만
```

- 산출물: `data/backtest.json`
- t회차 성적은 t회차 **이전** 자료로만 만든 세트로 매긴다 (미래 누출 없음).
- 로또는 5등 이상 적중률을 정확한 초기하 이론값과 무작위 기준선에 맞대어 보고, 연금복권은 1~5조 전부 구매 기준 수익률을 이론값(75%)과 비교한다.
- **어떤 전략도 무작위와 구분되지 않는 것이 정상이다.** 이 표는 그것을 확인하기 위한 기록이다.
- `ml`은 학습 구간 분리도와 평가 구간 분리도를 나란히 싣는다 — 과거에는 갈리고 미래에는 갈리지 않는다는 것을 보여준다.
- 인기 규칙 근거는 5등 당첨자 수가 주변 회차보다 많았던 회차의 당첨번호가 인기 패턴에 더 많이 걸리는지 비교한 것이다. 판매액 필드의 의미가 구간마다 달라 절대 기대값 비교는 하지 않는다.

## 앱 (PWA)

```bash
docker exec finddme-lucky python scripts/make_icons.py   # 아이콘 다시 만들기 (거의 쓸 일 없음)
docker exec -d finddme-lucky python scripts/serve.py     # http://localhost:8765
docker exec finddme-lucky pkill -f scripts/serve.py      # 끄기
```

- 소스는 `web/`, 데이터는 `data/`. 빌드 도구가 없어 파일을 고치고 새로고침하면 끝이다.
- dev 서버는 배포 레이아웃을 재현한다 — `/`는 `web/`, `/data/`는 저장소의 `data/`에서 읽는다.
- 탭: **홈**(두 복권 최신 결과·갱신 시각·갱신 지연 배너), **이번 주 번호**(전략별 세트와 과거 성적).
- 폰에 설치: 같은 네트워크에서 `http://<PC IP>:8765` 로 열거나, 배포 후 `https://finddme-lucky.github.io` 에서 "홈 화면에 추가".
- 오프라인에서는 마지막으로 받은 데이터와 그 갱신 시각이 그대로 보인다.
- `web/`에 **파일을 새로 추가**하면 `web/sw.js`의 `ASSETS` 목록에도 넣어야 오프라인에서 열린다. 내용만 고칠 때는 손댈 필요 없다.

JS 순수 함수 테스트:

```bash
docker exec finddme-lucky node --test tests/web/
```

## 테스트

```bash
docker exec finddme-lucky pytest
```
