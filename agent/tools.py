import random

_PLANS = {
    ("strength", 3): "Monday is chest and triceps — bench press, incline press, and dips, five sets of five. Wednesday is back and biceps — barbell rows, pull-ups, and curls. Friday is legs and shoulders — squats, Romanian deadlifts, and military press, five by five on ze big lifts.",

    ("strength", 4): "Monday squats, Tuesday bench press, Thursday deadlifts, Friday military press and pull-ups. Every main lift is five sets of five — zat is how you build real strength. Keep ze rest short and ze intensity high.",

    ("hypertrophy", 3): "Monday is chest and biceps — bench press, incline flyes, barbell curls, four sets of ten to twelve. Wednesday is back and triceps — pull-ups, cable rows, skull crushers. Friday is legs and shoulders — squats, leg press, lateral raises, feel every rep.",

    ("hypertrophy", 4): "Monday chest, Tuesday back, Thursday arms, Saturday legs and shoulders. Four to five sets of ten to fifteen reps on everything, no more. Focus on ze squeeze — if you don't feel ze muscle, you are wasting your time.",

    ("endurance", 3): "Monday is full body circuit — squats, push-ups, and dumbbell rows, twenty reps each, no rest between. Wednesday is cardio intervals and core work, twenty minutes hard. Friday is lunges, pull-ups, and dips, all to failure.",

    ("weight_loss", 3): "Monday is upper body supersets — bench into rows, overhead press into pull-ups, minimal rest, keep ze heart rate up. Wednesday is legs — squats, lunges, calf raises, fifteen reps each. Friday is full body metabolic — deadlifts, push-ups, and dumbbell thrusters, burn everything.",
}

_DEFAULT_PLAN = "Monday is chest and back — bench press and pull-ups, four sets of ten. Wednesday is legs — squats and Romanian deadlifts. Friday is shoulders and arms — military press, curls, and skull crushers."

_QUOTES: dict[str, list[str]] = {
    "motivational": [
        "Ze last three or four reps is vhat makes ze muscle grow. Zis area of pain divides ze champion from someone who is not.",
        "You can have results or excuses. Not both.",
        "Ze mind is ze limit. As long as ze mind can envision ze fact zat you can do someting, you can do it.",
        "Pain makes me grow. Growing is vhat I vant. Zerefore, for me pain is pleasure.",
        "I vant you to train like your life depends on it. Because your best life does.",
    ],
    "tough_love": [
        "Everybody pities ze veak. Jealousy you have to earn.",
        "If you don't find ze time, if you don't do ze vork, you don't get ze results.",
        "Ze day you stop blaming ozers is ze day you start vinning.",
        "You vant a great body? Zen stop making excuses and pick up ze bar.",
    ],
    "philosophical": [
        "For me life is continuously being hungry. Ze meaning of life is to move ahead, to go up, to achieve, to conquer.",
        "Ve are always stronger zan ve know. I learned zat from all zose years under ze iron.",
        "Ze vorst sing I can be is ze same as everybody else. I hate zat.",
    ],
}

_DEFAULT_QUOTES = _QUOTES["motivational"]


def generate_workout_plan(goal: str, experience_level: str, days_per_week: int) -> str:
    days = max(1, min(6, int(days_per_week)))
    # Clamp to closest supported day count (3 or 4) if exact match not found
    key = (goal.lower().strip(), days)
    if key not in _PLANS:
        closest = min((3, 4), key=lambda d: abs(d - days))
        key = (goal.lower().strip(), closest)
    plan = _PLANS.get(key, _DEFAULT_PLAN)
    return plan


def get_arnold_quote(mood: str) -> str:
    pool = _QUOTES.get(mood.lower().strip(), _DEFAULT_QUOTES)
    return random.choice(pool)
