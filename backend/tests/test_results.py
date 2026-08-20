"""Results aggregation + privacy contract (docs/03-lld.md §3.6, §8, invariant I1)."""

from app.api.results import build_result

# Budget chip → (min, max)
UNDER_200 = (0, 200)
R200_500 = (200, 500)
R500_1000 = (500, 1000)
R2000_PLUS = (2000, 5000)

SLOTS = [
    {"id": "s1", "starts_at": "2026-09-05T17:00:00Z", "ends_at": "2026-09-05T19:00:00Z",
     "label": None, "sort_order": 0},
    {"id": "s2", "starts_at": "2026-09-05T19:00:00Z", "ends_at": "2026-09-05T21:00:00Z",
     "label": None, "sort_order": 1},
    {"id": "s3", "starts_at": "2026-09-06T11:00:00Z", "ends_at": "2026-09-06T13:00:00Z",
     "label": None, "sort_order": 2},
]


def _resp(rid, name, slots, comp, budget, contribution=0, interests=()):
    lo, hi = budget
    return {
        "id": rid,
        "name": name,
        "companions": comp,
        "budget_min": lo,
        "budget_max": hi,
        "contribution": contribution,
        "interests": list(interests),
        "response_slots": [{"slot_id": s} for s in slots],
    }


def _seed_catchup():
    return {
        "id": "c1",
        "owner_id": "owner-1",
        "type": "food",
        "slots": SLOTS,
        "responses": [
            _resp("1", "Aarav", ["s1", "s2"], 0, R200_500, interests=["tea/coffee", "walk"]),
            _resp("2", "Diya", ["s1"], 1, R200_500, interests=["food", "games"]),
            _resp("3", "Kabir", ["s1", "s3"], 0, UNDER_200, interests=["walk", "park"]),
            _resp("4", "Meera", ["s1"], 2, R200_500, 100, ["food", "tea/coffee"]),
            _resp("5", "Rohan", ["s2", "s3"], 0, R500_1000, interests=["games", "food"]),
            _resp("6", "Sara", ["s1"], 0, UNDER_200, interests=["park", "walk"]),
            _resp("7", "Vivaan", ["s1", "s2"], 1, R500_1000, interests=["food", "sports"]),
            _resp("8", "Ananya", ["s3"], 0, R200_500, interests=["tea/coffee", "park"]),
            _resp("9", "Ishaan Kumar", ["s1"], 0, R2000_PLUS, 500, ["food", "day-trip"]),
            _resp("10", "Nisha", ["s1", "s2"], 0, R200_500, interests=["walk", "games"]),
        ],
    }


def test_seed_scenario_result():
    res = build_result(_seed_catchup())
    assert res.best_slot is not None
    assert res.best_slot.id == "s1"
    assert res.best_slot.attending_people == 8
    assert res.group_size == 12  # 8 responders + 4 companions
    assert res.budget.per_person.low == 200
    assert res.budget.per_person.high == 500  # Ishaan's 2000+ did NOT pull it up
    assert res.budget.total.high == 500 * 12
    assert res.budget.contributions_total == 600  # 100 + 500
    assert 80.0 <= res.budget.inclusion_pct <= 90.0
    assert 1 <= len(res.suggestions) <= 4
    assert res.response_count == 10


def test_privacy_contract_no_individual_data_leaks():
    res = build_result(_seed_catchup())
    dumped = res.model_dump()

    # Only aggregate keys are exposed.
    allowed = {
        "best_slot", "alternatives", "group_size", "budget",
        "suggestions", "rationale", "responded", "response_count", "message",
    }
    assert set(dumped.keys()) == allowed

    # `responded` carries first names only — no surnames.
    assert "Ishaan" in res.responded
    assert all(" " not in name for name in res.responded)

    # The outlier's private figures must never surface anywhere in the payload.
    blob = res.model_dump_json()
    for leak in ("5000", "2000", "budget_min", "budget_max", "companions", "response_slots"):
        assert leak not in blob


def test_empty_state():
    catchup = {"id": "c1", "owner_id": "o", "type": "food", "slots": SLOTS, "responses": []}
    res = build_result(catchup)
    assert res.best_slot is None
    assert res.response_count == 0
    assert res.message is not None


def test_no_overlap_state():
    catchup = {
        "id": "c1", "owner_id": "o", "type": "casual", "slots": SLOTS,
        "responses": [
            _resp("1", "A", ["s1"], 0, R200_500),
            _resp("2", "B", ["s2"], 0, R200_500),
            _resp("3", "C", ["s3"], 0, R200_500),
        ],
    }
    res = build_result(catchup)
    assert res.best_slot is None
    assert res.message is not None
    assert len(res.alternatives) == 3


def test_rationale_carries_no_wall_clock_time():
    """Regression: the server used to strftime a UTC timestamptz into the
    rationale, so a 8:00 PM IST slot read "2:30 PM" and contradicted the
    client-rendered header. The server cannot know the viewer's timezone, so it
    must not format times at all. Time formatting belongs to the client."""
    res = build_result(_seed_catchup())

    assert res.rationale is not None
    # s1 starts 17:00 UTC. Neither the UTC rendering nor any hour-like token
    # may appear in a server-built sentence.
    assert "PM" not in res.rationale
    assert "AM" not in res.rationale
    assert ":" not in res.rationale
    assert "5:00" not in res.rationale
    # The budget half is still there.
    assert "200" in res.rationale
    assert "500" in res.rationale
