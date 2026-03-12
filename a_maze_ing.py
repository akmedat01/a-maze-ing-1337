import os
import sys

from Parsing_folder import Parsing, error_handeling
from Algo import DFS
from Display import hexa_display
from Algo import Prime
from Display import draw_42
from Algo import BFS
from Display.visualizing_maze import display_maze


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

    def generate_maze(self, filename: str) -> None:
        try:
            config = Parsing.read_file(filename)
            error_handeling.check_mandatory_keys(config)
            error_handeling.check_mandatory_values(config)
            error_handeling.check_added_keys(config)
            error_handeling.check_boundries(config)
            parsed_Values = Parsing.parse_config(config)
            seed = None
            if "seed" in parsed_Values:
                seed = parsed_Values["seed"]
            maze = self.initial_maze(parsed_Values)
            draw_42.draw_42(maze, parsed_Values["height"],
                            parsed_Values["width"])
            if self.algo == "DFS":
                if parsed_Values["perfect"] == "True":
                    DFS.generate_perfect_maze(maze, 0, 0,
                                              parsed_Values["height"],
                                              parsed_Values["width"],
                                              seed)
                elif parsed_Values["perfect"] == "False":
                    DFS.generate_imperfect_maze(maze,
                                                parsed_Values["height"],
                                                parsed_Values["width"],
                                                seed)
            elif self.algo == "Prime":
                if parsed_Values["perfect"] == "True":
                    Prime.generate_maze_perfect(maze, 0, 0,
                                                parsed_Values["height"],
                                                parsed_Values["width"],
                                                seed)
                elif parsed_Values["perfect"] == "False":
                    Prime.generate_imperfect_maze(maze, 0, 0,
                                                  parsed_Values["height"],
                                                  parsed_Values["width"],
                                                  seed)
            hexa_display.print_maze_hex(maze, parsed_Values)
            path = BFS.bfs_solve(maze, parsed_Values["entry"],
                                 parsed_Values["exit"],
                                 parsed_Values["height"],
                                 parsed_Values["width"])
            hexa_display.write_path(path, parsed_Values)
        except ValueError as e:
            print(e)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)

    config_path = sys.argv[1]
    project_dir = os.path.dirname(os.path.abspath(config_path))
    maze_file = os.path.join(project_dir, "maze.txt")

    generator = MazeGenerator()
    generator.generate_maze(config_path)
    display_maze(maze_file)
