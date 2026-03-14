import curses
import os
import re
import sys
import time
from collections import deque
from typing import Any, Dict, Generator, List, Optional, Set, Tuple
from .draw_42 import draw_42

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]
Coord = Tuple[int, int]

WALL_CH = "█"
SPACE_CH = " "

COLOR_ENTRY = 1
COLOR_EXIT = 2
COLOR_WALL_BASE = 10
COLOR_PATH_BASE = 20
COLOR_42_CENTER_BASE = 30

WALL_COLORS: List[Tuple[int, int]] = [
    (curses.COLOR_WHITE, curses.COLOR_BLACK),
    (curses.COLOR_YELLOW, curses.COLOR_BLACK),
    (curses.COLOR_MAGENTA, curses.COLOR_BLACK),
    (curses.COLOR_CYAN, curses.COLOR_BLACK),
]

PATH_COLORS: List[Tuple[int, int]] = [
    (curses.COLOR_BLACK, curses.COLOR_CYAN),
    (curses.COLOR_BLACK, curses.COLOR_MAGENTA),
    (curses.COLOR_BLACK, curses.COLOR_YELLOW),
    (curses.COLOR_BLACK, curses.COLOR_WHITE),
]

INNER_42_COLORS: List[Tuple[Any, Any]] = [
    ("gray", "custom_gray"),
    (curses.COLOR_BLACK, curses.COLOR_MAGENTA),
    (curses.COLOR_BLACK, curses.COLOR_CYAN),
    (curses.COLOR_BLACK, curses.COLOR_GREEN),
    (curses.COLOR_BLACK, curses.COLOR_YELLOW),
    (curses.COLOR_BLACK, curses.COLOR_WHITE),
]

MAZE_ANIM_DELAY: float = 0.01
MAZE_ANIM_BATCH: int = 6
PATH_ANIM_DELAY: float = 0.02


def _parse_maze_file(
    filepath: str,
) -> Tuple[Maze, Coord, Coord, int, int]:
    with open(filepath, "r") as fh:
        lines = fh.readlines()

    def _coord(s: str) -> Coord:
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
                "north": bool(v & 1),
                "east": bool(v & 2),
                "south": bool(v & 4),
                "west": bool(v & 8),
            })
        maze.append(row)

    height = len(maze)
    width = len(maze[0]) if maze else 0
    return maze, entry, exit_, height, width


def _build_closed_grid(height: int, width: int) -> List[List[bool]]:
    return [[True] * (width * 2 + 1) for _ in range(height * 2 + 1)]


def _solve(
    maze: Maze,
    entry: Coord,
    exit_: Coord,
    height: int,
    width: int,
) -> str:
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

                if (
                    r > 0
                    and not cell["north"]
                    and not maze[r - 1][c]["south"]
                ):
                    yield (gr - 1, gc, True)
                if (
                    r < height - 1
                    and not cell["south"]
                    and not maze[r + 1][c]["north"]
                ):
                    yield (gr + 1, gc, True)
                if (
                    c > 0
                    and not cell["west"]
                    and not maze[r][c - 1]["east"]
                ):
                    yield (gr, gc - 1, True)
                if (
                    c < width - 1
                    and not cell["east"]
                    and not maze[r][c + 1]["west"]
                ):
                    yield (gr, gc + 1, True)


def build_42_pattern(
    height: int,
    width: int,
) -> Optional[List[Coord]]:
    pat_h, pat_w = 7, 11
    if height < pat_h + 2 or width < pat_w + 2:
        return None

    dummy_maze: Maze = [
        [
            {
                "north": False,
                "south": False,
                "east": False,
                "west": False,
                "visited": False,
            }
            for _ in range(width)
        ]
        for _ in range(height)
    ]
    draw_42.get_blocked_cells(dummy_maze, height, width)

    cells: List[Coord] = []
    for r in range(height):
        for c in range(width):
            if dummy_maze[r][c].get("visited"):
                cells.append((r, c))
    return cells


def _build_42_display_sets(
    cells: List[Coord],
) -> Tuple[Set[Coord], Set[Coord]]:
    center_set: Set[Coord] = set()
    protected_set: Set[Coord] = set()

    if not cells:
        return center_set, protected_set

    for r, c in cells:
        gr, gc = r * 2 + 1, c * 2 + 1
        center_set.add((gr, gc))

        for dr in (-1, 0, 1):
            for dc in (-1, 0, 1):
                protected_set.add((gr + dr, gc + dc))

    return center_set, protected_set


class MazeRenderer:
    def __init__(
        self,
        maze_path: str,
        pattern_42_cells: Optional[List[Coord]] = None,
    ) -> None:
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
        self._42_center_set, self._42_protected_set = (
            _build_42_display_sets(p42)
        )

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
        self._wall_idx = 0
        self._path_idx = 0
        self._inner42_idx = 0
        self._maze_drawn = False
        self._stdscr: Any = None

    def _required_size(self) -> Tuple[int, int]:
        rows = self._height * 2 + 11
        cols = (self._width * 2 + 1) * 2 + 3
        return rows, cols

    def _has_enough_space(self) -> bool:
        max_y, max_x = self._stdscr.getmaxyx()
        need_y, need_x = self._required_size()
        return bool(max_y >= need_y and max_x >= need_x)

    def _init_colors(self) -> None:
        curses.start_color()
        curses.use_default_colors()

        for i, (fg, bg) in enumerate(WALL_COLORS):
            curses.init_pair(COLOR_WALL_BASE + i, fg, bg)
        for i, (fg, bg) in enumerate(PATH_COLORS):
            curses.init_pair(COLOR_PATH_BASE + i, fg, bg)

        curses.init_pair(COLOR_ENTRY, curses.COLOR_BLACK, curses.COLOR_GREEN)
        curses.init_pair(COLOR_EXIT, curses.COLOR_BLACK, curses.COLOR_RED)

        for i, pair in enumerate(INNER_42_COLORS):
            if pair == ("gray", "custom_gray"):
                if curses.can_change_color() and curses.COLORS > 8:
                    try:
                        curses.init_color(8, 700, 700, 700)
                        curses.init_pair(
                            COLOR_42_CENTER_BASE + i,
                            curses.COLOR_BLACK,
                            8,
                        )
                    except curses.error:
                        curses.init_pair(
                            COLOR_42_CENTER_BASE + i,
                            curses.COLOR_BLACK,
                            curses.COLOR_WHITE,
                        )
                else:
                    curses.init_pair(
                        COLOR_42_CENTER_BASE + i,
                        curses.COLOR_BLACK,
                        curses.COLOR_WHITE,
                    )
            else:
                fg, bg = pair
                curses.init_pair(COLOR_42_CENTER_BASE + i, fg, bg)

    def _wcp(self) -> int:
        return COLOR_WALL_BASE + self._wall_idx

    def _pcp(self) -> int:
        return COLOR_PATH_BASE + self._path_idx

    def _c42p(self) -> int:
        return COLOR_42_CENTER_BASE + self._inner42_idx

    def _current_wall_fg(self) -> int:
        fg, _ = WALL_COLORS[self._wall_idx]
        return fg

    def _current_path_bg(self) -> int:
        _, bg = PATH_COLORS[self._path_idx]
        return bg

    def _current_42_bg(self) -> Any:
        pair = INNER_42_COLORS[self._inner42_idx]
        if pair == ("gray", "custom_gray"):
            return "custom_gray"
        _, bg = pair
        return bg

    def _path_clashes_with_wall(self) -> bool:
        return self._current_path_bg() == self._current_wall_fg()

    def _42_clashes_with_wall(self) -> bool:
        bg = self._current_42_bg()
        if bg == "custom_gray":
            return False
        return bool(bg == self._current_wall_fg())

    def _put(self, y: int, x: int, ch: str, attr: int = 0) -> None:
        try:
            self._stdscr.addstr(y, x, ch, attr)
        except curses.error:
            pass

    def _draw_too_small(self) -> None:
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
        wp = curses.color_pair(self._wcp())
        ep = curses.color_pair(COLOR_ENTRY) | curses.A_BOLD
        xp = curses.color_pair(COLOR_EXIT) | curses.A_BOLD
        pp = curses.color_pair(self._pcp()) | curses.A_BOLD
        center42 = curses.color_pair(self._c42p()) | curses.A_BOLD

        sy = grid_row + 1
        sx = gc * 2 + 1

        is_wall = self._grid[grid_row][gc]
        is_cell = (grid_row % 2 == 1 and gc % 2 == 1)
        maze_r = (grid_row - 1) // 2
        maze_c = (gc - 1) // 2
        on_path = (grid_row, gc) in self._path_drawn
        coord = (grid_row, gc)

        if self._maze_drawn and is_cell and (maze_r, maze_c) == self._entry:
            self._put(sy, sx, " ", ep)
            self._put(sy, sx + 1, " ", ep)
            return

        if self._maze_drawn and is_cell and (maze_r, maze_c) == self._exit:
            self._put(sy, sx, " ", xp)
            self._put(sy, sx + 1, " ", xp)
            return

        if on_path:
            self._put(sy, sx, " ", pp)
            self._put(sy, sx + 1, " ", pp)
            return

        if coord in self._42_center_set and (
            self._maze_drawn or not self._grid[grid_row][gc]
        ):
            self._put(sy, sx, " ", center42)
            self._put(sy, sx + 1, " ", center42)
            return

        if coord in self._42_protected_set or is_wall:
            self._put(sy, sx, WALL_CH, wp)
            self._put(sy, sx + 1, WALL_CH, wp)
            return

        self._put(sy, sx, SPACE_CH)
        self._put(sy, sx + 1, SPACE_CH)

    def _draw_full_grid(self) -> None:
        for gr in range(self._height * 2 + 1):
            for gc in range(self._width * 2 + 1):
                self._draw_cell(gr, gc)

    def _draw_menu(self) -> None:
        path_state = "ON" if self._show_path else "OFF"
        base_y = self._height * 2 + 3

        self._put(base_y, 0, "==== A-Maze-ing ====", curses.A_BOLD)
        self._put(base_y + 1, 0, "1. Re-generate a new maze")
        self._put(
            base_y + 2, 0,
            f"2. Show/Hide path from entry to exit  [{path_state}]",
        )
        self._put(base_y + 3, 0, "3. Rotate maze colors")
        self._put(base_y + 4, 0, "4. Quit")
        self._put(base_y + 5, 0, "5. Rotate 42 inner colors")
        self._put(base_y + 6, 0, "6. Rotate path colors")
        self._put(base_y + 7, 0, "Choice (1-6): ", curses.A_BOLD)

    def _full_redraw(self) -> None:
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
        if not self._has_enough_space():
            self._maze_drawn = False
            self._draw_too_small()
            return

        self._stdscr.clear()
        self._grid = _build_closed_grid(self._height, self._width)
        self._draw_full_grid()
        self._stdscr.refresh()
        time.sleep(0.3)

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

            if (gr, gc) in self._42_protected_set:
                self._grid[gr][gc] = True

            self._draw_cell(gr, gc)
            batch_counter += 1
            if batch_counter % MAZE_ANIM_BATCH == 0:
                self._stdscr.refresh()
                time.sleep(MAZE_ANIM_DELAY)

        self._maze_drawn = True
        self._full_redraw()

    def _animate_path(self) -> None:
        if not self._has_enough_space():
            self._draw_too_small()
            return

        self._path_drawn = set()
        pp = curses.color_pair(self._pcp()) | curses.A_BOLD

        for gr, gc in self._path_steps[1:-1]:
            if not self._has_enough_space():
                self._draw_too_small()
                return
            if (gr, gc) in self._42_protected_set:
                continue

            self._path_drawn.add((gr, gc))
            sy = gr + 1
            sx = gc * 2 + 1

            self._put(sy, sx, " ", pp)
            self._put(sy, sx + 1, " ", pp)

            self._stdscr.refresh()
            time.sleep(PATH_ANIM_DELAY)

    def _clear_path(self) -> None:
        old = set(self._path_drawn)
        self._path_drawn = set()
        for gr, gc in old:
            self._draw_cell(gr, gc)
        self._stdscr.refresh()

    def _reload(self) -> None:
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
        self._42_center_set, self._42_protected_set = (
            _build_42_display_sets(p42)
        )

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
        try:
            import a_maze_ing as _main
            _original = _main.display_maze
            _main.display_maze = lambda *a, **kw: None
            _main.main(self._config_path)
            _main.display_maze = _original
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
        self._show_path = not self._show_path
        if self._show_path:
            self._animate_path()
        else:
            self._clear_path()
        self._draw_menu()
        self._stdscr.refresh()

    def _action_rotate_color(self) -> None:
        self._wall_idx = (self._wall_idx + 1) % len(WALL_COLORS)

        if self._path_clashes_with_wall():
            self._action_rotate_path_color(redraw=False)

        if self._42_clashes_with_wall():
            self._action_rotate_42_color(redraw=False)

        self._full_redraw()

    def _action_rotate_42_color(self, redraw: bool = True) -> None:
        if len(INNER_42_COLORS) == 0:
            return

        for _ in range(len(INNER_42_COLORS)):
            self._inner42_idx = (
                self._inner42_idx + 1
            ) % len(INNER_42_COLORS)
            if not self._42_clashes_with_wall():
                break

        if redraw:
            self._full_redraw()

    def _action_rotate_path_color(self, redraw: bool = True) -> None:
        if len(PATH_COLORS) == 0:
            return

        for _ in range(len(PATH_COLORS)):
            self._path_idx = (self._path_idx + 1) % len(PATH_COLORS)
            if not self._path_clashes_with_wall():
                break

        if redraw:
            if self._show_path:
                self._full_redraw()
            else:
                self._draw_menu()
                self._stdscr.refresh()

    def _event_loop(self) -> None:
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
                    self._action_rotate_42_color()
            elif key == ord("6"):
                if self._has_enough_space():
                    self._action_rotate_path_color()

    def _run(self, stdscr: Any) -> None:
        self._stdscr = stdscr
        curses.curs_set(0)
        self._init_colors()

        if self._has_enough_space():
            self._animate_maze()
        else:
            self._draw_too_small()

        self._event_loop()

    def run(self) -> None:
        try:
            curses.wrapper(self._run)
        except Exception as exc:
            print(f"[visualizing_maze] error: {exc}")


def display_maze(
    maze_path: str,
    pattern_42_cells: Optional[List[Coord]] = None,
) -> None:
    MazeRenderer(maze_path, pattern_42_cells).run()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 visualizing_maze.py maze.txt")
        sys.exit(1)
    display_maze(sys.argv[1])
