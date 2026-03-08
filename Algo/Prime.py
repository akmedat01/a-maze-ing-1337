import random


class Prime:

    @classmethod
    def get_walls(cls, maze, row, col, height, width):
        walls = []
        if row - 1 >= 0:
            walls.append((row, col, "north", row - 1, col))
        if row + 1 <= height - 1:
            walls.append((row, col, "south", row + 1, col))
        if col - 1 >= 0:
            walls.append((row, col, "west", row, col - 1))
        if col + 1 <= width - 1:
            walls.append((row, col, "east", row, col + 1))
        return walls

    @classmethod
    def generate_maze_perfect(cls, maze, row, col, height, width):
        maze[row][col]["visited"] = True
        frontier = cls.get_walls(maze, row, col, height, width)
        while frontier:
            choice = random.choice(frontier)
            frontier.remove(choice)
            row, col, direction, n_row, n_col = choice
            if maze[n_row][n_col]["visited"]:
                continue
            maze[row][col][direction] = False
            if direction == "north":
                maze[n_row][n_col]["south"] = False
            elif direction == "south":
                maze[n_row][n_col]["north"] = False
            elif direction == "east":
                maze[n_row][n_col]["west"] = False
            elif direction == "west":
                maze[n_row][n_col]["east"] = False
            maze[n_row][n_col]["visited"] = True
            frontier.extend(cls.get_walls(maze, n_row, n_col, height, width))

    @classmethod
    def generate_imperfect_maze(cls, maze, row, col,
                                height, width, chance=0.1):
        cls.generate_maze_perfect(maze, row, col, height, width)
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
