# 调色板生成脚本 - 为4个角色生成不同颜色版本

import pygame
import os
from PIL import Image
import math

# 角色颜色配置
CHARACTER_PALETTES = {
    0: {  # 角色1 - 红色系
        'name': 'p1',
        'skin': [(255, 204, 170), (240, 185, 150)],
        'hair': [(220, 50, 50), (180, 30, 30)],
        'outfit': [(220, 50, 50), (180, 30, 30), (100, 20, 20)],
        'accent': [(255, 220, 50), (255, 200, 0)],
    },
    1: {  # 角色2 - 蓝色系
        'name': 'p2',
        'skin': [(255, 204, 170), (240, 185, 150)],
        'hair': [(50, 100, 220), (30, 70, 180)],
        'outfit': [(50, 100, 220), (30, 70, 180), (20, 40, 120)],
        'accent': [(100, 255, 255), (50, 220, 220)],
    },
    2: {  # 角色3 - 绿色系
        'name': 'p3',
        'skin': [(255, 204, 170), (240, 185, 150)],
        'hair': [(50, 200, 80), (30, 160, 50)],
        'outfit': [(50, 200, 80), (30, 160, 50), (20, 100, 30)],
        'accent': [(255, 255, 100), (220, 220, 50)],
    },
    3: {  # 角色4 - 紫色系
        'name': 'p4',
        'skin': [(255, 204, 170), (240, 185, 150)],
        'hair': [(180, 50, 200), (140, 30, 160)],
        'outfit': [(180, 50, 200), (140, 30, 160), (100, 20, 120)],
        'accent': [(255, 150, 255), (220, 100, 220)],
    },
}

def color_distance(c1, c2):
    """计算颜色距离"""
    return math.sqrt(sum((a-b)**2 for a, b in zip(c1[:3], c2[:3])))

def find_closest_color(target, palette):
    """在调色板中找到最接近的颜色"""
    min_dist = float('inf')
    closest = palette[0]
    for color in palette:
        dist = color_distance(target, color)
        if dist < min_dist:
            min_dist = dist
            closest = color
    return closest

def swap_palette(image_path, output_path, char_index):
    """为单个图片交换调色板"""
    try:
        img = Image.open(image_path).convert('RGBA')
        pixels = img.load()
        width, height = img.size

        palette = CHARACTER_PALETTES[char_index]

        # 基础调色板颜色 (Brawler Girl 的颜色)
        base_skin = [(255, 204, 170), (240, 185, 150)]
        base_hair = [(255, 165, 80), (220, 130, 50)]
        base_outfit = [(220, 100, 140), (180, 70, 110), (100, 40, 70)]
        base_accent = [(255, 220, 50), (255, 200, 0)]
        base_outline = [(60, 40, 50), (80, 60, 50)]
        base_dark = [(40, 25, 30), (30, 20, 25)]

        for y in range(height):
            for x in range(width):
                r, g, b, a = pixels[x, y]
                if a < 128:  # 透明像素
                    continue

                # 黑色轮廓
                if r < 50 and g < 50 and b < 50:
                    continue

                # 肤色
                if r > 200 and g > 140 and b > 100:
                    new_color = find_closest_color((r, g, b), palette['skin'])
                    pixels[x, y] = (*new_color, a)
                # 头发 (橙色/棕色)
                elif r > 180 and g > 100 and b < 100 and r > g:
                    new_color = find_closest_color((r, g, b), palette['hair'])
                    pixels[x, y] = (*new_color, a)
                # 衣服 (粉红色系)
                elif r > 150 and g < 130 and b < 120 and r > g and r > b:
                    new_color = find_closest_color((r, g, b), palette['outfit'])
                    pixels[x, y] = (*new_color, a)
                # 黄色装饰
                elif r > 220 and g > 180 and b < 100:
                    new_color = find_closest_color((r, g, b), palette['accent'])
                    pixels[x, y] = (*new_color, a)
                # 深色阴影
                elif r < 80 and g < 60 and b < 60:
                    new_color = find_closest_color((r, g, b), palette['outfit'])
                    pixels[x, y] = (*new_color[0]//2, new_color[1]//2, new_color[2]//2, a)

        img.save(output_path)
        return True
    except Exception as e:
        print(f"Error processing {image_path}: {e}")
        return False

def process_character(char_index):
    """处理整个角色文件夹"""
    # 获取sprites目录的上级目录 (assets目录)
    sprite_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    sprite_dir = os.path.join(sprite_dir, 'sprites')
    source_dir = os.path.join(sprite_dir, 'characters', 'p1')
    output_dir = os.path.join(sprite_dir, 'characters', f'p{char_index + 1}')

    if char_index == 0:
        print("P1 uses base colors, skipping...")
        return

    print(f"Processing P{char_index + 1} palette...")

    for filename in os.listdir(source_dir):
        if filename.endswith('.png'):
            input_path = os.path.join(source_dir, filename)
            output_path = os.path.join(output_dir, filename)
            swap_palette(input_path, output_path, char_index)

    print(f"P{char_index + 1} palette swap complete!")

if __name__ == '__main__':
    # 处理角色2, 3, 4的调色板
    for i in [1, 2, 3]:
        process_character(i)
    print("All palettes generated!")
