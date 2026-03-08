from collections import deque


class BFS:
    @classmethod
    def get_neighbors(cls, maze, row, col, height, width):
        neighbors = []
        if row - 1 >= 0 and not maze[row][col]["north"]:
            neighbors.append(("north", row - 1, col))
        if row + 1 <= height - 1 and not maze[row][col]["south"]:
            neighbors.append(("south", row + 1, col))
        if col - 1 >= 0 and not maze[row][col]["west"]:
            neighbors.append(("west", row, col - 1))
        if col + 1 <= width - 1 and not maze[row][col]["east"]:
            neighbors.append(("east", row, col + 1))
        return neighbors

    @classmethod
    def find_path(cls, maze, entry, exit, height, width):
        queue = deque()
        queue.append(entry)
        visited = {entry}
        parent = {(entry, "None"): None}
        while queue:
            row, col = queue.popleft()
            if (row, col) == exit:
                break
            for direction, n_row, n_col in cls.get_neighbors(maze, row, col,
                                                             height, width):
                if (n_row, n_col) not in visited:
                    visited.add((n_row, n_col))
                    parent[(n_row, n_col, direction)] = (row, col, direction)
                    queue.append((n_row, n_col))
