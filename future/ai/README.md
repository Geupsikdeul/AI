# 급식들 AI

희망 메뉴 분석, 투표 후보 선정, 새 메뉴 추천, 식단 초안 생성 함수를 제공합니다. 기본 모델은 `claude-haiku-5-5`이고 `AI_MODEL`로 바꿀 수 있습니다.

이 저장소는 [급식들 본체](https://github.com/Geupsikdeul/main)의 AI 코드입니다. `router.py`, `catalog.py`, 테스트는 본체의 `app` 패키지를 사용하므로 본체의 `future/ai/` 위치에 넣어 실행합니다.

본체의 `app/main.py`에 아래를 추가하면 API가 연결됩니다.

```python
from future.ai.router import router as ai_router
app.include_router(ai_router)
```

## 설정

```bash
pip install -r future/ai/requirements.txt
cp future/ai/.env.example future/ai/.env
```

`future/ai/.env`에 `ANTHROPIC_API_KEY`와 `AI_ADMIN_TOKEN`을 넣습니다. 이 파일은 git에 올라가지 않습니다.

## 함수

| 함수 | 입력 | 기능 |
|---|---|---|
| `wish_analysis.analyze_wishes` | 희망 메뉴 목록 | 메뉴 묶기와 요약 |
| `candidates.rank_candidates` | 분석 그룹, 최근 메뉴 | 투표 후보 선정 |
| `recommendation.recommend_poll_menus` | 분석 그룹, 학생별 알레르기, 기존 투표 메뉴 | 투표에 추가할 새 메뉴 추천 |
| `menu_draft.generate_menu_draft` | 시작일, 일수, 메뉴 목록, 필수 메뉴 | 식단 초안 생성과 규칙 검사 |

## API

서버에 연결되어 있고, 모든 요청에 `X-Admin-Token` 헤더가 필요합니다.

| API | 기능 |
|---|---|
| `POST /api/v1/admin/ai/wish-analysis` | 희망 메뉴 묶기와 요약 |
| `POST /api/v1/admin/ai/poll-candidates` | 희망 메뉴 분석 후 투표 후보 선정 |
| `POST /api/v1/admin/ai/poll-recommendations` | 희망 메뉴와 알레르기 집계로 새 메뉴 추천 |
| `POST /api/v1/admin/ai/menu-draft` | 날짜별 식단 초안 생성과 규칙 검사 |

식단 초안 요청 본문 예시는 `{"start_date": "2026-11-09", "days": 14, "must_include": ["P21"]}`입니다.

## 테스트

```bash
python -m pytest future/ai/tests
```
