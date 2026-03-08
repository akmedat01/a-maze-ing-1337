import curses
import importlib
import os
import re
import sys
import time
from collections import deque
from typing import Any, Dict, Generator, List, Optional, Set, Tuple

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]
Coord = Tuple[int, int]

WALL_CH = "█"
SPACE_CH = " "
PATH_CH = "·"

COLOR_WALL_BASE = 10
COLOR_PATH_BASE = 20
COLOR_ENTRY = 1
COLOR_EXIT = 2
COLOR_PATH = 3
COLOR_42_WALL = 4

WALL_COLORS: List[Tuple[int, int]] = [
    (curses.COLOR_WHITE, curses.COLOR_BLACK),
    (curses.COLOR_YELLOW, curses.COLOR_BLACK),
    (curses.COLOR_GREEN, curses.COLOR_BLACK),
    (curses.COLOR_RED, curses.COLOR_BLACK),
    (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    (curses.COLOR_CYAN, curses.COLOR_BLACK),
]

PATH_COLORS: List[Tuple[int, int]] = [
    (curses.COLOR_YELLOW, curses.COLOR_BLACK),
    (curses.COLOR_CYAN, curses.COLOR_BLACK),
    (curses.COLOR_GREEN, curses.COLOR_BLACK),
    (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    (curses.COLOR_RED, curses.COLOR_BLACK),
    (curses.COLOR_WHITE, curses.COLOR_BLACK),
]

MAZE_ANIM_DELAY: float = 0.005
MAZE_ANIM_BATCH: int = 6
PATH_ANIM_DELAY: float = 0.008


def _parse_maze_file(
    filepath: str,
) -> Tuple[Maze, Coord, Coord, int, int]:
    """Parse maze.txt into a 2-D list of cell dicts.

    Bit encoding: bit3=north, bit2=east, bit1=south, bit0=west.
    A set bit means the wall is closed.
    """
    with open(filepath, "r") as fh:
        lines = fh.readlines()

    def _coord(s: str) -> Coord:
        """Parse '(col, row)' into (row, col)."""
        s = s.strip().strip("()")
        col_str, row_str = s.split(",")
        return (int(row_str.strip()), int(col_str.strip()))

    hex_lines: List[str] = []
    meta_lines: List[str] = []
    separator_found = False

    for line in lines:
        stripped = line.strip()
        if not separator_found:
            if stripped == "":
                separator_found = True
            elif re.fullmatch(r"[0-9A-Fa-f]+", stripped):
                hex_lines.append(stripped)
        else:
            if stripped:
                meta_lines.append(stripped)

    if not separator_found or len(meta_lines) < 2:
        raise ValueError("maze file missing entry/exit coordinates")

    entry = _coord(meta_lines[0])
    exit_ = _coord(meta_lines[1])

    if not hex_lines:
        raise ValueError("maze file contains no hex rows")

    maze: Maze = []
    for token in hex_lines:
        row: MazeRow = []
        for ch in token:
            v = int(ch, 16)
            row.append({
                "north": bool(v & 8),
                "east": bool(v & 4),
                "south": bool(v & 2),
                "west": bool(v & 1),
            })
        maze.append(row)

    height = len(maze)
    width = len(maze[0]) if maze else 0
    return maze, entry, exit_, height, width


def _build_closed_grid(height: int, width: int) -> List[List[bool]]:
    """Return a fully-walled (2h+1)x(2w+1) boolean corner grid."""
    return [[True] * (width * 2 + 1) for _ in range(height * 2 + 1)]


def _solve(
    maze: Maze,
    entry: Coord,
    exit_: Coord,
    height: int,
    width: int,
) -> str:
    """Return the shortest path as an N/S/E/W string via BFS."""
    moves: List[Tuple[str, int, int, str]] = [
        ("N", -1, 0, "north"),
        ("S", 1, 0, "south"),
        ("E", 0, 1, "east"),
        ("W", 0, -1, "west"),
    ]
    queue: deque[Coord] = deque([entry])
    visited = {entry}
    parent: Dict[Coord, Optional[Tuple[Coord, str]]] = {entry: None}

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
        prev, letter = parent[cur]
        letters.append(letter)
        cur = prev
    letters.reverse()
    return "".join(letters)


def _path_steps(entry: Coord, path: str) -> List[Tuple[int, int]]:
    """Return corner-grid coords along the solution path with segments."""
    r, c = entry
    steps: List[Tuple[int, int]] = [(r * 2 + 1, c * 2 + 1)]
    for d in path:
        if d == "N":
            steps.append((r * 2, c * 2 + 1))
            r -= 1
        elif d == "S":
            steps.append((r * 2 + 2, c * 2 + 1))
            r += 1
        elif d == "E":
            steps.append((r * 2 + 1, c * 2 + 2))
            c += 1
        elif d == "W":
            steps.append((r * 2 + 1, c * 2))
            c -= 1
        steps.append((r * 2 + 1, c * 2 + 1))
    return steps


def _maze_reveal_gen(
    maze: Maze,
    height: int,
    width: int,
    entry: Coord,
    blocked_42: Set[Coord],
) -> Generator[Tuple[int, int, bool], None, None]:
    """Yield corner-grid coords in BFS wave-order, skipping 42 cells."""
    dirs = [
        (-1, 0, "north", "south"),
        (1, 0, "south", "north"),
        (0, 1, "east", "west"),
        (0, -1, "west", "east"),
    ]

    visited: List[List[bool]] = [[False] * width for _ in range(height)]
    er, ec = entry
    visited[er][ec] = True
    queue: deque[Coord] = deque([(er, ec)])

    while queue:
        r, c = queue.popleft()
        gr, gc = r * 2 + 1, c * 2 + 1
        yield (gr, gc, True)

        for dr, dc, wall_key, opposite_key in dirs:
            nr, nc = r + dr, c + dc

            if (
                0 <= nr < height
                and 0 <= nc < width
                and not maze[r][c][wall_key]
                and not maze[nr][nc][opposite_key]
            ):
                yield (gr + dr, gc + dc, True)

            if (
                0 <= nr < height
                and 0 <= nc < width
                and not visited[nr][nc]
                and not maze[r][c][wall_key]
                and not maze[nr][nc][opposite_key]
            ):
                visited[nr][nc] = True
                queue.append((nr, nc))

    for r in range(height):
        for c in range(width):
            if not visited[r][c]:
                if (r, c) in blocked_42:
                    continue
                gr, gc = r * 2 + 1, c * 2 + 1
                yield (gr, gc, True)
                cell = maze[r][c]

                if r > 0 and not cell["north"] and not maze[r - 1][c]["south"]:
                    yield (gr - 1, gc, True)
                if (
                    r < height - 1 and not cell["south"]
                    and not maze[r + 1][c]["north"]
                ):
                    yield (gr + 1, gc, True)
                if c > 0 and not cell["west"] and not maze[r][c - 1]["east"]:
                    yield (gr, gc - 1, True)
                if (
                    c < width - 1 and not cell["east"]
                    and not maze[r][c + 1]["west"]
                ):
                    yield (gr, gc + 1, True)


def build_42_pattern(height: int, width: int) -> Optional[List[Coord]]:
    """Return maze-cell coords forming the '42' digits, centred."""
    pat_h, pat_w = 7, 11
    if height < pat_h + 2 or width < pat_w + 2:
        return None

    sr = (height - pat_h) // 2
    sc = (width - pat_w) // 2

    digit_4: List[Tuple[int, int]] = [
        (0, 0),
        (1, 0),
        (2, 0), (2, 2),
        (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 2),
        (5, 2),
        (6, 2),
    ]
    digit_2: List[Tuple[int, int]] = [
        (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
        (1, 4),
        (2, 4),
        (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
        (4, 0),
        (5, 0),
        (6, 0), (6, 1), (6, 2), (6, 3), (6, 4),
    ]

    cells: List[Coord] = []
    for dr, dc in digit_4:
        cells.append((sr + dr, sc + dc))
    for dr, dc in digit_2:
        cells.append((sr + dr, sc + 6 + dc))
    return cells


def _build_42_mask_sets(
    cells: List[Coord],
) -> Tuple[Set[Coord], Set[Coord], Set[Coord]]:
    """Build 42 sets on the corner-grid.

    boundary_set:
        coords that belong to the blocked 42 shape and stay normal wall color.

    fill_set:
        only the true stroke centers/segments that get highlight color.

    mask_set:
        union of boundary + fill.
    """
    if not cells:
        return set(), set(), set()

    cell_set: Set[Coord] = set(cells)

    boundary_set: Set[Coord] = set()
    fill_set: Set[Coord] = set()

    for r, c in cells:
        gr, gc = r * 2 + 1, c * 2 + 1

        fill_set.add((gr, gc))

        boundary_set.add((gr - 1, gc))
        boundary_set.add((gr + 1, gc))
        boundary_set.add((gr, gc - 1))
        boundary_set.add((gr, gc + 1))

        if (r - 1, c) in cell_set:
            fill_set.add((gr - 1, gc))
        if (r + 1, c) in cell_set:
            fill_set.add((gr + 1, gc))
        if (r, c - 1) in cell_set:
            fill_set.add((gr, gc - 1))
        if (r, c + 1) in cell_set:
            fill_set.add((gr, gc + 1))

    boundary_set -= fill_set
    mask_set = boundary_set | fill_set
    return mask_set, boundary_set, fill_set


class MazeRenderer:
    """Curses-based interactive maze visualiser."""

    def __init__(
        self,
        maze_path: str,
        pattern_42_cells: Optional[List[Coord]] = None,
    ) -> None:
        """Initialise by parsing maze.txt and computing all derived state."""
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

        self._grid = _build_closed_grid(self._height, self._width)

        p42: List[Coord] = (
            pattern_42_cells if pattern_42_cells is not None
            else (build_42_pattern(self._height, self._width) or [])
        )

        self._blocked_42: Set[Coord] = set(p42)
        self._42_mask_set: Set[Coord]
        self._42_boundary_set: Set[Coord]
        self._42_fill_set: Set[Coord]

        (
            self._42_mask_set,
            self._42_boundary_set,
            self._42_fill_set,
        ) = _build_42_mask_sets(p42)

        self._path = _solve(
            self._maze,
            self._entry,
            self._exit,
            self._height,
            self._width,
        )
        self._path_steps: List[Tuple[int, int]] = (
            _path_steps(self._entry, self._path) if self._path else []
        )
        self._path_drawn: Set[Coord] = set()
        self._show_path = False
        self._show_42_color = False
        self._wall_idx = 0
        self._path_idx = 0
        self._maze_drawn = False
        self._stdscr: Any = None

    def _required_size(self) -> Tuple[int, int]:
        """Return minimum terminal size needed for maze + menu."""
        rows = self._height * 2 + 11
        cols = (self._width * 2 + 1) * 2 + 3
        return rows, cols

    def _has_enough_space(self) -> bool:
        """Return True if terminal is large enough for maze + menu."""
        max_y, max_x = self._stdscr.getmaxyx()
        need_y, need_x = self._required_size()
        return max_y >= need_y and max_x >= need_x

    def _init_colors(self) -> None:
        """Initialise all curses colour pairs."""
        curses.start_color()
        curses.use_default_colors()

        for i, (fg, bg) in enumerate(WALL_COLORS):
            curses.init_pair(COLOR_WALL_BASE + i, fg, bg)
        for i, (fg, bg) in enumerate(PATH_COLORS):
            curses.init_pair(COLOR_PATH_BASE + i, fg, bg)

        curses.init_pair(
            COLOR_ENTRY, curses.COLOR_BLACK, curses.COLOR_GREEN
        )
        curses.init_pair(
            COLOR_EXIT, curses.COLOR_BLACK, curses.COLOR_RED
        )
        curses.init_pair(
            COLOR_PATH, curses.COLOR_YELLOW, curses.COLOR_BLACK
        )
        curses.init_pair(
            COLOR_42_WALL, curses.COLOR_MAGENTA, curses.COLOR_BLACK
        )

    def _wcp(self) -> int:
        """Return the active wall colour-pair number."""
        return COLOR_WALL_BASE + self._wall_idx

    def _pcp(self) -> int:
        """Return the active path colour-pair number."""
        return COLOR_PATH_BASE + self._path_idx

    def _put(self, y: int, x: int, ch: str, attr: int = 0) -> None:
        """Write one character, silently ignoring out-of-bounds errors."""
        try:
            self._stdscr.addstr(y, x, ch, attr)
        except curses.error:
            pass

    def _draw_too_small(self) -> None:
        """Show a message when terminal size is too small."""
        self._stdscr.clear()
        max_y, max_x = self._stdscr.getmaxyx()
        need_y, need_x = self._required_size()

        messages = [
            "Window too small for the maze.",
            f"Current size: {max_x}x{max_y}",
            f"Needed size : {need_x}x{need_y}",
            "Please enlarge the terminal window.",
            "Press Q or 4 to quit.",
        ]

        start_y = max(0, max_y // 2 - len(messages) // 2)
        for i, msg in enumerate(messages):
            x = max(0, (max_x - len(msg)) // 2)
            self._put(start_y + i, x, msg, curses.A_BOLD)

        self._stdscr.refresh()

    def _draw_cell(self, grid_row: int, gc: int) -> None:
        """Draw one corner-grid cell.

        Priority:
        entry/exit > path dot > 42 mask > wall > open space
        """
        wp = curses.color_pair(self._wcp())
        ep = curses.color_pair(COLOR_ENTRY)
        xp = curses.color_pair(COLOR_EXIT)
        pp = curses.color_pair(self._pcp()) | curses.A_BOLD
        f42 = curses.color_pair(COLOR_42_WALL) | curses.A_BOLD

        sy = grid_row + 1
        sx = gc * 2 + 1

        is_wall = self._grid[grid_row][gc]
        is_cell = (grid_row % 2 == 1 and gc % 2 == 1)
        maze_r = (grid_row - 1) // 2
        maze_c = (gc - 1) // 2
        on_path = (grid_row, gc) in self._path_drawn

        in_42_mask = (grid_row, gc) in self._42_mask_set
        in_42_fill = (grid_row, gc) in self._42_fill_set

        if self._maze_drawn and is_cell and (maze_r, maze_c) == self._entry:
            self._put(sy, sx, WALL_CH, ep)
            self._put(sy, sx + 1, WALL_CH, ep)
            return

        if self._maze_drawn and is_cell and (maze_r, maze_c) == self._exit:
            self._put(sy, sx, WALL_CH, xp)
            self._put(sy, sx + 1, WALL_CH, xp)
            return

        if on_path:
            self._put(sy, sx, PATH_CH, pp)
            self._put(sy, sx + 1, PATH_CH, pp)
            return

        if in_42_mask:
            if self._show_42_color and in_42_fill:
                self._put(sy, sx, WALL_CH, f42)
                self._put(sy, sx + 1, WALL_CH, f42)
            else:
                self._put(sy, sx, WALL_CH, wp)
                self._put(sy, sx + 1, WALL_CH, wp)
            return

        if is_wall:
            self._put(sy, sx, WALL_CH, wp)
            self._put(sy, sx + 1, WALL_CH, wp)
            return

        self._put(sy, sx, SPACE_CH)
        self._put(sy, sx + 1, SPACE_CH)

    def _draw_full_grid(self) -> None:
        """Redraw every corner-grid cell from the current live state."""
        for gr in range(self._height * 2 + 1):
            for gc in range(self._width * 2 + 1):
                self._draw_cell(gr, gc)

    def _draw_menu(self) -> None:
        """Render the interactive menu below the maze."""
        path_state = "ON" if self._show_path else "OFF"
        s42 = "ON" if self._show_42_color else "OFF"
        base_y = self._height * 2 + 3

        self._put(base_y, 0, "==== A-Maze-ing ====", curses.A_BOLD)
        self._put(base_y + 1, 0, "1. Re-generate a new maze")
        self._put(
            base_y + 2, 0,
            f"2. Show/Hide path from entry to exit  [{path_state}]",
        )
        self._put(base_y + 3, 0, "3. Rotate maze colors")
        self._put(base_y + 4, 0, "4. Quit")
        self._put(base_y + 5, 0, f"5. Toggle 42 pattern color  [{s42}]")
        self._put(base_y + 6, 0, "6. Rotate path colors")
        self._put(base_y + 7, 0, "Choice (1-6): ", curses.A_BOLD)

    def _full_redraw(self) -> None:
        """Clear screen and redraw maze and menu from scratch."""
        if not self._has_enough_space():
            self._maze_drawn = False
            self._draw_too_small()
            return

        if not self._maze_drawn:
            self._animate_maze()
            return

        self._stdscr.clear()
        self._draw_full_grid()
        self._draw_menu()
        self._stdscr.refresh()

    def _animate_maze(self) -> None:
        """Animate maze reveal as a BFS wave; 42-blocked cells stay solid."""
        if not self._has_enough_space():
            self._maze_drawn = False
            self._draw_too_small()
            return

        self._stdscr.clear()
        self._grid = _build_closed_grid(self._height, self._width)
        self._draw_full_grid()
        self._stdscr.refresh()
        time.sleep(0.25)

        gen = _maze_reveal_gen(
            self._maze,
            self._height,
            self._width,
            self._entry,
            self._blocked_42,
        )
        batch_counter = 0

        for gr, gc, _ in gen:
            if not self._has_enough_space():
                self._maze_drawn = False
                self._draw_too_small()
                return

            self._grid[gr][gc] = False

            if (gr, gc) in self._42_mask_set:
                self._grid[gr][gc] = True

            self._draw_cell(gr, gc)
            batch_counter += 1
            if batch_counter % MAZE_ANIM_BATCH == 0:
                self._stdscr.refresh()
                time.sleep(MAZE_ANIM_DELAY)

        self._stdscr.refresh()
        self._draw_menu()
        self._stdscr.refresh()
        self._maze_drawn = True

    def _animate_path(self) -> None:
        """Draw path dots one by one along the solution route."""
        if not self._has_enough_space():
            self._draw_too_small()
            return

        self._path_drawn = set()
        pp = curses.color_pair(self._pcp()) | curses.A_BOLD

        for gr, gc in self._path_steps:
            if not self._has_enough_space():
                self._draw_too_small()
                return
            if (gr, gc) in self._42_mask_set:
                continue
            self._path_drawn.add((gr, gc))
            sy = gr + 1
            sx = gc * 2 + 1
            self._put(sy, sx, PATH_CH, pp)
            self._put(sy, sx + 1, PATH_CH, pp)
            self._stdscr.refresh()
            time.sleep(PATH_ANIM_DELAY)

    def _clear_path(self) -> None:
        """Erase path dots and restore the underlying cells."""
        old = set(self._path_drawn)
        self._path_drawn = set()
        for gr, gc in old:
            self._draw_cell(gr, gc)
        self._stdscr.refresh()

    def _reload(self) -> None:
        """Re-parse maze.txt and recompute all derived state."""
        (
            self._maze,
            self._entry,
            self._exit,
            self._height,
            self._width,
        ) = _parse_maze_file(self._maze_path)
        self._grid = _build_closed_grid(self._height, self._width)

        p42 = build_42_pattern(self._height, self._width) or []
        self._blocked_42 = set(p42)

        (
            self._42_mask_set,
            self._42_boundary_set,
            self._42_fill_set,
        ) = _build_42_mask_sets(p42)

        self._path = _solve(
            self._maze,
            self._entry,
            self._exit,
            self._height,
            self._width,
        )
        self._path_steps = (
            _path_steps(self._entry, self._path) if self._path else []
        )
        self._path_drawn = set()
        self._show_path = False
        self._maze_drawn = False

    def _action_regenerate(self) -> None:
        """Call the maze generator, reload state, and re-animate."""
        project_dir = os.path.dirname(self._maze_path)
        if project_dir not in sys.path:
            sys.path.insert(0, project_dir)
        try:
            amaze = importlib.import_module("a_maze_ing")
            importlib.reload(amaze)
            amaze.MazeGenerator().generate_maze(self._config_path)
        except Exception as exc:
            self._stdscr.clear()
            self._put(0, 0, f"Error: {exc}", curses.A_BOLD)
            self._stdscr.refresh()
            self._stdscr.getch()
            self._full_redraw()
            return
        self._reload()
        self._animate_maze()

    def _action_toggle_path(self) -> None:
        """Toggle the path overlay on or off."""
        self._show_path = not self._show_path
        if self._show_path:
            self._animate_path()
        else:
            self._clear_path()
        self._draw_menu()
        self._stdscr.refresh()

    def _action_rotate_color(self) -> None:
        """Cycle to the next wall colour."""
        self._wall_idx = (self._wall_idx + 1) % len(WALL_COLORS)
        self._full_redraw()

    def _action_toggle_42_color(self) -> None:
        """Toggle the 42-pattern highlight on or off."""
        self._show_42_color = not self._show_42_color
        self._full_redraw()

    def _action_rotate_path_color(self) -> None:
        """Cycle to the next path colour."""
        self._path_idx = (self._path_idx + 1) % len(PATH_COLORS)
        if self._show_path:
            self._full_redraw()
        else:
            self._draw_menu()
            self._stdscr.refresh()

    def _event_loop(self) -> None:
        """Block on key input and dispatch the corresponding action."""
        self._stdscr.keypad(True)

        while True:
            key = self._stdscr.getch()

            if key == curses.KEY_RESIZE:
                if self._has_enough_space():
                    if not self._maze_drawn:
                        self._animate_maze()
                    else:
                        self._full_redraw()
                else:
                    self._maze_drawn = False
                    self._draw_too_small()
                continue

            if key == ord("1"):
                if self._has_enough_space():
                    self._action_regenerate()
            elif key == ord("2"):
                if self._has_enough_space():
                    self._action_toggle_path()
            elif key == ord("3"):
                if self._has_enough_space():
                    self._action_rotate_color()
            elif key in (ord("4"), ord("q"), ord("Q"), 27):
                break
            elif key == ord("5"):
                if self._has_enough_space():
                    self._action_toggle_42_color()
            elif key == ord("6"):
                if self._has_enough_space():
                    self._action_rotate_path_color()

    def _run(self, stdscr: Any) -> None:
        """Set up curses, animate the maze, then enter the event loop."""
        self._stdscr = stdscr
        curses.curs_set(0)
        self._init_colors()

        if self._has_enough_space():
            self._animate_maze()
        else:
            self._draw_too_small()

        self._event_loop()

    def run(self) -> None:
        """Launch the curses visualiser."""
        try:
            curses.wrapper(self._run)
        except Exception as exc:
            print(f"[visualizing_maze] error: {exc}")


def display_maze(
    maze_path: str,
    pattern_42_cells: Optional[List[Coord]] = None,
) -> None:
    """Parse maze.txt and open the interactive curses visualiser."""
    MazeRenderer(maze_path, pattern_42_cells).run()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 visualizing_maze.py maze.txt")
        sys.exit(1)
    display_maze(sys.argv[1])
