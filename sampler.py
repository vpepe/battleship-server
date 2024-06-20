from board import Board
import numpy as np
from copy import deepcopy
import matplotlib.pyplot as plt
import matplotlib
import math
import random

#This is required for thread-safety for the webapp, but it turns off interactivity.
#matplotlib.use("Agg")

class SeenShip(object):
    def __init__(self, board: Board, label) -> None:
        board = board.to_symbolic_array()
        self.label = label
        self.locations = np.where(board == label)
        self.length_seen = len(self.locations[0])
        location_tuples = [
            (self.locations[0][i], self.locations[1][i]) for i in range(self.length_seen)
        ]
        
        self.location_tuples = location_tuples
        if self.length_seen > 1:
            if all([i == self.locations[0][0] for i in self.locations[0]]):
                self.orientation = ["H"]
                self.extremities = (
                    min(location_tuples, key=lambda item: item[1]),
                    max(location_tuples, key=lambda item: item[1]),
                )
                self.length = self.extremities[1][1] - self.extremities[0][1] + 1
            elif all([i == self.locations[1][0] for i in self.locations[1]]):
                self.orientation = ["V"]
                self.extremities = (
                    min(location_tuples, key=lambda item: item[0]),
                    max(location_tuples, key=lambda item: item[0]),
                )
                self.length = self.extremities[1][0] - self.extremities[0][0] + 1
            else:
                raise ValueError(f"{self.label} ship oriented incorrectly")
        elif self.length_seen == 1:
            self.orientation = ["H", "V"]
            self.extremities = (location_tuples[0], location_tuples[0])
            self.length = 1
        else:
            self.orientation = None
            self.extremities = (None, None)
            self.length = 0

def next_step(board: Board, ship_labels: list, ship_lengths: list):
    new_boards = []
    ships = [SeenShip(board, ship) for ship in ship_labels]
    board = board.to_symbolic_array()
    max_index, max_length = len(board[0]), max(
        ship_lengths
    )
    for ship in ships:
        if ship.length + 1 <= max_length:
            if ship.orientation is not None:
                for orientation in ship.orientation:
                    if orientation == "H":
                        if ship.extremities[1][1] + 1 < max_index:
                            if (
                                board[ship.extremities[1][0]][
                                    ship.extremities[1][1] + 1
                                ]
                                == "H"
                            ):
                                new_board = deepcopy(board)
                                new_board[ship.extremities[1][0]][
                                    ship.extremities[1][1] + 1
                                ] = ship.label
                                new_boards.append(new_board)
                        if ship.extremities[0][1] - 1 >= 0:
                            if (
                                board[ship.extremities[0][0]][
                                    ship.extremities[0][1] - 1
                                ]
                                == "H"
                            ):
                                new_board = deepcopy(board)
                                new_board[ship.extremities[0][0]][
                                    ship.extremities[0][1] - 1
                                ] = ship.label
                                new_boards.append(new_board)
                    if orientation == "V":
                        if ship.extremities[1][0] + 1 < max_index:
                            if (
                                board[ship.extremities[1][0] + 1][
                                    ship.extremities[1][1]
                                ]
                                == "H"
                            ):
                                new_board = deepcopy(board)
                                new_board[ship.extremities[1][0] + 1][
                                    ship.extremities[1][1]
                                ] = ship.label
                                new_boards.append(new_board)
                        if ship.extremities[0][0] - 1 >= 0:
                            if (
                                board[ship.extremities[0][0] - 1][
                                    ship.extremities[0][1]
                                ]
                                == "H"
                            ):
                                new_board = deepcopy(board)
                                new_board[ship.extremities[0][0] - 1][
                                    ship.extremities[0][1]
                                ] = ship.label
                                new_boards.append(new_board)
    new_boards = np.unique(np.array(new_boards), axis=0).tolist()
    new_boards = [Board(Board.convert_to_numeric(np.array(i))) for i in new_boards]

    return new_boards

def occlusion_fixing(starting_board, ship_labels):
    symbolic_board = starting_board.to_symbolic_array()
    for ship in ship_labels:
        ship_part = SeenShip(starting_board,ship)
        ship_length = ship_part.length
        ship_extremities = ship_part.extremities
        if ship_length > 1: 
            ship_tiles = []
            for i in range(ship_length):
                if ship_part.orientation[0] == "H":
                    ship_tiles.append((ship_extremities[0][0],ship_extremities[0][1]+i))
                if ship_part.orientation[0] == "V":
                    ship_tiles.append((ship_extremities[0][0]+i,ship_extremities[0][1]))
            for tile in ship_tiles:
                if symbolic_board[tile[0]][tile[1]] in ["H","W",ship]:
                    symbolic_board[tile[0]][tile[1]] = ship
                else:
                    return None
    return Board.from_symbolic_array(symbolic_board)

def is_board_valid(board: Board, ship_labels, ship_lengths):
    valid = all(
            [
                SeenShip(board, ship).length in ship_lengths or SeenShip(board, ship).length == 0 
                for ship in ship_labels
            ])
    return valid

def all_steps(starting_board: Board, ship_labels: list, ship_lengths: list):
    queue, cache, results = [starting_board], [], []
    while len(queue) != 0:
        for _ in queue:
            board = queue.pop(0)
            if board not in cache:
                cache.append(board)
                new_boards = next_step(
                    board, ship_labels, ship_lengths
                )
                for new_board in new_boards: #these are now board objects
                    if new_board not in cache:
                        queue.append(new_board)
            else:
                continue
    for processed_board in cache:
        if is_board_valid(processed_board, ship_labels, ship_lengths):
            results.append(processed_board)
    return results

def missing_ships_in_board(board: Board, ship_labels): #quick helper function to return which ships are missing from some given boardstate
    return [ship for ship in ship_labels if SeenShip(board, ship).length == 0]

def seed_board(board: Board, missing_ships):
    symbolic_board = board.to_symbolic_array()
    trace = []
    hidden_tiles = np.where(np.array(symbolic_board) == "H")
    location_tuples = [
        (hidden_tiles[0][i], hidden_tiles[1][i]) for i in range(len(hidden_tiles[0]))
    ]

    if len(location_tuples) < len(missing_ships): #not enough empty slots on the board to accommodate all missing ships!
        return []

    seeded_board = deepcopy(symbolic_board)
    seeds = random.sample(location_tuples, len(missing_ships))
    for index, seed in enumerate(seeds):
        seeded_board[seed[0]][seed[1]] = missing_ships[index]
        trace.append((missing_ships[index],(seed[0], seed[1]), math.log(1/(len(location_tuples)-(index+1)))))

    returnable_board = Board.from_symbolic_array(seeded_board)

    return returnable_board, trace

def to_heatmap(board_list, ship_labels, inches: int = 6, dpi: int = 128, returnData = False):
    board_list = [board.to_symbolic_array() for board in board_list]
    for board_index, board in enumerate(board_list):
        for row_index, row in enumerate(board):
            for item_index, item in enumerate(row):
                if item in ship_labels:
                    board_list[board_index][row_index][item_index] = 1
                else:
                    board_list[board_index][row_index][item_index] = 0

    
    heatmap = np.sum([board.astype(int) for board in board_list], axis=0)

    if returnData:
        return heatmap

    length = len(board_list[0])

    fig, ax = plt.subplots(figsize=(inches, inches), dpi=dpi)
    ax.matshow(heatmap, cmap="viridis")

    # Add gridlines
    ax.set_xticks(np.arange(-0.5, length, 1), minor=True)
    ax.set_yticks(np.arange(-0.5, length, 1), minor=True)
    ax.grid(which="minor", color="w", linestyle="-", linewidth=2)

    # Add labels
    ax.set_xticks(np.arange(0, length, 1))
    ax.set_yticks(np.arange(0, length, 1))
    ax.set_xticklabels(
        [chr(ord("A") + i) for i in np.arange(0, length, 1)],
        fontsize=24,
        fontweight="bold",
        color="#9b9c97",
    )
    ax.set_yticklabels(
        np.arange(1, length + 1, 1),
        fontsize=24,
        fontweight="bold",
        color="#9b9c97",
    )

    # Hide ticks
    ax.tick_params(axis="both", which="both", length=0)

    # Set border to white
    for spine in ax.spines.values():
        spine.set_edgecolor("white")

    plt.close(fig)
    return fig

def occlude_board(board, ship_revelation_probability = 0.5, water_revelation_probability = 0.5):
    board_list = board.to_symbolic_array()
    for row_index, row in enumerate(board_list):
        for tile_index, tile in enumerate(row):
            if tile == "H":
                continue
            elif tile == "W":
                if random.random() > water_revelation_probability:
                    board_list[row_index][tile_index] = "H" 
            else:
                if random.random() > ship_revelation_probability:
                    board_list[row_index][tile_index] = "H" 
    return Board.from_symbolic_array(board_list)

def sample_board(partial_board, ship_labels, ship_lengths):
    partial_board = occlusion_fixing(partial_board, ship_labels)
    if partial_board is None:
        return None, None, 0
    missing_ships = missing_ships_in_board(partial_board, ship_labels)
    partial_board, trace = seed_board(partial_board, missing_ships)

    while not is_board_valid(partial_board, ship_labels, ship_lengths): #I still don't know if this is a good ending condition, but fine for now
        board_ships_old = [SeenShip(partial_board, ship) for ship in ship_labels]
        all_continuations = next_step(partial_board, ship_labels, ship_lengths)
        try:
            partial_board = random.choice(all_continuations)
        except IndexError:
            return None, None, 0
        board_ships_new = [SeenShip(partial_board, ship) for ship in ship_labels]
        for index, ship in enumerate(board_ships_new):
            old_locations = board_ships_old[index].location_tuples
            new_locations = ship.location_tuples
            if len(new_locations) != 1 and len(new_locations) > len(old_locations):
                trace.append((ship.label,new_locations[-1],math.log(1/len(all_continuations))))

    symbolic_board = partial_board.to_symbolic_array()
    symbolic_board[symbolic_board=="H"] = "W"

    return Board.from_symbolic_array(symbolic_board), trace, sum([i[2] for i in trace])