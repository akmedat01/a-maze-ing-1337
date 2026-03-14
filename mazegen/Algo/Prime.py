import random
from typing import Any, Dict, List, Tuple

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]


class Prime:

    @classmethod
    def get_walls(cls, maze: Maze, row: int, col: int, height: int,
                  width: int) -> List[Tuple[int, int, str, int, int]]:
        walls = []
        if row - 1 >= 0:
            walls.append((row, col, "north", row - 1, col))
        if row + 1 <= height - 1:
            walls.append((row, col, "south", row + 1, col))
        if col - 1 >= 0:
            walls.append((row, col, "west", row, col - 1))
        if col + 1 <= width - 1:
            walls.append((row, col, "east", row, col + 1))
        return walls

    @classmethod
    def generate_maze_perfect(cls, maze: Maze, row: int, col: int, height: int,
                              width: int) -> None:
        maze[row][col]["visited"] = True
        frontier = cls.get_walls(maze, row, col, height, width)
        while frontier:
            choice = random.choice(frontier)
            frontier.remove(choice)
            row, col, direction, n_row, n_col = choice
            if maze[n_row][n_col]["visited"]:
                continue
            maze[row][col][direction] = False
            if direction == "north":
                maze[n_row][n_col]["south"] = False
            elif direction == "south":
                maze[n_row][n_col]["north"] = False
            elif direction == "east":
                maze[n_row][n_col]["west"] = False
            elif direction == "west":
                maze[n_row][n_col]["east"] = False
            maze[n_row][n_col]["visited"] = True
            for wall in cls.get_walls(maze, n_row, n_col, height, width):
                if wall not in frontier:
                    frontier.append(wall)

    @classmethod
    def has_large_open_area(cls, maze: Maze, height: int,
                            width: int, size: int = 3) -> bool:
        for r in range(height - size + 1):
            for c in range(width - size + 1):
                fully_open = True
                # loop over all cells inside the size x size block
                for i in range(size):
                    for j in range(size):
                        cell_r = r + i
                        cell_c = c + j
                        # check right neighbor
                        if j < size - 1:
                            if (maze[cell_r][cell_c]["east"] or maze[cell_r]
                                    [cell_c+1]["west"]):
                                fully_open = False
                                break
                        # check bottom neighbor
                        if i < size - 1:
                            if (maze[cell_r][cell_c]["south"] or maze[cell_r+1]
                                    [cell_c]["north"]):
                                fully_open = False
                                break
                    if not fully_open:
                        break
                if fully_open:
                    return True  # found a size x size open block
        return False  # no large open area found

    @classmethod
    def generate_imperfect_maze(cls, maze: Maze, row: int, col: int,
                                height: int, width: int,
                                chance: float = 0.1) -> None:
        cls.generate_maze_perfect(maze, row, col, height, width)
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
                    # check bounds
                    if 0 <= new_row < height and 0 <= new_col < width:
                        # remove wall both sides
                        maze[row][col][direction] = False
                        maze[new_row][new_col][opposite] = False
                        # check if this creates a large open area
                        if cls.has_large_open_area(maze, height, width):
                            # undo the wall removal
                            maze[row][col][direction] = True
                            maze[new_row][new_col][opposite] = True
