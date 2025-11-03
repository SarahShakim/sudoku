import pygame
import time
import asyncio
from sudoku import solve, valid, generate_puzzle, DIFFICULTY
import sys

IS_WEB = sys.platform == "emscripten"

pygame.init()
pygame.font.init()

GRID_ROWS = GRID_COLS = 9

BG_COLOR = (245, 245, 245)
GRID_LINE = (0, 0, 0)
SUBGRID_LINE = (0, 0, 0)
SELECTION = (209, 72, 54)
TEMP_NUM = (120, 120, 120)
FIXED_NUM = (20, 20, 20)
PANEL_BG = (255, 255, 255)
PANEL_TEXT = (30, 30, 30)
PANEL_BORDER = (220, 220, 220)

BASE_FONT_SIZE = 24

def clamp(v, lo, hi): return max(lo, min(hi, v))

def compute_layout(win):
    w, h = win.get_size()
    w = max(w, 560); h = max(h, 640)
    padding = int(min(w, h) * 0.03)
    grid_size = int(min(w, h) * 0.70)
    grid_x = (w - grid_size) // 2
    grid_y = padding + 10
    cell_gap = grid_size // GRID_ROWS
    panel_top = grid_y + grid_size + 15
    panel_h = max(int(h * 0.22), 160)
    panel_h = min(panel_h, h - panel_top - padding)
    panel_rect = pygame.Rect(padding, panel_top, w - padding * 2, panel_h)
    scale = grid_size / 540

    num_font   = pygame.font.Font(None, max(int(42 * scale), 18))
    text_font  = pygame.font.Font(None, max(int(BASE_FONT_SIZE * scale), 14))
    title_font = pygame.font.Font(None, max(int(32 * scale), 16))

    return {
        "w": w, "h": h, "padding": padding,
        "grid_size": grid_size, "grid_x": grid_x, "grid_y": grid_y, "cell_gap": cell_gap,
        "panel_rect": panel_rect, "num_font": num_font, "text_font": text_font, "title_font": title_font
    }

class Grid:
    def __init__(self, rows, cols, difficulty="medium"):
        self.rows = rows
        self.cols = cols
        self.board = generate_puzzle(difficulty=difficulty)  # randomized, unique
        self.cubes = [[Cube(self.board[i][j], i, j) for j in range(cols)] for i in range(rows)]
        self.model = None
        self.selected = None

    def update_model(self):
        self.model = [[self.cubes[i][j].value for j in range(self.cols)] for i in range(self.rows)]

    def place(self, val):
        if not self.selected: return False
        r, c = self.selected
        if self.cubes[r][c].value == 0:
            self.cubes[r][c].set(val)
            self.update_model()
            model_copy = [row[:] for row in self.model]
            if valid(model_copy, val, (r, c)) and solve(model_copy):
                return True
            self.cubes[r][c].set(0)
            self.cubes[r][c].set_temp(0)
            self.update_model()
        return False

    def sketch(self, val):
        if not self.selected: return
        r, c = self.selected
        if self.cubes[r][c].value == 0:
            self.cubes[r][c].set_temp(val)

    def draw(self, win, layout):
        GX, GY, GS, GAP = layout["grid_x"], layout["grid_y"], layout["grid_size"], layout["cell_gap"]
        for i in range(self.rows + 1):
            thick = 3 if i % 3 == 0 else 1
            pygame.draw.line(win, SUBGRID_LINE if thick == 3 else GRID_LINE, (GX, GY + i * GAP), (GX + GS, GY + i * GAP), thick)
            pygame.draw.line(win, SUBGRID_LINE if thick == 3 else GRID_LINE, (GX + i * GAP, GY), (GX + i * GAP, GY + GS), thick)

        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].draw(win, layout)

        if self.selected:
            i, j = self.selected
            x = GX + j * GAP; y = GY + i * GAP
            pygame.draw.rect(win, SELECTION, pygame.Rect(x + 2, y + 2, GAP - 4, GAP - 4), 3, border_radius=6)

    def select(self, row, col):
        for i in range(self.rows):
            for j in range(self.cols):
                self.cubes[i][j].selected = False
        self.cubes[row][col].selected = True
        self.selected = (row, col)

    def clear(self):
        if not self.selected: return
        r, c = self.selected
        if self.cubes[r][c].value == 0:
            self.cubes[r][c].set_temp(0)

    def click(self, pos, layout):
        x, y = pos
        GX, GY, GS, GAP = layout["grid_x"], layout["grid_y"], layout["grid_size"], layout["cell_gap"]
        if GX <= x < GX + GS and GY <= y < GY + GS:
            j = (x - GX) // GAP; i = (y - GY) // GAP
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

    def set(self, val):
        self.value = val
        self.temp = 0

    def set_temp(self, val):
        self.temp = val

    def draw(self, win, layout):
        GX, GY, GAP = layout["grid_x"], layout["grid_y"], layout["cell_gap"]
        num_font, text_font = layout["num_font"], layout["text_font"]
        x = GX + self.col * GAP
        y = GY + self.row * GAP

        if self.temp != 0 and self.value == 0:
            text = text_font.render(str(self.temp), True, (120, 120, 120))
            win.blit(text, (x + 6, y + 4))
        elif self.value != 0:
            text = num_font.render(str(self.value), True, (20, 20, 20))
            win.blit(text, (x + (GAP - text.get_width()) // 2, y + (GAP - text.get_height()) // 2))

def draw_panel(win, play_time, strikes, status_msg, layout, difficulty):
    panel_rect = layout["panel_rect"]
    title_font, text_font = layout["title_font"], layout["text_font"]

    pygame.draw.rect(win, PANEL_BG, panel_rect, border_radius=10)
    pygame.draw.rect(win, PANEL_BORDER, panel_rect, width=1, border_radius=10)

    title = title_font.render(f"Sudoku — {difficulty.title()} — Instructions", True, PANEL_TEXT)
    win.blit(title, (panel_rect.x + 14, panel_rect.y + 10))

    stats = text_font.render(f"Time: {format_time(play_time)}    Mistakes: {strikes}", True, PANEL_TEXT)
    win.blit(stats, (panel_rect.x + 14, panel_rect.y + 46))

    instructions = [
        "• Press N = New game (same difficulty). E/M/H = Easy/Medium/Hard.",
        "• Click a cell, then press 1-9 to pencil-in (gray).",
        "• Press Enter to commit a penciled number. Wrong commits add a mistake and clears the cell.",
        "• Press Delete/Backspace to clear a penciled cell. Arrow keys move selection.",
    ]
    y = panel_rect.y + 74
    for line in instructions:
        t = text_font.render(line, True, (50, 50, 50))
        win.blit(t, (panel_rect.x + 14, y))
        y += int(text_font.get_height() * 1.2)

    if status_msg:
        good = ("Success" in status_msg) or ("Solved" in status_msg)
        color = (0, 120, 0) if good else (170, 0, 0)
        msg = text_font.render(status_msg, True, color)
        win.blit(msg, (panel_rect.right - msg.get_width() - 14, panel_rect.y + 12))

def redraw_window(win, board, play_time, strikes, status_msg, layout, difficulty):
    win.fill(BG_COLOR)
    title = layout["title_font"].render("Sudoku", True, (40, 40, 40))
    win.blit(title, (layout["grid_x"], layout["grid_y"] - title.get_height() - 6))
    board.draw(win, layout)
    draw_panel(win, play_time, strikes, status_msg, layout, difficulty)

def format_time(secs):
    secs = int(secs); m = secs // 60; s = secs % 60
    return f"{m:02d}:{s:02d}"

async def main():
    import asyncio
    pygame.init()
    pygame.font.init()

    await asyncio.sleep(0)

    try:
        if IS_WEB:
            flags = 0
            size  = (0, 0)
        else:
            flags = pygame.SCALED | pygame.RESIZABLE
            size  = (900, 1000)

        win = pygame.display.set_mode(size, flags)
    except pygame.error:
        win = pygame.display.set_mode((800, 600))

    pygame.display.set_caption("Sudoku")

    current_difficulty = "medium"
    board = Grid(GRID_ROWS, GRID_COLS, difficulty=current_difficulty)
    run = True
    start = time.time()
    strikes = 0
    status_msg = ""
    board.select(0, 0)
    clock = pygame.time.Clock()

    while run:
        play_time = round(time.time() - start)
        layout = compute_layout(win)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False

            if (not IS_WEB) and event.type == pygame.VIDEORESIZE:
                win = pygame.display.set_mode((event.w, event.h), pygame.SCALED | pygame.RESIZABLE)

            if event.type == pygame.KEYDOWN:
                if pygame.K_1 <= event.key <= pygame.K_9:
                    board.sketch(event.key - pygame.K_0)
                elif event.key in (pygame.K_DELETE, pygame.K_BACKSPACE):
                    board.clear(); status_msg = ""
                elif event.key == pygame.K_RETURN:
                    if board.selected:
                        i, j = board.selected
                        if board.cubes[i][j].temp != 0:
                            if board.place(board.cubes[i][j].temp):
                                status_msg = "Success"
                            else:
                                status_msg = "Wrong"; strikes += 1
                            if board.is_finished():
                                status_msg = "Solved! 🎉"
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    i, j = board.selected or (0, 0)
                    if event.key == pygame.K_UP:    i = clamp(i - 1, 0, GRID_ROWS - 1)
                    if event.key == pygame.K_DOWN:  i = clamp(i + 1, 0, GRID_ROWS - 1)
                    if event.key == pygame.K_LEFT:  j = clamp(j - 1, 0, GRID_COLS - 1)
                    if event.key == pygame.K_RIGHT: j = clamp(j + 1, 0, GRID_COLS - 1)
                    board.select(i, j)
                elif event.key == pygame.K_n:
                    board = Grid(GRID_ROWS, GRID_COLS, difficulty=current_difficulty)
                    board.select(0, 0); start = time.time(); strikes = 0; status_msg = "New game started!"
                elif event.key in (pygame.K_e, pygame.K_m, pygame.K_h):
                    current_difficulty = {pygame.K_e:"easy", pygame.K_m:"medium", pygame.K_h:"hard"}[event.key]
                    board = Grid(GRID_ROWS, GRID_COLS, difficulty=current_difficulty)
                    board.select(0, 0); start = time.time(); strikes = 0; status_msg = f"New {current_difficulty.title()} game!"

            if event.type == pygame.MOUSEBUTTONDOWN:
                clicked = board.click(pygame.mouse.get_pos(), layout)
                if clicked:
                    board.select(*clicked); status_msg = ""

        redraw_window(win, board, play_time, strikes, status_msg, layout, current_difficulty)
        pygame.display.flip()
        clock.tick(60)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
