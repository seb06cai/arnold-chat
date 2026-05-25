from tools import generate_workout_plan, get_arnold_quote


def test_generate_plan_returns_string():
    result = generate_workout_plan("hypertrophy", "beginner", 3)
    assert isinstance(result, str) and len(result) > 50


def test_generate_plan_includes_day_markers():
    result = generate_workout_plan("strength", "intermediate", 4)
    assert "Day 1" in result or "Monday" in result


def test_generate_plan_unknown_goal_falls_back():
    result = generate_workout_plan("yoga", "beginner", 3)
    assert isinstance(result, str) and len(result) > 20


def test_get_quote_motivational():
    result = get_arnold_quote("motivational")
    assert isinstance(result, str) and len(result) > 10


def test_get_quote_tough_love():
    result = get_arnold_quote("tough_love")
    assert isinstance(result, str) and len(result) > 10


def test_get_quote_unknown_mood_falls_back():
    result = get_arnold_quote("confused")
    assert isinstance(result, str) and len(result) > 10
