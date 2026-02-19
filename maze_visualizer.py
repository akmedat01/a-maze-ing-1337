import sys

NORTH = "▔"
SOUTH = "▁"
WEST = "▌"
EAST = "▐"
SPACE = " "
CELL_W = 3


def load_mazefile(filename: str) -> list[list[str]]:
    with open(filename, "r") as f:
        lines = [line.strip() for line in f.read().splitlines() if line.strip()]
    return [list(line) for line in lines]


def hexa_to_walls(hexa_value: str) -> dict[str, bool]:
    """Convert a single hex character to its 4 walls.

    north = 8 (bit 3)
    east  = 4 (bit 2)
    south = 2 (bit 1)
    west  = 1 (bit 0)
    """
    n = int(hexa_value, 16)
    return {
        "north": bool(n & 8),  # 8
        "east":  bool(n & 4),  # 4
        "south": bool(n & 2),  # 2
        "west":  bool(n & 1),  # 1
    }


def draw_maze(grid: list[list[str]]) -> None:
    rows = len(grid)
    cols = len(grid[0])

    def w(y: int, x: int) -> dict[str, bool]:
        return hexa_to_walls(grid[y][x])

    def border_line(y: int, side: str) -> str:
        line = ""
        char = NORTH if side == "north" else SOUTH
        for x in range(cols):
            walls = w(y, x)
            left = WEST if walls["west"] else (char if walls[side] else SPACE)
            segment = char * CELL_W if walls[side] else SPACE * CELL_W
            line += left + segment
        line += EAST if w(y, cols - 1)["east"] else SPACE
        return line

    def middle_line(y: int) -> str:
        line = ""
        for x in range(cols):
            walls = w(y, x)
            left = WEST if walls["west"] else SPACE
            line += left + SPACE * CELL_W
        line += EAST if w(y, cols - 1)["east"] else SPACE
        return line

    print(border_line(0, "north"))
    for y in range(rows):
        print(middle_line(y))
        print(border_line(y, "south"))


def main() -> None:
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <maze_file>")
        sys.exit(1)
    try:
        grid = load_mazefile(sys.argv[1])
    except FileNotFoundError:
        print(f"Error: file '{sys.argv[1]}' not found.")
        sys.exit(1)
    if not grid or not grid[0]:
        print("Error: maze file is empty or malformed.")
        sys.exit(1)
    draw_maze(grid)


if __name__ == "__main__":
    main()
