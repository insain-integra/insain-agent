"""
FastAPI-сервис калькуляторов.

Эндпоинты: список калькуляторов, расчёт по slug, опции для формы.
CORS для insain.ru. Ошибки: 404 (неизвестный slug), 400 (ValueError), 500.
"""

from __future__ import annotations

import logging
import sys
from typing import Any, Dict

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from calculators import CALCULATORS, get_calculator

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


@app.post("/api/v1/calc/{slug}")
def calc(slug: str, body: Dict[str, Any]) -> Dict[str, Any]:
    """Расчёт: JSON body с параметрами, возврат результата (cost, price, time_hours, ...)."""
    calculator = get_calculator(slug)  # KeyError → 404
    return calculator.execute(body)  # ValueError → 400


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
