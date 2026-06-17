from flask import Flask, render_template, request
import random
import os
from supabase import create_client

app = Flask(__name__)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)

PICK_1_WEIGHTS = [22, 20, 18, 16, 13, 11]
PICK_2_WEIGHTS = [24, 21, 18, 15, 12, 10]
PICK_3_WEIGHTS = [26, 22, 18, 14, 11, 9]


def weighted_draw(available_seeds, weights):
    available_weights = [weights[seed - 1] for seed in available_seeds]
    return random.choices(available_seeds, weights=available_weights, k=1)[0]


def enforce_max_drop(drawn):
    final_order = drawn[:]
    used = set(final_order)

    for pick in range(4, 7):
        remaining = [seed for seed in range(1, 7) if seed not in used]
        forced = None

        for seed in remaining:
            if pick > seed + 2:
                forced = seed
                break

        selected = forced if forced else remaining[0]
        final_order.append(selected)
        used.add(selected)

    return final_order


def get_next_run_number(league_year):
    response = (
        supabase.table("lottery_runs")
        .select("run_number")
        .eq("league_year", league_year)
        .order("run_number", desc=True)
        .limit(1)
        .execute()
    )

    if response.data:
        return response.data[0]["run_number"] + 1

    return 1


def save_lottery_run(league_year, teams, results, final_order):
    run_number = get_next_run_number(league_year)

    row = {
        "league_year": league_year,
        "run_number": run_number,

        "seed_1_team": teams[1],
        "seed_2_team": teams[2],
        "seed_3_team": teams[3],
        "seed_4_team": teams[4],
        "seed_5_team": teams[5],
        "seed_6_team": teams[6],

        "pick_1_team": results[0]["team"],
        "pick_2_team": results[1]["team"],
        "pick_3_team": results[2]["team"],
        "pick_4_team": results[3]["team"],
        "pick_5_team": results[4]["team"],
        "pick_6_team": results[5]["team"],

        "full_order": final_order,
    }

    supabase.table("lottery_runs").insert(row).execute()
    return run_number


@app.route("/", methods=["GET", "POST"])
def home():
    results = None
    saved_run_number = None

    if request.method == "POST":
        league_year = int(request.form.get("league_year") or 2026)

        teams = {
            1: request.form.get("team1") or "Team 1",
            2: request.form.get("team2") or "Team 2",
            3: request.form.get("team3") or "Team 3",
            4: request.form.get("team4") or "Team 4",
            5: request.form.get("team5") or "Team 5",
            6: request.form.get("team6") or "Team 6",
        }

        available = [1, 2, 3, 4, 5, 6]

        pick_1 = weighted_draw(available, PICK_1_WEIGHTS)
        available.remove(pick_1)

        pick_2 = weighted_draw(available, PICK_2_WEIGHTS)
        available.remove(pick_2)

    # Pick 3 must enforce the max-drop rule for Seed 1.
# If Seed 1 has not been drawn by Pick 3, Seed 1 must get Pick 3.
if 1 in available:
    pick_3 = 1
else:
    pick_3 = weighted_draw(available, PICK_3_WEIGHTS)

        final_order = enforce_max_drop([pick_1, pick_2, pick_3])

        results = [
            {
                "pick": index + 1,
                "seed": seed,
                "team": teams[seed],
                "movement": seed - (index + 1),
            }
            for index, seed in enumerate(final_order)
        ]

        saved_run_number = save_lottery_run(league_year, teams, results, final_order)

    return render_template(
        "index.html",
        results=results,
        saved_run_number=saved_run_number,
    )


@app.route("/history")
def history():
    response = (
        supabase.table("lottery_runs")
        .select("*")
        .order("created_at", desc=True)
        .execute()
    )

    runs = response.data or []

    daily_counts = {}

    for run in runs:
        date_only = run["created_at"][:10]
        daily_counts[date_only] = daily_counts.get(date_only, 0) + 1

    return render_template(
        "history.html",
        runs=runs,
        daily_counts=daily_counts,
    )


if __name__ == "__main__":
    app.run(debug=True)
