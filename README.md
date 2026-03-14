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

The maze is represented as a 2D grid of cells. Each cell stores four boolean
values — `north`, `east`, `south`, `west` — where `True` means the wall is
present and `False` means it has been carved open, plus a `visited` flag
that helps the generation algorithms track which cells have already been
processed. All walls start closed and are selectively removed during generation.

The "42" pattern is carved into the center of the maze before generation
begins. These cells are fully walled and marked as visited so the generation
algorithms treat them as obstacles and route around them.

---

## Algorithm Choice

Two generation algorithms are supported, selectable via the `ALGO` key in the
config file.

**DFS (Depth-First Search)** — the default. Starting from cell (0,0), the
algorithm recursively visits a random unvisited neighbour, carving a wall
between them. This produces long, winding corridors with few dead ends —
a "river-like" maze. For imperfect mazes, additional walls are randomly
removed after generation to create loops and multiple paths.

**Prim's Algorithm** — starts from cell (0,0) and maintains a frontier list
of candidate walls. At each step a random wall from the frontier is chosen
and carved if the neighbour has not been visited. This produces a more
"organic", branchy maze with shorter dead ends compared to DFS. Imperfect
mode also removes extra walls after generation.

Both algorithms guarantee a connected maze. Perfect mode produces exactly
one path between any two cells; imperfect mode introduces loops.

## Pathfinding

The shortest path is found using **BFS (Breadth-First Search)**. Starting
from the entry point, BFS explores neighbours level by level, only crossing
open walls. Each visited cell records its parent and the direction taken.
Once the exit is reached, the path is reconstructed by walking back through
the parent map and reversing the result.

The output is a string of directions: `N`, `S`, `E`, `W`. If no path exists
the string is empty. BFS guarantees the shortest path in an unweighted maze.

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

The maze generator is packaged as a standalone pip-installable package called
`mazegen`. It can be used independently of this project with no knowledge of
the config file or display system.

### Installation
```bash
pip install mazegen-1.0.0-py3-none-any.whl
```

### Basic Example
```python
from mazegen import MazeGenerator, BFS

gen = MazeGenerator(height=10, width=10)
maze = gen.generate_maze()

solution = BFS.bfs_solve(maze, entry=(0, 0), exit_=(9, 9), height=10, width=10)
print(solution)  # e.g. "SSSEEENESE"
```

### Custom Parameters
```python
gen = MazeGenerator(
    height=20,
    width=20,
    algo="PRIM",      # "DFS" or "PRIM", default is "DFS"
    perfect=True,     # True for perfect maze, False for imperfect
)
maze = gen.generate_maze()
```

### Maze Structure

The maze is a list of rows, each row a list of cell dicts:
```python
{"north": bool, "east": bool, "south": bool, "west": bool}
```

`True` means the wall is present, `False` means it is open.
```python
maze[row][col]["north"]  # True if the north wall of this cell is closed
```

### Rebuilding the Package
```bash
python3 -m venv env
source env/bin/activate
pip install build
python -m build
# output: dist/mazegen-1.0.0-py3-none-any.whl
```

## Team & Project Management

**Roles:**
- **aayat** — Visualisation (`visualizing_maze.py`) & Makefile
- **mabar** — Parsing, Error Handling, Maze Generation, Pathfinding, Hex Output, Reusable Package

**Planning:**
We split the project into two independent parts from the start — aayat handled
everything visual and mabar handled everything logic-related. This allowed us
to work in parallel without blocking each other. We used Git for version control
and coordinated through regular check-ins to integrate both parts.

**What worked well / what could be improved:**
The separation of responsibilities worked well — each part of the codebase had
a clear owner which made debugging easier. The modular structure (each algorithm
in its own file, display separate from logic) also made it straightforward to
add features like a second generation algorithm or the reusable package.

On the improvement side, we could have defined the interfaces between our modules
earlier — for example agreeing on the maze data structure format from day one
would have saved some back-and-forth when integrating the visualisation with
the generator.

**Tools used:**
- **Git** — version control and collaboration
- **mypy** — static type checking
- **flake8** — code style linting
- **Python curses** — terminal rendering for the visualisation
- **Claude (Anthropic)** — debugging assistance and code review
- **VS Code** — primary code editor

## Resources

## Resources

### Maze Generation
- [Maze Generation Algorithms — Jamis Buck's blog](https://weblog.jamisbuck.org/2011/2/7/maze-generation-algorithm-recap) — the most referenced blog on maze algorithms, covers DFS, Prim, and many more with visualizations
- [Computerphile — Maze Algorithms (YouTube)](https://www.youtube.com/watch?v=rop0W4QDOUI) — a clear visual explanation of how maze generation works

### Pathfinding
- [BFS in Python — Real Python](https://realpython.com/python-interview-problems/#graphs-breadth-first-search) — practical BFS explanation in Python
- [Computerphile — Dijkstra's Algorithm (YouTube)](https://www.youtube.com/watch?v=GazC3A4OQTE) — great intuition for graph traversal and shortest path

### Curses / Terminal Rendering
- [Python curses — official docs](https://docs.python.org/3/library/curses.html)
- [Curses Programming with Python — official HOWTO](https://docs.python.org/3/howto/curses.html) — the best starting point for curses

### Python Packaging
- [Python Packaging User Guide](https://packaging.python.org/en/latest/tutorials/packaging-projects/) — official guide for building and publishing packages
- [pyproject.toml explained](https://realpython.com/pyproject-toml/) — Real Python walkthrough

### Tools
- [Claude (Anthropic)](https://claude.ai) — used for debugging, understanding concepts, and code review