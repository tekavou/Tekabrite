import time
import board
import displayio
import busio
import adafruit_lis3dh
import random
from adafruit_matrixportal.matrix import Matrix

class ScoreDisplay:
    DIGITS = {
        0: [
            [1, 1, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        1: [
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
            [0, 1, 0],
        ],
        2: [
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
        ],
        3: [
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ],
        4: [
            [1, 0, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [0, 0, 1],
        ],
        5: [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ],
        6: [
            [1, 1, 1],
            [1, 0, 0],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        7: [
            [1, 1, 1],
            [0, 0, 1],
            [0, 0, 1],
            [0, 1, 0],
            [0, 1, 0],
        ],
        8: [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
        ],
        9: [
            [1, 1, 1],
            [1, 0, 1],
            [1, 1, 1],
            [0, 0, 1],
            [1, 1, 1],
        ],
    }

    def __init__(self, display, palette):
        self.bitmap = displayio.Bitmap(7, 5, len(palette))
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=palette)
        self.group = displayio.Group()
        self.group.append(self.tile_grid)
        self.group.x = 23  # Position on the right side
        self.group.y = 6
        display.root_group.append(self.group)
        self.score = 0
        self.update_score()

    def draw_digit(self, digit, offset):
        pattern = self.DIGITS[digit]
        for y, row in enumerate(pattern):
            for x, pixel in enumerate(row):
                self.bitmap[offset + x, y] = 3 if pixel else 0

    def update_score(self):
        tens = self.score // 10
        ones = self.score % 10
        self.draw_digit(tens, 0)
        self.draw_digit(ones, 4)

    def increment_score(self, lines=1):
        self.score = (self.score + lines) % 100
        self.update_score()


class NextUp:
    def __init__(self, width, height, palette):
        self.width = width
        self.height = height
        self.palette = palette

        # Create a bitmap without border
        self.bitmap = displayio.Bitmap(self.width, self.height, len(self.palette))

        # Create a tile grid for displaying the bitmap
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)

        # Create a group for the display
        self.group = displayio.Group()
        self.group.append(self.tile_grid)
        self.group.x = 1  # Position on the screen
        self.group.y = 5

    def display_piece(self, shape):
        # Clear the grid
        for x in range(self.width):
            for y in range(self.height):
                self.bitmap[x, y] = 0  # Clear to background (assume 0 is background)

        # Draw the piece shape shifted right by 2 columns
        shape_x_offset = (self.width // 2) - 2 + 2  # Shift right by 2
        shape_y_offset = (self.height // 2) - 2
        for dx, dy in shape:
            self.bitmap[shape_x_offset + dx, shape_y_offset + dy] = 2  # Draw using third color


class Piece:
    def __init__(self, shapes, x, y, game_width, game_min_x, game_max_x):
        self.shapes = shapes
        self.x = x
        self.y = y
        self.rotation_index = 0
        self.game_width = game_width
        self.game_min_x = game_min_x
        self.game_max_x = game_max_x


    def rotate(self):        
        self.rotation_index = (self.rotation_index + 1) % len(self.shapes)
        new_width = self.get_width()        

        # Adjust for width
        if self.x + new_width > self.game_max_x:
            self.x = self.game_max_x - new_width

        return self.shapes[self.rotation_index]


    def get_current_shape(self):
        return self.shapes[self.rotation_index]

    def get_width(self):
        current_shape = self.get_current_shape()
        min_x = min(x for x, _ in current_shape)
        max_x = max(x for x, _ in current_shape)        
        return max_x - min_x + 1

    def get_height(self):
        current_shape = self.get_current_shape()
        min_y = min(y for _, y in current_shape)
        max_y = max(y for _, y in current_shape)
        return max_y - min_y + 1


class TetrisGame:
    
    def __init__(self, width, height):
        self.setup_palette()
        self.setup_display(width, height)
        self.setup_game_board(width, height)
        self.setup_controls()
        self.pieces = self.load_pieces()
        self.next_piece_preview = NextUp(8, 8, self.palette)  # Initialize the NextUp display
        self.display.root_group.append(self.next_piece_preview.group)  # Add NextUp display to the main group
        self.next_piece = self.get_random_piece()  # Initialize the next piece
        self.current_piece = self.new_piece()  # Initialize the current piece
        self.update_next_piece_display()  # Display the next piece
        self.score_display = ScoreDisplay(self.display, self.palette)

    def setup_display(self, width, height):
        self.matrix = Matrix(width=32, height=32)
        self.display = self.matrix.display
        self.display.auto_refresh = False
        self.bitmap = displayio.Bitmap(32, 32, 4)
        self.tile_grid = displayio.TileGrid(self.bitmap, pixel_shader=self.palette)
        self.group = displayio.Group()
        self.group.append(self.tile_grid)
        self.display.root_group = self.group

    def setup_palette(self):
        self.palette = displayio.Palette(4)
        self.palette[0] = 0x000000  # Black
        self.palette[1] = 0x0000FF  # Blue
        self.palette[2] = 0xFF0000  # Red
        self.palette[3] = 0xFFFFFF  # Green

    def setup_game_board(self, width, height):
        self.width = width
        self.height = height
        self.game_min_x = (32 - width) // 2
        self.start_y = (32 - height) // 2
        self.game_max_x = self.game_min_x + width
        self.end_y = self.start_y + height
        self.draw_border()

    def setup_controls(self):
        self.i2c = busio.I2C(board.SCL, board.SDA)
        self.accelerometer = adafruit_lis3dh.LIS3DH_I2C(self.i2c, address=0x19)
        self.accelerometer.range = adafruit_lis3dh.RANGE_2_G

    def draw_border(self):
        for y in range(self.start_y - 1, self.end_y + 1):
            for x in range(self.game_min_x - 1, self.game_max_x + 1):
                if x < self.game_min_x or x >= self.game_max_x or y < self.start_y or y >= self.end_y:
                    self.bitmap[x, y] = 1  # Set border cells to blue


    def load_pieces(self):
        return {
            'I': [[(0, 0), (0, 1), (0, 2), (0, 3)], [(0, 0), (1, 0), (2, 0), (3, 0)]],
            'O': [[(0, 0), (1, 0), (0, 1), (1, 1)]],
            'S': [[(1, 0), (2, 0), (0, 1), (1, 1)], [(0, 0), (0, 1), (1, 1), (1, 2)]],
            'Z': [[(0, 0), (1, 0), (1, 1), (2, 1)], [(1, 0), (0, 1), (1, 1), (0, 2)]],
            'J': [[(0, 0), (0, 1), (1, 1), (2, 1)], [(0, 0), (1, 0), (0, 1), (0, 2)], [(0, 0), (1, 0), (2, 0), (2, 1)], [(1, 0), (1, 1), (0, 2), (1, 2)]],
            'L': [[(2, 0), (0, 1), (1, 1), (2, 1)], [(0, 0), (0, 1), (0, 2), (1, 2)], [(0, 0), (1, 0), (2, 0), (0, 1)], [(0, 0), (1, 0), (1, 1), (1, 2)]],
            'T': [[(0, 1), (1, 1), (2, 1), (1, 0)], [(0, 0), (0, 1), (0, 2), (1, 1)], [(0, 0), (1, 0), (2, 0), (1, 1)], [(1, 0), (0, 1), (1, 1), (1, 2)]]
        }
    
    def draw_border(self):
        for y in range(self.start_y - 1, self.end_y + 1):  # Includes border thickness
            for x in range(self.game_min_x - 1, self.game_max_x + 1):  # Includes border thickness
                if x < self.game_min_x or x >= self.game_max_x or y < self.start_y or y >= self.end_y:
                    self.bitmap[x, y] = 1  # Blue border

    def get_random_piece(self):
        return random.choice(list(self.pieces.keys()))

    def new_piece(self):
        # Set current piece to next piece and generate a new next piece
        piece_shape = self.next_piece
        self.next_piece = self.get_random_piece()  # Update the next piece
        self.update_next_piece_display()  # Update the display of the next piece
        return Piece(self.pieces[piece_shape], self.game_min_x + self.width // 2 - 2, self.start_y, self.width, self.game_min_x, self.game_max_x)

    def update_next_piece_display(self):
        # Update the next piece preview display
        shape = self.pieces[self.next_piece][0]  # Get the first rotation of the next piece
        self.next_piece_preview.display_piece(shape)

    def draw_piece(self, erase=False):
        shape = self.current_piece.get_current_shape()        
        color_index = 0 if erase else 2        
        
        for dx, dy in shape:                       
            x, y = self.current_piece.x + dx, self.current_piece.y + dy
            if self.game_min_x <= x < self.game_max_x and self.start_y <= y < self.end_y:
                self.bitmap[x, y] = color_index if not erase else 0

    def check_collision(self, dx=0, dy=0):
        #Check for collisions when the piece is moved by dx, dy.
        shape = self.current_piece.get_current_shape()
        for offset_x, offset_y in shape:
            # Calculate new position with the given delta x (dx) and delta y (dy)
            new_x = self.current_piece.x + offset_x + dx
            new_y = self.current_piece.y + offset_y + dy

            # Check for collisions with the boundaries
            if new_x < self.game_min_x or new_x >= self.game_max_x or new_y >= self.end_y:
                return True

            # Check for collisions with other blocks
            if new_y >= 0 and self.bitmap[new_x, new_y] != 0:  # Ensure the y-index is within the grid
                return True

        return False

    def clear_full_lines(self):
        full_lines = []
        for y in range(self.start_y, self.end_y):
            if all(self.bitmap[x, y] == 3 for x in range(self.game_min_x, self.game_max_x)):
                full_lines.append(y)

        num_lines_cleared = len(full_lines)
        
        if num_lines_cleared > 0:
            self.score_display.increment_score(num_lines_cleared)  # Move score increment here

        for _ in range(num_lines_cleared):
            for color in [1, 0]:
                for y in full_lines:
                    for x in range(self.game_min_x, self.game_max_x):
                        self.bitmap[x, y] = color
                self.display.refresh()
                time.sleep(0.25)
        
        if full_lines:
            lowest_full_line = min(full_lines)
            highest_full_line = max(full_lines)

            for y in range(highest_full_line, self.start_y - 1, -1):
                source_y = y - num_lines_cleared
                if source_y >= self.start_y:
                    for x in range(self.game_min_x, self.game_max_x):
                        self.bitmap[x, y] = self.bitmap[x, source_y]
                else:
                    for x in range(self.game_min_x, self.game_max_x):
                        self.bitmap[x, y] = 0

            self.display.refresh()


    def freeze_piece(self):
        shape = self.current_piece.get_current_shape()
        for dx, dy in shape:
            x, y = self.current_piece.x + dx, self.current_piece.y + dy
            if self.game_min_x <= x < self.game_max_x and self.start_y <= y < self.end_y:
                self.bitmap[x, y] = 3  # Change to green when frozen
        self.clear_full_lines()

    def move_down(self):
        if not self.check_collision(dy=1):
            self.current_piece.y += 1
        else:
            self.freeze_piece()
            if self.check_game_over():
                self.game_over_animation()
                return  # Optionally restart the game or end the game session
            self.current_piece = self.new_piece()

    def check_game_over(self):
        # Check if any block in the top row is filled (excluding the borders if any)
        for x in range(self.game_min_x, self.game_max_x):
            if self.bitmap[x, self.start_y] != 0:  # Assuming start_y is the first playable row
                self.game_over()
                break

    def game_over(self):
        # Go through each cell from top to bottom, erasing only colored cells
        for y in range(self.start_y, self.end_y):
            for x in range(self.game_min_x, self.game_max_x):
                if self.bitmap[x, y] != 0:  # Check if the cell is filled
                    self.bitmap[x, y] = 0  # Erase the block
                    self.display.refresh()
                    time.sleep(0.1)  # Faster erasure time
        # Optionally, reset the game or end the game session here

    def game_over_animation(self):
        for y in range(self.end_y - 1, self.start_y - 1, -1):  # From bottom to top
            for x in range(self.game_min_x, self.game_max_x):
                self.bitmap[x, y] = 0  # Clear the cell
                self.display.refresh()
                time.sleep(0.1)  # Delay to visualize the clearing process


    def move_piece(self, x):
        current_time = time.monotonic()
        if current_time - self.last_move_time <= self.rotate_interval:
            return
        
        #move = int(x / 2)
        move = int((x / 2)**2) * (1 if x > 0 else -1)
        new_x = self.current_piece.x + move

        if move > 0:  # Moving right
            self.move_right(new_x)
        elif move < 0:  # Moving left
            self.move_left(new_x)
        self.last_move_time = current_time

    def move_left(self, new_x): 
        if not self.check_collision(dx=-1):
            self.current_piece.x = max(new_x, self.game_min_x)

    def move_right(self, new_x):  
        if not self.check_collision(dx=1):      
            right_bound = self.game_max_x - self.get_piece_width()
            self.current_piece.x = min(new_x, right_bound)

    def rotate_piece(self):
        original_rotation = self.current_piece.rotation_index
        self.current_piece.rotate()
        if self.check_collision():  # Check collision after rotation with no dx, dy
            self.current_piece.rotation_index = original_rotation  # Revert rotation if collision

    def get_piece_width(self):
        shape = self.current_piece.get_current_shape()
        # Calculate the piece's span from the leftmost to the rightmost points
        min_x = min(dx for dx, _ in shape)
        max_x = max(dx for dx, _ in shape)
        return max_x - min_x + 1  # Plus one to include the starting block

    def try_rotate(self):
        current_time = time.monotonic()
        if current_time - self.last_rotate_time > self.rotate_interval:
            self.rotate_piece()
            self.last_rotate_time = current_time

    def process_down_movement(self):        
        if self.tilt_downwards > 5:            
            speed = speed = max(0.1, self.base_speed - self.tilt_coefficient * abs(self.tilt_downwards))
        else:
            speed = self.base_speed
                
        current_time = time.monotonic()
        
        if current_time - self.last_down_time > speed:
            self.move_down()
            self.last_down_time = current_time

    def game_loop(self):
        self.rotate_interval = 0.5  # Interval for rotation to prevent too frequent rotation
        self.move_interval = 0.02 
        self.tilt_coefficient = 0.1 
        self.base_speed = 1.0
        
        self.last_down_time = time.monotonic()
        self.last_rotate_time = time.monotonic()
        self.last_move_time = time.monotonic()

        while True:
            self.draw_piece(erase=True)
            x, y, _ = self.accelerometer.acceleration
            self.tilt_downwards = y  # Save the tilt value for downward movement speed adjustment

            # Check if it's time to rotate
            if y < -3:
                self.try_rotate()

            # Handle left/right movement based on x-tilt
            if abs(x) > 1.5:
                self.move_piece(x)

            # Handle downward movement
            self.process_down_movement()

            self.draw_piece()
            self.display.refresh()
            
game = TetrisGame(10, 20)
game.game_loop()
