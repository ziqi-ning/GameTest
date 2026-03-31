# 寝室场景 - DormStage

import pygame
from typing import Tuple, List
from stages.stage_1 import Stage


class DormStage(Stage):
    """寝室对战场景 - 四个上下铺床，多层平台"""

    def __init__(self, width: int = 1280, height: int = 720):
        super().__init__(width, height)
        self.name = "寝室风云"
        self.description = "四人寝室，上下铺对决！"

        # 寝室墙壁颜色（暖黄色调）
        self.wall_color_top = (90, 70, 55)
        self.wall_color_bottom = (70, 55, 42)
        self.floor_color = (100, 75, 50)
        self.floor_dark = (80, 60, 40)

        # 上下铺配置：每组床有两层（0=下铺站立面, 1=上铺站立面）
        # 格式：(x, y, width, height) - 站立面的矩形
        self.platforms: List[Tuple[int, int, int, int]] = []

        # --- 左1号上下铺 ---
        # 下铺站立面
        self.platforms.append((60, 480, 160, 20))
        # 上铺站立面
        self.platforms.append((60, 300, 160, 20))

        # --- 左2号上下铺 ---
        self.platforms.append((260, 400, 150, 20))
        self.platforms.append((260, 250, 150, 20))

        # --- 右1号上下铺 ---
        self.platforms.append((1060, 480, 160, 20))
        self.platforms.append((1060, 300, 160, 20))

        # --- 右2号上下铺 ---
        self.platforms.append((870, 400, 150, 20))
        self.platforms.append((870, 250, 150, 20))

        # --- 中间下铺（偏左）---
        self.platforms.append((420, 460, 140, 20))

        # --- 中间上铺（偏右）---
        self.platforms.append((720, 460, 140, 20))

        # 床的装饰信息（用于绘制）
        self.beds = [
            # 左1
            {"x": 60, "y_lower": 480, "y_upper": 300, "w": 160, "h": 20,
             "lower_frame_bottom": 500, "upper_frame_bottom": 320,
             "upper_legs_top": 308, "lower_legs_top": 488},
            # 左2
            {"x": 260, "y_lower": 400, "y_upper": 250, "w": 150, "h": 20,
             "lower_frame_bottom": 420, "upper_frame_bottom": 270,
             "upper_legs_top": 258, "lower_legs_top": 408},
            # 右1
            {"x": 1060, "y_lower": 480, "y_upper": 300, "w": 160, "h": 20,
             "lower_frame_bottom": 500, "upper_frame_bottom": 320,
             "upper_legs_top": 308, "lower_legs_top": 488},
            # 右2
            {"x": 870, "y_lower": 400, "y_upper": 250, "w": 150, "h": 20,
             "lower_frame_bottom": 420, "upper_frame_bottom": 270,
             "upper_legs_top": 258, "lower_legs_top": 408},
            # 中左
            {"x": 420, "y_lower": 460, "y_upper": 460, "w": 140, "h": 20,
             "lower_frame_bottom": 480, "upper_frame_bottom": 480,
             "upper_legs_top": 468, "lower_legs_top": 468},
            # 中右
            {"x": 720, "y_lower": 460, "y_upper": 460, "w": 140, "h": 20,
             "lower_frame_bottom": 480, "upper_frame_bottom": 480,
             "upper_legs_top": 468, "lower_legs_top": 468},
        ]

        # 寝室内装饰元素
        self.decorations = []

    def _render_bg_to_cache(self) -> pygame.Surface:
        """将寝室背景预渲染到缓存"""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # 渐变墙面
        for y in range(self.height):
            ratio = y / self.height
            r = int(90 * (1 - ratio * 0.3) + 70 * ratio)
            g = int(70 * (1 - ratio * 0.3) + 55 * ratio)
            b = int(55 * (1 - ratio * 0.3) + 42 * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y), 1)
        # 墙线细节
        pygame.draw.line(surf, (110, 85, 65), (0, 0), (self.width, 0), 8)
        pygame.draw.line(surf, (120, 90, 60), (0, 560), (self.width, 560), 5)
        for y in range(80, 560, 120):
            for x in range(0, self.width, 4):
                pygame.draw.line(surf, (100, 78, 55), (x, y), (x + 2, y), 1)
        # 窗户
        wx, wy, ww, wh = 900, 60, 300, 200
        pygame.draw.rect(surf, (80, 65, 45), (wx - 6, wy - 6, ww + 12, wh + 12), border_radius=4)
        pygame.draw.rect(surf, (15, 20, 40), (wx, wy, ww, wh))
        import random
        random.seed(42)
        for _ in range(20):
            sx = wx + random.randint(0, ww - 2)
            sy = wy + random.randint(0, wh // 2 - 2)
            brightness = random.randint(180, 255)
            pygame.draw.circle(surf, (brightness, brightness, brightness), (sx, sy), 1)
        pygame.draw.circle(surf, (240, 230, 180), (wx + 240, wy + 50), 30)
        pygame.draw.circle(surf, (15, 20, 40), (wx + 250, wy + 45), 28)
        pygame.draw.line(surf, (80, 65, 45), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 4)
        pygame.draw.line(surf, (80, 65, 45), (wx, wy + wh // 2), (wx, wy + wh), 4)
        pygame.draw.rect(surf, (80, 65, 45), (wx, wy, ww, wh), 4, border_radius=2)
        # 串灯电线
        light_positions = [(100, 55), (200, 58), (300, 52), (400, 57), (500, 54),
                           (600, 56), (700, 53), (800, 58), (900, 55), (1000, 52), (1100, 57), (1200, 54)]
        prev = light_positions[0]
        for lx, ly in light_positions[1:]:
            pygame.draw.line(surf, (60, 45, 30), prev, (lx, ly + 6), 1)
            prev = (lx, ly + 6)
        colors = [(255, 100, 100), (255, 220, 100), (100, 220, 255), (200, 100, 255), (255, 180, 100)]
        for i, (lx, ly) in enumerate(light_positions):
            c = colors[i % len(colors)]
            pygame.draw.circle(surf, c, (lx, ly), 6)
            pygame.draw.circle(surf, (255, 255, 220), (lx, ly), 3)
        # 海报
        pygame.draw.rect(surf, (30, 30, 60), (30, 80, 80, 110))
        pygame.draw.rect(surf, (220, 200, 50), (35, 85, 70, 50))
        pygame.draw.rect(surf, (200, 50, 50), (35, 145, 70, 40))
        pygame.draw.rect(surf, (255, 255, 255), (30, 80, 80, 110), 2)
        pygame.draw.rect(surf, (60, 20, 20), (140, 120, 70, 90))
        pygame.draw.rect(surf, (220, 170, 50), (145, 125, 60, 40))
        pygame.draw.rect(surf, (255, 255, 255), (140, 120, 70, 90), 2)
        pygame.draw.rect(surf, (40, 80, 40), (500, 100, 60, 80))
        pygame.draw.rect(surf, (200, 220, 200), (505, 105, 50, 30))
        pygame.draw.rect(surf, (255, 255, 255), (500, 100, 60, 80), 2)
        pygame.draw.rect(surf, (255, 100, 100), (1250, 100, 25, 30))
        pygame.draw.rect(surf, (100, 200, 255), (1230, 140, 20, 25))
        pygame.draw.rect(surf, (255, 220, 100), (1255, 170, 18, 22))
        # 衣柜
        cx, cy, cw, ch = 1190, 220, 80, 280
        pygame.draw.rect(surf, (90, 70, 50), (cx, cy, cw, ch))
        pygame.draw.line(surf, (70, 55, 38), (cx + cw // 2, cy + 10), (cx + cw // 2, cy + ch - 10), 2)
        pygame.draw.circle(surf, (160, 130, 90), (cx + cw // 2 - 12, cy + ch // 2), 4)
        pygame.draw.circle(surf, (160, 130, 90), (cx + cw // 2 + 12, cy + ch // 2), 4)
        pygame.draw.line(surf, (110, 85, 60), (cx - 3, cy), (cx + cw + 3, cy), 4)
        pygame.draw.line(surf, (70, 55, 38), (cx, cy), (cx, cy + ch), 3)
        return surf

    def _render_ground_to_cache(self) -> pygame.Surface:
        """将寝室地面预渲染到缓存"""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        ground_rect = (0, self.ground_y, self.width, self.height - self.ground_y)
        pygame.draw.rect(surf, (100, 75, 50), ground_rect)
        for y in range(self.ground_y, self.height, 20):
            offset = ((y - self.ground_y) // 20) % 2
            for x in range(-offset * 80, self.width, 160):
                pygame.draw.rect(surf, (80, 60, 40), (x, y, 155, 18), 1)
        pygame.draw.line(surf, (130, 100, 65), (0, self.ground_y), (self.width, self.ground_y), 3)
        return surf

    def draw_background(self, surface: pygame.Surface):
        """绘制寝室背景（使用缓存）"""
        self._ensure_cache()
        if self._bg_cache:
            surface.blit(self._bg_cache, (0, 0))

    def _draw_wall_details(self, surface: pygame.Surface):
        pass  # 已缓存到 _bg_cache

    def _draw_window(self, surface: pygame.Surface):
        pass

    def _draw_string_lights(self, surface: pygame.Surface):
        pass

    def _draw_posters(self, surface: pygame.Surface):
        pass

    def _draw_closet(self, surface: pygame.Surface):
        pass

    def _draw_wall_details(self, surface: pygame.Surface):
        """墙面细节 - 墙线、天花板线"""
        # 天花板线
        pygame.draw.line(surface, (110, 85, 65), (0, 0), (self.width, 0), 8)
        # 墙面踢脚线
        pygame.draw.line(surface, (120, 90, 60), (0, 560), (self.width, 560), 5)
        # 墙面横向分隔线（模拟墙纸）
        for y in range(80, 560, 120):
            for x in range(0, self.width, 4):
                pygame.draw.line(surface, (100, 78, 55), (x, y), (x + 2, y), 1)

    def _draw_window(self, surface: pygame.Surface):
        """绘制窗户（右上角）"""
        wx, wy = 900, 60
        ww, wh = 300, 200

        # 窗框外沿
        pygame.draw.rect(surface, (80, 65, 45), (wx - 6, wy - 6, ww + 12, wh + 12), border_radius=4)
        # 夜空背景
        pygame.draw.rect(surface, (15, 20, 40), (wx, wy, ww, wh))

        # 星星
        import random
        random.seed(42)
        for _ in range(20):
            sx = wx + random.randint(0, ww - 2)
            sy = wy + random.randint(0, wh // 2 - 2)
            brightness = random.randint(180, 255)
            pygame.draw.circle(surface, (brightness, brightness, brightness), (sx, sy), 1)

        # 月亮
        pygame.draw.circle(surface, (240, 230, 180), (wx + 240, wy + 50), 30)
        pygame.draw.circle(surface, (15, 20, 40), (wx + 250, wy + 45), 28)

        # 窗格
        pygame.draw.line(surface, (80, 65, 45), (wx + ww // 2, wy), (wx + ww // 2, wy + wh), 4)
        pygame.draw.line(surface, (80, 65, 45), (wx, wy + wh // 2), (wx + ww, wy + wh // 2), 4)
        # 窗框
        pygame.draw.rect(surface, (80, 65, 45), (wx, wy, ww, wh), 4, border_radius=2)

    def _draw_string_lights(self, surface: pygame.Surface):
        """绘制串灯"""
        light_positions = [
            (100, 55), (200, 58), (300, 52), (400, 57), (500, 54),
            (600, 56), (700, 53), (800, 58), (900, 55), (1000, 52),
            (1100, 57), (1200, 54),
        ]
        # 电线
        prev = light_positions[0]
        for lx, ly in light_positions[1:]:
            pygame.draw.line(surface, (60, 45, 30), prev, (lx, ly + 6), 1)
            prev = (lx, ly + 6)

        # 灯泡
        colors = [(255, 100, 100), (255, 220, 100), (100, 220, 255), (200, 100, 255), (255, 180, 100)]
        for i, (lx, ly) in enumerate(light_positions):
            c = colors[i % len(colors)]
            pygame.draw.circle(surface, c, (lx, ly), 6)
            pygame.draw.circle(surface, (255, 255, 220), (lx, ly), 3)

    def _draw_posters(self, surface: pygame.Surface):
        """绘制海报"""
        # 左墙海报 1
        pygame.draw.rect(surface, (30, 30, 60), (30, 80, 80, 110))
        pygame.draw.rect(surface, (220, 200, 50), (35, 85, 70, 50))
        pygame.draw.rect(surface, (200, 50, 50), (35, 145, 70, 40))
        pygame.draw.rect(surface, (255, 255, 255), (30, 80, 80, 110), 2)

        # 左墙海报 2
        pygame.draw.rect(surface, (60, 20, 20), (140, 120, 70, 90))
        pygame.draw.rect(surface, (220, 170, 50), (145, 125, 60, 40))
        pygame.draw.rect(surface, (255, 255, 255), (140, 120, 70, 90), 2)

        # 中间海报（左侧墙上）
        pygame.draw.rect(surface, (40, 80, 40), (500, 100, 60, 80))
        pygame.draw.rect(surface, (200, 220, 200), (505, 105, 50, 30))
        pygame.draw.rect(surface, (255, 255, 255), (500, 100, 60, 80), 2)

        # 右墙上小贴纸
        pygame.draw.rect(surface, (255, 100, 100), (1250, 100, 25, 30))
        pygame.draw.rect(surface, (100, 200, 255), (1230, 140, 20, 25))
        pygame.draw.rect(surface, (255, 220, 100), (1255, 170, 18, 22))

    def _draw_closet(self, surface: pygame.Surface):
        """绘制衣柜（右墙上）"""
        cx, cy, cw, ch = 1190, 220, 80, 280
        # 柜体
        pygame.draw.rect(surface, (90, 70, 50), (cx, cy, cw, ch))
        # 门缝
        pygame.draw.line(surface, (70, 55, 38), (cx + cw // 2, cy + 10), (cx + cw // 2, cy + ch - 10), 2)
        # 把手
        pygame.draw.circle(surface, (160, 130, 90), (cx + cw // 2 - 12, cy + ch // 2), 4)
        pygame.draw.circle(surface, (160, 130, 90), (cx + cw // 2 + 12, cy + ch // 2), 4)
        # 顶部装饰
        pygame.draw.line(surface, (110, 85, 60), (cx - 3, cy), (cx + cw + 3, cy), 4)
        pygame.draw.line(surface, (70, 55, 38), (cx, cy), (cx, cy + ch), 3)

    def _draw_floor(self, surface: pygame.Surface):
        """绘制木地板"""
        ground_rect = (0, self.ground_y, self.width, self.height - self.ground_y)
        pygame.draw.rect(surface, self.floor_color, ground_rect)

        # 木地板纹理（横向板条）
        for y in range(self.ground_y, self.height, 20):
            offset = ((y - self.ground_y) // 20) % 2
            for x in range(-offset * 80, self.width, 160):
                pygame.draw.rect(surface, self.floor_dark, (x, y, 155, 18), 1)

        # 地面高光线（踢脚线处）
        pygame.draw.line(surface, (130, 100, 65), (0, self.ground_y), (self.width, self.ground_y), 3)

    def _draw_bed_frame(self, surface: pygame.Surface, bed: dict):
        """绘制一张床架（上铺和下铺）"""
        x = bed["x"]
        w = bed["w"]

        # 木框颜色
        frame_color = (130, 95, 60)
        frame_dark = (100, 72, 42)
        frame_light = (160, 118, 72)
        mattress_color = (180, 160, 120)
        mattress_dark = (140, 120, 85)
        pillow_color = (240, 235, 220)
        blanket_blue = (80, 110, 160)
        blanket_red = (160, 70, 70)

        def draw_single_bed(y_top, frame_bottom, legs_top, is_upper: bool, blanket_color):
            """绘制单层床"""
            bed_h = frame_bottom - y_top
            # 床架侧边框（左边）
            pygame.draw.rect(surface, frame_dark, (x - 4, y_top, 6, bed_h + 4))
            pygame.draw.rect(surface, frame_color, (x - 4, y_top, 4, bed_h + 4))
            # 床架侧边框（右边）
            pygame.draw.rect(surface, frame_dark, (x + w, y_top, 6, bed_h + 4))
            pygame.draw.rect(surface, frame_color, (x + w, y_top, 4, bed_h + 4))

            # 床垫（浅色矩形，比框略窄）
            mx = x + 3
            mw = w - 6
            pygame.draw.rect(surface, mattress_dark, (mx, y_top, mw, bed_h))
            pygame.draw.rect(surface, mattress_color, (mx + 2, y_top + 2, mw - 4, bed_h - 4))

            # 床单（被褥）
            blanket_h = min(bed_h - 8, 40)
            pygame.draw.rect(surface, blanket_color, (mx + 4, y_top + bed_h - blanket_h, mw - 8, blanket_h - 4))
            # 被子压线
            for by in range(y_top + bed_h - blanket_h + 6, y_top + bed_h - 4, 6):
                pygame.draw.line(surface, (100, 85, 65), (mx + 6, by), (mx + mw - 6, by), 1)

            # 枕头
            pillow_h = min(12, bed_h - 6)
            pygame.draw.rect(surface, pillow_color, (mx + 6, y_top + 4, 36, pillow_h))
            pygame.draw.rect(surface, (220, 215, 200), (mx + 8, y_top + 6, 14, pillow_h - 4))

            # 床腿（两根）
            leg_h = legs_top - y_top
            if leg_h > 0:
                # 左腿
                pygame.draw.rect(surface, frame_dark, (x - 2, legs_top, 6, leg_h))
                pygame.draw.rect(surface, frame_color, (x - 2, legs_top, 4, leg_h))
                # 右腿
                pygame.draw.rect(surface, frame_dark, (x + w - 4, legs_top, 6, leg_h))
                pygame.draw.rect(surface, frame_color, (x + w - 4, legs_top, 4, leg_h))
                # 横撑
                if leg_h > 40:
                    mid_y = legs_top + leg_h // 2
                    pygame.draw.line(surface, frame_dark, (x - 2, mid_y), (x + w + 2, mid_y), 3)

        # 下铺
        draw_single_bed(
            bed["y_lower"], bed["lower_frame_bottom"], bed["lower_legs_top"],
            False, blanket_blue
        )

        # 上铺（如果上下铺y相同则为单层床，跳过上铺）
        if bed["y_upper"] != bed["y_lower"]:
            draw_single_bed(
                bed["y_upper"], bed["upper_frame_bottom"], bed["upper_legs_top"],
                True, blanket_red
            )

    def draw_ground(self, surface: pygame.Surface):
        """绘制地面（使用缓存）"""
        self._ensure_cache()
        if self._ground_cache:
            surface.blit(self._ground_cache, (0, 0))

    def draw_platforms(self, surface: pygame.Surface):
        """绘制平台表面（床面高亮线，表示可站立）"""
        # 绘制站立面的高亮，表示可以跳上去
        for px, py, pw, ph in self.platforms:
            # 站立面边缘高亮
            pygame.draw.line(surface, (200, 160, 100), (px, py), (px + pw, py), 3)
            # 半透明站立区
            s = pygame.Surface((pw, 6), pygame.SRCALPHA)
            s.fill((160, 130, 80, 60))
            surface.blit(s, (px, py))

    def draw(self, surface: pygame.Surface):
        """绘制场景"""
        self.draw_background(surface)
        self.draw_ground(surface)
        # 按Y排序绘制床（从远到近）
        sorted_beds = sorted(self.beds, key=lambda b: min(b["y_lower"], b["y_upper"]))
        for bed in sorted_beds:
            self._draw_bed_frame(surface, bed)
        self.draw_platforms(surface)
