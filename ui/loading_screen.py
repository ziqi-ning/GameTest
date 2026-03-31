# 加载界面 - 显示加载进度条

import pygame
import math


class LoadingScreen:
    """地图加载进度界面"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        # 加载进度 [0.0, 1.0]
        self.progress = 0.0
        self.target_progress = 0.0
        self._display_progress = 0.0

        # 动画状态
        self.anim_timer = 0.0
        self.phase_in = 0.0  # 淡入计时

        # 当前加载阶段描述
        self.status_text = "初始化..."
        self.map_name = ""

        # 粒子装饰
        self.particles = []
        self._init_particles()

        # 字体
        self._init_fonts()

    def _init_fonts(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.title_font = pygame.font.SysFont(font_name, 56, bold=True)
                self.status_font = pygame.font.SysFont(font_name, 24)
                self.hint_font = pygame.font.SysFont(font_name, 20)
                return
            except Exception:
                continue
        self.title_font = pygame.font.Font(None, 56)
        self.status_font = pygame.font.Font(None, 24)
        self.hint_font = pygame.font.Font(None, 20)

    def _init_particles(self):
        """初始化装饰粒子"""
        import random
        random.seed(42)
        for _ in range(30):
            self.particles.append({
                'x': random.uniform(0, self.screen_width),
                'y': random.uniform(0, self.screen_height),
                'vx': random.uniform(-15, 15),
                'vy': random.uniform(-30, -10),
                'size': random.uniform(1, 3),
                'alpha': random.uniform(40, 120),
                'phase': random.uniform(0, math.pi * 2),
            })

    def set_progress(self, value: float, status: str = ""):
        """设置加载进度 [0, 1]"""
        self.target_progress = max(0.0, min(1.0, value))
        if status:
            self.status_text = status

    def set_map_name(self, name: str):
        """设置地图名称"""
        self.map_name = name

    def update(self, dt: float):
        """更新动画"""
        self.anim_timer += dt
        self.phase_in = min(1.0, self.phase_in + dt * 2.5)

        # 平滑进度条
        self._display_progress += (self.target_progress - self._display_progress) * min(1.0, dt * 12)

        # 更新粒子
        for p in self.particles:
            p['x'] += p['vx'] * dt
            p['y'] += p['vy'] * dt
            p['phase'] += dt * 2.0

            # 环绕屏幕
            if p['x'] < 0:
                p['x'] = self.screen_width
            elif p['x'] > self.screen_width:
                p['x'] = 0
            if p['y'] < 0:
                p['y'] = self.screen_height

    def draw(self, surface: pygame.Surface):
        """绘制加载界面"""
        # 淡入透明度
        alpha = int(255 * self.phase_in)

        # 深色背景
        bg = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
        bg.fill((5, 5, 15))
        pygame.Surface.blit(surface, bg, (0, 0))

        # 绘制粒子
        for p in self.particles:
            px = p['x'] + math.sin(p['phase']) * 3
            py = p['y'] + math.cos(p['phase'] * 0.7) * 2
            a = int(p['alpha'] * self.phase_in)
            if a > 0:
                glow = pygame.Surface((int(p['size'] * 4 + 4), int(p['size'] * 4 + 4)), pygame.SRCALPHA)
                pygame.draw.circle(glow, (100, 150, 255, a // 2),
                                 (int(p['size'] * 2 + 2), int(p['size'] * 2 + 2)), int(p['size'] * 2 + 2))
                pygame.Surface.blit(surface, glow,
                                   (int(px - p['size'] * 2 - 2), int(py - p['size'] * 2 - 2)))

        # 绘制装饰圆环
        cx, cy = self.screen_width // 2, self.screen_height // 2 - 40
        ring_count = 3
        for i in range(ring_count):
            t = (self.anim_timer * 0.5 + i / ring_count) % 1.0
            radius = 80 + t * 100
            ring_alpha = int(60 * (1 - t) * self.phase_in)
            if ring_alpha > 0:
                ring_surf = pygame.Surface((radius * 2 + 10, radius * 2 + 10), pygame.SRCALPHA)
                pygame.draw.circle(ring_surf, (80, 120, 255, ring_alpha),
                                 (radius + 5, radius + 5), radius, 2)
                pygame.Surface.blit(surface, ring_surf,
                                   (int(cx - radius - 5), int(cy - radius - 5)))

        # 标题
        title = self.title_font.render("LOADING", True, (220, 220, 255))
        title.set_alpha(alpha)
        title_rect = title.get_rect(center=(cx, cy - 120))
        surface.blit(title, title_rect)

        # 地图名称
        if self.map_name:
            map_text = self.status_font.render(self.map_name, True, (180, 180, 220))
            map_text.set_alpha(alpha)
            map_rect = map_text.get_rect(center=(cx, cy - 75))
            surface.blit(map_text, map_rect)

        # 进度条背景
        bar_w = 500
        bar_h = 16
        bar_x = cx - bar_w // 2
        bar_y = cy + 20

        # 背景槽
        bar_bg = pygame.Surface((bar_w, bar_h), pygame.SRCALPHA)
        bar_bg.fill((40, 40, 60, alpha))
        pygame.draw.rect(bar_bg, (60, 60, 90, alpha), (0, 0, bar_w, bar_h), 2, border_radius=8)
        pygame.Surface.blit(surface, bar_bg, (bar_x, bar_y))

        # 进度填充
        fill_w = int(bar_w * self._display_progress)
        if fill_w > 0:
            # 渐变色进度
            for bx in range(fill_w):
                ratio = bx / bar_w
                r = int(80 + ratio * 60)
                g = int(140 + ratio * 60)
                b = int(255)
                bar_fill = pygame.Surface((1, bar_h - 4), pygame.SRCALPHA)
                bar_fill.fill((r, g, b, alpha))
                pygame.Surface.blit(surface, bar_fill, (bar_x + 2 + bx, bar_y + 2))

            # 进度条高光
            highlight = pygame.Surface((fill_w, bar_h // 3), pygame.SRCALPHA)
            highlight.fill((255, 255, 255, int(40 * alpha / 255)))
            pygame.Surface.blit(surface, highlight, (bar_x + 2, bar_y + 2))

            # 进度条边缘
            pygame.draw.rect(surface, (100, 160, 255, alpha),
                           (bar_x, bar_y, fill_w, bar_h), 1, border_radius=8)

            # 末端发光点
            glow_x = bar_x + fill_w
            glow_surf = pygame.Surface((20, bar_h + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (150, 200, 255, int(80 * alpha / 255)),
                             (10, bar_h // 2 + 5), 8)
            pygame.Surface.blit(surface, glow_surf, (glow_x - 10, bar_y - 5))

        # 百分比文字
        pct_text = self.status_font.render(
            f"{int(self._display_progress * 100)}%", True, (200, 200, 230)
        )
        pct_text.set_alpha(alpha)
        pct_rect = pct_text.get_rect(center=(cx, bar_y + bar_h + 28))
        surface.blit(pct_text, pct_rect)

        # 状态描述
        status = self.status_font.render(self.status_text, True, (140, 140, 180))
        status.set_alpha(alpha)
        status_rect = status.get_rect(center=(cx, bar_y + bar_h + 58))
        surface.blit(status, status_rect)

        # 底部提示
        hint = self.hint_font.render("正在准备战斗...", True, (100, 100, 130))
        hint.set_alpha(int(alpha * 0.6))
        hint_rect = hint.get_rect(center=(cx, self.screen_height - 50))
        surface.blit(hint, hint_rect)
