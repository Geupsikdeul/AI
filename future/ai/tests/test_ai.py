import json
from datetime import date

import anthropic
import httpx2
import pytest
from fastapi.testclient import TestClient

from app import database as db
from app.main import app

from future.ai.candidates import rank_candidates
from future.ai.llm import AIError
from future.ai.menu_draft import AIDraft, AIMeal, CatalogMenu, generate_menu_draft, service_slots, validate_draft
from future.ai.recommendation import allergen_counts, recommend_poll_menus
from future.ai.wish_analysis import Wish, WishGroup, analyze_wishes

MONDAY = date(2026, 11, 9)


def menu_catalog():
    rows = [
        ("B1", "breakfast", "소고기 미역국", ["달걀"]),
        ("B2", "breakfast", "따끈한 누룽지", ["대두"]),
        ("B3", "breakfast", "프렌치토스트", ["밀"]),
        ("B4", "breakfast", "전복죽", ["대두"]),
        ("D1", "dinner", "치킨마요 덮밥", ["닭고기"]),
        ("D2", "dinner", "바질 크림 파스타", ["밀"]),
        ("D3", "dinner", "제육볶음", ["돼지고기"]),
        ("D4", "dinner", "마파두부 덮밥", ["대두"]),
        ("P21", "dinner", "경양식 돈까스", None),
        ("P22", "dinner", "불향 제육볶음", None),
    ]
    return [
        CatalogMenu(id=menu_id, meal_type=meal_type, main=main, details="", allergens=allergens)
        for menu_id, meal_type, main, allergens in rows
    ]


def fake_client(payload=None, status=200, stop_reason="end_turn", seen=None):
    def handler(request):
        if seen is not None:
            seen.append(json.loads(request.content))
        if status != 200:
            return httpx2.Response(status, json={"type": "error", "error": {"type": "api_error", "message": "x"}})
        return httpx2.Response(
            200,
            json={
                "id": "msg_1",
                "type": "message",
                "role": "assistant",
                "model": "claude-haiku-5-5",
                "content": [{"type": "text", "text": json.dumps(payload, ensure_ascii=False)}],
                "stop_reason": stop_reason,
                "stop_sequence": None,
                "usage": {"input_tokens": 1, "output_tokens": 1},
            },
        )

    return anthropic.Anthropic(
        api_key="test",
        max_retries=0,
        http_client=anthropic.DefaultHttpxClient(transport=httpx2.MockTransport(handler)),
    )


def wishes():
    return [
        Wish(id=1, menu_name="마라탕", reason="맛있어요", likes=10),
        Wish(id=2, menu_name="마라 탕", reason="매운 게 좋아요", likes=5),
        Wish(id=3, menu_name="떡볶이", reason="시험 끝나고", likes=7),
    ]


def group(name, category, likes, count=1, menus=None):
    return WishGroup(
        name=name, category=category, summary="", wish_ids=list(range(count)),
        menu_names=menus or [name], wish_count=count, total_likes=likes,
    )


def test_analysis_recomputes_numbers_and_keeps_every_wish():
    seen = []
    payload = {
        "groups": [
            {"name": "마라탕", "category": "중식", "wish_ids": [1, 2, 2, 99], "summary": "매운 음식 선호"},
        ],
        "overall_summary": "매운 메뉴 요청이 많습니다.",
    }
    result = analyze_wishes(wishes(), client=fake_client(payload, seen=seen))

    assert seen[0]["model"] == "claude-haiku-5-5"
    assert seen[0]["output_config"]["format"]["type"] == "json_schema"
    assert "author" not in seen[0]["messages"][0]["content"]
    assert [(g.name, g.wish_ids, g.total_likes) for g in result.groups] == [
        ("마라탕", [1, 2], 15),
        ("떡볶이", [3], 7),
    ]


def test_analysis_without_wishes_skips_api():
    result = analyze_wishes([], client=fake_client(status=500))
    assert result.groups == []


@pytest.mark.parametrize(
    ("kwargs", "code"),
    [
        ({"status": 401}, "AI_NOT_CONFIGURED"),
        ({"status": 429}, "AI_RATE_LIMITED"),
        ({"status": 500}, "AI_UPSTREAM_ERROR"),
        ({"payload": {"groups": [], "overall_summary": ""}, "stop_reason": "refusal"}, "AI_REFUSED"),
        ({"payload": {"groups": [], "overall_summary": ""}, "stop_reason": "max_tokens"}, "AI_OUTPUT_TRUNCATED"),
    ],
)
def test_api_failures_become_ai_errors(kwargs, code):
    with pytest.raises(AIError) as error:
        analyze_wishes(wishes(), client=fake_client(**kwargs))
    assert error.value.code == code


def test_missing_api_key_is_reported(monkeypatch, tmp_path):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    monkeypatch.delenv("ANTHROPIC_AUTH_TOKEN", raising=False)
    monkeypatch.setenv("ANTHROPIC_CONFIG_DIR", str(tmp_path))
    with pytest.raises(AIError) as error:
        analyze_wishes(wishes())
    assert error.value.code == "AI_NOT_CONFIGURED"


def test_rank_prefers_likes_and_penalizes_recent_menu():
    result = rank_candidates(
        [group("제육볶음", "한식", 100), group("마라탕", "중식", 80)],
        ["불향 제육볶음"],
    )
    assert [item.name for item in result] == ["마라탕", "제육볶음"]
    assert result[1].recently_served is True


def test_rank_keeps_category_variety():
    result = rank_candidates(
        [group("비빔밥", "한식", 100), group("불고기", "한식", 90), group("파스타", "양식", 10)],
        [],
        limit=2,
    )
    assert {item.name for item in result} == {"비빔밥", "파스타"}


def full_draft(days=5):
    meals = []
    for index, (day, meal_type) in enumerate(service_slots(MONDAY, days)):
        prefix = "B" if meal_type == "breakfast" else "D"
        meals.append(AIMeal(service_date=day, meal_type=meal_type, menu_id=f"{prefix}{index // 2 % 4 + 1}"))
    return AIDraft(meals=meals, notes="")


def test_slots_skip_weekend():
    assert len(service_slots(MONDAY, 7)) == 10


def test_valid_draft_uses_catalog_allergens():
    catalog = menu_catalog()
    ai_draft = full_draft()
    result = validate_draft(ai_draft, service_slots(MONDAY, 5), catalog, [])
    assert result.violations == []
    expected = {menu.id: menu.allergens for menu in catalog}
    assert all(meal.allergens == expected[meal.menu_id] for meal in result.meals)


def test_draft_rules_are_reported():
    draft = full_draft()
    draft.meals[2].menu_id = draft.meals[0].menu_id
    draft.meals[1].menu_id = "없는메뉴"
    result = validate_draft(draft, service_slots(MONDAY, 5), menu_catalog(), ["D4"])
    text = "\n".join(result.violations)
    assert "없는메뉴" in text
    assert "반복" in text
    assert "메뉴가 비어" in text


def test_poll_menu_is_flagged_without_allergen_info():
    draft = full_draft()
    draft.meals[1].menu_id = "P21"
    result = validate_draft(draft, service_slots(MONDAY, 5), menu_catalog(), ["P21"])
    assert any("알레르기 정보" in item for item in result.violations)
    assert result.meals[1].allergens_confirmed is False


def test_draft_prompt_hides_allergens_and_runs():
    seen = []
    client = fake_client(full_draft().model_dump(), seen=seen)
    result = generate_menu_draft(MONDAY, 5, menu_catalog(), client=client)
    assert "allergens" not in seen[0]["messages"][0]["content"]
    assert len(result.meals) == 10


def test_unrequested_menu_without_allergens_is_not_offered():
    seen = []
    draft = full_draft()
    draft.meals[1].menu_id = "P22"
    client = fake_client(draft.model_dump(), seen=seen)
    result = generate_menu_draft(MONDAY, 5, menu_catalog(), ["P21"], client=client)
    prompt = seen[0]["messages"][0]["content"]
    assert "P21" in prompt
    assert "P22" not in prompt
    assert any("P22" in item for item in result.violations)


def test_same_food_with_different_ids_is_reported():
    draft = full_draft()
    draft.meals[1].menu_id = "D3"
    draft.meals[3].menu_id = "P22"
    result = validate_draft(draft, service_slots(MONDAY, 5), menu_catalog(), [])
    assert any("불향 제육볶음" in item and "반복" in item for item in result.violations)


def test_notes_use_menu_names_instead_of_ids():
    draft = full_draft()
    draft.notes = "필수 메뉴 P21은 수요일에 넣었습니다."
    result = validate_draft(draft, service_slots(MONDAY, 5), menu_catalog(), [])
    assert result.notes == "필수 메뉴 경양식 돈까스은 수요일에 넣었습니다."


def recommendation(name, allergens, based_on):
    return {
        "name": name, "category": "중식", "description": "설명",
        "estimated_allergens": allergens, "based_on_groups": based_on, "reason": "이유",
    }


def test_small_allergy_groups_are_not_shared():
    students = [["달걀"]] * 5 + [["땅콩"]] * 4
    assert allergen_counts(students) == {"달걀": 5}


def test_recommendation_sends_only_aggregates_and_scores_with_code():
    seen = []
    payload = {
        "recommendations": [
            recommendation("순한 마라 볶음", ["대두"], ["마라탕"]),
            recommendation("치즈 떡볶이", ["우유", "밀"], ["떡볶이"]),
            recommendation("근거 없는 메뉴", [], ["없는 그룹"]),
            recommendation("돈까스", [], ["마라탕"]),
        ]
    }
    groups = [group("마라탕", "중식", 100), group("떡볶이", "분식", 80)]
    students = [["우유", "달걀"]] * 6 + [["대두"]] * 2 + [[]] * 2
    result = recommend_poll_menus(groups, students, ["경양식 돈까스"], client=fake_client(payload, seen=seen))

    prompt = seen[0]["messages"][0]["content"]
    assert '"우유": 6' in prompt
    assert "대두" not in prompt.split("</allergy_stats>")[0]
    assert [item.name for item in result.recommendations] == ["순한 마라 볶음", "치즈 떡볶이"]
    first, second = result.recommendations
    assert (first.safe_ratio, first.score) == (0.8, 0.8)
    assert (second.safe_ratio, second.score) == (0.4, 0.32)
    assert first.allergens_confirmed is False
    assert result.students_counted == 10


def test_recommendation_without_groups_skips_api():
    result = recommend_poll_menus([], [["달걀"]], [], client=fake_client(status=500))
    assert result.recommendations == []


@pytest.fixture
def api(tmp_path, monkeypatch):
    monkeypatch.setattr(db, "DB_PATH", tmp_path / "test.db")
    monkeypatch.setenv("AI_ADMIN_TOKEN", "secret")
    with TestClient(app) as client:
        yield client


def test_admin_token_is_required(api, monkeypatch):
    assert api.post("/api/v1/admin/ai/wish-analysis").status_code == 401
    assert api.post("/api/v1/admin/ai/wish-analysis", headers={"X-Admin-Token": "bad"}).status_code == 401
    monkeypatch.delenv("AI_ADMIN_TOKEN")
    assert api.post("/api/v1/admin/ai/wish-analysis", headers={"X-Admin-Token": "secret"}).status_code == 503


def test_poll_candidates_route(api, monkeypatch):
    payload = {
        "groups": [{"name": "마라탕", "category": "중식", "wish_ids": [1], "summary": "요약"}],
        "overall_summary": "전체",
    }
    client = fake_client(payload)
    monkeypatch.setattr("future.ai.llm.anthropic.Anthropic", lambda **_: client)
    response = api.post("/api/v1/admin/ai/poll-candidates", headers={"X-Admin-Token": "secret"})
    assert response.status_code == 200
    assert response.json()["candidates"][0]["name"] == "마라탕"


def test_recommendation_route_reads_all_profiles(api, monkeypatch):
    captured = {}

    def fake_recommend(groups, students, existing):
        captured["students"] = students
        return recommend_poll_menus([], students, existing)

    analysis = analyze_wishes([])
    monkeypatch.setattr("future.ai.router.analyze_wishes", lambda _: analysis)
    monkeypatch.setattr("future.ai.router.recommend_poll_menus", fake_recommend)
    db.set_allergies(1, ["달걀"])
    response = api.post("/api/v1/admin/ai/poll-recommendations", headers={"X-Admin-Token": "secret"})
    assert response.status_code == 200
    assert captured["students"] == [["달걀"]]


def test_menu_draft_rejects_unknown_menu(api):
    response = api.post(
        "/api/v1/admin/ai/menu-draft",
        headers={"X-Admin-Token": "secret"},
        json={"start_date": "2026-11-09", "must_include": ["없는메뉴"]},
    )
    assert response.status_code == 400
