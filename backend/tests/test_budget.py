from app.budget.engine import BudgetInput, compute_band


def _people(pairs):
    """pairs: list of (min, max, count)."""
    out = []
    for lo, hi, n in pairs:
        out.extend(BudgetInput(lo, hi) for _ in range(n))
    return out


def test_brief_example_outlier_does_not_inflate():
    # 6 people ~500, 3 ~1000, 1 at 10000 (the outlier from the brief).
    people = _people([(200, 500, 6), (500, 1000, 3), (2000, 10000, 1)])
    band = compute_band(people, group_size=10)
    # Band settles at the inclusive value; the 10000 outlier must not pull it up.
    assert band.per_person_high == 500
    assert band.inclusion_pct == 100.0
    assert band.total_high == 500 * 10


def test_outlier_magnitude_is_irrelevant():
    base = compute_band(_people([(200, 500, 6), (500, 1000, 3), (2000, 10000, 1)]), 10)
    huge = compute_band(_people([(200, 500, 6), (500, 1000, 3), (2000, 999999, 1)]), 10)
    assert base.per_person_high == huge.per_person_high  # outlier size changes nothing


def test_single_response():
    band = compute_band(_people([(200, 500, 1)]), group_size=1)
    assert band.per_person_high == 500
    assert band.inclusion_pct == 100.0


def test_all_identical():
    band = compute_band(_people([(300, 300, 5)]), group_size=5)
    assert band.per_person_low == 300
    assert band.per_person_high == 300


def test_seed_scenario_s1_band():
    # The 12-person S1 crowd from the seed data: mostly 200-500, some 500-1000,
    # one 2000+ (Ishaan). Expect ~200-500 with ~83% inclusion.
    people = _people([(0, 200, 2), (200, 500, 7), (500, 1000, 2), (2000, 5000, 1)])
    band = compute_band(people, group_size=12)
    assert band.per_person_low == 200
    assert band.per_person_high == 500
    assert 80.0 <= band.inclusion_pct <= 90.0
    assert band.total_low == 200 * 12
    assert band.total_high == 500 * 12
