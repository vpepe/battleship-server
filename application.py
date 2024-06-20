from flask import Flask, request, render_template, session, redirect, url_for
from flask_cors import CORS
import battleship_gui_funcs as gui
import board
import sampler
import time
import numpy as np
import matplotlib
import authored_boards
from random import randrange

#----------- EXPERIMENT HYPERPARAMETERS ---------------------
test_games = 1                              #How many trial games a participant is given
games_per_participant = test_games + 2      #How many total games a participant is given

test_ships = ["B", "R"]                       #Ships available in the trial games
test_lengths = [3, 4]                         #Ship lengths available in the trial games
test_board_size = 5                           #Board size in the trial games
test_occlusion = {"water": 0.3, "ships": 0.2} #Occlusion probabilities in the trial games
                                              #These should be higher since there are fewer tiles/ships

ships = ["B", "R", "P", "O"]                  #Ships available in the rest of the games
lengths = [4,5,6,7,8,9,10]                    #Ship lengths available in the rest of the games
board_size = 10                               #Board size in the rest of the games
occlusion = {"water": 0.2, "ships": 0.05}     #Occlusion probabilities in the rest of the games

#Option to use authored boards instead of random ones for all of the games.
preset_boards = authored_boards.presets
preset_boards = None #Remove me to use the preset boards in authored_boards.py 

#---------------------------------------------------------

matplotlib.use("Agg")

app = Flask(__name__)
app.secret_key = "bc0ccbebb445f0001adbb5828021d4c8cc09e8539a6ba443fb723a5868dfa3cc"
CORS(app)

test_grid = np.full((test_board_size,test_board_size), fill_value = -1, dtype = int)

board_grid = np.full((board_size,board_size), fill_value= -1, dtype=int)

try:
    authored_boards_serialized = str([(board.Board(pair[0]).to_serialized(),board.Board(pair[1]).to_serialized()) for pair in preset_boards])
    print("Authored boards detected...")
except:
    print("No authored boards detected!")
    authored_boards_serialized = None

def progress_tracker(games_played, games_per_participant):
    return (games_played / games_per_participant) * 100


@app.route("/")
def instructions():
    session["participant_data"] = {
        "PROLIFIC_ID": request.args.get("PROLIFIC_PID", default="null", type=str),
        "SESSION_ID": request.args.get("SESSION_ID", default="null", type=str),
        "STUDY_ID": request.args.get("STUDY_ID", default="null", type=str),
        "moves": None,
        "starting_board": None,
        "true_board": None,
    }
    session["authored_boards"] = authored_boards_serialized
    return render_template("instructions.html")


@app.route("/start")
def start_experiment():
    session["games_played"] = 0
    return redirect(url_for("game"))


@app.route("/game")
def game():
    session["start_time"] = time.time()

    if session["authored_boards"] is None or session["games_played"]+1 <= test_games:
        true_board = None

        grid_to_sample = board_grid if session["games_played"]+1 > test_games else test_grid
        ships_to_sample = ships if session["games_played"]+1 > test_games else test_ships
        lengths_to_sample = lengths if session["games_played"]+1 > test_games else test_lengths
        occlusion_probs = occlusion if session["games_played"]+1 > test_games else test_occlusion

        while true_board == None:
            true_board = sampler.sample_board(board.Board(grid_to_sample), ships_to_sample, lengths_to_sample)[0]

        session["true_board"] = true_board.to_serialized()

        session["occluded"] = sampler.occlude_board(
            board.Board.from_serialized(session["true_board"]), occlusion_probs["water"], occlusion_probs["ships"]
        ).to_serialized()
    else:
        authored_boards = eval(session["authored_boards"])
        board_pair = authored_boards.pop(randrange(len(authored_boards)))
        session["true_board"] = board_pair[0]
        session["occluded"] = board_pair[1]
        session["authored_boards"] = str(authored_boards)

    session["ended"] = "F"

    session["participant_data"]["moves"] = []
    session["participant_data"]["starting_board"] = session["occluded"]
    session["participant_data"]["true_board"] = session["true_board"]

    base64_image = board.Board.from_serialized(session["occluded"]).to_base64()
    return render_template(
        "battleship.html",
        base64_image=base64_image,
        solved=session["ended"],
        progress=progress_tracker(session["games_played"], games_per_participant),
    )


@app.route("/game", methods=["POST"])
def game_post():
    text = request.form["text"]
    try:
        processed_text = text.upper()

        session["occluded"] = gui.uncover_tile(
            processed_text,
            board.Board.from_serialized(session["occluded"]),
            board.Board.from_serialized(session["true_board"]),
        ).to_serialized()
        session["participant_data"]["moves"].append(
            (processed_text, time.time() - session["start_time"])
        )
    except Exception as e:
        pass

    base64_image = board.Board.from_serialized(session["occluded"]).to_base64()

    if session["authored_boards"] is None:
        ships_present = ships if session["games_played"]+1 > test_games else test_ships
    else:
        ships_present = authored_boards.ships

    sunk_data = [
        (
            board.SYMBOL_MEANING_MAPPING[ship],
            (
                True
                if gui.has_ship_sunk(
                    board.Board.from_serialized(session["occluded"]),
                    board.Board.from_serialized(session["true_board"]),
                    ship,
                )
                else False
            ),
        )
        for ship in ships_present
    ]
    sunk = " | ".join(
        [
            f"{datum[0]} {'sunk' if datum[1] == True else 'not sunk'}".capitalize()
            for datum in sunk_data
        ]
    )

    if all([datum[1] for datum in sunk_data]):
        sunk = "All ships sunk! You win!"
        session["ended"] = "T"

        with open("logs.txt", "a", encoding="utf-8") as f:
            f.write(
                str(
                    ";".join(
                        [str(i) for i in list(session["participant_data"].values())]
                    )
                )+"\n"
            )

        session["games_played"] += 1

        if session["games_played"] == games_per_participant:
            return render_template(
                "last_win.html",
                progress=progress_tracker(
                    session["games_played"], games_per_participant
                ),
            )
        elif session["games_played"] == test_games:
            return render_template(
                "thank_you.html",
                progress=progress_tracker(
                    session["games_played"], games_per_participant
                ),
            )
        else:
            return render_template(
                "win.html",
                progress=progress_tracker(
                    session["games_played"], games_per_participant
                ),
            )

    return render_template(
        "battleship.html",
        ships_sunk=sunk,
        base64_image=base64_image,
        solved=session["ended"],
        progress=progress_tracker(session["games_played"], games_per_participant),
    )


@app.route("/next_game")
def next_game():
    if session["games_played"] >= games_per_participant:
        return redirect(url_for("thank_you"))
    return redirect(url_for("game"))


@app.route("/thank_you")
def thank_you():
    return render_template("thank_you.html")


if __name__ == "__main__":
    app.run(debug=True)
