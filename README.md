*This project has been created as part of the 42 curriculum by mabar, aayat*

# A-maze-ing

## Description
This project is about creating a program that generates a maze and finds the shortest path from two points inside of it. The maze can be perfect (one unique path between any two points) or imperfect (multiple paths). We generate the maze using DFS or Prim's algorithm, find the shortest path using BFS, and visualise the result using Python's curses library.

## Instructions

### Prerequisites

- Python 3.10 or later
- A terminal emulator with 256-color support (e.g. iTerm2, GNOME Terminal, Windows Terminal)
- `flake8` and `mypy` for linting (optional)

### Setup & Run

```bash
make install   # install linting tools (optional)
make run       # generate and display the maze
```

The program is launched as `python3 a_maze_ing.py config.txt`.

### Makefile Reference

- **`make run`** — Launch the main program with the default config file.
- **`make debug`** — Launch with Python's built-in debugger (`pdb`).
- **`make lint`** — Run `flake8` + `mypy` with standard options.
- **`make lint-strict`** — Run `flake8` + `mypy --strict`.
- **`make install`** — Install `flake8` and `mypy` via pip.
- **`make clean`** — Remove `__pycache__`, `.mypy_cache`, and `.pyc` files.

---

## Configuration File

The config file uses `KEY=VALUE` format, one pair per line. Lines starting with `#` are comments and are ignored.

| Key | Description | Example |
|-----|-------------|---------|
| `WIDTH` | Maze width in cells | `WIDTH=20` |
| `HEIGHT` | Maze height in cells | `HEIGHT=20` |
| `ENTRY` | Entry coordinates `(col,row)` | `ENTRY=0,0` |
| `EXIT` | Exit coordinates `(col,row)` | `EXIT=18,19` |
| `OUTPUT_FILE` | Output filename | `OUTPUT_FILE=maze.txt` |
| `PERFECT` | Perfect maze? (`True`/`False`) | `PERFECT=False` |
| `SEED` *(optional)* | Seed for reproducibility | `SEED=42` |

---

## Maze Generation

> *(mabar)*

---

## Algorithm Choice

> *(mabar)*

---

## Pathfinding

> *(mabar)*

---

## Visualisation

The visualisation module (`visualizing_maze.py`) renders the maze as a live, interactive display inside the terminal using Python's `curses` library. No external packages or GUI frameworks are required.

The renderer works on a corner grid of size `(2h+1) × (2w+1)`. Odd-indexed positions represent cell centers; even-indexed positions represent walls. Each grid position maps to two terminal columns to match character aspect ratio. The main class `MazeRenderer` handles parsing, animation, colors, and keyboard input.

### Animated Maze Reveal

When a maze is loaded or regenerated, cells are uncovered in BFS wave order starting from the entry point at a rate of 6 positions per frame (10ms delay), so the maze appears to expand outward from the inside.

### The "42" Pattern

If the maze is at least 9×13 cells, the digits "4" and "2" are rendered in the center using a 7×5 pixel-art font. These cells are fully walled, visually distinct, and protected — neither the path animation nor wall rendering can overwrite them.

### Color System

Three color themes are independently rotatable:

| Theme | Key | Options |
|-------|-----|---------|
| Wall color | `3` | White, Yellow, Magenta, Cyan |
| "42" inner color | `5` | Gray, Magenta, Cyan, Green, Yellow, White |
| Path color | `6` | Cyan, Magenta, Yellow, White |

Colors are automatically adjusted to avoid clashes between themes.

### Interactive Controls

```
1          →  Re-generate a new maze
2          →  Show / Hide shortest path
3          →  Rotate wall color theme
4 / q      →  Quit
5          →  Rotate "42" color theme
6          →  Rotate path color theme
```

The display handles terminal resize events automatically. If the window is too small, it shows the required dimensions and recovers when resized.

---

## Output File Format

Each cell is encoded as one hex digit where each bit represents a closed wall:

```
Bit 0 (value 1)  →  North
Bit 1 (value 2)  →  East
Bit 2 (value 4)  →  South
Bit 3 (value 8)  →  West
```

`0` = fully open, `F` = all walls closed. After the hex grid, a blank line is followed by the entry coordinates, exit coordinates, and the shortest path string using `N`, `E`, `S`, `W`.

---

## Reusable Module

> *(mabar)*

---

## Team & Project Management

**Roles:**
- **aayat** — Visualisation (`visualizing_maze.py`) & Makefile
- **mabar** — ...

**Planning:** *(mabar)*

**What worked well / what could be improved:** *(mabar)*

**Tools used:** *(mabar)*

---

## Resources

*(mabar)*