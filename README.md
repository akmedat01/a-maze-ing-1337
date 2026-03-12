# A-maze-ing
This project has been created as part of the 42 curriculum by mabar, aayat

## Description
This project is about creating a program that Generate a Maze, and find the shortest path from two points inside of it
The Maze could be a perfect (one path from a point to another) or imperfect one (many paths)
We did generate the Maze using the DFS or the Prime algo, find the path using BFS and Visualisation using Curses 

## Instructions

### Prerequisites

- Python 3.x
- A terminal emulator with 256-color support (e.g. iTerm2, GNOME Terminal, Windows Terminal)
- `flake8` and `mypy` (optional, for code quality checks)

### Setup & Run

```bash
# Install linting tools (optional)
make install

# Run the program
make run
```

The program is launched as `python3 a_maze_ing.py config.txt`. The `config.txt` file controls maze parameters such as dimensions, generation algorithm, and entry/exit coordinates.

### Makefile Reference

The Makefile provides the following targets:

- **`make run`** — Launch the main program with the default config file.
- **`make debug`** — Launch with Python's built-in debugger (`pdb`) for step-by-step inspection.
- **`make lint`** — Run `flake8` for style checks and `mypy` with standard options (`--warn-return-any`, `--warn-unused-ignores`, `--disallow-untyped-defs`, `--check-untyped-defs`, `--ignore-missing-imports`).
- **`make lint-strict`** — Run `mypy --strict` for maximum type safety enforcement.
- **`make install`** — Install `flake8` and `mypy` via pip.
- **`make clean`** — Recursively delete `__pycache__` directories, `.mypy_cache`, and compiled `.pyc` files.

---

## Visualisation

The visualisation module (`visualizing_maze.py`) renders the maze as a live, interactive display inside the terminal using Python's standard `curses` library. No external packages or GUI frameworks are required.

### Architecture

The renderer works on a **corner grid** of size `(2h+1) × (2w+1)`, where `h` and `w` are the maze's height and width in cells. Odd-row/odd-column positions represent cell centers; even positions represent walls or corners. Each grid position maps to two terminal columns to account for character aspect ratio.

The main class `MazeRenderer` handles:
- Parsing the hex-encoded maze file
- Building and maintaining the corner grid state
- Animating the maze reveal and path
- Managing the color system
- Processing keyboard input

### Animated Maze Reveal

When a maze is loaded or regenerated, it is not drawn all at once. A BFS traversal starting from the entry cell yields grid coordinates in wave order. Cells are "opened" (drawn as space) in this order at a rate of 6 positions per frame with a 10ms delay, so the maze appears to expand outward from the entry point. The "42" cells are protected during this process and remain visible at all times.

### Pathfinding & Path Display

The shortest path from entry to exit is computed internally by `_solve()` using BFS on the maze graph. The result is a string of directional characters (`N`, `S`, `E`, `W`). Pressing `2` animates the path step by step (20ms per step) along the corner grid. Pressing `2` again instantly clears it. Path cells are drawn in the current path color and cannot overwrite entry, exit, or "42" cells.

### The "42" Easter Egg

If the maze has at least 9 rows and 13 columns, the digits "4" and "2" are rendered in the center of the maze using a 7×5 pixel-art font (with a 1-column gap between digits). This is handled by two modules:

- **`draw_42.py`** — Called at maze generation time. It marks the digit cells as fully walled and already visited, which causes the generation algorithm to treat them as obstacles and carve around them.
- **`build_42_pattern()` / `_build_42_display_sets()`** in `visualizing_maze.py` — Called at render time. These functions compute three sets of corner-grid coordinates: the cell centers (colored with the "42" theme), the protected border (rendered as wall), and the blocked maze cells (excluded from path animation).

### Color System

The renderer supports three independently rotatable color themes:

| Theme | Key | Options |
|-------|-----|---------|
| Wall color | `3` | White, Yellow, Magenta, Cyan |
| "42" inner color | `5` | Gray, Magenta, Cyan, Green, Yellow, White |
| Path color | `6` | Cyan, Magenta, Yellow, White |

When rotating colors, the renderer automatically detects and skips combinations where the path or "42" background would match the wall foreground, ensuring the display always remains readable.

### Hex Output Format (`hexa_display.py`)

Mazes are serialized to text files using a compact single-character-per-cell encoding. Each cell becomes one hexadecimal digit computed from its four wall states:

```
Bit 3 (value 8)  →  North wall closed
Bit 2 (value 4)  →  East wall closed
Bit 1 (value 2)  →  South wall closed
Bit 0 (value 1)  →  West wall closed
```

Examples: `0` = no walls (open cell), `F` = all walls closed, `5` = North + South walls only.

The output file structure is:
```
<hex row 0>
<hex row 1>
...
<hex row h-1>

(entry_col, entry_row)
(exit_col, exit_row)
[solution path string, appended separately]
```

### Interactive Controls

```
Key 1          →  Re-generate a new maze (re-runs the generator, reloads, re-animates)
Key 2          →  Show / Hide shortest path
Key 3          →  Rotate wall color theme
Key 4 / q / Q / ESC  →  Quit
Key 5          →  Rotate "42" inner color theme
Key 6          →  Rotate path color theme
```

The display is responsive to terminal resize events (`KEY_RESIZE`). If the window is too small, a message shows the current and required dimensions. When resized to a sufficient size, the maze display recovers automatically.

---

## Maze Generation

> *(to be completed by mabar)*

---

## Pathfinding

> *(to be completed by mabar)*

---

## Authors
- **aayat** — Visualisation (`visualizing_maze.py`, `hexa_display.py`, `draw_42.py`) & Makefile
- **mabar** — Maze generation & Pathfinding