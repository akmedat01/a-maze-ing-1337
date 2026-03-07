from typing import List, Optional, Tuple

Coord = Tuple[int, int]


def build_42_pattern(
    height: int,
    width: int,
) -> Optional[List[Coord]]:
    """Return maze cell coords forming a '42' in the center.

    The '4' digit is 5 cols wide, '2' is 5 cols wide, separated
    by a 1-col gap. Total shape is 11 cols x 7 rows.
    All returned cells should be rendered as fully closed walls.
    Returns None if the maze is too small to fit the pattern,
    and prints an error message to stderr in that case.

    Args:
        height: Number of maze rows.
        width: Number of maze columns.

    Returns:
        List of (row, col) coords, or None if maze too small.
    """
    pat_h = 7
    pat_w = 11
    if height < pat_h + 2 or width < pat_w + 2:
        print(
            f"Maze too small for '42' pattern "
            f"(need at least {pat_h + 2}x{pat_w + 2}, "
            f"got {height}x{width})"
        )
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
