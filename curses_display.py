import curses


class CursesDisplay:
    NORTH = 8
    EAST = 4
    SOUTH = 2
    WEST = 1

    @classmethod
    def read_maze_file(cls, filename):
        maze = []
        with open(filename, "r") as f:
            for line in f:
                line = line.strip()
                if line:
                    maze.append([int(ch, 16) for ch in line])
        return maze

    @classmethod
    def draw_maze(cls, stdscr, maze, entry=None, exit_=None, path=None):
        curses.curs_set(0)
        curses.start_color()
        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)
        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_BLACK)
        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)
        curses.init_pair(4, curses.COLOR_RED, curses.COLOR_BLACK)
        stdscr.clear()

        height = len(maze)
        width = len(maze[0])
        path_set = set(path) if path else set()

        for row in range(height):
            for col in range(width):
                cell = maze[row][col]
                sy = row * 2
                sx = col * 4

                stdscr.addch(sy, sx, '+', curses.color_pair(1))
                stdscr.addstr(sy, sx + 1, "---" if cell & cls.NORTH else "   ", curses.color_pair(1))
                stdscr.addch(sy + 1, sx, '|' if cell & cls.WEST else ' ', curses.color_pair(1))

                if entry and (row, col) == entry:
                    stdscr.addstr(sy + 1, sx + 1, " E ", curses.color_pair(3) | curses.A_BOLD)
                elif exit_ and (row, col) == exit_:
                    stdscr.addstr(sy + 1, sx + 1, " X ", curses.color_pair(4) | curses.A_BOLD)
                elif (row, col) in path_set:
                    stdscr.addstr(sy + 1, sx + 1, " . ", curses.color_pair(2))
                else:
                    stdscr.addstr(sy + 1, sx + 1, "   ", curses.color_pair(1))

                if col == width - 1:
                    stdscr.addch(sy, sx + 4, '+', curses.color_pair(1))
                    stdscr.addch(sy + 1, sx + 4, '|' if cell & cls.EAST else ' ', curses.color_pair(1))

            if row == height - 1:
                for col in range(width):
                    cell = maze[row][col]
                    sx = col * 4
                    stdscr.addch(height * 2, sx, '+', curses.color_pair(1))
                    stdscr.addstr(height * 2, sx + 1, "---" if cell & cls.SOUTH else "   ", curses.color_pair(1))
                stdscr.addch(height * 2, width * 4, '+', curses.color_pair(1))

        stdscr.addstr(height * 2 + 2, 0, "E=Entry  X=Exit  .=Path  q=Quit", curses.color_pair(1))
        stdscr.refresh()

        while True:
            if stdscr.getch() == ord('q'):
                break

    @classmethod
    def display(cls, filename, entry=None, exit_=None, path=None):
        maze = cls.read_maze_file(filename)
        curses.wrapper(cls.draw_maze, maze, entry, exit_, path)


if __name__ == "__main__":
    CursesDisplay.display("maze.txt", entry=(0, 0), exit_=(1, 4), path=None)
