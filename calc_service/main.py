"""
FastAPI-сервис калькуляторов.

Эндпоинты: список калькуляторов, расчёт по slug, опции для формы.
CORS для insain.ru. Ошибки: 404 (неизвестный slug), 400 (ValueError), 500.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from calculators import CALCULATORS, get_calculator
from materials import ALL_MATERIALS, MaterialCatalog, MaterialSpec

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
    stream=sys.stdout,
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Калькуляторы Insain",
    description="API расчёта стоимости продукции (печать, резка, ламинация и др.)",
    version="1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://insain.ru", "http://insain.ru"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Логирование запросов в stdout."""
    logger.info("%s %s", request.method, request.url.path)
    response = await call_next(request)
    return response


@app.get("/api/v1/calculators")
def list_calculators() -> list[Dict[str, str]]:
    """Список калькуляторов: slug, name, description."""
    return [
        {
            "slug": calc.slug,
            "name": calc.name,
            "description": calc.description,
        }
        for calc in CALCULATORS.values()
    ]


@app.get("/api/v1/options/{slug}")
def get_options(slug: str) -> Dict[str, Any]:
    """Опции для формы калькулятора (материалы, режимы и т.д.)."""
    calc = get_calculator(slug)  # KeyError → 404
    return calc.get_options()


@app.get("/api/v1/param_schema/{slug}")
def get_param_schema(slug: str) -> Dict[str, Any]:
    """
    Детальная схема параметров калькулятора для агента / фронтенда.

    Возвращает структуру с описанием параметров (обязательность, дефолты, источники).
    """
    calc = get_calculator(slug)  # KeyError → 404
    return calc.get_param_schema()


@app.get("/api/v1/tool_schema/{slug}")
def get_tool_schema(slug: str) -> Dict[str, Any]:
    """Схема инструмента для function calling (name, description, parameters)."""
    calc = get_calculator(slug)  # KeyError → 404
    return calc.get_tool_schema()


@app.post("/api/v1/calc/{slug}")
def calc(slug: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Расчёт: JSON body с параметрами, возврат результата (cost, price, time_hours, ...)."""
    calculator = get_calculator(slug)  # KeyError → 404
    return calculator.execute(body)  # ValueError → 400


class ChoicesRequest(BaseModel):
    slug: str                    # калькулятор
    param: str                   # имя параметра
    query: Optional[str] = None  # поисковый запрос
    filters: Optional[Dict[str, Any]] = None  # дополнительные фильтры
    limit: int = 10


class ChoiceItem(BaseModel):
    id: str
    title: str
    description: str
    hint: Optional[str] = None


@app.post("/api/v1/choices")
def search_choices(request: ChoicesRequest) -> Dict[str, List[ChoiceItem]]:
    """
    Поиск вариантов для параметра.

    Примеры:
        {"slug": "laser", "param": "material", "query": "акрил 3"}
        → вернёт AcrylWhite3, AcrylTrans3
    """
    logger.info(
        "choices search: slug=%s param=%s query=%r filters=%r limit=%s",
        request.slug,
        request.param,
        request.query,
        request.filters,
        request.limit,
    )

    calc = get_calculator(request.slug)  # KeyError → 404

    # Получить param_schema и описание параметра
    param_schema = calc.get_param_schema()
    params: List[Dict[str, Any]] = param_schema.get("params") or []
    param_def = next((p for p in params if p.get("name") == request.param), None)

    if not param_def:
        raise HTTPException(status_code=404, detail=f"Parameter not found: {request.param}")

    choices_config: Dict[str, Any] = param_def.get("choices") or {}

    if "inline" in choices_config:
        # Статические choices (например, режимы производства).
        items_raw: List[Dict[str, Any]] = choices_config["inline"]
    elif "source" in choices_config:
        source = str(choices_config["source"])
        items_raw = _resolve_choices_source(source, request.query, request.filters)
    else:
        raise HTTPException(status_code=400, detail="No choices defined for this parameter")

    # Фильтр по query по title и description (поиск по токенам).
    if request.query:
        # Разбиваем запрос на токены по пробелам и ищем каждый токен
        # сперва только в title, затем (если пусто) в title+description.
        tokens = [t for t in request.query.lower().split() if t]
        filtered_title: List[Dict[str, Any]] = []
        filtered_all: List[Dict[str, Any]] = []
        for item in items_raw:
            title = str(item.get("title") or "").lower()
            desc = str(item.get("description") or "").lower()
            if not tokens:
                continue
            if all(token in title for token in tokens):
                filtered_title.append(item)
            haystack = f"{title} {desc}"
            if all(token in haystack for token in tokens):
                filtered_all.append(item)
        # Если есть точные совпадения только по title — используем их,
        # иначе fallback к более широкому совпадению по title+description.
        items_raw = filtered_title or filtered_all

    # Лимит
    items_raw = items_raw[: max(1, request.limit)]

    items: List[ChoiceItem] = []
    for item in items_raw:
        # Унификация полей: id / title / description / hint
        item_id = str(item.get("id") or item.get("code") or item.get("value") or "")
        if not item_id:
            continue
        title = str(item.get("title") or item.get("name") or item_id)
        description = str(item.get("description") or "")
        hint = item.get("hint")
        if hint is None and "thickness" in item and item.get("thickness") is not None:
            try:
                hint = f"{float(item['thickness'])} мм"
            except Exception:
                hint = None
        items.append(ChoiceItem(id=item_id, title=title, description=description, hint=hint))

    return {"items": items}


def _resolve_choices_source(
    source: str,
    query: Optional[str],
    filters: Optional[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Резолвинг source в список вариантов.

    Поддерживаемые источники:
    - "materials:hardsheet" → все материалы из каталога hardsheet
    - "materials:sheet"     → материалы из sheet
    - "materials:laminat"   → плёнки ламинации и т.п.
    - "materials:misc#Attachment" → секция Attachment из misc (category)
    """
    if source.startswith("materials:"):
        catalog_name = source.split(":", 1)[1]
        section: Optional[str] = None
        if "#" in catalog_name:
            catalog_name, section = catalog_name.split("#", 1)

        catalog: Optional[MaterialCatalog] = ALL_MATERIALS.get(catalog_name)
        if not catalog:
            raise HTTPException(status_code=400, detail=f"Unknown material catalog: {catalog_name}")

        all_materials: Dict[str, MaterialSpec] = catalog.list_all()
        materials: List[MaterialSpec] = list(all_materials.values())

        # Фильтрация по "секции", если указана: используем поле category.
        if section:
            materials = [m for m in materials if getattr(m, "category", None) == section]

        # Дополнительные фильтры (например, max_thickness_mm).
        if filters:
            max_thickness = filters.get("max_thickness_mm")
            if max_thickness is not None:
                try:
                    limit = float(max_thickness)
                    materials = [
                        m
                        for m in materials
                        if m.thickness is not None and m.thickness <= limit
                    ]
                except Exception:
                    pass

        return [
            {
                "id": m.code,
                "title": m.title,
                "description": m.description,
                "hint": f"{m.thickness} мм" if m.thickness is not None else None,
                "thickness": m.thickness,
            }
            for m in materials
        ]

    # Заглушка для будущих типов источников (например, presswall:variants).
    raise HTTPException(status_code=400, detail=f"Unknown source: {source}")


@app.exception_handler(ValueError)
def value_error_handler(request: Request, exc: ValueError):
    """Ошибка расчёта или неизвестный slug → 400."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=400,
        content={"detail": str(exc)},
    )


@app.exception_handler(KeyError)
def key_error_handler(request: Request, exc: KeyError):
    """Неизвестный slug → 404."""
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc)},
    )


@app.exception_handler(Exception)
def generic_exception_handler(request: Request, exc: Exception):
    """Любая другая ошибка → 500."""
    import traceback
    logger.exception("Unhandled error: %s", exc)
    from fastapi.responses import JSONResponse
    return JSONResponse(
        status_code=500,
        content={"detail": "Внутренняя ошибка сервера"},
    )
