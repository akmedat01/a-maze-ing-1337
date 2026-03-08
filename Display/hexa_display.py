from collections import deque


class hexa_display:
    @classmethod
    def convert_maze_col(cls, col):
        i = 0
        if col["north"]:
            i += 8
        if col["east"]:
            i += 4
        if col["south"]:
            i += 2
        if col["west"]:
            i += 1
        return hex(i)[2]

    @classmethod
    def solve(cls, maze, entry, exit_, height, width):
        moves = [("N", -1, 0, "north"), ("S", 1, 0, "south"),
                 ("E", 0, 1, "east"), ("W", 0, -1, "west")]
        queue = deque([entry])
        visited = {entry}
        parent = {entry: None}
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
        letters = []
        cur = exit_
        while parent[cur] is not None:
            prev, letter = parent[cur]
            letters.append(letter)
            cur = prev
        letters.reverse()
        return "".join(letters)

    @classmethod
    def print_maze_hex(cls, maze, parsed_values):
        height = len(maze)
        width = len(maze[0]) if maze else 0
        entry = parsed_values["entry"]
        exit_ = parsed_values["exit"]
        path = cls.solve(maze, entry, exit_, height, width)
        with open(parsed_values["output"], "w") as maze_file:
            for row in maze:
                for col in row:
                    a = cls.convert_maze_col(col)
                    if a == 'a':
                        maze_file.write("A")
                    elif a == 'b':
                        maze_file.write("B")
                    elif a == 'c':
                        maze_file.write("C")
                    elif a == 'd':
                        maze_file.write("D")
                    elif a == 'e':
                        maze_file.write("E")
                    elif a == "f":
                        maze_file.write("F")
                    else:
                        maze_file.write(a)
                maze_file.write("\n")
            maze_file.write("\n")
            maze_file.write(f"({entry[1]}, {entry[0]})\n")
            maze_file.write(f"({exit_[1]}, {exit_[0]})\n")
            maze_file.write(path + "\n")
