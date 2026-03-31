# 城堡天空场景 - CastleStage

import pygame
import random
import math
from typing import Tuple, List
from stages.stage_1 import Stage


class CastleStage(Stage):
    """城堡天空对战场景 - 云朵与浮空平台"""

    def __init__(self, width: int = 1280, height: int = 720):
        super().__init__(width, height)
        self.name = "天空城堡"
        self.description = "云端之上，城堡对决！"

        # 平台列表（可站立面）
        self.platforms: List[Tuple[int, int, int, int]] = []

        # --- 左城堡云台 ---
        self.platforms.append((50,  440, 200, 20))   # 左城堡下方云台
        self.platforms.append((100, 280, 150, 20))   # 左城堡高台

        # --- 左侧飘云 ---
        self.platforms.append((280, 360, 180, 20))
        self.platforms.append((320, 220, 140, 20))

        # --- 中央高层云 ---
        self.platforms.append((530, 310, 220, 20))   # 中央大云台
        self.platforms.append((580, 180, 150, 20))   # 中央最高云

        # --- 右侧飘云 ---
        self.platforms.append((820, 360, 180, 20))
        self.platforms.append((860, 220, 140, 20))

        # --- 右城堡云台 ---
        self.platforms.append((1030, 440, 200, 20))  # 右城堡下方云台
        self.platforms.append((1030, 280, 150, 20))  # 右城堡高台

        # 云朵数据（用于绘制）
        self.clouds = []
        self._generate_clouds()

        # 城堡数据
        self.left_castle_x = 0
        self.right_castle_x = width

        # 背景星星
        self.stars = []
        random.seed(77)
        for _ in range(60):
            self.stars.append((
                random.randint(0, width),
                random.randint(0, height // 2),
                random.randint(1, 3)
            ))

        # 萤火虫
        self.fireflies = []
        random.seed(88)
        for _ in range(12):
            self.fireflies.append({
                'x': random.randint(100, width - 100),
                'y': random.randint(300, 550),
                'phase': random.uniform(0, math.pi * 2),
                'speed': random.uniform(0.3, 1.0),
                'brightness': random.randint(150, 255),
            })

    def _render_bg_to_cache(self) -> pygame.Surface:
        """将城堡背景预渲染到缓存"""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        # 天空渐变
        for y in range(self.height):
            ratio = y / self.height
            if ratio < 0.4:
                t = ratio / 0.4
                r = int(20 + t * 20)
                g = int(10 + t * 30)
                b = int(50 + t * 40)
            elif ratio < 0.7:
                t = (ratio - 0.4) / 0.3
                r = int(40 + t * 160)
                g = int(40 + t * 60)
                b = int(90 - t * 20)
            else:
                t = (ratio - 0.7) / 0.3
                r = int(200 + t * 40)
                g = int(100 - t * 40)
                b = int(70 - t * 60)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y), 1)
        # 星星
        for sx, sy, sr in self.stars:
            pygame.draw.circle(surf, (200, 200, 200), (sx, sy), sr)
        # 月亮
        mx, my = 1050, 80
        for i in range(4, 0, -1):
            glow_color = (255, 240, 180)
            glow_s = pygame.Surface((60 + i * 10, 60 + i * 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (*glow_color, 30 - i * 6),
                             (30 + i * 5, 30 + i * 5), 30 + i * 5)
            surf.blit(glow_s, (mx - 30 - i * 5, my - 30 - i * 5))
        pygame.draw.circle(surf, (255, 248, 220), (mx, my), 35)
        pygame.draw.circle(surf, (230, 225, 200), (mx + 8, my - 5), 12)
        pygame.draw.circle(surf, (230, 225, 200), (mx - 5, my + 10), 8)
        pygame.draw.circle(surf, (230, 225, 200), (mx + 2, my + 5), 6)
        # 背景云
        for cloud in self.bg_clouds:
            self._draw_cloud(surf, cloud['x'], cloud['y'], cloud['scale'], alpha=40)
        # 城堡剪影
        self._draw_castle(surf, 0, left=True)
        self._draw_castle(surf, self.width, left=False)
        return surf

    def _render_ground_to_cache(self) -> pygame.Surface:
        """将城堡云海地面预渲染到缓存"""
        surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
        for y in range(self.ground_y, self.height):
            ratio = (y - self.ground_y) / (self.height - self.ground_y)
            r = int(100 - ratio * 40)
            g = int(90 - ratio * 30)
            b = int(130 - ratio * 50)
            pygame.draw.line(surf, (r, g, b), (0, y), (self.width, y), 1)
        pygame.draw.line(surf, (150, 160, 200), (0, self.ground_y), (self.width, self.ground_y), 2)
        return surf

    def _generate_clouds(self):
        """生成装饰性云朵（背景装饰，不参与碰撞）"""
        random.seed(99)
        self.bg_clouds = []
        for _ in range(15):
            cx = random.randint(0, self.width)
            cy = random.randint(50, 400)
            scale = random.uniform(0.5, 1.5)
            self.bg_clouds.append({'x': cx, 'y': cy, 'scale': scale})

    def draw_background(self, surface: pygame.Surface):
        """绘制城堡背景（使用缓存）"""
        self._ensure_cache()
        if self._bg_cache:
            surface.blit(self._bg_cache, (0, 0))
        # 萤火虫（动态，每帧更新）
        self._draw_fireflies(surface, 0)

    def _draw_sky_gradient(self, surface: pygame.Surface):
        """日落天空渐变"""
        for y in range(self.height):
            ratio = y / self.height
            if ratio < 0.4:
                # 上部：深蓝紫色夜空
                t = ratio / 0.4
                r = int(20 + t * 20)
                g = int(10 + t * 30)
                b = int(50 + t * 40)
            elif ratio < 0.7:
                # 中部：紫红晚霞
                t = (ratio - 0.4) / 0.3
                r = int(40 + t * 160)
                g = int(40 + t * 60)
                b = int(90 - t * 20)
            else:
                # 下部：橙黄暖光
                t = (ratio - 0.7) / 0.3
                r = int(200 + t * 40)
                g = int(100 - t * 40)
                b = int(70 - t * 60)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))

    def _draw_stars(self, surface: pygame.Surface):
        """绘制星星"""
        for sx, sy, sr in self.stars:
            brightness = 200 + int(math.sin(pygame.time.get_ticks() * 0.001 + sx) * 40)
            c = min(brightness, 255)
            pygame.draw.circle(surface, (c, c, min(c + 20, 255)), (sx, sy), sr)

    def _draw_moon(self, surface: pygame.Surface):
        """绘制月亮"""
        mx, my = 1050, 80
        # 光晕
        for i in range(4, 0, -1):
            alpha = 30 - i * 6
            glow_color = (255, 240, 180)
            glow_surf = pygame.Surface((60 + i * 10, 60 + i * 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color, max(alpha, 10)),
                               (30 + i * 5, 30 + i * 5), 30 + i * 5)
            surface.blit(glow_surf, (mx - 30 - i * 5, my - 30 - i * 5))
        # 月亮本体
        pygame.draw.circle(surface, (255, 248, 220), (mx, my), 35)
        pygame.draw.circle(surface, (230, 225, 200), (mx + 8, my - 5), 12)
        pygame.draw.circle(surface, (230, 225, 200), (mx - 5, my + 10), 8)
        pygame.draw.circle(surface, (230, 225, 200), (mx + 2, my + 5), 6)

    def _draw_bg_clouds(self, surface: pygame.Surface):
        """绘制背景装饰云朵"""
        for cloud in self.bg_clouds:
            self._draw_cloud(surface, cloud['x'], cloud['y'],
                           cloud['scale'], alpha=40)

    def _draw_castles(self, surface: pygame.Surface):
        """绘制城堡剪影"""
        # 左城堡
        self._draw_castle(surface, 0, left=True)
        # 右城堡
        self._draw_castle(surface, self.width, left=False)

    def _draw_castle(self, surface: pygame.Surface, base_x: int, left: bool):
        """绘制单个城堡"""
        frame_color = (15, 12, 30)
        detail_color = (25, 20, 45)

        # 城堡主体在画面外延伸进来
        if left:
            x_start = -200
        else:
            x_start = self.width - 50

        # 主塔
        self._draw_castle_tower(surface, x_start + 80, 100, 140, 500, left)
        self._draw_castle_tower(surface, x_start + 240, 200, 100, 400, left)
        self._draw_castle_tower(surface, x_start + 360, 300, 80, 300, left)

        # 连接城墙
        if left:
            pygame.draw.rect(surface, frame_color, (x_start + 160, 350, 120, 250))
            pygame.draw.rect(surface, detail_color, (x_start + 160, 340, 120, 260))
        else:
            pygame.draw.rect(surface, frame_color, (x_start + 40, 350, 120, 250))
            pygame.draw.rect(surface, detail_color, (x_start + 40, 340, 120, 260))

        # 城堡窗户（亮光）
        window_color = (255, 200, 100)
        windows = [
            (x_start + 120, 180), (x_start + 150, 180),
            (x_start + 120, 250), (x_start + 150, 250),
            (x_start + 120, 320), (x_start + 150, 320),
            (x_start + 270, 280), (x_start + 300, 280),
        ]
        for wx, wy in windows:
            pygame.draw.rect(surface, window_color, (wx, wy, 15, 20))
            # 窗户光晕
            glow = pygame.Surface((30, 34), pygame.SRCALPHA)
            glow.fill((255, 200, 100, 30))
            surface.blit(glow, (wx - 7, wy - 7))

        # 旗帜
        flag_x = x_start + 150 if left else x_start + 150
        flag_y = 100
        pole_color = (80, 60, 40)
        # 旗杆
        pygame.draw.line(surface, pole_color, (flag_x, flag_y - 50), (flag_x, flag_y + 30), 3)
        # 旗帜
        points = [(flag_x, flag_y - 45)]
        t = pygame.time.get_ticks() * 0.003
        wave = math.sin(t) * 3
        points.append((flag_x + 30 + wave, flag_y - 40))
        points.append((flag_x + 28 + math.sin(t + 1) * 3, flag_y - 25))
        points.append((flag_x, flag_y - 20))
        if len(points) == 4:
            pygame.draw.polygon(surface, (180, 50, 50), points)

    def _draw_castle_tower(self, surface: pygame.Surface, x: int, y: int, w: int, h: int, left: bool):
        """绘制城堡塔楼"""
        frame_color = (15, 12, 30)
        detail_color = (25, 20, 45)

        # 塔身
        pygame.draw.rect(surface, frame_color, (x, y, w, h))
        pygame.draw.rect(surface, detail_color, (x + 3, y + 3, w - 6, h - 6))

        # 垛口
        merlon_w = 14
        merlon_h = 20
        merlon_gap = 8
        for mx in range(x, x + w - merlon_w + 1, merlon_w + merlon_gap):
            pygame.draw.rect(surface, frame_color, (mx, y - merlon_h, merlon_w, merlon_h))
            pygame.draw.rect(surface, detail_color, (mx + 2, y - merlon_h + 2, merlon_w - 4, merlon_h - 4))

    def _draw_cloud(self, surface: pygame.Surface, cx: int, cy: int,
                    scale: float = 1.0, alpha: int = 255):
        """绘制一朵云"""
        blobs = [
            (0, 0, 40),
            (30, -10, 50),
            (60, 0, 40),
            (15, 10, 35),
            (45, 10, 35),
        ]
        for bx, by, br in blobs:
            bx = cx + bx * scale
            by = cy + by * scale
            r = int(br * scale)
            if alpha < 255:
                cloud_surf = pygame.Surface((r * 2 + 4, r * 2 + 4), pygame.SRCALPHA)
                pygame.draw.circle(cloud_surf, (220, 230, 250, alpha),
                                   (r + 2, r + 2), r)
                surface.blit(cloud_surf, (bx - r - 2, by - r - 2))
            else:
                pygame.draw.circle(surface, (220, 230, 250), (bx, by), r)

    def _draw_fireflies(self, surface: pygame.Surface, dt: float):
        """绘制萤火虫（动态）"""
        for ff in self.fireflies:
            ff['phase'] += ff['speed'] * dt * 2
            brightness = int((math.sin(ff['phase']) * 0.5 + 0.5) * ff['brightness'])
            x = ff['x'] + math.sin(ff['phase'] * 0.7) * 20
            y = ff['y'] + math.cos(ff['phase'] * 0.5) * 15
            # 光晕
            glow = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(glow, (150, 255, 100, 80), (10, 10), 8)
            surface.blit(glow, (int(x) - 10, int(y) - 10))
            pygame.draw.circle(surface, (200, 255, 150), (int(x), int(y)), 2)

    def _draw_cloud_platform(self, surface: pygame.Surface, x: int, y: int, w: int):
        """绘制云朵平台"""
        # 云朵主体
        cx = x + w // 2
        blobs = [
            (cx - w * 0.3, y + 8, 30),
            (cx - w * 0.15, y, 40),
            (cx, y - 5, 45),
            (cx + w * 0.15, y, 40),
            (cx + w * 0.3, y + 8, 30),
            (cx - w * 0.2, y + 15, 25),
            (cx + w * 0.2, y + 15, 25),
        ]
        for bx, by, br in blobs:
            pygame.draw.circle(surface, (240, 245, 255), (bx, by), br)
            pygame.draw.circle(surface, (220, 230, 250), (bx, by + 3), br - 5)

    def draw_ground(self, surface: pygame.Surface):
        """绘制地面（使用缓存 + 动态波浪）"""
        self._ensure_cache()
        if self._ground_cache:
            surface.blit(self._ground_cache, (0, 0))
        # 云海波浪（动态）
        t = pygame.time.get_ticks() * 0.001
        for i in range(3):
            wave_y = self.ground_y + 5 + i * 15
            points = []
            for x in range(0, self.width + 40, 40):
                wy = wave_y + math.sin((x + i * 100) * 0.03 + t + i) * 8
                points.append((x, wy))
            if len(points) >= 2:
                for j in range(len(points) - 1):
                    color = (200, 215, 240)
                    pygame.draw.line(surface, color, points[j], points[j + 1], 2)

    def draw_platforms(self, surface: pygame.Surface):
        """绘制平台站立面"""
        for px, py, pw, ph in self.platforms:
            self._draw_cloud_platform(surface, px, py, pw)
            # 站立高光线
            pygame.draw.line(surface, (255, 255, 255), (px + 20, py), (px + pw - 20, py), 2)

    def draw(self, surface: pygame.Surface):
        """绘制场景"""
        self.draw_background(surface)
        self.draw_ground(surface)
        self.draw_platforms(surface)
