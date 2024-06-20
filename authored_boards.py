import numpy as np

ships = ["B", "R", "P", "O"]                  
lengths = [2]                                  
board_size = 3                              
occlusion = {"water": 0.2, "ships": 0.05}    

presets = [
        (np.array([[1, 1, 0],
                  [0, 0, 0],
                  [0, 2, 2]]), 
         np.array([[1, -1, 0],
                  [-1, -1, -1],
                  [0, -1, 2]])),
        (np.array([[3, 3, 0],
                  [0, 0, 0],
                  [0, 4, 4]]), 
         np.array([[3, -1, -1],
                  [-1, -1, -1],
                  [-1, -1, 4]])),
        (np.array([[2, 2, 0],
                  [0, 0, 0],
                  [0, 3, 3]]), 
         np.array([[2, -1, -1],
                  [-1, -1, -1],
                  [-1, -1, 3]]))
]