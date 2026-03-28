# 战斗场景

import pygame
from typing import Tuple, List

class Stage:
    """对战场景基类"""

    def __init__(self, width: int, height: int):
        self.width = width
        self.height = height
        self.ground_y = 580
        self.background_color = (30, 30, 50)
        self.platforms: List[Tuple[int, int, int, int]] = []

        # 背景元素
        self.bg_elements: List = []

    def draw_background(self, surface: pygame.Surface):
        """绘制背景"""
        # 渐变背景
        for y in range(self.height):
            ratio = y / self.height
            r = int(20 + ratio * 20)
            g = int(20 + ratio * 20)
            b = int(40 + ratio * 30)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))

        # 绘制背景装饰
        self._draw_decorations(surface)

    def _draw_decorations(self, surface: pygame.Surface):
        """绘制装饰元素"""
        # 城市剪影
        buildings = [
            (50, 400, 80, 180),
            (150, 350, 100, 230),
            (280, 380, 70, 200),
            (400, 320, 120, 260),
            (550, 360, 90, 220),
            (700, 340, 110, 240),
            (850, 370, 80, 210),
            (950, 350, 100, 230),
            (1080, 390, 70, 190),
            (1180, 330, 90, 250),
        ]

        for x, y, w, h in buildings:
            # 建筑轮廓
            pygame.draw.rect(surface, (15, 15, 25), (x, y, w, h))

            # 窗户
            window_color = (40, 40, 60)
            for wy in range(y + 10, y + h - 20, 25):
                for wx in range(x + 10, x + w - 10, 20):
                    pygame.draw.rect(surface, window_color, (wx, wy, 12, 15))

    def draw_ground(self, surface: pygame.Surface):
        """绘制地面"""
        # 地面
        ground_rect = (0, self.ground_y, self.width, self.height - self.ground_y)
        pygame.draw.rect(surface, (40, 40, 55), ground_rect)

        # 地面线
        pygame.draw.line(surface, (80, 80, 100), (0, self.ground_y), (self.width, self.ground_y), 3)

        # 地面纹理
        for x in range(0, self.width, 40):
            pygame.draw.line(surface, (50, 50, 65), (x, self.ground_y + 10), (x + 20, self.ground_y + 10), 2)

    def draw(self, surface: pygame.Surface):
        """绘制场景"""
        self.draw_background(surface)
        self.draw_ground(surface)


class Stage1(Stage):
    """默认对战场景"""

    def __init__(self, width: int = 1280, height: int = 720):
        super().__init__(width, height)
        self.name = "城市夜景"
        self.description = "经典对战舞台"
