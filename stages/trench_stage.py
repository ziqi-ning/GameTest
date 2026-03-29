# 战壕地图 - TrenchStage
# 双方各占一侧战壕，战壕高墙提供掩护，中间多层平台供交战

import pygame
import random
import math
from typing import Tuple, List
from stages.stage_1 import Stage


class TrenchStage(Stage):
    """战壕对战场景 - 双方战壕对垒，中间多层掩体平台"""

    def __init__(self, width: int = 1280, height: int = 720):
        super().__init__(width, height)
        self.name = "战壕对垒"
        self.description = "双方战壕对峙，借助掩体主动出击！"

        self.platforms: List[Tuple[int, int, int, int]] = []

        # ── 左侧战壕 ──────────────────────────────────────────
        # 战壕底部站立面（低于地面，形成壕沟感）
        self.platforms.append((30,  520, 220, 20))   # 左壕底
        # 战壕内部中层台阶
        self.platforms.append((30,  430, 120, 20))   # 左壕台阶
        # 战壕顶部壕沿（高墙顶端，可站立俯射）
        self.platforms.append((30,  310, 200, 20))   # 左壕沿

        # ── 右侧战壕 ──────────────────────────────────────────
        self.platforms.append((1030, 520, 220, 20))  # 右壕底
        self.platforms.append((1130, 430, 120, 20))  # 右壕台阶
        self.platforms.append((1050, 310, 200, 20))  # 右壕沿

        # ── 中间无人地带：多层掩体平台 ────────────────────────
        # 第一层（最低，接近地面）
        self.platforms.append((380,  490, 140, 20))  # 中左低掩体
        self.platforms.append((760,  490, 140, 20))  # 中右低掩体

        # 第二层（中层）
        self.platforms.append((480,  380, 120, 20))  # 中左中掩体
        self.platforms.append((680,  380, 120, 20))  # 中右中掩体

        # 第三层（高层，中央制高点）
        self.platforms.append((570,  270, 140, 20))  # 中央制高点

        # 战壕墙体数据（用于绘制，不参与碰撞）
        # 格式：(x, y, w, h, color)
        self.walls = [
            # 左战壕外墙（高墙）
            (30,  310, 20, 270, (80, 70, 55)),
            # 左战壕内墙
            (230, 380, 20, 200, (70, 62, 48)),
            # 右战壕外墙
            (1230, 310, 20, 270, (80, 70, 55)),
            # 右战壕内墙
            (1030, 380, 20, 200, (70, 62, 48)),
        ]

        # 铁丝网装饰位置
        self.barbed_wire = [
            (240, 375),   # 左壕内墙顶
            (1030, 375),  # 右壕内墙顶
        ]

        # 弹坑装饰
        random.seed(42)
        self.craters = []
        for _ in range(6):
            cx = random.randint(300, 980)
            cy = random.randint(540, 570)
            cr = random.randint(18, 35)
            self.craters.append((cx, cy, cr))

        # 背景烟雾粒子
        self.smoke_particles = []
        random.seed(55)
        for _ in range(8):
            self.smoke_particles.append({
                'x': random.randint(200, 1080),
                'y': random.randint(300, 500),
                'r': random.randint(20, 50),
                'alpha': random.randint(30, 80),
                'phase': random.uniform(0, math.pi * 2),
            })

    def draw_background(self, surface: pygame.Surface):
        """绘制战壕背景"""
        self._draw_sky(surface)
        self._draw_ground(surface)
        self._draw_craters(surface)
        self._draw_trench_walls(surface)
        self._draw_smoke(surface)
        self._draw_barbed_wire(surface)
        self.draw_platforms(surface)

    def _draw_sky(self, surface: pygame.Surface):
        """阴沉战场天空"""
        for y in range(self.height):
            ratio = y / self.height
            # 灰黄色战场天空
            r = int(80 + ratio * 60)
            g = int(70 + ratio * 50)
            b = int(50 + ratio * 30)
            pygame.draw.line(surface, (r, g, b), (0, y), (self.width, y))

        # 远处爆炸光晕（背景装饰）
        for pos, color in [((200, 200), (180, 120, 40)), ((1050, 180), (160, 100, 30))]:
            glow = pygame.Surface((120, 80), pygame.SRCALPHA)
            pygame.draw.ellipse(glow, (*color, 40), (0, 0, 120, 80))
            surface.blit(glow, (pos[0] - 60, pos[1] - 40))

    def _draw_ground(self, surface: pygame.Surface):
        """绘制泥土地面"""
        ground_y = self.ground_y
        # 主地面
        pygame.draw.rect(surface, (85, 68, 45), (0, ground_y, self.width, self.height - ground_y))
        # 地面纹理线
        for i in range(0, self.width, 40):
            shade = random.randint(-8, 8)
            c = max(0, min(255, 85 + shade))
            pygame.draw.line(surface, (c, c - 15, c - 35),
                             (i, ground_y), (i + 20, ground_y + 5), 2)

        # 左右战壕坑（地面下陷区域）
        # 左壕坑
        pygame.draw.rect(surface, (60, 48, 30), (30, 520, 220, 60))
        pygame.draw.rect(surface, (50, 40, 25), (30, 540, 220, 40))
        # 右壕坑
        pygame.draw.rect(surface, (60, 48, 30), (1030, 520, 220, 60))
        pygame.draw.rect(surface, (50, 40, 25), (1030, 540, 220, 40))

    def _draw_craters(self, surface: pygame.Surface):
        """绘制弹坑"""
        for cx, cy, cr in self.craters:
            # 弹坑阴影
            pygame.draw.ellipse(surface, (45, 35, 20),
                                (cx - cr, cy - cr // 2, cr * 2, cr))
            # 弹坑内部
            pygame.draw.ellipse(surface, (55, 43, 28),
                                (cx - cr + 4, cy - cr // 2 + 2, cr * 2 - 8, cr - 4))

    def _draw_trench_walls(self, surface: pygame.Surface):
        """绘制战壕墙体"""
        # 左战壕结构
        # 外墙（高墙主体）
        pygame.draw.rect(surface, (75, 62, 45), (30, 310, 200, 270))
        # 外墙顶部（壕沿加固）
        pygame.draw.rect(surface, (95, 80, 58), (30, 305, 200, 15))
        # 外墙纹理（沙袋感）
        for row in range(5):
            for col in range(4):
                bx = 35 + col * 48
                by = 320 + row * 50
                pygame.draw.rect(surface, (88, 72, 52), (bx, by, 44, 22), border_radius=4)
                pygame.draw.rect(surface, (65, 53, 38), (bx, by, 44, 22), 1, border_radius=4)

        # 左壕内墙
        pygame.draw.rect(surface, (68, 55, 40), (230, 380, 20, 200))
        pygame.draw.rect(surface, (85, 70, 50), (230, 375, 20, 12))

        # 右战壕结构（镜像）
        pygame.draw.rect(surface, (75, 62, 45), (1050, 310, 200, 270))
        pygame.draw.rect(surface, (95, 80, 58), (1050, 305, 200, 15))
        for row in range(5):
            for col in range(4):
                bx = 1055 + col * 48
                by = 320 + row * 50
                pygame.draw.rect(surface, (88, 72, 52), (bx, by, 44, 22), border_radius=4)
                pygame.draw.rect(surface, (65, 53, 38), (bx, by, 44, 22), 1, border_radius=4)

        # 右壕内墙
        pygame.draw.rect(surface, (68, 55, 40), (1030, 380, 20, 200))
        pygame.draw.rect(surface, (85, 70, 50), (1030, 375, 20, 12))

        # 中间掩体木箱
        boxes = [(380, 470), (760, 470), (480, 360), (680, 360), (570, 250)]
        for bx, by in boxes:
            # 木箱主体
            pygame.draw.rect(surface, (110, 85, 55), (bx, by, 140, 30), border_radius=3)
            pygame.draw.rect(surface, (90, 68, 42), (bx, by, 140, 30), 2, border_radius=3)
            # 木箱纹理
            pygame.draw.line(surface, (90, 68, 42), (bx + 46, by), (bx + 46, by + 30), 1)
            pygame.draw.line(surface, (90, 68, 42), (bx + 93, by), (bx + 93, by + 30), 1)
            pygame.draw.line(surface, (90, 68, 42), (bx, by + 15), (bx + 140, by + 15), 1)

    def _draw_smoke(self, surface: pygame.Surface):
        """绘制战场烟雾"""
        t = pygame.time.get_ticks() / 1000.0
        for p in self.smoke_particles:
            drift = math.sin(t * 0.3 + p['phase']) * 15
            smoke = pygame.Surface((p['r'] * 2, p['r'] * 2), pygame.SRCALPHA)
            pygame.draw.circle(smoke, (180, 170, 150, p['alpha']),
                               (p['r'], p['r']), p['r'])
            surface.blit(smoke, (int(p['x'] + drift) - p['r'], p['y'] - p['r']))

    def _draw_barbed_wire(self, surface: pygame.Surface):
        """绘制铁丝网"""
        for wx, wy in self.barbed_wire:
            # 铁丝主线
            pygame.draw.line(surface, (100, 100, 90), (wx, wy), (wx + 60, wy), 2)
            # 刺
            for i in range(0, 60, 8):
                pygame.draw.line(surface, (120, 115, 100),
                                 (wx + i, wy), (wx + i + 4, wy - 5), 1)
                pygame.draw.line(surface, (120, 115, 100),
                                 (wx + i, wy), (wx + i - 4, wy - 5), 1)

    def draw_platforms(self, surface: pygame.Surface):
        """绘制平台（战壕顶面和掩体顶面）"""
        # 战壕顶面用泥土色，掩体顶面用木箱色
        trench_platforms = [
            (30, 520, 220), (30, 430, 120), (30, 310, 200),
            (1030, 520, 220), (1130, 430, 120), (1050, 310, 200),
        ]
        box_platforms = [
            (380, 490, 140), (760, 490, 140),
            (480, 380, 120), (680, 380, 120),
            (570, 270, 140),
        ]
        for px, py, pw in trench_platforms:
            pygame.draw.rect(surface, (95, 80, 58), (px, py, pw, 8), border_radius=2)
        for px, py, pw in box_platforms:
            pygame.draw.rect(surface, (115, 90, 58), (px, py, pw, 8), border_radius=2)
