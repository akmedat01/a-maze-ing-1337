import random


class DFS:
    @classmethod
    def check_neighbors(cls, maze, row, col, height, width):
        neighbors = []
        if row - 1 >= 0 and not maze[row - 1][col]["visited"]:
            neighbors.append(("north", row - 1, col))
        if row + 1 <= height - 1 and not maze[row + 1][col]["visited"]:
            neighbors.append(("south", row + 1, col))
        if col - 1 >= 0 and not maze[row][col - 1]["visited"]:
            neighbors.append(("west", row, col - 1))
        if col + 1 <= width - 1 and not maze[row][col + 1]["visited"]:
            neighbors.append(("east", row, col + 1))
        return neighbors

    @classmethod
    def generate_perfect_maze(cls, maze, row, col, height, width):
        maze[row][col]["visited"] = True
        neighbors = cls.check_neighbors(maze, row, col, height, width)
        random.shuffle(neighbors)
        for direction, n_row, n_col in neighbors:
            if not maze[n_row][n_col]["visited"]:
                maze[row][col][direction] = False
                if direction == "north":
                    maze[n_row][n_col]["south"] = False
                elif direction == "south":
                    maze[n_row][n_col]["north"] = False
                elif direction == "east":
                    maze[n_row][n_col]["west"] = False
                elif direction == "west":
                    maze[n_row][n_col]["east"] = False
                cls.generate_perfect_maze(maze, n_row, n_col,
                                          height, width)

    @classmethod
    def generate_imperfect_maze(cls, maze, height, width, chance=0.1):
        cls.generate_perfect_maze(maze, 0, 0, height, width)
        directions = [
            ("north", -1, 0, "south"),
            ("south", 1, 0, "north"),
            ("west", 0, -1, "east"),
            ("east", 0, 1, "west")
        ]
        for row in range(height):
            for col in range(width):
                # random chance to break a wall
                if random.random() < chance:
                    direction, dr, dc, opposite = random.choice(directions)
                    new_row = row + dr
                    new_col = col + dc
                    # check bounds
                    if 0 <= new_row < height and 0 <= new_col < width:
                        # remove wall both sides
                        maze[row][col][direction] = False
                        maze[row][col]["visited"] = True
                        maze[new_row][new_col][opposite] = False
                        maze[new_row][new_col]["visited"] = True
