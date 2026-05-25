import random

_PLANS = {
    ("strength", 3): """\
Day 1 — Monday: Chest and Triceps
  Flat Barbell Bench Press: 5 sets x 5 reps
  Incline Dumbbell Press: 4 sets x 6 reps
  Tricep Dips: 3 sets to failure

Day 2 — Wednesday: Back and Biceps
  Barbell Rows: 5 sets x 5 reps
  Pull-Ups: 4 sets x 6 reps
  Standing Barbell Curls: 3 sets x 8 reps

Day 3 — Friday: Legs and Shoulders
  Barbell Back Squat: 5 sets x 5 reps
  Romanian Deadlift: 4 sets x 6 reps
  Standing Military Press: 4 sets x 5 reps""",

    ("strength", 4): """\
Day 1 — Monday: Squat
  Barbell Back Squat: 5 sets x 5 reps
  Romanian Deadlift: 3 sets x 6 reps

Day 2 — Tuesday: Bench
  Flat Barbell Bench Press: 5 sets x 5 reps
  Close-Grip Bench Press: 3 sets x 6 reps

Day 3 — Thursday: Deadlift
  Conventional Deadlift: 5 sets x 5 reps
  Barbell Rows: 4 sets x 5 reps

Day 4 — Friday: Press
  Standing Military Press: 5 sets x 5 reps
  Wide-Grip Pull-Ups: 4 sets x 6 reps""",

    ("hypertrophy", 3): """\
Day 1 — Monday: Chest and Biceps
  Flat Barbell Bench Press: 4 sets x 10 reps
  Incline Dumbbell Flyes: 4 sets x 12 reps
  Standing Barbell Curls: 3 sets x 12 reps

Day 2 — Wednesday: Back and Triceps
  Wide-Grip Pull-Ups: 4 sets x 10 reps
  Seated Cable Rows: 4 sets x 12 reps
  Skull Crushers: 3 sets x 12 reps

Day 3 — Friday: Legs and Shoulders
  Barbell Back Squat: 4 sets x 10 reps
  Leg Press: 3 sets x 12 reps
  Side Lateral Raises: 4 sets x 15 reps""",

    ("hypertrophy", 4): """\
Day 1 — Monday: Chest
  Flat Barbell Bench Press: 5 sets x 10 reps
  Incline Dumbbell Press: 4 sets x 12 reps
  Cable Crossovers: 3 sets x 15 reps

Day 2 — Tuesday: Back
  Wide-Grip Pull-Ups: 4 sets x 10 reps
  Barbell Rows: 4 sets x 12 reps
  One-Arm Dumbbell Rows: 3 sets x 12 reps

Day 3 — Thursday: Arms
  Standing Barbell Curls: 4 sets x 12 reps
  Hammer Curls: 3 sets x 12 reps
  Skull Crushers: 4 sets x 12 reps
  Tricep Pushdowns: 3 sets x 15 reps

Day 4 — Saturday: Legs and Shoulders
  Barbell Back Squat: 5 sets x 10 reps
  Leg Press: 4 sets x 12 reps
  Standing Military Press: 4 sets x 10 reps
  Side Lateral Raises: 4 sets x 15 reps""",

    ("endurance", 3): """\
Day 1 — Monday: Full Body Circuit
  Barbell Squat: 3 sets x 20 reps
  Push-Ups: 3 sets x 25 reps
  Dumbbell Rows: 3 sets x 20 reps per arm

Day 2 — Wednesday: Cardio and Core
  Treadmill Intervals: 20 minutes
  Plank: 3 holds x 60 seconds
  Leg Raises: 3 sets x 20 reps

Day 3 — Friday: Full Body
  Lunges: 3 sets x 20 reps per leg
  Pull-Ups: 3 sets to failure
  Parallel Bar Dips: 3 sets to failure""",

    ("weight_loss", 3): """\
Day 1 — Monday: Upper Body Supersets
  Bench Press superset with Rows: 4 sets x 12 reps, minimal rest
  Overhead Press superset with Pull-Ups: 3 sets x 10 reps

Day 2 — Wednesday: Lower Body
  Barbell Squat: 4 sets x 15 reps
  Lunges: 3 sets x 15 reps per leg
  Calf Raises: 4 sets x 20 reps

Day 3 — Friday: Metabolic Full Body
  Deadlift: 3 sets x 10 reps
  Push-Ups: 3 sets x 20 reps
  Dumbbell Thrusters: 3 sets x 15 reps""",
}

_DEFAULT_PLAN = """\
Day 1 — Monday: Chest and Back
  Flat Barbell Bench Press: 4 sets x 10 reps
  Wide-Grip Pull-Ups: 4 sets x 10 reps

Day 2 — Wednesday: Legs
  Barbell Back Squat: 4 sets x 10 reps
  Romanian Deadlift: 3 sets x 10 reps

Day 3 — Friday: Shoulders and Arms
  Standing Military Press: 4 sets x 10 reps
  Standing Barbell Curls: 3 sets x 10 reps
  Skull Crushers: 3 sets x 10 reps"""

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
    return (
        f"[VOICE AGENT: Read this plan aloud naturally. "
        f"No markdown, no asterisks, no bullet points. Speak each day as plain sentences.]\n\n"
        f"Here is your program, designed by ze Austrian Oak himself:\n\n{plan}"
    )


def get_arnold_quote(mood: str) -> str:
    pool = _QUOTES.get(mood.lower().strip(), _DEFAULT_QUOTES)
    return random.choice(pool)
