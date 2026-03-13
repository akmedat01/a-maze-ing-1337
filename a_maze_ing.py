from Algo import DFS
from Algo import Prime
from Display import draw_42


class MazeGenerator:
    def __init__(self) -> None:
        self.algo = "Prime"

    def initial_maze(self, config):
        maze = [
            [
                {"north": True, "east": True, "south": True, "west": True,
                 "visited": False}
                for _ in range(config["width"])
            ]
            for _ in range(config["height"])
        ]
        return maze

    def set_algo(self, algo: str) -> None:
        self.algo = algo

    def generate_maze(self, parsed_Values: dict) -> None:
        maze = self.initial_maze(parsed_Values)
        cord_42 = draw_42.draw_42(maze, parsed_Values["height"],
                                  parsed_Values["width"])
        if parsed_Values["entry"] in cord_42:
            raise ValueError("Entry Point inside the 42 pattern - change it")
        if parsed_Values["exit"] in cord_42:
            raise ValueError("Exit Point inside the 42 pattern - change it")
        if self.algo == "DFS":
            if parsed_Values["perfect"] == "True":
                DFS.generate_perfect_maze(maze, 0, 0,
                                          parsed_Values["height"],
                                          parsed_Values["width"])
            elif parsed_Values["perfect"] == "False":
                DFS.generate_imperfect_maze(maze,
                                            parsed_Values["height"],
                                            parsed_Values["width"])
        elif self.algo == "Prime":
            if parsed_Values["perfect"] == "True":
                Prime.generate_maze_perfect(maze, 0, 0,
                                            parsed_Values["height"],
                                            parsed_Values["width"])
            elif parsed_Values["perfect"] == "False":
                Prime.generate_imperfect_maze(maze, 0, 0,
                                              parsed_Values["height"],
                                              parsed_Values["width"])
        return maze
