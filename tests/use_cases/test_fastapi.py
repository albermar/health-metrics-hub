# parse http query params into python values
# dependency injection (DI) creates DB session
# orchestrate: build repo + use case + call use case (composition root)
# map domain -> pydantic (API DTO) response


#we should avoid calling postgres directly

from __future__ import annotations

from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.routers.kpis import router, get_output_repo
from app.domain.entities import DailyKPIsOutput


class FakeOutputRepo:
    def __init__(self, rows: list[DailyKPIsOutput]):
        self._rows = rows
        self.calls: list[tuple[datetime, datetime]] = []

    def get_output(self, start: datetime, end: datetime) -> list[DailyKPIsOutput]:
        self.calls.append((start, end))
        return self._rows


def make_client_with_repo(fake_repo: FakeOutputRepo) -> TestClient:
    app = FastAPI()
    app.include_router(router)

    # FastAPI-native override: swap the real repo provider for our fake
    app.dependency_overrides[get_output_repo] = lambda: fake_repo

    return TestClient(app)


def test_kpis_happy_path_returns_200_and_json_list():
    rows = [
        DailyKPIsOutput(
            date=datetime(2024, 1, 1, tzinfo=timezone.utc),
            kcal_out_total=2500,
            balance_kcal=-200,
            balance_7d_average=None,
            protein_per_kg=1.6,
            healthy_food_pct=0.8,
            adherence_steps=1.0,
            weight_7d_avg=None,
            waist_change_7d=None,
        )
    ]
    fake_repo = FakeOutputRepo(rows=rows)
    client = make_client_with_repo(fake_repo)

    resp = client.get("/kpis/", params={"start_date": "2024-01-01", "end_date": "2024-01-07"})

    assert resp.status_code == 200
    data = resp.json()
    assert isinstance(data, list)
    assert len(data) == 1

    # Check a couple fields (DTO mapping)
    assert "date" in data[0]
    assert data[0]["kcal_out_total"] == 2500
    assert data[0]["balance_kcal"] == -200

    # Repo called exactly once with parsed datetimes
    assert len(fake_repo.calls) == 1


def test_kpis_start_after_end_returns_400_and_repo_not_called():
    fake_repo = FakeOutputRepo(rows=[])
    client = make_client_with_repo(fake_repo)

    resp = client.get("/kpis/", params={"start_date": "2024-01-10", "end_date": "2024-01-09"})

    assert resp.status_code == 400
    assert "Start date must be before end date." in resp.json()["detail"]

    # Business rule triggers before hitting repo
    assert fake_repo.calls == []
