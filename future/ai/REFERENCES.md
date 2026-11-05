# 급식들 AI 개발 참고 자료

확인일: 2026-11-05

상태 표시
- `원문 확인`: 해당 페이지를 직접 열어 내용을 확인함
- `검색 요약`: 검색 결과 요약으로만 확인함. 값을 쓰기 전에 원문 확인 필요

## 1. AI 도입 방식 (로컬 vs API)

결정: Claude API (Claude Haiku 5.5) 사용, 2026-11-05 확정

개발 환경: Apple M4 Pro, RAM 24GB, 디스크 여유 516GB. Ollama 미설치, `ANTHROPIC_API_KEY` 없음.

1회 비용은 입력 5,000토큰, 출력 2,000토큰 기준입니다.

| 선택지 | 입력 / 출력 ($/MTok) | 1회 비용 | 무료 사용 | 데이터 학습 | 연령 조건 |
|---|---|---|---|---|---|
| 로컬: Ollama + EXAONE 3.5 7.8B | 없음 | $0 | 계속 무료 | 외부 전송 없음 | 라이선스에 연령 조건 없음. 연구 목적, 상업 이용 금지 |
| Groq: `openai/gpt-oss-20b` | 0.075 / 0.30 | $0.000975 | Free 플랜 있음, 한도 미확인 | 기본 미사용 | 만 18세 이상 |
| Upstage: Solar Mini 4 | 0.10 / 0.40 (VAT 별도) | $0.0013 | 가입 크레딧 $10 | 유료 미사용, 무료 사용분은 학습 가능 (요약본으로 확인) | 만 18세 미만 가입 불가 |
| Anthropic: Claude Haiku 5.5 | 0.10 / 0.50 | $0.0015 | 미확인 | 기본 미사용 | 계정 최소 연령 미확인 |
| Google: `gemini-3.1-flash-lite` | 0.25 / 1.50 | $0.00425 | 있음, 입력 데이터가 제품 개선에 쓰이고 사람이 검토 가능 | 무료는 사용, 유료는 미사용 | 만 18세 이상, 미성년자가 이용할 가능성이 높은 서비스 금지 |


| 자료 | 내용 | 상태 |
|---|---|---|
| [Claude Pricing](https://platform.claude.com/docs/en/about-claude/pricing) | Haiku 5.5: 입력 $0.10, 출력 $0.50 / MTok (100K 토큰 이하). Sonnet 5.5: 입력 $2, 출력 $10 / MTok. Batch API 50% 할인 | 원문 확인 |
| [Claude Models overview](https://platform.claude.com/docs/en/models/overview) | 모델 ID `claude-haiku-5-5`, `claude-sonnet-5-5`. 컨텍스트 1M 토큰, 최대 출력 128K 토큰 | 원문 확인 |
| [Anthropic 학습 사용 정책](https://privacy.claude.com/en/articles/7996885-how-do-you-use-personal-data-in-model-training) | API 입력은 기본적으로 모델 학습에 쓰지 않음. 피드백 제출이나 옵트인은 예외 | 원문 확인 |
| [Anthropic 데이터 보관 정책](https://privacy.claude.com/en/articles/7996866-how-long-do-you-store-my-organization-s-data) | API 입출력은 30일 내 자동 삭제. 정책 위반, 법령 준수 등은 예외 | 원문 확인 |
| [미성년자 대상 서비스 지침](https://support.claude.com/en/articles/9307344-responsible-use-of-anthropic-s-models-guidelines-for-organizations-serving-minors) | 미성년자가 API 제품과 직접 상호작용하면 연령 확인, 콘텐츠 필터링, 모니터링, AI 고지 등이 필요. API 계정 최소 연령은 이 페이지에 없음 | 원문 확인 |
| [EXAONE 3.5 라이선스](https://huggingface.co/LGAI-EXAONE/EXAONE-3.5-7.8B-Instruct/blob/main/LICENSE) | 연구 목적만 허용(평가, 학술 연구, 비상업 대회 포함), 상업 이용 금지. 결과 발표 시 모델명과 버전 표기 필수. 수업 과제와 무료 공개 서비스는 명시되어 있지 않음 | 원문 확인 |
| [Gemini API 가격](https://aistudio.google.com/docs/pricing) | `gemini-3.1-flash-lite` 유료 입력 $0.25, 출력 $1.50 / MTok. 무료 등급 입력은 제품 개선에 사용 | 원문 확인 |
| [Gemini API 약관](https://aistudio.google.com/docs/terms) | 만 18세 이상. 미성년자 대상이거나 미성년자가 이용할 가능성이 높은 서비스에 사용 금지. 무료 서비스에 개인정보 입력 금지 | 원문 확인 |
| [Groq 모델 목록](https://console.groq.com/docs/models) | `openai/gpt-oss-20b` 입력 $0.075, 출력 $0.30 / MTok | 원문 확인 |
| [Groq 서비스 약관](https://console.groq.com/docs/legal/services-agreement) | 만 18세 이상. 입력과 출력은 기본적으로 학습에 쓰지 않음 | 원문 확인 |
| [Upstage 가격](https://www.upstage.ai/pricing) | Solar Mini 4 입력 $0.10, 출력 $0.40 / MTok, VAT 별도 | 원문 확인 |
| [Upstage 시작 가이드](https://console.upstage.ai/docs/getting-started) | 가입 시 무료 크레딧 $10. 표시된 예제는 OpenAI Python 클라이언트 사용 | 원문 확인 |
| [Upstage 이용약관](https://www.upstage.ai/terms-of-service) | 만 18세 미만 가입 불가, 만 14세 이상은 LMS 서비스만 가능 | 원문 확인 |
| [Ollama exaone3.5](https://ollama.com/library/exaone3.5) | 2.4B 1.6GB, 7.8B 4.8GB, 32B 19GB, 컨텍스트 32K | 원문 확인 |
| [Ollama GitHub](https://github.com/ollama/ollama) | MIT 라이선스. README에 모델 크기별 RAM 안내 없음 | 원문 확인 |

## 2. 희망 메뉴 분석

| 자료 | 내용 | 상태 |
|---|---|---|
| [ko-sroberta-multitask](https://huggingface.co/jhgan/ko-sroberta-multitask) | 한국어 문장 임베딩, 768차원, 최대 128토큰, KorSTS Spearman 85.60. 라이선스 표기를 찾지 못함 | 원문 확인 |
| [BGE-M3](https://huggingface.co/BAAI/bge-m3) | MIT 라이선스, 1024차원, 100개 이상 언어 지원. 페이지에서 한국어를 따로 명시하지는 않음 | 원문 확인 |
| [Sentence Transformers Clustering](https://sbert.net/examples/sentence_transformer/applications/clustering/README.html) | k-Means, Agglomerative, Fast Clustering, Topic Modeling 소개. 앞의 세 방식 설명 일부는 요약본으로 확인 | 원문 확인 |
| [KoSimCSE-roberta](https://huggingface.co/BM-K/KoSimCSE-roberta) | 한국어 문장 임베딩 모델, CC BY-SA 4.0 | 검색 요약 |

## 3. 추천 후보 점수화

외부 자료 없이 이 프로젝트에 맞춰 직접 정한 공식입니다.

- 점수 = 공감 수 비율 × 0.7 + 제안 수 비율 × 0.3
- 최근 2주 식단 또는 앞으로 2주 식단과 겹치면 점수를 50% 감점
- 먼저 카테고리별 최고점 메뉴를 고르고 남은 자리를 점수순으로 채움

새 메뉴 추천의 점수도 직접 정한 공식입니다.

- 점수 = 인기도 × 먹을 수 있는 학생 비율
- 인기도 = 추천 근거 그룹의 최대 공감 수 / 전체 그룹의 최대 공감 수
- 알레르기 성분은 Claude의 추정값이라 영양사 확인이 필요함

## 4. 식단 초안 생성

| 자료 | 내용 | 상태 |
|---|---|---|
| [NEIS 급식식단정보 (공공데이터포털)](https://data.go.kr/data/15139198/openapi.do) | 교육부 제공, 무료, JSON+XML, 이용허락범위 제한 없음, 실시간 갱신, 인증키 필요 | 원문 확인 |
| 같은 페이지 | 요리명, 칼로리, 영양소, 알레르기 번호 제공 | 검색 요약 |

## 5. 개인정보와 안전

| 자료 | 내용 | 상태 |
|---|---|---|
| [학교급식법 개정 보도자료 (2013)](https://m.korea.kr/briefing/pressReleaseView.do?newsId=155896468) | 알레르기 유발 식품 사전 공지와 식단표 표시 의무화 | 검색 요약 |

## 6. 원문을 확인하지 못한 자료

아래 내용은 개발 근거로 쓰기 전에 확인이 필요합니다.

| 자료 | 필요한 내용 | 실패 이유 |
|---|---|---|
| [학교급식법 시행규칙](https://www.law.go.kr/법령/학교급식법시행규칙) | 알레르기 식품 번호 목록, 영양관리기준 | 본문이 제목만 표시됨 |
| [학교급식법](https://www.law.go.kr/법령/학교급식법) | 알레르기 관련 조항 | 본문이 제목만 표시됨 |
| [개인정보 보호법](https://www.law.go.kr/법령/개인정보보호법) | 제22조의2 아동의 개인정보 보호 | 본문이 제목만 표시됨 |
| [NEIS 급식식단정보 명세](https://open.neis.go.kr/portal/data/service/selectServicePage.do?infId=OPEN17320190722180924242823) | 요청 인자, 출력 항목, 알레르기 번호 표기 | HTTP 500 |
| [생성형 AI 개인정보 처리 안내서 소개](https://smartcity.go.kr/?p=48889) | 안내서 핵심 내용 | 안내서가 아닌 포털 메인 화면이 표시됨 |
