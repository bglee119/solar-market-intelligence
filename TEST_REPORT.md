# 검증 결과 — 2026-10-14

| 항목 | 결과 | 검증 범위 |
|---|---|---|
| 프런트 프로덕션 빌드 | 통과 | Vite, React, Recharts 실제 번들 생성 |
| Python 테스트 | 13개 통과 | 중복, JST, 가격 단위/지역/출처 격리, 동일일 멱등성, 잘못된 가격·URL, 피드 스키마, ECB 교차환율, CSV 추출, 실패 보존, 장기 이력 |
| JS 테스트 | 3개 통과 | 카테고리·제조사·검색·날짜 조합, CSV 인젝션/인용, 추이 날짜·단위 필터 |
| React 실제 데이터 렌더링 | 통과 | 서버 렌더링. 제목·원문 링크·상태 UI 확인 |
| 실제 ECB 요청 | 성공 | 공식 XML 2026-10-13 기준 환율. USD/JPY, CNY/JPY |
| 실제 METI 요청 | 실패 | robots.txt 403. 우회 없음, 기존 데이터 유지 |
| 초기 원문 링크 | 웹 조회 확인 | pv magazine 3건, EnergyTrend 2건, 환경성 1건 |
| pandas 품질 집계 | 통과 | 5개 개별 시계열 관측 수·기준일 집계 |
| Windows/Android 브라우저 | 미검증 | 반응형 구현. 현재 환경의 허용된 브라우저 QA 도구 부재 |
| GitHub Actions 실제 실행 | 미검증 | 저장소 생성 및 쓰기 권한 확인. Actions/Pages 실행 검증 대기. 워크플로 코드만 준비 |
| GitHub Pages 실배포 | 미검증 | 저장소 생성 및 쓰기 권한 확인. Actions/Pages 실행 검증 대기 |
| 예약 자동 실행 | 미검증 | UTC 23:10 예약식 및 workflow_dispatch 구현. 실제 예약 트리거 미실행 |

빌드의 번들 크기 경고는 실패가 아닙니다. 현재 React/Recharts 번들은 약 603KB(압축 약 182KB)입니다.
샘플 관측치로 가격 추이선을 만들지 않았습니다. 30일 차트는 동일 시계열의 기준일이 두 개 이상 축적되어야 표시됩니다.

Sites 실제 배포는 성공했습니다: https://solar-market-intelligence-japan.bglee119.chatgpt.site
공개 저장소 https://github.com/bglee119/solar-market-intelligence 생성 및 쓰기 권한을 확인했습니다. Sites 게시 성공을 GitHub Pages 또는 예약 수집 성공으로 간주하지 않습니다.
