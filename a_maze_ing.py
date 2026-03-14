from mazegen import Parsing, error_handeling
from mazegen import MazeGenerator
import os
import sys
from mazegen import display_maze
from mazegen import BFS
from mazegen import hexa_display
import random


def main(filename: str) -> None:
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
            random.seed(seed)
        algo = parsed_Values.get("algo", "DFS")
        maze_a = MazeGenerator(parsed_Values["height"], parsed_Values["width"],
                               algo, parsed_Values["perfect"])
        maze_set = maze_a.generate_maze()
        error_handeling.check_cell_42(maze_set,
                                      parsed_Values["entry"], "entry")
        error_handeling.check_cell_42(maze_set,
                                      parsed_Values["exit"], "exit")
        hexa_display.print_maze_hex(maze_set, parsed_Values)
        path = BFS.bfs_solve(maze_set, parsed_Values["entry"],
                             parsed_Values["exit"],
                             parsed_Values["height"],
                             parsed_Values["width"])
        hexa_display.write_path(path, parsed_Values)
        project_dir = os.path.dirname(os.path.abspath(filename))
        maze_file = os.path.join(project_dir, parsed_Values["output"])
        display_maze(maze_file)
    except ValueError as e:
        print(e)


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 a_maze_ing.py config.txt")
        sys.exit(1)
    config_path = sys.argv[1]
    main(config_path)
