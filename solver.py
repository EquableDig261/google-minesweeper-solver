import pyautogui
import time
import numpy as np
import math
from copy import deepcopy

global color_vectors
color_vectors = [(25, 118, 210),    # Blue   - 1
                 (56, 142, 60),     # Green  - 2
                 (211, 47, 47),     # Red    - 3
                 (123, 31, 162),    # Purple - 4
                 (255, 143, 0),     # Orange - 5
                 (3, 152, 167)]     # Teal   - 6

global starting_position
starting_position = (0, 0)

def is_tile_empty(pixel_color): # +- 2 for each color around read values for dark and light
    if pixel_color[0] < 160 or pixel_color[0] > 172: 
        return False
    if pixel_color[1] < 207 or pixel_color[1] > 217:
        return False
    if pixel_color[2] < 71 or pixel_color[2] > 83:
        return False
    return True

def is_tile_zero(x, y, canvas): # just checks brightness values of all pixels and makes sure they are high colours are dark
    corner_coordinates = canvas.grid_to_corner_xy(x, y)
    number_screenshot = canvas.screenshot.crop((corner_coordinates[0], corner_coordinates[1], corner_coordinates[0] + canvas.tile_length - 1, corner_coordinates[1] + canvas.tile_length - 1))
    grey_number_screenshot = number_screenshot.convert("L")
    spread = grey_number_screenshot.getcolors()
    for i in spread:
        if i[1] < 190:
            return False
    return True 

def get_canvas_position(screenshot): 
    height = screenshot.height
    width = screenshot.width

    x_offset = 0 # itterates through starting from the left mid of the screen accross till it finds canvas, sets that to x_offset
    while not is_tile_empty(screenshot.getpixel((x_offset, height/2))) and x_offset < width-1:
        x_offset+=1

    if x_offset == width - 1: # if the offset is the entire screen it errors with NO CANVAS FOUND
        raise Exception("NO CANVAS FOUND")

    canvas_width = 0 # itterates from the left most position of the grid to the right most position and sets the distance to canvas_width
    while is_tile_empty(screenshot.getpixel((x_offset + canvas_width, height/2))):
        canvas_width += 1

    counter = 0 # itterates from x_offset up until off grid then gives the current y coordinate + 1 as y_offset
    while is_tile_empty(screenshot.getpixel((x_offset, height/2 - counter))):
        counter += 1
    y_offset = height/2 - counter + 1

    counter = 0 # itterates from top to bottom and sets height
    while is_tile_empty(screenshot.getpixel((x_offset, height/2 + counter))):
        counter += 1
    canvas_height = height/2 + counter - y_offset

    # x and y offsets refer to the coordinates of the 1st pixel of the canvas on top left

    return (int(x_offset), int(y_offset), int(canvas_width), int(canvas_height))

def get_grid_dimensions(screenshot, x_offset, y_offset, canvas_width, canvas_height):
    grid_width = 0
    previous_color = (0, 0, 0)
    for i in range(canvas_width): # simply goes left to right or up to down counting the number of times it encounters a new square
        color = screenshot.getpixel((x_offset + i, y_offset + 1))
        if (color == (162, 209, 73) or color == (170, 215, 81)) and color != previous_color:
            grid_width += 1
        previous_color = color

    grid_height = 0
    previous_color = (0, 0, 0)
    for i in range(canvas_height):
        color = screenshot.getpixel((x_offset + 1, y_offset + i))
        if (color == (162, 209, 73) or color == (170, 215, 81)) and color != previous_color:
            grid_height += 1
        previous_color = color

    return (grid_width, grid_height)



def color_from_grid(x, y, canvas): 
    return canvas.screenshot.getpixel((canvas.grid_to_centre_xy(x, y)))

def get_darkest_color(x, y, canvas): # converts to greyscale finds darkest pixel and returns the color of it in the non greyscale image
    corner_coordinates = canvas.grid_to_corner_xy(x, y)
    number_screenshot = canvas.screenshot.crop((corner_coordinates[0], corner_coordinates[1], corner_coordinates[0] + canvas.tile_length - 1, corner_coordinates[1] + canvas.tile_length - 1))
    number_screenshot_grey = number_screenshot.convert("L")
    number_screenshot_grey = np.array(number_screenshot)
    min_location = np.unravel_index(np.argmin(number_screenshot_grey, axis=None), number_screenshot_grey.shape)
    min_location = (int(min_location[1]), int(min_location[0]))
    return number_screenshot.getpixel((min_location[0], min_location[1]))

def get_color_id(color): # give it the rgb of a color and it returns the closest color vector each of which correspond to a color
    smallest_distance = math.inf
    smallest_distance_key = 0
    for key, vector in enumerate(color_vectors):
        distance = math.sqrt((color[0] - vector[0])**2 + (color[1] - vector[1])**2 + (color[2] - vector[2])**2)
        if distance < smallest_distance:
            smallest_distance = distance
            smallest_distance_key = key
    return smallest_distance_key + 1 

def get_color(x, y, canvas): # encompasses all tile detection, first identifies empties and zeros then runs the number detection
    if is_tile_empty(canvas.screenshot.getpixel(canvas.grid_to_centre_xy(x, y))):
        return "e"
    if is_tile_zero(x, y, canvas):
        return "z"
    return get_color_id(get_darkest_color(x, y, canvas))

def create_grid(canvas): #just creates a 2d list for each tile in the canvas
    grid = []
    for y in range(canvas.grid_height):
        grid.append([])
        for x in range(canvas.grid_width):
            grid[y].append("e")
    return grid

def update_grid(grid, canvas): # scans the grid and checks every empty for changes which it updates the grid with
    time.sleep(0.5)
    canvas.take_screenshot()
    for y in range(canvas.grid_height):
        for x in range(canvas.grid_width):
            if grid[y][x] == "e" or grid[y][x] == "c":
                grid[y][x] = get_color(x, y, canvas)
    return grid

def click(coordinates): # shorthand mouse goto and click
    pyautogui.moveTo(coordinates[0], coordinates[1])
    pyautogui.leftClick()

def grid_contains_empty(grid): # this function ensures the program stops when it has finished as all empties will be gone is the goal
    for y in grid:
        for x in y:
            if x == "e":
                return True
    return False

def get_places_to_click(grid): # returns a list of coordinates of places to click from the computed grid
    places_to_click = []
    for y_key, y_value in enumerate(grid):
        for x_key, x_value in enumerate(y_value):
            if x_value == "c":
                places_to_click.append((x_key, y_key))
    return places_to_click

def solve(grid, canvas): # a simple alg that gets current mines and empties checks if they fulfill a number if they do set all empties to mines
    checks = []

    for y_key, y_value in enumerate(grid):
        for x_key, x_value in enumerate(y_value):
            if type(x_value) == int:
                mine_counter = 0
                for i in range(-1, 2):
                    for ii in range(-1, 2):
                        if y_key + i >= 0 and y_key + i < canvas.grid_height and x_key + ii >= 0 and x_key + ii < canvas.grid_width:
                            if grid[y_key + i][x_key + ii] == "e" or grid[y_key + i][x_key + ii] == "m":
                                mine_counter += 1
                if mine_counter == x_value:
                    grid[y_key][x_key] = "z"
                    for i in range(-1, 2):
                        for ii in range(-1, 2):
                            if y_key + i >= 0 and y_key + i < canvas.grid_height and x_key + ii >= 0 and x_key + ii < canvas.grid_width:
                                if grid[y_key + i][x_key + ii] == "e":
                                    grid[y_key + i][x_key + ii] = "m"
                else:
                    checks.append((y_key, x_key))
    for check in checks: # check each number that wasn't able to be cleared and check if all mines are filled, if they are it can be determined that all remianing empties are safe
        mine_counter = 0
        for i in range(-1, 2):
            for ii in range(-1, 2):
                if check[0] + i >= 0 and check[0] + i < canvas.grid_height and check[1] + ii >= 0 and check[1] + ii < canvas.grid_width:
                    if grid[check[0] + i][check[1] + ii] == "m":
                        mine_counter += 1
        if mine_counter == grid[check[0]][check[1]]:
            grid[check[0]][check[1]] = "z"
            for i in range(-1, 2):
                for ii in range(-1, 2):
                    if check[0] + i >= 0 and check[0] + i < canvas.grid_height and check[1] + ii >= 0 and check[1] + ii < canvas.grid_width:
                        if grid[check[0] + i][check[1] + ii] == "e":
                            grid[check[0] + i][check[1] + ii] = "c"
    return grid

# ------------------------------------------------------------------------------------------------- #

def group_numbers(grid): # groups numbers by region to speed up processing on brute force
    found = set([])
    groups = []
    for y_key, y_value in enumerate(grid):
        for x_key, x_value in enumerate(y_value):
            if type(x_value) == int:
                current_group = []
                for i in range(-2, 3):
                    for ii in range(-2, 3):
                        if y_key + i < len(grid) and y_key + i >= 0 and x_key + ii >= 0 and x_key + ii < len(grid[0]):
                            if type(grid[y_key + i][x_key + ii]) == int:
                                surrounding_mines = 0
                                for iii in range(-1, 2):
                                    for iv in range(-1, 2):
                                        if y_key + i + iii < len(grid) and y_key + i + iii >= 0 and x_key + ii + iv >= 0 and x_key + ii + iv < len(grid[0]) and grid[y_key + i + iii][x_key + ii + iv] == 'm':
                                            surrounding_mines += 1
                                current_group.append(((x_key + ii, y_key + i), grid[y_key + i][x_key + ii] - surrounding_mines))
                found_flag = False
                for i in current_group:
                    if i[0] in found:
                        for ii_k, ii_v in enumerate(groups):
                            if i in ii_v:
                                groups[ii_k].update(set(current_group))
                                found_flag = True
                if not found_flag:
                    groups.append(set(current_group))
                found.add((x_key, y_key))
    return groups
            
def group_empties(grid, number_groups): # groups the empties in each region into coordinates and pointers to position of numbers that surround the empty
    empty_groups = []
    for number_group in number_groups:
        found_empties = set()
        empty_groups.append([])
        for number in number_group:
            for iii in range(-1, 2):
                for iv in range(-1, 2):
                    if number[0][1] + iii >= 0 and number[0][1] + iii < len(grid) and number[0][0] + iv >= 0 and number[0][0] + iv < len(grid[0]) and grid[number[0][1] + iii][number[0][0] + iv] == 'e':
                        if (number[0][0] + iv, number[0][1] + iii) in found_empties:
                            for i in empty_groups[-1]:
                                if (number[0][0] + iv, number[0][1] + iii) == i[0]:
                                    i[1].append(number[0])
                        else:
                            found_empties.add((number[0][0] + iv, number[0][1] + iii))
                            empty_groups[-1].append([(number[0][0] + iv, number[0][1] + iii), [number[0]]])
    return empty_groups

def sweep(grid, number_groups, empty_groups): # brute force on each group
    for key, empty_group in enumerate(empty_groups):
        successful_binary_strings = []
        for integer in range(2**len(empty_group)):
            number_group_dict = {nkey[0]: nkey[1] for nkey in number_groups[key]}
            binary = str(bin(integer))[2:].zfill(len(empty_group))
            for char_key, character in enumerate(binary):
                if character == "1":
                    for i in empty_group[char_key][1]:
                        number_group_dict[(i[0], i[1])] -= 1
            if all(tile_value == 0 for tile_key, tile_value in number_group_dict.items()):
                successful_binary_strings.append(binary)
        for i in range(len(empty_group)):
            if len(successful_binary_strings) == 0:
                raise Exception("IMPOSSIBLE GRID, GIVE UP")
            value = successful_binary_strings[0][i]
            if all(binar[i] == value for binar in successful_binary_strings):
                if successful_binary_strings[0][i] == "1":
                    grid[empty_group[i][0][1]][empty_group[i][0][0]] = "m"
                else:
                    grid[empty_group[i][0][1]][empty_group[i][0][0]] = "c"
    return grid

def remove_useless_numbers(grid): # removes numbers that have no value to the program as they provide no additional info as surrounded by non-empties
    for y_key, y_value in enumerate(grid):
        for x_key, x_value in enumerate(y_value):
            if type(x_value) == int:
                empty_flag = False
                for iii in range(-1, 2):
                    for iv in range(-1, 2):
                        if y_key + iii >= 0 and x_key + iv >= 0 and y_key + iii < len(grid) and x_key + iv < len(grid[0]):
                            if grid[y_key + iii][x_key + iv] == "e":
                                empty_flag = True
                if not empty_flag:
                    grid[y_key][x_key] = "z"
    return grid

def amds(grid):
    try:
        start_time = time.time()
        number_groups = group_numbers(grid)
        print([len(number_group) for number_group in number_groups])
        empty_groups = group_empties(grid, number_groups)
        grid = sweep(grid, number_groups, empty_groups)
        print(f"time taken: {time.time() - start_time}, for {[len(number_group) for number_group in number_groups]} sqaures!")
        return remove_useless_numbers(grid)
    except:
        "Impossible Found, reshoting"
        canvas.take_screenshot()
        grid = update_grid(grid)
        amds(grid)
        return grid

# ------------------------------------------------------------------------------------------------- #

def select_canvas(canvas_type):
    if canvas_type == "dynamic":
        canvas = Canvas(False)
        print("Found Canvas At:")
        print(canvas.get_presets())
        return canvas
    if canvas_type == "large":
        canvas = Canvas(True)
        canvas.set_presets(678, 478, 900, 750, 24, 20, 37)
        return canvas
    if canvas_type == "small":
        canvas = Canvas(True)
        canvas.set_presets(791, 583, 675, 540, 10, 8, 67)
        return canvas
    raise Exception("CANVAS TYPE UNDEFINED")

# ------------------------------------------------------------------------------------------------- #

class Canvas:
    def __init__(self, is_preset):
        self.screenshot = pyautogui.screenshot()
        if not is_preset:
            canvas_position = get_canvas_position(self.screenshot)
            self.x_offset, self.y_offset, self.canvas_width, self.canvas_height = canvas_position
            self.grid_width, self.grid_height = get_grid_dimensions(self.screenshot, self.x_offset, self.y_offset, self.canvas_width, self.canvas_height)
            self.tile_length = (self.canvas_width - self.grid_width/2)/self.grid_width

    def set_presets(self, x_offset, y_offset, canvas_width, canvas_height, grid_width, grid_height, tile_length):
        self.x_offset = x_offset
        self.y_offset = y_offset
        self.canvas_width = canvas_width
        self.canvas_height = canvas_height
        self.grid_width = grid_width
        self.grid_height = grid_height
        self.tile_length = tile_length

    def get_presets(self):
        return self.x_offset, self.y_offset, self.canvas_width, self.canvas_height, self.grid_width, self.grid_height, self.tile_length

    def take_screenshot(self):
        self.screenshot = pyautogui.screenshot()
        while not self.screenshot.getpixel(self.grid_to_corner_xy(starting_position[0], starting_position[1])) == (229, 194, 159):
            self.screenshot = pyautogui.screenshot()
            print("NULL SCREENSHOT --- RE-SNAPPING")

    def grid_to_centre_xy(self, grid_x, grid_y):
        corner_coordinates = self.grid_to_corner_xy(grid_x, grid_y)
        canvas_x = corner_coordinates[0] + math.floor(self.tile_length/2)
        canvas_y = corner_coordinates[1] + math.floor(self.tile_length/2)
        return (int(canvas_x), int(canvas_y))

    def grid_to_corner_xy(self, grid_x, grid_y):
        canvas_x = grid_x * self.tile_length + (self.x_offset) + math.ceil(grid_x/2)
        canvas_y = grid_y * self.tile_length + (self.y_offset) + math.ceil(grid_y/2)
        return (int(canvas_x), int(canvas_y))

# ------------------------------------------------------------------------------------------------- #

canvas_type = "dynamic"

canvas = select_canvas(canvas_type)

grid = create_grid(canvas)
click(canvas.grid_to_centre_xy(0, 0))
time.sleep(1)

grid = update_grid(deepcopy(grid), canvas)

# ------------------------------------------------------------------------------------------------- # 

while grid_contains_empty(grid):
    previous_grid = grid
    grid = solve(deepcopy(grid), canvas)
    if grid == previous_grid:
        print("running amds")
        grid = amds(grid)
        if grid == previous_grid:
            canvas.take_screenshot()
    places_to_click = get_places_to_click(grid)
    for location in places_to_click:
        click(canvas.grid_to_centre_xy(location[0], location[1]))
    pyautogui.moveTo(canvas.grid_to_centre_xy(0, 0))
    grid = update_grid(deepcopy(grid), canvas)

print("COMPLETE")