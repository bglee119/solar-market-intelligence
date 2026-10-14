# Solar Market Intelligence Japan

한국어 태양광 산업 대시보드. React + Vite + Recharts, Python 수집기, JSON 이력, GitHub Actions / Pages 배포 코드입니다. 유료 AI·뉴스·DB API를 호출하지 않습니다.

## 현재 상태 — 2026-10-14

- React/Vite 프로덕션 빌드와 순수 로직 테스트 통과. React 서버 렌더링으로 실제 JSON과 링크 표시 확인.
- ECB 공식 XML 실수집 성공: USD/JPY, CNY/JPY. 거래환율이 아닌 EUR 기준 교차환율입니다.
- METI RSS: 현재 실행 환경에서 robots.txt HTTP 403. 접근 우회하지 않고 실패를 기록했습니다.
- 뉴스 6건과 태양광 가격 3개 시계열은 웹 원문을 확인해 초기 입력했습니다. 모든 항목에 자동 수집이 아니라는 표시가 있습니다. ECB 2개 시계열을 합해 가격 모니터에는 5개가 있습니다.
- 나머지 원재료·기관별 수집은 미확보 또는 이용조건/파서 검토 대기. 해당 가격은 비워 둡니다.
- **공개 저장소 bglee119/solar-market-intelligence 및 쓰기 권한 확인. GitHub Actions 실제 실행, Pages 배포, 예약 실행은 각각 검증 대기입니다.**
- ChatGPT Sites 배포본은 데이터가 포함된 최초 게시 스냅샷입니다. GitHub Actions가 Sites를 갱신하지는 않습니다. GitHub Pages 전환 이후에는 해당 Pages URL 하나를 고정 운영 URL로 사용합니다.
- Windows/Android 반응형 CSS 구현. 실제 브라우저 자동화 도구가 없어 클릭·모바일 화면 검증은 미실시입니다.

## 로컬 실행

Python 3.12 이상, Node 22 이상 권장. 아래 명령은 프로젝트 루트에서 실행합니다.

```sh
python -m pip install -r requirements.txt
npm ci
python -m unittest discover -s tests -v
npm test
node tests/render.mjs
python -m collector.collect
python -m collector.report
npm run build
npm run dev
```

`collector.report`는 pandas로 시계열별 관측일 수·최초/최종 기준일을 집계합니다. 수집기 자체는 표준 라이브러리로 실행할 수 있습니다. 테스트의 합성 fixture는 테스트 코드에만 있으며 배포 데이터에는 포함되지 않습니다.

## GitHub 운영 활성화

1. 연결된 GitHub 계정에 `solar-market-intelligence` 저장소를 생성합니다. 무료 GitHub Pages를 사용하려면 무료 계정에서는 공개 저장소 구성을 선택합니다. 기업 내부 비밀자료는 넣지 않습니다.
2. 이 프로젝트의 코드를 `main` 브랜치에 업로드합니다. `.openai/hosting.json`은 Sites 전용이라 GitHub 이관본에는 없어도 됩니다.
3. 저장소 Settings → Pages → Build and deployment → Source에서 **GitHub Actions**를 선택합니다.
4. Actions 실행과 GITHUB_TOKEN의 contents 쓰기·Pages 배포 권한을 허용합니다. 브랜치 보호가 봇 커밋을 금지하면 저장소 정책에 맞게 별도 데이터 브랜치 방식으로 조정해야 합니다.
5. Actions → **Daily solar intelligence** → Run workflow를 실행합니다.
6. collect-build의 테스트·수집·데이터 커밋, deploy의 실제 URL 검증을 각각 확인합니다. 수집이 일부 실패해도 상태 화면은 배포한 후 워크플로를 실패 표시합니다. 결제나 유료 러너는 활성화하지 않습니다.
7. 사이트의 마지막 성공 시각과 데이터 기준일을 확인합니다. 수동 실행 성공은 예약 실행 확인과 다릅니다. 다음 예약 실행의 event가 schedule인지 따로 확인합니다.

예약식은 `10 23 * * *`: **UTC 23:10 = 다음 날 JST 08:10**입니다. 기본 브랜치에서 실행되며 GitHub 사정으로 지연되거나 누락될 수 있습니다. 공개 저장소가 장기간 비활성 상태이면 예약이 비활성화될 수 있으므로 Actions 상태도 관리해야 합니다. GitHub에서 추가 비용이 생기는 유료 플랜·유료 러너 사용은 전제하지 않았습니다.

정상 배포 후 URL 형태: `https://<github-user>.github.io/solar-market-intelligence/` (현재 실제 URL 아님).

GitHub 문서:
- https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule
- https://docs.github.com/en/pages/getting-started-with-github-pages/what-is-github-pages

## 수집·분석 규칙

- 활성 소스만 요청. 매 실행 robots 확인, 불명확하거나 403이면 해당 소스를 중단. 404 robots만 규칙 없음으로 처리. 타 호스트 리다이렉트는 검토 전 거부.
- 요청 간 최소 1초, robots crawl-delay 반영. timeout 12초, 429/5xx 1회 재시도. 로그인·페이월·차단 우회 없음.
- RSS/Atom 기사 게시일을 JST로 정규화. 게시일이 없거나 미래이거나 최근 30일 밖이면 현재 피드에서 제외. 발표일을 알 수 없는 경우 null. published 대신 updated만 있을 경우 date_precision을 updated_timestamp로 기록하며 원본 소스 확인이 필요합니다.
- 기사 원문 URL을 제한된 호스트에서 검증한 뒤 저장. 본문 저장·유료 LLM 요약·자동 번역 없음. 영문/일문 피드는 원문 제목을 유지합니다.
- URL 추적 파라미터 및 정규화 제목으로 중복 제거. 서로 다르게 표현된 동일 사건의 의미 중복까지 제거하는 기능은 아닙니다.
- 비교 키: 품목 + 규격 + 지역 + 통화 + 단위 + 출처 + 거래조건. 단위/통화 환산을 임의 적용하지 않습니다.
- 동일 기준일 재수집은 새 관측치로 늘리지 않음. 이전 관측치가 없으면 변동률 null. 소스가 보도한 상승률을 역산해 과거 가격을 만들지 않습니다.
- 자동 분석: 비교 가능한 가격 ±1% 이상 변화, 제목의 공급과잉/감산/관세 키워드. 기사 주장을 실제 실현된 수급 변화로 확정하지 않습니다.
- 자사 재고원가·일본 판매가격·확정 정책 일정 미확보 시 판단 유보. 구매 추천 없음.

## 이력과 장애

- `public/data/latest.json`: 현재 화면과 수집 상태. JSON 스키마 버전 1.
- `prices.json`: 전체 가격 관측 이력. `news.json`: 전체 기사 이력. 30일은 표시 범위이지 삭제 기준이 아닙니다.
- `history/*.json`: 실행시각별 스냅샷. `history/index.json`: 이전 자료 선택 목록.
- `runs.json`: 최근 365회 실행 결과 및 소스별 오류. Git 이력으로 이전 버전 보존.
- `quality.json`: pandas 기준 데이터 품질 요약.
- 파일별 임시 파일 후 atomic rename. 파싱/접근 실패 시 기존 기사와 가격을 보존. 잘못된 JSON 자체가 있는 경우 조용히 초기화하지 않고 실행 오류로 중단합니다.
- 일부 소스만 성공하면 partial. last_success_at은 최소 한 소스 성공, last_full_success_at은 활성 소스 전체 성공입니다. 이것은 데이터가 새로 발표됐다는 의미와 다릅니다.
- 프로세스 강제 종료·GitHub 전역 장애 등으로 새 상태를 배포할 수 없을 때는 기존 사이트가 유지됩니다. 화면의 36시간 경과 표시가 갱신 중단 신호이며 정확한 장애 원인은 Actions 로그에서 확인합니다.

## 소스 추가와 유지보수

`config/sources.json`에서 URL, 이용조건, 활성 여부를 관리합니다. 상용 뉴스/가격 사이트는 공개 열람과 자동 재배포 허용이 동일하지 않으므로 검토 전 비활성입니다. robots 검사도 저작권 허가를 대신하지 않습니다.

- `rss`: RSS/Atom 제목·게시일·원문 URL. `allowed_hosts`는 명시적 목록.
- `ecb`: 공식 EUR 기준 환율 XML → JPY/USD, JPY/CNY 교차환율.
- `price_csv`: 재사용이 확인된 공개 CSV용 어댑터. `reuse_approved: true`가 필수. 현재 연결된 시세 공급자는 없습니다. 필드는 `item,spec,region,price,currency,unit,as_of,basis,confidence`이며 가격 기준일은 YYYY-MM-DD입니다. source/url은 승인된 설정값으로 덮어씁니다.
- `review`: 아직 파서와 접근조건이 검증되지 않은 소스.

매월 실패 소스·데이터 최신성·GitHub 예약 활성화 상태를 확인합니다. 소스 구조가 변경되면 fixture와 파서를 함께 수정하고 테스트 후 배포합니다. 의존성은 lockfile로 고정하며 보안 업데이트 시 테스트·빌드를 재확인합니다. 현재 30일 가격선이 비어 있는 것은 이력이 부족하기 때문이며 데이터가 쌓이면 표시됩니다.

## 프로젝트 구조

```text
collector/collect.py       공개 수집, 접근검사, 상태/이력 저장
collector/normalize.py     날짜/중복/단위/변동률/규칙 기반 분석
collector/prices.py        승인된 공개 가격 CSV 정규화
collector/report.py        pandas 품질 집계
config/sources.json        출처별 정책과 수집 상태
config/items.json          요청 품목 커버리지
src/main.jsx              React 화면
src/data.mjs              필터/CSV/추이 로직
src/style.css             데스크톱/모바일 디자인
public/data/              실제 데이터와 출처, 실행 이력
.github/workflows/daily.yml 수집→테스트→빌드→Pages 배포
TEST_REPORT.md             검증 결과와 미검증 범위
SOURCE_AUDIT.md            데이터 소스 검토 기록
```
