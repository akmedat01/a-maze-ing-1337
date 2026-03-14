from .Algo import DFS
from .Algo import Prime
from .Display.draw_42 import draw_42


class MazeGenerator:
    def __init__(self, height: int, width: int,
                 algo: str = "DFS", perfect: bool = True) -> None:
        self.algo = algo
        self.height = height
        self.width = width
        self.perfect = perfect

    def initial_maze(self, height: int,
                     width: int) -> list[list[dict[str, bool]]]:
        maze = [
            [
                {"north": True, "east": True, "south": True, "west": True,
                 "visited": False}
                for _ in range(width)
            ]
            for _ in range(height)
        ]
        return maze

    def set_algo(self, algo: str) -> None:
        self.algo = algo

    def generate_maze(self) -> list[list[dict[str, bool]]]:
        maze = self.initial_maze(self.height, self.width)
        draw_42.get_blocked_cells(maze, self.height,
                                  self.width)
        if self.algo == "DFS":
            if self.perfect:
                DFS.generate_perfect_maze(maze, 0, 0,
                                          self.height,
                                          self.width)
            else:
                DFS.generate_imperfect_maze(maze,
                                            self.height,
                                            self.width)
        elif self.algo == "PRIM":
            if self.perfect:
                Prime.generate_maze_perfect(maze, 0, 0,
                                            self.height,
                                            self.width)
            else:
                Prime.generate_imperfect_maze(maze, 0, 0,
                                              self.height,
                                              self.width)
        return maze
