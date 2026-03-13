import random
from typing import Any, Dict, List, Tuple

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]


class DFS:
    @classmethod
    def check_neighbors(cls, maze: Maze, row: int, col: int, height: int,
                        width: int) -> List[Tuple[str, int, int]]:
        neighbors = []
        if row - 1 >= 0 and not maze[row - 1][col]["visited"]:
            neighbors.append(("north", row - 1, col))
        if row + 1 <= height - 1 and not maze[row + 1][col]["visited"]:
            neighbors.append(("south", row + 1, col))
        if col - 1 >= 0 and not maze[row][col - 1]["visited"]:
            neighbors.append(("west", row, col - 1))
        if col + 1 <= width - 1 and not maze[row][col + 1]["visited"]:
            neighbors.append(("east", row, col + 1))
        return neighbors

    @classmethod
    def generate_perfect_maze(cls, maze: Maze, row: int, col: int, height: int,
                              width: int) -> None:
        maze[row][col]["visited"] = True
        neighbors = cls.check_neighbors(maze, row, col, height, width)
        random.shuffle(neighbors)
        for direction, n_row, n_col in neighbors:
            if not maze[n_row][n_col]["visited"]:
                maze[row][col][direction] = False
                if direction == "north":
                    maze[n_row][n_col]["south"] = False
                elif direction == "south":
                    maze[n_row][n_col]["north"] = False
                elif direction == "east":
                    maze[n_row][n_col]["west"] = False
                elif direction == "west":
                    maze[n_row][n_col]["east"] = False
                cls.generate_perfect_maze(maze, n_row, n_col,
                                          height, width)

    @classmethod
    def has_large_open_area(cls, maze: Maze, height: int,
                            width: int, size: int = 3) -> bool:
        for r in range(height - size + 1):
            for c in range(width - size + 1):
                fully_open = True
                for i in range(size):
                    for j in range(size):
                        cell_r = r + i
                        cell_c = c + j
                        if j < size - 1:
                            if (maze[cell_r][cell_c]["east"] or maze[cell_r]
                                    [cell_c+1]["west"]):
                                fully_open = False
                                break
                        if i < size - 1:
                            if (maze[cell_r][cell_c]["south"] or maze[cell_r+1]
                                    [cell_c]["north"]):
                                fully_open = False
                                break
                    if not fully_open:
                        break
                if fully_open:
                    return True
        return False

    @classmethod
    def generate_imperfect_maze(cls, maze: Maze, height: int, width: int,
                                chance: float = 0.1) -> None:
        cls.generate_perfect_maze(maze, 0, 0, height, width)
        directions = [
            ("north", -1, 0, "south"),
            ("south", 1, 0, "north"),
            ("west", 0, -1, "east"),
            ("east", 0, 1, "west")
        ]
        for row in range(height):
            for col in range(width):
                if random.random() < chance:
                    direction, dr, dc, opposite = random.choice(directions)
                    new_row = row + dr
                    new_col = col + dc
                    if 0 <= new_row < height and 0 <= new_col < width:
                        maze[row][col][direction] = False
                        maze[new_row][new_col][opposite] = False
                        if cls.has_large_open_area(maze, height, width):
                            maze[row][col][direction] = True
                            maze[new_row][new_col][opposite] = True
