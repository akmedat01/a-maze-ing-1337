from typing import Any, Dict, List

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]


class hexa_display:
    @classmethod
    def convert_maze_col(cls, col: dict[str, bool]) -> str:
        i = 0
        if col["north"]:
            i += 1
        if col["east"]:
            i += 2
        if col["south"]:
            i += 4
        if col["west"]:
            i += 8
        return hex(i)[2]

    @classmethod
    def print_maze_hex(cls, maze: Maze, parsed_values: Dict[str, Any]) -> None:
        entry = parsed_values["entry"]
        exit_ = parsed_values["exit"]
        with open(parsed_values["output"], "w") as maze_file:
            for row in maze:
                for col in row:
                    a = cls.convert_maze_col(col)
                    if a == 'a':
                        maze_file.write("A")
                    elif a == 'b':
                        maze_file.write("B")
                    elif a == 'c':
                        maze_file.write("C")
                    elif a == 'd':
                        maze_file.write("D")
                    elif a == 'e':
                        maze_file.write("E")
                    elif a == "f":
                        maze_file.write("F")
                    else:
                        maze_file.write(a)
                maze_file.write("\n")
            maze_file.write("\n")
            maze_file.write(f"({entry[1]}, {entry[0]})\n")
            maze_file.write(f"({exit_[1]}, {exit_[0]})\n")

    @classmethod
    def write_path(cls, path: str, parsed_values: Dict[str, Any]) -> None:
        with open(parsed_values["output"], "a+") as maze_file:
            maze_file.write(path + "\n")
