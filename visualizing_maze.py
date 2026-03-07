import curses
import importlib
import os
import re
import sys
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]
Coord = Tuple[int, int]

WALL_CH = "█"
SPACE_CH = " "

COLOR_WALL_BASE = 10
COLOR_ENTRY = 1
COLOR_EXIT = 2
COLOR_PATH = 3
COLOR_42 = 4

WALL_COLORS: List[Tuple[int, int]] = [
    (curses.COLOR_WHITE,   curses.COLOR_BLACK),
    (curses.COLOR_YELLOW,  curses.COLOR_BLACK),
    (curses.COLOR_GREEN,   curses.COLOR_BLACK),
    (curses.COLOR_RED,     curses.COLOR_BLACK),
    (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    (curses.COLOR_CYAN,    curses.COLOR_BLACK),
]

ANIM_DELAY: float = 0.01


def _parse_maze_file(
    filepath: str,
) -> Tuple[Maze, Coord, Coord, int, int]:
    """Parse maze.txt into a 2-D list of cell dicts.

    Accepts any format: rows on separate lines or space-separated.
    Hex digit bits: bit3=north, bit2=east, bit1=south, bit0=west.
    A set bit means the wall is closed.

    Args:
        filepath: Path to the maze.txt file.

    Returns:
        Tuple of (maze, entry, exit_, height, width).

    Raises:
        FileNotFoundError: If filepath does not exist.
        ValueError: If the file format is invalid.
    """
    with open(filepath, "r") as f:
        content = f.read()

    def _coord(s: str) -> Coord:
        """Parse '(col, row)' into (row, col).

        Args:
            s: Coordinate string from maze.txt.

        Returns:
            (row, col) tuple.
        """
        s = s.strip().strip("()")
        a, b = s.split(",")
        return (int(b.strip()), int(a.strip()))

    coords = re.findall(r"\(\s*\d+\s*,\s*\d+\s*\)", content)
    if len(coords) < 2:
        raise ValueError("maze file missing entry/exit coordinates")

    entry = _coord(coords[0])
    exit_ = _coord(coords[1])

    clean = re.sub(r"\(\s*\d+\s*,\s*\d+\s*\)", "", content)
    tokens = re.findall(r"[0-9A-Fa-f]+", clean)
    hex_rows = [t for t in tokens if len(t) > 1]

    if not hex_rows:
        raise ValueError("maze file contains no hex rows")

    maze: Maze = []
    for token in hex_rows:
        row: MazeRow = []
        for ch in token:
            v = int(ch, 16)
            row.append({
                "north": bool(v & 8),
                "east":  bool(v & 4),
                "south": bool(v & 2),
                "west":  bool(v & 1),
            })
        maze.append(row)

    height = len(maze)
    width = len(maze[0]) if maze else 0
    return maze, entry, exit_, height, width


def _build_grid(
    maze: Maze,
    height: int,
    width: int,
) -> List[List[bool]]:
    """Build a corner-based boolean grid from the maze.

    The grid has dimensions (height*2+1) x (width*2+1).
    True means wall, False means open passage.
    Even row/col indices are wall corners or wall segments.
    Odd row/col indices are cell centers.

    Args:
        maze: 2-D list of cell dicts.
        height: Number of maze rows.
        width: Number of maze columns.

    Returns:
        2-D boolean grid where True = wall.
    """
    gh = height * 2 + 1
    gw = width * 2 + 1
    grid = [[True] * gw for _ in range(gh)]

    for r in range(height):
        for c in range(width):
            cell = maze[r][c]
            gr = r * 2 + 1
            gc = c * 2 + 1
            grid[gr][gc] = False
            if not cell["north"]:
                grid[gr - 1][gc] = False
            if not cell["south"]:
                grid[gr + 1][gc] = False
            if not cell["west"]:
                grid[gr][gc - 1] = False
            if not cell["east"]:
                grid[gr][gc + 1] = False

    return grid


def _solve(
    maze: Maze,
    entry: Coord,
    exit_: Coord,
    height: int,
    width: int,
) -> str:
    """Return shortest path as N/S/E/W string using BFS.

    Args:
        maze: 2-D list of cell dicts.
        entry: (row, col) start cell.
        exit_: (row, col) end cell.
        height: Number of rows.
        width: Number of columns.

    Returns:
        Direction string, empty string if no path exists.
    """
    moves: List[Tuple[str, int, int, str]] = [
        ("N", -1,  0, "north"),
        ("S",  1,  0, "south"),
        ("E",  0,  1, "east"),
        ("W",  0, -1, "west"),
    ]
    queue: deque[Coord] = deque([entry])
    visited = {entry}
    parent: Dict[Coord, Optional[Tuple[Coord, str]]] = {
        entry: None
    }

    while queue:
        r, c = queue.popleft()
        if (r, c) == exit_:
            break
        for letter, dr, dc, wk in moves:
            nr, nc = r + dr, c + dc
            if (nr, nc) in visited:
                continue
            if not (0 <= nr < height and 0 <= nc < width):
                continue
            if maze[r][c][wk]:
                continue
            visited.add((nr, nc))
            parent[(nr, nc)] = ((r, c), letter)
            queue.append((nr, nc))

    if exit_ not in parent:
        return ""
    letters: List[str] = []
    cur: Coord = exit_
    while parent[cur] is not None:
        prev, letter = parent[cur]  # type: ignore[misc]
        letters.append(letter)
        cur = prev
    letters.reverse()
    return "".join(letters)


def _path_grid_coords(entry: Coord, path: str) -> set:
    """Return corner-grid coords of the full solution path.

    Includes both cell centers and the wall-segment coords
    between consecutive cells so the path draws as a solid
    continuous line through the corridors.

    Args:
        entry: Starting maze cell (row, col).
        path: Direction string from _solve.

    Returns:
        Set of (grid_row, grid_col) coordinates.
    """
    r, c = entry
    coords: set = {(r * 2 + 1, c * 2 + 1)}
    for d in path:
        if d == "N":
            coords.add((r * 2, c * 2 + 1))
            r -= 1
        elif d == "S":
            coords.add((r * 2 + 2, c * 2 + 1))
            r += 1
        elif d == "E":
            coords.add((r * 2 + 1, c * 2 + 2))
            c += 1
        elif d == "W":
            coords.add((r * 2 + 1, c * 2))
            c -= 1
        coords.add((r * 2 + 1, c * 2 + 1))
    return coords


def build_42_pattern(
    height: int,
    width: int,
) -> Optional[List[Coord]]:
    """Return maze cell coords forming a '42' in the center.

    The '4' digit is 5 cols wide, '2' is 5 cols wide, with a
    1-col gap. Total shape is 11 cols x 7 rows.
    Returns None if the maze is too small to fit the pattern.

    Args:
        height: Number of maze rows.
        width: Number of maze columns.

    Returns:
        List of (row, col) coords, or None if maze too small.
    """
    pat_h = 7
    pat_w = 11
    if height < pat_h + 2 or width < pat_w + 2:
        return None

    sr = (height - pat_h) // 2
    sc = (width - pat_w) // 2

    digit_4: List[Tuple[int, int]] = [
        (0, 0), (1, 0), (2, 0), (3, 0), (3, 1),
        (3, 2), (3, 3), (3, 4), (4, 4), (5, 4),
        (6, 4),
    ]

    digit_2: List[Tuple[int, int]] = [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 4), (2, 4), (3, 0), (3, 1), (3, 2),
        (3, 3), (3, 4), (4, 0), (5, 0),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4),
    ]

    cells: List[Coord] = []
    for dr, dc in digit_4:
        cells.append((sr + dr, sc + dc))
    for dr, dc in digit_2:
        cells.append((sr + dr, sc + 6 + dc))

    return cells


class MazeRenderer:
    """Render a maze from maze.txt using a corner-based grid.

    Builds a (height*2+1) x (width*2+1) boolean grid where
    each cell occupies one character on screen. Wall segments
    are drawn as solid Unicode block characters.
    Path renders as a solid cyan line through the corridors.
    The '42' pattern is shown as blue filled cells in the center.

    Attributes:
        _maze_path: Absolute path to maze.txt.
        _config_path: Absolute path to config.txt.
        _maze: 2-D list of cell dicts.
        _grid: Corner-based boolean wall grid.
        _entry: Entry cell (row, col).
        _exit: Exit cell (row, col).
        _height: Number of maze rows.
        _width: Number of maze columns.
        _pattern_42: 42-pattern cell coordinates.
        _pattern_42_set: Set for fast lookup.
        _path: Solution direction string.
        _path_grid: Corner-grid set of path coords.
        _show_path: Whether path overlay is active.
        _wall_idx: Index into WALL_COLORS list.
        _stdscr: Active curses window.
    """

    def __init__(
        self,
        maze_path: str,
        pattern_42_cells: Optional[List[Coord]] = None,
    ) -> None:
        """Initialise renderer by reading maze.txt.

        Args:
            maze_path: Path to the maze.txt file.
            pattern_42_cells: Optional 42-pattern coordinates.
                If None, auto-generated from maze dimensions.

        Raises:
            FileNotFoundError: If maze_path does not exist.
            ValueError: If the maze file format is invalid.
        """
        self._maze_path = os.path.abspath(maze_path)
        self._config_path = os.path.join(
            os.path.dirname(self._maze_path), "config.txt"
        )
        (
            self._maze,
            self._entry,
            self._exit,
            self._height,
            self._width,
        ) = _parse_maze_file(self._maze_path)
        self._grid = _build_grid(
            self._maze, self._height, self._width
        )
        if pattern_42_cells is not None:
            self._pattern_42: List[Coord] = pattern_42_cells
        else:
            p42 = build_42_pattern(self._height, self._width)
            self._pattern_42 = p42 if p42 is not None else []
        self._pattern_42_set: set = set(self._pattern_42)
        self._path = _solve(
            self._maze, self._entry, self._exit,
            self._height, self._width,
        )
        self._path_grid: set = (
            _path_grid_coords(self._entry, self._path)
            if self._path else set()
        )
        self._show_path = False
        self._wall_idx = 0
        self._stdscr: Any = None

    def _init_colors(self) -> None:
        """Initialise all curses colour pairs.

        Returns:
            None
        """
        curses.start_color()
        curses.use_default_colors()
        for i, (fg, bg) in enumerate(WALL_COLORS):
            curses.init_pair(COLOR_WALL_BASE + i, fg, bg)
        curses.init_pair(
            COLOR_ENTRY, curses.COLOR_BLACK, curses.COLOR_GREEN
        )
        curses.init_pair(
            COLOR_EXIT, curses.COLOR_BLACK, curses.COLOR_RED
        )
        curses.init_pair(
            COLOR_PATH, curses.COLOR_BLACK, curses.COLOR_YELLOW
        )
        curses.init_pair(
            COLOR_42, curses.COLOR_BLACK, curses.COLOR_BLUE
        )

    def _wcp(self) -> int:
        """Return the active wall colour pair number.

        Returns:
            Curses colour pair integer.
        """
        return COLOR_WALL_BASE + self._wall_idx

    def _put(
        self, y: int, x: int, ch: str, attr: int = 0
    ) -> None:
        """Write a character to the screen safely.

        Args:
            y: Screen row.
            x: Screen column.
            ch: Character to draw.
            attr: Curses attribute or colour pair.

        Returns:
            None
        """
        try:
            self._stdscr.addstr(y, x, ch, attr)
        except curses.error:
            pass

    def _draw_grid_row(self, grid_row: int) -> None:
        """Draw one row of the corner grid onto the screen.

        Each grid column is 2 screen chars wide to fix aspect ratio.
        Path is drawn as solid cyan blocks through open passages.

        Args:
            grid_row: Row index in the corner grid (0..height*2).

        Returns:
            None
        """
        wp = curses.color_pair(self._wcp())
        ep = curses.color_pair(COLOR_ENTRY)
        xp = curses.color_pair(COLOR_EXIT)
        pp = curses.color_pair(COLOR_PATH)
        fp = curses.color_pair(COLOR_42)

        gw = self._width * 2 + 1
        screen_y = grid_row + 1

        for gc in range(gw):
            screen_x = gc * 2 + 1
            is_wall = self._grid[grid_row][gc]
            is_cell = (grid_row % 2 == 1 and gc % 2 == 1)
            maze_r = (grid_row - 1) // 2
            maze_c = (gc - 1) // 2
            on_path = (
                self._show_path
                and (grid_row, gc) in self._path_grid
            )

            if is_wall:
                self._put(screen_y, screen_x, WALL_CH, wp)
                self._put(screen_y, screen_x + 1, WALL_CH, wp)

            elif on_path:
                bold_pp = pp | curses.A_BOLD
                self._put(screen_y, screen_x, WALL_CH, bold_pp)
                self._put(screen_y, screen_x + 1, WALL_CH, bold_pp)

            elif is_cell and (maze_r, maze_c) == self._entry:
                self._put(screen_y, screen_x, WALL_CH, ep)
                self._put(screen_y, screen_x + 1, WALL_CH, ep)

            elif is_cell and (maze_r, maze_c) == self._exit:
                self._put(screen_y, screen_x, WALL_CH, xp)
                self._put(screen_y, screen_x + 1, WALL_CH, xp)

            elif (
                is_cell
                and (maze_r, maze_c) in self._pattern_42_set
            ):
                self._put(screen_y, screen_x, WALL_CH, fp)
                self._put(screen_y, screen_x + 1, WALL_CH, fp)

            else:
                self._put(screen_y, screen_x, SPACE_CH)
                self._put(screen_y, screen_x + 1, SPACE_CH)

    def _draw_full_grid(self) -> None:
        """Draw the entire corner grid.

        Returns:
            None
        """
        gh = self._height * 2 + 1
        for gr in range(gh):
            self._draw_grid_row(gr)

    def _draw_menu(self) -> None:
        """Draw the numbered menu below the maze.

        Returns:
            None
        """
        state = "ON" if self._show_path else "OFF"
        base_y = self._height * 2 + 3
        self._put(base_y, 0, "==== A-Maze-ing ====", curses.A_BOLD)
        self._put(base_y + 1, 0, "1. Re-generate a new maze")
        self._put(
            base_y + 2, 0,
            f"2. Show/Hide path from entry to exit  [{state}]"
        )
        self._put(base_y + 3, 0, "3. Rotate maze colors")
        self._put(base_y + 4, 0, "4. Quit")
        self._put(
            base_y + 5, 0, "Choice (1-4): ", curses.A_BOLD
        )

    def _full_redraw(self) -> None:
        """Clear and redraw the entire scene.

        Returns:
            None
        """
        self._stdscr.clear()
        self._draw_full_grid()
        self._draw_menu()
        self._stdscr.refresh()

    def _animate(self) -> None:
        """Reveal the maze row by row from top to bottom.

        Returns:
            None
        """
        self._stdscr.clear()
        self._stdscr.refresh()
        gh = self._height * 2 + 1
        for gr in range(gh):
            self._draw_grid_row(gr)
            if gr % 2 == 0:
                self._stdscr.refresh()
                time.sleep(ANIM_DELAY)
        self._draw_menu()
        self._stdscr.refresh()

    def _reload(self) -> None:
        """Re-parse maze.txt and recompute grid and path.

        Returns:
            None
        """
        (
            self._maze,
            self._entry,
            self._exit,
            self._height,
            self._width,
        ) = _parse_maze_file(self._maze_path)
        self._grid = _build_grid(
            self._maze, self._height, self._width
        )
        p42 = build_42_pattern(self._height, self._width)
        self._pattern_42 = p42 if p42 is not None else []
        self._pattern_42_set = set(self._pattern_42)
        self._path = _solve(
            self._maze, self._entry, self._exit,
            self._height, self._width,
        )
        self._path_grid = (
            _path_grid_coords(self._entry, self._path)
            if self._path else set()
        )

    def _action_regenerate(self) -> None:
        """Generate a new maze, write it, reload and animate.

        Returns:
            None
        """
        project_dir = os.path.dirname(self._maze_path)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
        try:
            amaze = importlib.import_module("a_maze_ing")
            importlib.reload(amaze)
            gen = amaze.MazeGenerator()
            gen.generate_maze(self._config_path)
        except Exception as exc:
            self._stdscr.clear()
            self._put(0, 0, f"Error: {exc}", curses.A_BOLD)
            self._stdscr.refresh()
            self._stdscr.getch()
            self._full_redraw()
            return
        self._show_path = False
        self._reload()
        self._animate()

    def _action_toggle_path(self) -> None:
        """Toggle the solution path on or off and redraw.

        Returns:
            None
        """
        self._show_path = not self._show_path
        self._full_redraw()

    def _action_rotate_color(self) -> None:
        """Advance to the next wall colour and redraw.

        Returns:
            None
        """
        self._wall_idx = (self._wall_idx + 1) % len(WALL_COLORS)
        self._full_redraw()

    def _event_loop(self) -> None:
        """Wait for a menu choice and dispatch the action.

        Returns:
            None
        """
        self._stdscr.keypad(True)
        while True:
            key = self._stdscr.getch()
            if key == ord("1"):
                self._action_regenerate()
            elif key == ord("2"):
                self._action_toggle_path()
            elif key == ord("3"):
                self._action_rotate_color()
            elif key in (ord("4"), ord("q"), ord("Q"), 27):
                break

    def _run(self, stdscr: Any) -> None:
        """Initialise curses, animate, then enter the event loop.

        Args:
            stdscr: Curses window provided by curses.wrapper.

        Returns:
            None
        """
        self._stdscr = stdscr
        curses.curs_set(0)
        self._init_colors()
        self._animate()
        self._event_loop()

    def run(self) -> None:
        """Launch the curses visualiser.

        Returns:
            None
        """
        try:
            curses.wrapper(self._run)
        except Exception as exc:
            print(f"[draw_maze] error: {exc}")


def display_maze(
    maze_path: str,
    pattern_42_cells: Optional[List[Coord]] = None,
) -> None:
    """Read maze.txt and open the curses maze visualiser.

    Args:
        maze_path: Path to the maze.txt file.
        pattern_42_cells: Optional 42-pattern cell coordinates.
            If None, the pattern is auto-generated from maze size.

    Returns:
        None
    """
    renderer = MazeRenderer(maze_path, pattern_42_cells)
    renderer.run()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 draw_maze.py path/to/maze.txt")
        sys.exit(1)
    display_maze(sys.argv[1])