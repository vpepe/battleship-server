from board import Board
from sampler import *
import io
import base64

def uncover_tile(tile: str, occludedBoard: Board, trueBoard: Board) -> Board:
    # Letter -> Column, Number -> Row; Numpy arrays index the row first, then the columns

    column = ord(tile[0]) - ord("A")
    row = int(tile[1:]) - 1

    trueTile = trueBoard.to_symbolic_array()[row][column]
    print(row, column)
    occludedBoardSymbolic = occludedBoard.to_symbolic_array()
    occludedBoardSymbolic[row][column] = trueTile

    return Board.from_symbolic_array(occludedBoardSymbolic)


def has_ship_sunk(occludedBoard: Board, trueBoard: Board, shipLabel: str) -> bool:
    return (
        SeenShip(occludedBoard, shipLabel).length_seen
        == SeenShip(trueBoard, shipLabel).length
    )

def general_to_base64(img):
    bytes = io.BytesIO()
    img.savefig(bytes, format="png", bbox_inches="tight")
    bytes.seek(0)
    return base64.b64encode(bytes.read()).decode("utf-8")

def index_to_coordinate(index):
    letter = chr(ord("A") + index[1])
    number = index[0] + 1
    return letter+str(number)

def quickSampler(samples, base_board, ship_labels, ship_lengths):
    boards = []
    for _ in range(samples):
        solution = None
        while solution == None:
            solution = sample_board(base_board,ship_labels,ship_lengths)[0]
        boards.append(solution)
    return boards

def probability_maximiser(samples, board, ship_labels):
    heatmap_data = to_heatmap(samples,ship_labels,returnData=True)
    locations_dirty = np.where(board.to_symbolic_array() != "H")
    locations = [
            (locations_dirty[0][i], locations_dirty[1][i]) for i in range(len(locations_dirty[0]))
        ]
    for location in locations:
        heatmap_data[location[0]][location[1]] = float("-1")
    
    max_index = np.unravel_index(heatmap_data.argmax(), heatmap_data.shape)

    return index_to_coordinate(max_index)

def heterogeneity_maximiser(samples,current_board,ship_labels):
    samples = [sample.to_symbolic_array() for sample in samples]
    ship_samples = {}
    for ship in ship_labels:
        ship_samples[ship] = []
        for board_index, board in enumerate(samples):
            board_to_edit = deepcopy(samples[board_index])
            for row_index, row in enumerate(board):
                for item_index, item in enumerate(row):
                    if item == ship:
                        board_to_edit[row_index][item_index] = 1
                    else:
                        board_to_edit[row_index][item_index] = 0
            ship_samples[ship].append(board_to_edit)
        ship_samples[ship] = np.sum([np.array(board.astype(int)) for board in ship_samples[ship]], axis=0)

    total_ship = np.sum([np.array(ship_samples[ship]).astype(int) for ship in ship_labels], axis = 0)
    for ship in ship_labels:
        ship_samples[ship] = np.divide(ship_samples[ship],total_ship,np.zeros(ship_samples[ship].shape, dtype=float), where = total_ship != 0)

    final = np.abs(np.divide(np.sum([np.subtract(ship_samples[ship],1/len(ship_labels)) for ship in ship_labels],axis=0),len(ship_labels)))

    locations_dirty = np.where(current_board.to_symbolic_array() != "H")
    locations = [
            (locations_dirty[0][i], locations_dirty[1][i]) for i in range(len(locations_dirty[0]))
        ]
    for location in locations:
        final[location[0]][location[1]] = float("inf")       

    min_index = np.unravel_index(final.argmin(), final.shape)
    return index_to_coordinate(min_index)