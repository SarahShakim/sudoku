import pygame
import time
import asyncio
import sys
from grid import Grid

IS_WEB = sys.platform == "emscripten"

pygame.init()
pygame.font.init()

GRID_ROWS = GRID_COLS = 9

BG_COLOR = (245, 245, 245)
TEMP_NUM = (120, 120, 120)
FIXED_NUM = (20, 20, 20)
PANEL_BG = (255, 255, 255)
PANEL_TEXT = (30, 30, 30)
PANEL_BORDER = (220, 220, 220)

BASE_FONT_SIZE = 24

MIN_W, MIN_H = 560, 640
PADDING_FACTOR = 0.03
GRID_FACTOR = 0.70
GRID_MARGIN_TOP = 10
PANEL_SPACING = 15
PANEL_MIN_FACTOR = 0.22
PANEL_MIN_PX = 160
GRID_REFERENCE_PX = 540

font_cache = {} #{(path, size): pygame.font.Font}
panel_static_cache = {}
panel_stats_cache = {}
panel_status_cache = {}

def clamp(v, lo, hi): return max(lo, min(hi, v))

def compute_layout(win):
    w, h = win.get_size()
    w = max(w, MIN_W)
    h = max(h, MIN_H)

    smin = w if w < h else h

    padding = int(smin * PADDING_FACTOR)
    grid_size = int(smin * GRID_FACTOR)
    grid_x = (w - grid_size) // 2
    grid_y = padding + GRID_MARGIN_TOP
    cell_gap = grid_size // GRID_ROWS

    panel_top = grid_y + grid_size + PANEL_SPACING

    panel_h_tgt = int(h * PANEL_MIN_FACTOR)
    panel_h_max = max(0, h - panel_top - padding)
    panel_h = clamp(panel_h_tgt, PANEL_MIN_PX, panel_h_max)

    panel_rect = pygame.Rect(padding, panel_top, w - padding * 2, panel_h)

    scale = grid_size / GRID_REFERENCE_PX

    num_size = max(int(42 * scale), 18)
    text_size = max(int(BASE_FONT_SIZE * scale), 14)
    title_size = max(int(32 * scale), 16)

    num_font   = get_font(num_size)
    text_font  = get_font(text_size)
    title_font = get_font(title_size)

    return {
        "w": w, "h": h, "padding": padding,
        "grid_size": grid_size, "grid_x": grid_x, "grid_y": grid_y, "cell_gap": cell_gap,
        "panel_rect": panel_rect, "num_font": num_font, "text_font": text_font, "title_font": title_font
    }

def get_font(size, path=None):
    key = (path, int(size))
    f = font_cache.get(key)
    
    if f is None: 
        f = pygame.font.Font(path, int(size))
        font_cache[key] = f
    
    return f

def get_static_panel_assets(difficulty, title_font, text_font, panel_width):
    key = (difficulty, title_font.get_height(), text_font.get_height, panel_width)
    cached = panel_static_cache.get(key)

    if cached: 
        return cached
    
    title_text = f"Sudoku — {difficulty.title()} — Instructions"

    instructions = [
        "• Press N = New game (same difficulty). E/M/H = Easy/Medium/Hard.",
        "• Click a cell, then press 1-9 to pencil-in (gray).",
        "• Press Enter to commit a penciled number.\n  Wrong commits add a mistake and clears the cell.",
        "\n• Press Delete/Backspace to clear a penciled cell. Arrow keys move selection.",
    ]

    title_surface = title_font.render(title_text, True, PANEL_TEXT)

    instruction_surfaces = [text_font.render(line, True, (50, 50, 50)) for line in instructions]
    line_height = int(text_font.get_height() * 1.2)

    title_position = (14, 10)
    stats_position = (14, 46)
    instructions_start_y = 74

    cached = {
        "title_surf": title_surface,
        "title_pos_rel": title_position,
        "stats_pos_rel": stats_position,
        "instr_surfs": instruction_surfaces,
        "instr_positions_rel": [(14, instructions_start_y + i * line_height) for i in range(len(instruction_surfaces))],
        "line_height": line_height,
    }

    panel_static_cache[key] = cached

    return cached

def get_stats_surface(text_font, play_time, strikes):
    second = int(play_time)
    fkey = text_font.get_height()
    bucket = panel_stats_cache.setdefault(fkey, {"last": None, "surf": None})

    if bucket["last"] != (second, strikes):
        bucket["last"] = (second, strikes)
        surface = text_font.render(f"Time: {format_time(second)}    Mistakes: {strikes}", True, PANEL_TEXT)
        bucket["surf"] = surface
    
    return bucket["surf"]

def get_status_surface(text_font, status_msg):
    fkey = text_font.get_height()
    bucket = panel_status_cache.setdefault(fkey, {"last_msg": None, "surf": None})

    if bucket["last_msg"] != status_msg:
        bucket["last_msg"] = status_msg
        if status_msg: 
            good = ("Success" in status_msg) or ("Solved" in status_msg)
            color = (0, 120, 0) if good else (170, 0, 0)
            bucket["surf"] = text_font.render(status_msg, True, color)
        else:
            bucket["surf"] = None
    
    return bucket["surf"]

def draw_panel(win, play_time, strikes, status_msg, layout, difficulty):
    panel_rect = layout["panel_rect"]
    title_font, text_font = layout["title_font"], layout["text_font"]

    pygame.draw.rect(win, PANEL_BG, panel_rect, border_radius=10)
    pygame.draw.rect(win, PANEL_BORDER, panel_rect, width=1, border_radius=10)

    assets = get_static_panel_assets(difficulty, title_font, text_font, panel_rect.w)

    stats_surface = get_stats_surface(text_font, play_time, strikes)

    status_surface = get_status_surface(text_font, status_msg)

    ox, oy = panel_rect.x, panel_rect.y
    items = [
        (assets["title_surf"], (ox + assets["title_pos_rel"][0], oy + assets["title_pos_rel"][1])),
        (stats_surface, (ox + assets["stats_pos_rel"][0], oy + assets["stats_pos_rel"][1])),
    ]

    items.extend(
        (surf, (ox + px, oy + py))
        for surf, (px, py) in zip(assets["instr_surfs"], assets["instr_positions_rel"])
    )

    if status_surface:
        items.append((status_surface, (panel_rect.right - status_surface.get_width() - 14, panel_rect.y + 12)))

    win.blits(items)

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
                                status_msg = "Solved!!"
                elif event.key in (pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT):
                    i, j = board.selected or (0, 0)
                    if event.key == pygame.K_UP: 
                        i = clamp(i - 1, 0, GRID_ROWS - 1)
                    if event.key == pygame.K_DOWN:
                        i = clamp(i + 1, 0, GRID_ROWS - 1)
                    if event.key == pygame.K_LEFT:
                        j = clamp(j - 1, 0, GRID_COLS - 1)
                    if event.key == pygame.K_RIGHT:
                        j = clamp(j + 1, 0, GRID_COLS - 1)
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
