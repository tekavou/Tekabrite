import time
import board
import displayio
import random
from adafruit_matrixportal.matrix import Matrix

class AudioVisualizer:
    def __init__(self, width, height):
        self.matrix = Matrix(width=32, height=32)
        self.display = self.matrix.display
        self.display.auto_refresh = False
        self.bitmap = displayio.Bitmap(32, 32, 5)  # Adjusted to 5 colors
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=self.setup_palette())
        self.group = displayio.Group()
        self.group.append(self.tile_grid)
        self.display.root_group = self.group
        self.columns = [6] * 12  # Initial values for the 12 channels

    def setup_palette(self):
        palette = displayio.Palette(5)
        palette[0] = 0x000000  # Black
        palette[1] = 0x0000FF  # Blue
        palette[2] = 0x00FF00  # Green
        palette[3] = 0xFFFF00  # Yellow
        palette[4] = 0xFF0000  # Red
        return palette

    def clear_visualizer(self):
        for x in range(4, 28):
            for y in range(20, 32):
                self.bitmap[x, y] = 0

    def weighted_random_change(self):
        changes = [-3, -2, -1, 0, 1, 2, 3]
        weights = [1, 2, 4, 8, 4, 2, 1]
        total_weight = sum(weights)
        rand_value = random.uniform(0, total_weight)
        cumulative_weight = 0
        for change, weight in zip(changes, weights):
            cumulative_weight += weight
            if rand_value < cumulative_weight:
                return change

    def update_visualizer(self):
        self.clear_visualizer()
        for i in range(12):
            prev_value = self.columns[i]
            change = self.weighted_random_change()
            new_value = prev_value + change
            new_value = max(1, min(12, new_value))
            self.columns[i] = new_value
            x1 = i * 2 + 4
            x2 = x1 + 1
            for y in range(32 - new_value, 32):
                color = 0  # Default to black
                if y >= 29:
                    color = 1  # Blue
                elif 26 <= y < 29:
                    color = 2  # Green
                elif 23 <= y < 26:
                    color = 3  # Yellow
                elif 20 <= y < 23:
                    color = 4  # Red
                self.bitmap[x1, y] = color
                self.bitmap[x2, y] = color

    def run(self):
        while True:
            self.update_visualizer()
            self.display.refresh()
            time.sleep(0.1)  # Update frequency

visualizer = AudioVisualizer(32, 32)
visualizer.run()