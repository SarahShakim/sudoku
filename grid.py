import pygame
import time
import asyncio
from sudoku import solve, valid, generate_puzzle, DIFFICULTY
import sys
from cube import Cube
pygame.init()
pygame.font.init()

SUBGRID_LINE = (0, 0, 0)
SELECTION = (209, 72, 54)
GRID_LINE = (0, 0, 0)

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
            j = (x - GX) // GAP
            i = (y - GY) // GAP
            return int(i), int(j)
        return None

    def is_finished(self):
        for i in range(self.rows):
            for j in range(self.cols):
                if self.cubes[i][j].value == 0:
                    return False
        return True