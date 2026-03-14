from typing import Any, Dict, List

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]


class draw_42:
    @classmethod
    def get_blocked_cells(cls, maze: Maze, height: int, width: int) -> None:
        pat_h = 7
        pat_w = 11
        if height < pat_h + 2 or width < pat_w + 2:
            print("Maze too small to display the '42' pattern.")
            return

        sr = (height - pat_h) // 2
        sc = (width - pat_w) // 2

        digit_4 = [
            (0, 0),
            (1, 0),
            (2, 0),
            (3, 0), (3, 1), (3, 2), (3, 3),
                                    (4, 3),
                                    (5, 3),
                                    (6, 3),
        ]

        digit_2 = [
            (0, 0), (0, 1), (0, 2), (0, 3), (0, 4),
            (1, 4),
            (2, 4),
            (3, 0), (3, 1), (3, 2), (3, 3), (3, 4),
            (4, 0),
            (5, 0),
            (6, 0), (6, 1), (6, 2), (6, 3), (6, 4),
        ]

        blocked = set()

        for dr, dc in digit_4:
            blocked.add((sr + dr, sc + dc))

        for dr, dc in digit_2:
            blocked.add((sr + dr, sc + 6 + dc))

        for row, col in blocked:
            maze[row][col]["north"] = True
            maze[row][col]["south"] = True
            maze[row][col]["east"] = True
            maze[row][col]["west"] = True
            maze[row][col]["visited"] = True

        directions = [
            (-1, 0, "north", "south"),
            (1, 0, "south", "north"),
            (0, -1, "west", "east"),
            (0, 1, "east", "west"),
        ]

        for row, col in blocked:
            for dr, dc, wall, opposite in directions:
                nr, nc = row + dr, col + dc
                if 0 <= nr < height and 0 <= nc < width:
                    maze[row][col][wall] = True
                    maze[nr][nc][opposite] = True
