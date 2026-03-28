# 血条UI组件

import pygame
from typing import Tuple

class HealthBar:
    """血条组件"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 is_player1: bool = True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_player1 = is_player1

        # 血量值
        self.current_health = 1000
        self.max_health = 1000
        self.display_health = 1000  # 平滑显示
        self.smooth_speed = 8.0

        # 颜色
        self.bg_color = (40, 40, 50)
        self.health_high = (50, 200, 80)
        self.health_med = (220, 180, 30)
        self.health_low = (200, 30, 30)
        self.border_color = (80, 80, 100)

        # 字体
        self.font = None
        self._init_font()

    def _init_font(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.font = pygame.font.SysFont(font_name, 24, bold=True)
                return
            except:
                continue
        self.font = pygame.font.Font(None, 24)

    def set_health(self, health: int):
        """设置血量"""
        self.current_health = max(0, min(health, self.max_health))

    def update(self, dt: float):
        """更新血条显示（平滑过渡）"""
        if self.display_health > self.current_health:
            # 血量下降
            self.display_health -= self.smooth_speed * dt * 100
            if self.display_health < self.current_health:
                self.display_health = self.current_health
        elif self.display_health < self.current_health:
            # 血量恢复
            self.display_health += self.smooth_speed * dt * 100
            if self.display_health > self.current_health:
                self.display_health = self.current_health

    def get_health_color(self) -> Tuple[int, int, int]:
        """根据血量获取颜色"""
        ratio = self.display_health / self.max_health
        if ratio > 0.5:
            return self.health_high
        elif ratio > 0.25:
            return self.health_med
        else:
            return self.health_low

    def draw(self, surface: pygame.Surface):
        """绘制血条"""
        # 背景
        pygame.draw.rect(surface, self.bg_color,
                        (self.x, self.y, self.width, self.height))

        # 血量条
        health_ratio = self.display_health / self.max_health
        health_width = int(self.width * health_ratio)

        if health_width > 0:
            # 根据血量选择颜色
            health_color = self.get_health_color()

            if self.is_player1:
                pygame.draw.rect(surface, health_color,
                               (self.x, self.y, health_width, self.height))
            else:
                # P2血条从右向左
                pygame.draw.rect(surface, health_color,
                               (self.x + self.width - health_width, self.y,
                                health_width, self.height))

            # 高光效果
            highlight_height = max(2, self.height // 4)
            highlight_color = tuple(min(255, c + 40) for c in health_color)
            if self.is_player1:
                pygame.draw.rect(surface, highlight_color,
                               (self.x, self.y, health_width, highlight_height))
            else:
                pygame.draw.rect(surface, highlight_color,
                               (self.x + self.width - health_width, self.y,
                                health_width, highlight_height))

        # 边框
        pygame.draw.rect(surface, self.border_color,
                        (self.x, self.y, self.width, self.height), 2)

    def draw_name(self, surface: pygame.Surface, name: str, font: pygame.font.Font = None):
        """绘制角色名"""
        if font is None:
            font = self.font
        if self.is_player1:
            text = font.render(name, True, (255, 255, 255))
            surface.blit(text, (self.x, self.y - 25))
        else:
            text = font.render(name, True, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.right = self.x + self.width
            surface.blit(text, (text_rect.right - text.get_width(), self.y - 25))


class SpecialBar:
    """必杀技能量槽"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 is_player1: bool = True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_player1 = is_player1

        self.current_energy = 0
        self.max_energy = 100

        self.bg_color = (50, 50, 60)
        self.energy_color = (100, 200, 255)
        self.energy_ready_color = (255, 220, 50)
        self.border_color = (80, 80, 100)

    def set_energy(self, energy: int):
        """设置能量"""
        self.current_energy = max(0, min(energy, self.max_energy))

    def update(self, dt: float):
        """更新能量槽"""
        pass

    def draw(self, surface: pygame.Surface):
        """绘制能量槽"""
        # 背景
        pygame.draw.rect(surface, self.bg_color,
                        (self.x, self.y, self.width, self.height))

        # 能量条
        energy_ratio = self.current_energy / self.max_energy
        energy_width = int(self.width * energy_ratio)

        if energy_width > 0:
            # 判断是否满能量（可以使用必杀技）
            if energy_ratio >= 1.0:
                energy_color = self.energy_ready_color
            else:
                energy_color = self.energy_color

            if self.is_player1:
                pygame.draw.rect(surface, energy_color,
                               (self.x, self.y, energy_width, self.height))
            else:
                pygame.draw.rect(surface, energy_color,
                               (self.x + self.width - energy_width, self.y,
                                energy_width, self.height))

        # 边框
        pygame.draw.rect(surface, self.border_color,
                        (self.x, self.y, self.width, self.height), 1)


class ComboDisplay:
    """连击显示"""

    def __init__(self):
        self.combo_count = 0
        self.timer = 0.0
        self.font = None
        self._init_font()

    def _init_font(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.font = pygame.font.SysFont(font_name, 36, bold=True)
                return
            except:
                continue
        self.font = pygame.font.Font(None, 36)

    def set_combo(self, count: int):
        """设置连击数"""
        if count > self.combo_count:
            self.combo_count = count
            self.timer = 2.0  # 显示2秒

    def update(self, dt: float):
        """更新显示"""
        if self.timer > 0:
            self.timer -= dt

    def draw(self, surface: pygame.Surface, x: int, y: int):
        """绘制连击数"""
        if self.timer <= 0 or self.combo_count <= 1:
            return

        # 淡出效果
        alpha = int(255 * min(1.0, self.timer))
        if alpha <= 0:
            return

        # 创建半透明表面
        combo_text = f"{self.combo_count} 连击!"
        text = self.font.render(combo_text, True, (255, 220, 50))

        # 添加阴影
        shadow = self.font.render(combo_text, True, (100, 50, 0))

        # 绘制阴影
        shadow.set_alpha(alpha)
        surface.blit(shadow, (x + 2, y + 2))

        # 绘制文字
        text.set_alpha(alpha)
        surface.blit(text, (x, y))
