from app.suggestions.base import SuggestionContext
from app.suggestions.rules import RulesSuggestionProvider

provider = RulesSuggestionProvider()


def test_never_exceeds_band_high():
    ctx = SuggestionContext(type="food", band_low=200, band_high=500, interests=["food"])
    out = provider.suggest(ctx)
    assert out
    for s in out:
        assert s.est_per_person_high <= ctx.band_high


def test_cheapest_option_always_present():
    ctx = SuggestionContext(type="outing", band_low=0, band_high=400, interests=["beach"])
    out = provider.suggest(ctx)
    # The lowest entry cost among returned should be 0 (a free option exists).
    assert min(s.est_per_person_low for s in out) == 0


def test_interest_influences_ranking():
    ctx = SuggestionContext(type="casual", band_low=200, band_high=800, interests=["games"])
    titles = [s.title for s in provider.suggest(ctx)]
    assert any("games" in t.lower() or "board" in t.lower() for t in titles)


def test_returns_between_1_and_4():
    ctx = SuggestionContext(type="food", band_low=200, band_high=900, interests=[])
    out = provider.suggest(ctx)
    assert 1 <= len(out) <= 4
