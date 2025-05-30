import cv2
import numpy as np
import os
from PIL import Image

def closest_color(pixel, color_lookup):
    lite_brite_colors = np.array(list(color_lookup.values()))
    abs_diff = np.abs(lite_brite_colors - pixel)
    total_diff = abs_diff.sum(axis=1)
    return list(color_lookup.keys())[np.argmin(total_diff)]

def apply_edge_detection_and_masking(img_array):
    gray = cv2.cvtColor(img_array, cv2.COLOR_RGB2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    edges = cv2.Canny(blurred, 50, 150)
    dilated_edges = cv2.dilate(edges, np.ones((3, 3), np.uint8), iterations=1)
    contours, _ = cv2.findContours(dilated_edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    mask = np.zeros_like(gray)
    cv2.fillPoly(mask, contours, 255)
    img_masked = img_array.copy()
    img_masked[mask == 0] = [0, 0, 0]
    return img_masked, mask * 255, edges

def convert_to_blocks_and_dominate_color(img_array):
    block_size = 32
    img_blocks = np.zeros((img_array.shape[0] // block_size, img_array.shape[1] // block_size, 3), dtype=np.uint8)
    for y in range(img_blocks.shape[0]):
        for x in range(img_blocks.shape[1]):
            block = img_array[y*block_size:(y+1)*block_size, x*block_size:(x+1)*block_size]
            dominant_color = np.median(block, axis=(0, 1)).astype(np.uint8)
            img_blocks[y, x] = dominant_color
    return img_blocks

def save_color_data_to_txt(img_blocks, filename, is_litebrite=False, color_lookup=None):
    with open(filename, 'w') as file:
        if is_litebrite:
            file.write('# Lite Brite Color Lookup:\n')
            for key, value in color_lookup.items():
                file.write(f'{key}: {value}\n')
            file.write('\n# Grid:\n')
            processed_grid = [[closest_color(color, color_lookup) for color in row] for row in img_blocks]
        else:
            unique_colors = np.unique(img_blocks.reshape(-1, 3), axis=0)
            color_key = {tuple(color): chr(65 + i) for i, color in enumerate(unique_colors)}
            file.write('# Blocks Color Lookup:\n')
            for key, value in color_key.items():
                file.write(f'{value}: {key}\n')
            file.write('\n# Grid:\n')
            processed_grid = [[color_key[tuple(color)] for color in row] for row in img_blocks]
        
        for row in processed_grid:
            file.write(''.join(row) + '\n')

def process_image(input_path, output_directory, color_lookup):
    img = Image.open(input_path).convert('RGB')
    img_array = np.array(img)

    img_masked, mask, edges = apply_edge_detection_and_masking(img_array)
    img_blocks = convert_to_blocks_and_dominate_color(img_masked)

    base_name = os.path.splitext(os.path.basename(input_path))[0]

    # Save all images and generate text output
    Image.fromarray(img_masked).save(os.path.join(output_directory, f"{base_name}_masked.png"))    
    Image.fromarray(edges).save(os.path.join(output_directory, f"{base_name}_edges.png"))

    blocks_img = Image.fromarray(np.repeat(np.repeat(img_blocks, 32, axis=0), 32, axis=1))
    blocks_img.save(os.path.join(output_directory, f"{base_name}_blocks.png"))
    save_color_data_to_txt(img_blocks, os.path.join(output_directory, f"{base_name}_blocks.txt"))

    lite_brite_blocks = np.array([[color_lookup[closest_color(block, color_lookup)] for block in row] for row in img_blocks], dtype=np.uint8)
    lite_brite_img = Image.fromarray(np.repeat(np.repeat(lite_brite_blocks, 32, axis=0), 32, axis=1))
    lite_brite_img.save(os.path.join(output_directory, f"{base_name}_litebrite.png"))
    save_color_data_to_txt(lite_brite_blocks, os.path.join(output_directory, f"{base_name}_litebrite.txt"), is_litebrite=True, color_lookup=color_lookup)

input_directory = 'input'
output_directory = 'output/convert'
color_lookup = {
    'W': (255, 255, 255),  # White
    'B': (1, 1, 230),      # Blue
    'P': (128, 0, 128),    # Purple
    'G': (0, 255, 0),      # Green
    'Y': (255, 255, 0),    # Yellow
    'O': (255, 165, 0),    # Orange
    'K': (0, 0, 0)         # Black
}

if not os.path.exists(output_directory):
    os.makedirs(output_directory)

for filename in os.listdir(input_directory):
    if filename.lower().endswith(('.webp', '.jpg', '.jpeg', '.png')):
        process_image(os.path.join(input_directory, filename), output_directory, color_lookup)