from collections import deque
from typing import Any, Dict, List, Optional, Tuple

MazeRow = List[Dict[str, Any]]
Maze = List[MazeRow]
Coord = Tuple[int, int]


class BFS:
    @classmethod
    def bfs_solve(cls, maze: Maze, entry: Coord, exit_: Coord,
                  height: int, width: int) -> str:
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
            val = parent[cur]
            assert val is not None
            prev, letter = val
            letters.append(letter)
            cur = prev
        letters.reverse()
        return "".join(letters)
