class FakeOutputRepo:
    def __init__(self, result):
        self.result = result
        self.calls = []

    def get_output(self, start, end):
        self.calls.append((start, end))
        return self.result


import pytest
from datetime import datetime, timezone

from app.business.use_cases import GetKPIs


def test_get_kpis_raises_when_start_after_end():
    repo = FakeOutputRepo(result=[])

    use_case = GetKPIs(output_repo=repo)

    start = datetime(2024, 1, 10, tzinfo=timezone.utc)
    end = datetime(2024, 1, 9, tzinfo=timezone.utc)

    with pytest.raises(ValueError) as exc:
        use_case.execute(start=start, end=end)

    assert "Start date must be before end date." in str(exc.value)
    assert repo.calls == []  # must not call repo on invalid input


from datetime import datetime, timezone

from app.business.use_cases import GetKPIs
from app.domain.entities import DailyKPIsOutput


def test_get_kpis_calls_repo_and_returns_rows():
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
    repo = FakeOutputRepo(result=rows)
    use_case = GetKPIs(output_repo=repo)

    start = datetime(2024, 1, 1, tzinfo=timezone.utc)
    end = datetime(2024, 1, 7, tzinfo=timezone.utc)

    result = use_case.execute(start=start, end=end)

    assert result == rows
    assert repo.calls == [(start, end)]


from datetime import datetime, timezone

from app.business.use_cases import GetKPIs


def test_get_kpis_allows_same_day_range():
    repo = FakeOutputRepo(result=[])
    use_case = GetKPIs(output_repo=repo)

    day = datetime(2024, 1, 5, tzinfo=timezone.utc)

    result = use_case.execute(start=day, end=day)

    assert result == []
    assert repo.calls == [(day, day)]
