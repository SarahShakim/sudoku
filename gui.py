# GUI.py
import pygame
from sudoku import solve, valid   # keeping your module name as-is
import time

pygame.init()
pygame.font.init()

# ---------- Layout / Style ----------
GRID_ROWS = GRID_COLS = 9
WINDOW_W = 720
WINDOW_H = 800
PADDING = 25                 # outer margin
GRID_SIZE = 560              # square area for 9x9 grid
CELL_GAP = GRID_SIZE // GRID_ROWS
PANEL_H = 160                # bottom info/instructions panel height

BG_COLOR = (245, 245, 245)
GRID_LINE = (0, 0, 0)
SUBGRID_LINE = (0, 0, 0)
SELECTION = (209, 72, 54)      # red-ish
TEMP_NUM = (120, 120, 120)
FIXED_NUM = (20, 20, 20)
PANEL_BG = (255, 255, 255)
PANEL_TEXT = (30, 30, 30)

TITLE_FONT = pygame.font.SysFont(None, 32, bold=True)
TEXT_FONT = pygame.font.SysFont(None, 24)
NUM_FONT = pygame.font.SysFont(None, 42)

# Grid top-left so it’s centered with padding
GRID_X = (WINDOW_W - GRID_SIZE) // 2
GRID_Y = PADDING + 10

def clamp(v, lo, hi):
    return max(lo, min(hi, v))

class Grid:
    board = [
        [7, 8, 0, 4, 0, 0, 1, 2, 0],
        [6, 0, 0, 0, 7, 5, 0, 0, 9],
        [0, 0, 0, 6, 0, 1, 0, 7, 8],
        [0, 0, 7, 0, 4, 0, 2, 6, 0],
        [0, 0, 1, 0, 5, 0, 9, 3, 0],
        [9, 0, 4, 0, 6, 0, 0, 0, 5],
        [0, 7, 0, 3, 0, 0, 0, 1, 2],
        [1, 2, 0, 0, 0, 7, 4, 0, 0],
        [0, 4, 9, 2, 0, 6, 0, 0, 7]
    ]

    def __init__(self, rows, cols):
        self.rows = rows
        self.cols = cols
        self.cubes = [[Cube(self.board[i][j], i, j) for j in range(cols)] for i in range(rows)]
        self.model = None
        self.selected = None  # (row, col)

    def update_model(self):
        self.model = [[self.cubes[i][j].value for j in range(self.cols)] for i in range(self.rows)]

    def place(self, val):
        if not self.selected:
            return False
        row, col = self.selected
        if self.cubes[row][col].value == 0:
            self.cubes[row][col].set(val)
            self.update_model()

            if valid(self.model, val, (row, col)) and solve([row[:] for row in self.model]):
                return True
            else:
                self.cubes[row][col].set(0)
                self.cubes[row][col].set_temp(0)
                self.update_model()
                return False

    def sketch(self, val):
        if not self.selected:
            return
        row, col = self.selected
        if self.cubes[row][col].value == 0:
            self.cubes[row][col].set_temp(val)

    def draw(self, win):
        # Grid lines
        for i in range(self.rows + 1):
            thick = 3 if i % 3 == 0 else 1
            # horizontal
            pygame.draw.line(
                win, SUBGRID_LINE if thick == 3 else GRID_LINE,
                (GRID_X, GRID_Y + i * CELL_GAP),
                (GRID_X + GRID_SIZE, GRID_Y + i * CELL_GAP),
                thick
            )
            # vertical
            pygame.draw.line(
                win, SUBGRID_LINE if thick == 3 else GRID_LINE,
                (GRID_X + i * CELL_GAP, GRID_Y),
                (GRID_X + i * CELL_GAP, GRID_Y + GRID_SIZE),
                thick
            )

        # Cells
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].draw(win)

        # Selection outline (draw after cells so it sits on top)
        if self.selected:
            i, j = self.selected
            x = GRID_X + j * CELL_GAP
            y = GRID_Y + i * CELL_GAP
            pygame.draw.rect(win, SELECTION, pygame.Rect(x+2, y+2, CELL_GAP-4, CELL_GAP-4), 3, border_radius=6)

    def select(self, row, col):
        # Reset all other
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].selected = False

        self.cubes[row][col].selected = True
        self.selected = (row, col)

    def clear(self):
        if not self.selected:
            return
        row, col = self.selected
        if self.cubes[row][col].value == 0:
            self.cubes[row][col].set_temp(0)

    def click(self, pos):
        """
        :param pos: (x, y)
        :return: (row, col) or None
        """
        x, y = pos
        if GRID_X <= x < GRID_X + GRID_SIZE and GRID_Y <= y < GRID_Y + GRID_SIZE:
            j = (x - GRID_X) // CELL_GAP
            i = (y - GRID_Y) // CELL_GAP
            return int(i), int(j)
        return None

    def is_finished(self):
        for i in range(self.rows):
            for j in range(self.cols):
                if self.cubes[i][j].value == 0:
                    return False
        return True


class Cube:
    def __init__(self, value, row, col):
        self.value = value
        self.temp = 0
        self.row = row
        self.col = col
        self.selected = False

    def draw(self, win):
        x = GRID_X + self.col * CELL_GAP
        y = GRID_Y + self.row * CELL_GAP

        # Numbers
        if self.temp != 0 and self.value == 0:
            text = TEXT_FONT.render(str(self.temp), True, TEMP_NUM)
            win.blit(text, (x + 6, y + 4))
        elif self.value != 0:
            text = NUM_FONT.render(str(self.value), True, FIXED_NUM)
            win.blit(text, (x + (CELL_GAP - text.get_width()) // 2,
                            y + (CELL_GAP - text.get_height()) // 2))

    def set(self, val):
        self.value = val
        self.temp = 0

    def set_temp(self, val):
        self.temp = val


def draw_panel(win, play_time, strikes, status_msg):
    # Panel background
    panel_rect = pygame.Rect(PADDING, GRID_Y + GRID_SIZE + 15, WINDOW_W - PADDING*2, PANEL_H)
    pygame.draw.rect(win, PANEL_BG, panel_rect, border_radius=10)
    pygame.draw.rect(win, (220, 220, 220), panel_rect, width=1, border_radius=10)

    # Header
    title = TITLE_FONT.render("Sudoku — Instructions", True, PANEL_TEXT)
    win.blit(title, (panel_rect.x + 14, panel_rect.y + 10))

    # Stats (time + strikes)
    stats = TEXT_FONT.render(f"Time: {format_time(play_time)}    Mistakes: {strikes}", True, PANEL_TEXT)
    win.blit(stats, (panel_rect.x + 14, panel_rect.y + 46))

    # Instructions text (wrapped manually with simple lines)
    instructions = [
        "• Click a cell, then press 1–9 to pencil-in (gray).",
        "• Press Enter to commit a penciled number.",
        "• Press Delete/Backspace to clear a penciled cell.",
        "• Arrow keys move the selection.",
        "• A wrong commit adds a mistake (X).",
    ]
    y = panel_rect.y + 74
    for line in instructions:
        t = TEXT_FONT.render(line, True, (50, 50, 50))
        win.blit(t, (panel_rect.x + 14, y))
        y += 24

    # Optional status message (e.g., “Success”, “Wrong”, “Solved!”)
    if status_msg:
        msg = TEXT_FONT.render(status_msg, True, (0, 120, 0) if "Success" in status_msg or "Solved" in status_msg else (170, 0, 0))
        win.blit(msg, (panel_rect.right - msg.get_width() - 14, panel_rect.y + 12))


def redraw_window(win, board, play_time, strikes, status_msg):
    win.fill(BG_COLOR)
    # Title above grid
    title = TITLE_FONT.render("Sudoku", True, (40, 40, 40))
    win.blit(title, (GRID_X, GRID_Y - 28))

    # Grid + numbers
    board.draw(win)

    # Panel
    draw_panel(win, play_time, strikes, status_msg)

def format_time(secs):
    secs = int(secs)
    m = secs // 60
    s = secs % 60
    return f"{m:02d}:{s:02d}"

def main():
    win = pygame.display.set_mode((WINDOW_W, WINDOW_H))
    pygame.display.set_caption("Sudoku")
    board = Grid(GRID_ROWS, GRID_COLS)
    key = None
    run = True
    start = time.time()
    strikes = 0
    status_msg = ""
    # Start with a default selection so arrow keys work
    board.select(0, 0)

    while run:
        play_time = round(time.time() - start)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if event.type == pygame.KEYDOWN:
                # Number keys to set pencil (temp)
                if pygame.K_1 <= event.key <= pygame.K_9:
                    key = event.key - pygame.K_0
                    board.sketch(key)

                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    board.clear()
                    key = None
                    status_msg = ""

                elif event.key == pygame.K_RETURN:
                    if board.selected:
                        i, j = board.selected
                        if board.cubes[i][j].temp != 0:
                            if board.place(board.cubes[i][j].temp):
                                status_msg = "Success"
                            else:
                                status_msg = "Wrong"
                                strikes += 1
                            key = None

                            if board.is_finished():
                                status_msg = "Solved! 🎉"
                                run = False

                # Arrow keys to move selection
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    if not board.selected:
                        board.select(0, 0)
                    else:
                        i, j = board.selected
                        if event.key == pygame.K_UP:
                            i = clamp(i - 1, 0, GRID_ROWS - 1)
                        elif event.key == pygame.K_DOWN:
                            i = clamp(i + 1, 0, GRID_ROWS - 1)
                        elif event.key == pygame.K_LEFT:
                            j = clamp(j - 1, 0, GRID_COLS - 1)
                        elif event.key == pygame.K_RIGHT:
                            j = clamp(j + 1, 0, GRID_COLS - 1)
                        board.select(i, j)

            if event.type == pygame.MOUSEBUTTONDOWN:
                pos = pygame.mouse.get_pos()
                clicked = board.click(pos)
                if clicked:
                    board.select(clicked[0], clicked[1])
                    key = None
                    status_msg = ""

        redraw_window(win, board, play_time, strikes, status_msg)
        pygame.display.update()

    # small pause to let user see "Solved!" if it happened
    pygame.time.wait(600)
    pygame.quit()


if __name__ == "__main__":
    main()
