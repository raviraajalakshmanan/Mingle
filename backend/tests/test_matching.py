from datetime import UTC, datetime

from app.matching.engine import Response, Slot, match

S1 = Slot("s1", datetime(2026, 9, 5, 17, tzinfo=UTC), datetime(2026, 9, 5, 19, tzinfo=UTC))
S2 = Slot("s2", datetime(2026, 9, 5, 19, tzinfo=UTC), datetime(2026, 9, 5, 21, tzinfo=UTC))
S3 = Slot("s3", datetime(2026, 9, 6, 11, tzinfo=UTC), datetime(2026, 9, 6, 13, tzinfo=UTC))


def test_clear_winner_with_companions():
    responses = [
        Response("a", ["s1", "s2"], companions=0),
        Response("b", ["s1"], companions=1),
        Response("c", ["s1"], companions=2),
        Response("d", ["s2"], companions=0),
    ]
    r = match(responses, [S1, S2, S3])
    assert r.best is not None
    assert r.best.slot.id == "s1"
    assert r.best.people == 3
    assert r.best.headcount == 1 + 2 + 3  # 6


def test_tie_breaks_to_earlier_start():
    # s1 and s2 both have headcount 2, 2 people; s1 starts earlier -> wins.
    responses = [
        Response("a", ["s1"], companions=1),
        Response("b", ["s1"]),
        Response("c", ["s2"], companions=1),
        Response("d", ["s2"]),
    ]
    r = match(responses, [S2, S1])  # order shouldn't matter
    assert r.best.slot.id == "s1"


def test_no_overlap_returns_none_with_alternatives():
    # Each person on a distinct slot -> no slot has >= 2 people.
    responses = [
        Response("a", ["s1"]),
        Response("b", ["s2"]),
        Response("c", ["s3"]),
    ]
    r = match(responses, [S1, S2, S3])
    assert r.best is None
    assert r.no_overlap is True
    assert len(r.alternatives) == 3


def test_no_responses():
    r = match([], [S1, S2])
    assert r.best is None
    assert r.no_overlap is False
