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

## 테스트

```bash
docker exec finddme-lucky pytest
```
