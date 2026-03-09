from __future__ import annotations

from fastapi.testclient import TestClient
import sys
from pathlib import Path

# Добавляем директорию calc_service в sys.path, чтобы можно было импортировать main.
_calc_service = Path(__file__).resolve().parent.parent
if _calc_service.name == "calc_service" and str(_calc_service) not in sys.path:
    sys.path.insert(0, str(_calc_service))

from main import app


client = TestClient(app)


def test_param_schema_endpoint() -> None:
    """Все калькуляторы возвращают param_schema."""
    response = client.get("/api/v1/calculators")
    assert response.status_code == 200

    calculators = response.json()
    assert isinstance(calculators, list)
    assert calculators

    for calc in calculators:
        slug = calc["slug"]

        resp = client.get(f"/api/v1/param_schema/{slug}")
        assert resp.status_code == 200

        schema = resp.json()
        assert schema["slug"] == slug
        assert "params" in schema
        assert isinstance(schema["params"], list)
        assert len(schema["params"]) > 0

