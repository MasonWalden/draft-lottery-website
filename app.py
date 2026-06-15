from flask import Flask, render_template, request
import random

app = Flask(__name__)

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


@app.route("/", methods=["GET", "POST"])
def home():
    results = None

    if request.method == "POST":
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

        pick_3 = weighted_draw(available, PICK_3_WEIGHTS)

        final_order = enforce_max_drop([pick_1, pick_2, pick_3])

        results = [
            {
                "pick": index + 1,
                "seed": seed,
                "team": teams[seed],
                "movement": seed - (index + 1)
            }
            for index, seed in enumerate(final_order)
        ]

    return render_template("index.html", results=results)


if __name__ == "__main__":
    app.run(debug=True)
