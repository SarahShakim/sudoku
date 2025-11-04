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