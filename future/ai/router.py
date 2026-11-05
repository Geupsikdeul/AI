from __future__ import annotations

import json
import os
import secrets
from datetime import date, timedelta

from fastapi import APIRouter, Depends, Header, HTTPException
from pydantic import BaseModel, Field

from app import database as db
from app.demo_data import POLL, calendar_items

from .candidates import rank_candidates
from .catalog import menu_catalog
from .llm import AIError
from .menu_draft import generate_menu_draft
from .recommendation import recommend_poll_menus
from .wish_analysis import Wish, WishAnalysis, analyze_wishes


def api_error(status: int, code: str, message: str) -> HTTPException:
    return HTTPException(status_code=status, detail={"error": {"code": code, "message": message, "detail": None}})


def require_admin(x_admin_token: str | None = Header(default=None)) -> None:
    expected = os.getenv("AI_ADMIN_TOKEN")
    if not expected:
        raise api_error(503, "AI_NOT_CONFIGURED", "AI_ADMIN_TOKEN이 설정되지 않았습니다.")
    if not x_admin_token or not secrets.compare_digest(x_admin_token.encode(), expected.encode()):
        raise api_error(401, "AI_UNAUTHORIZED", "관리자 토큰을 확인해 주세요.")


router = APIRouter(prefix="/api/v1/admin/ai", tags=["ai"], dependencies=[Depends(require_admin)])


class MenuDraftRequest(BaseModel):
    start_date: date
    days: int = Field(default=14, ge=1, le=14)
    must_include: list[str] = Field(default_factory=list, max_length=10)


def run_wish_analysis() -> WishAnalysis:
    rows = db.rows("SELECT id, menu_name, reason, likes FROM wishes")
    try:
        return analyze_wishes([Wish(**row) for row in rows])
    except AIError as exc:
        raise api_error(exc.status, exc.code, exc.message) from exc


@router.post("/wish-analysis")
def wish_analysis() -> dict:
    return run_wish_analysis().model_dump()


@router.post("/poll-candidates")
def poll_candidates() -> dict:
    analysis = run_wish_analysis()
    today = date.today()
    served = calendar_items(today - timedelta(days=14), today + timedelta(days=14))
    recent_menus = [day[meal]["main"] for day in served for meal in ("breakfast", "dinner") if day[meal]["available"]]
    candidates = rank_candidates(analysis.groups, recent_menus)
    return {"analysis": analysis.model_dump(), "candidates": [item.model_dump() for item in candidates]}


@router.post("/poll-recommendations")
def poll_recommendations() -> dict:
    analysis = run_wish_analysis()
    students = [json.loads(row["allergies"]) for row in db.rows("SELECT allergies FROM profiles")]
    existing = [option["menu_name"] for option in POLL["options"]]
    try:
        result = recommend_poll_menus(analysis.groups, students, existing)
    except AIError as exc:
        raise api_error(exc.status, exc.code, exc.message) from exc
    return result.model_dump()


@router.post("/menu-draft")
def menu_draft(payload: MenuDraftRequest) -> dict:
    catalog = menu_catalog()
    known = {menu.id for menu in catalog}
    unknown = [menu_id for menu_id in payload.must_include if menu_id not in known]
    if unknown:
        raise api_error(400, "UNKNOWN_MENU", f"목록에 없는 메뉴입니다: {', '.join(unknown)}")
    try:
        draft = generate_menu_draft(payload.start_date, payload.days, catalog, payload.must_include)
    except AIError as exc:
        raise api_error(exc.status, exc.code, exc.message) from exc
    return draft.model_dump()
