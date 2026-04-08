from app.core.time_utils import parse_temporal_intent


def test_parse_relative_temporal_query():
    intent = parse_temporal_intent("What changed 2 weeks ago?")
    assert intent.target is not None
    assert intent.window_days == 7
