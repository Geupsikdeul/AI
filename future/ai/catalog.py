from __future__ import annotations

from app.demo_data import BREAKFAST_MENUS, DINNER_MENUS, POLL

from .menu_draft import CatalogMenu


def menu_catalog() -> list[CatalogMenu]:
    menus = [
        CatalogMenu(id=f"{prefix}{index}", meal_type=meal_type, main=main, details=details, allergens=allergens)
        for prefix, meal_type, source in (("B", "breakfast", BREAKFAST_MENUS), ("D", "dinner", DINNER_MENUS))
        for index, (main, details, allergens) in enumerate(source, start=1)
    ]
    menus += [
        CatalogMenu(id=f"P{option['id']}", meal_type="dinner", main=option["menu_name"], details=option["description"], allergens=None)
        for option in POLL["options"]
    ]
    return menus
