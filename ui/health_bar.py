# 血条UI组件

import math
import pygame
from typing import Tuple

class HealthBar:
    """血条组件"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 is_player1: bool = True,
                 character_color: Tuple[int, int, int] = (50, 200, 80),
                 secondary_color: Tuple[int, int, int] = (220, 180, 30)):
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

        # 角色颜色（用于渐变效果）
        self.character_color = character_color
        self.secondary_color = secondary_color

        # 颜色
        self.bg_color = (40, 40, 50)
        self.health_high = character_color  # 使用角色主色
        self.health_med = secondary_color   # 使用角色次色
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


class SkillBar:
    """双技能槽UI - 华丽版"""

    def __init__(self, x: int, y: int, is_player1: bool = True,
                 skill1_color: Tuple[int, int, int] = (255, 100, 100),
                 skill2_color: Tuple[int, int, int] = (100, 200, 255)):
        self.x = x
        self.y = y
        self.is_player1 = is_player1
        self.skill1_color = skill1_color
        self.skill2_color = skill2_color

        # 技能槽尺寸
        self.slot_width = 50
        self.slot_height = 50
        self.slot_spacing = 8

        # 能量
        self.skill1_energy = 0
        self.skill2_energy = 0
        self.max_energy = 100

        # 动画
        self.slot1_glow = 0.0
        self.slot2_glow = 0.0
        self.pulse_time = 0.0

        # 冷却/充能动画
        self.skill1_cooling = False
        self.skill2_cooling = False
        self.cooldown_timer = 0.0

    def set_energy(self, skill1: int, skill2: int):
        """设置两个技能的能量"""
        self.skill1_energy = max(0, min(skill1, self.max_energy))
        self.skill2_energy = max(0, min(skill2, self.max_energy))

    def trigger_cooldown(self, skill_index: int, duration: float):
        """触发技能冷却"""
        if skill_index == 0:
            self.skill1_cooling = True
            self.skill1_energy = 0
        else:
            self.skill2_cooling = True
            self.skill2_energy = 0
        self.cooldown_timer = duration

    def update(self, dt: float):
        """更新动画"""
        self.pulse_time += dt

        # 更新发光效果
        if self.skill1_energy >= self.max_energy:
            self.slot1_glow = 0.5 + 0.5 * abs(math.sin(self.pulse_time * 4))
        else:
            self.slot1_glow = 0.0

        if self.skill2_energy >= self.max_energy:
            self.slot2_glow = 0.5 + 0.5 * abs(math.sin(self.pulse_time * 4 + math.pi))
        else:
            self.slot2_glow = 0.0

        # 更新冷却
        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0:
                self.skill1_cooling = False
                self.skill2_cooling = False

    def draw(self, surface: pygame.Surface, skill1_name: str = "必杀1", skill2_name: str = "必杀2"):
        """绘制技能槽"""

        # 计算位置
        if self.is_player1:
            x1 = self.x
            x2 = self.x + self.slot_width + self.slot_spacing
        else:
            x1 = self.x - self.slot_width - self.slot_spacing
            x2 = self.x

        # 绘制技能1
        self._draw_skill_slot(surface, x1, self.y, self.slot_width, self.slot_height,
                             self.skill1_energy, self.skill1_color, self.slot1_glow,
                             skill1_name, "1", self.skill1_cooling, self.cooldown_timer)

        # 绘制技能2
        self._draw_skill_slot(surface, x2, self.y, self.slot_width, self.slot_height,
                             self.skill2_energy, self.skill2_color, self.slot2_glow,
                             skill2_name, "2", self.skill2_cooling, self.cooldown_timer)

    def _draw_skill_slot(self, surface: pygame.Surface, x: int, y: int, w: int, h: int,
                        energy: int, base_color: Tuple[int, int, int], glow: float,
                        name: str, key: str, cooling: bool, cooldown_time: float):
        """绘制单个技能槽"""

        # 外发光效果
        if glow > 0:
            glow_radius = int(10 * glow)
            glow_surface = pygame.Surface((w + glow_radius * 2, h + glow_radius * 2), pygame.SRCALPHA)
            glow_color = (*base_color, int(100 * glow))
            pygame.draw.rect(glow_surface, glow_color,
                            (glow_radius - 2, glow_radius - 2, w + 4, h + 4),
                            border_radius=8)
            surface.blit(glow_surface, (x - glow_radius, y - glow_radius))

        # 背景框
        bg_color = (30, 30, 40) if not cooling else (50, 30, 30)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=6)

        # 能量填充
        energy_ratio = energy / self.max_energy
        fill_height = int(h * energy_ratio)

        if fill_height > 0:
            # 渐变色填充
            for i in range(fill_height):
                ratio = i / h
                r = int(base_color[0] * (1 - ratio * 0.3))
                g = int(base_color[1] * (1 - ratio * 0.3))
                b = int(base_color[2] * (1 - ratio * 0.3))
                pygame.draw.line(surface, (r, g, b), (x + 2, y + h - i - 1), (x + w - 2, y + h - i - 1))

        # 冷却遮罩
        if cooling and cooldown_time > 0:
            cooldown_ratio = cooldown_time / 2.0  # 假设2秒冷却
            cover_height = int(h * cooldown_ratio)
            cover = pygame.Surface((w, cover_height), pygame.SRCALPHA)
            cover.fill((0, 0, 0, 180))
            surface.blit(cover, (x, y))

        # 边框 - 就绪时发光
        if energy >= self.max_energy and not cooling:
            border_color = base_color
            # 闪烁效果
            pulse = abs(math.sin(self.pulse_time * 6))
            border_width = 2 + int(pulse * 2)
        else:
            border_color = (80, 80, 100)
            border_width = 2

        pygame.draw.rect(surface, border_color, (x, y, w, h), border_width, border_radius=6)

        # 技能图标区域
        icon_size = 20
        icon_x = x + (w - icon_size) // 2
        icon_y = y + 8

        # 绘制简单图标形状
        if "爱国" in name or "护盾" in name:
            # 盾牌形状
            points = [(icon_x + icon_size//2, icon_y),
                     (icon_x + icon_size - 2, icon_y + 4),
                     (icon_x + icon_size - 2, icon_y + icon_size - 6),
                     (icon_x + icon_size//2, icon_y + icon_size - 2),
                     (icon_x + 2, icon_y + icon_size - 6),
                     (icon_x + 2, icon_y + 4)]
            pygame.draw.polygon(surface, base_color, points)
        elif "实验室" in name:
            # 魔法球形状
            pygame.draw.circle(surface, base_color, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2 - 2)
            pygame.draw.circle(surface, (255, 255, 255), (icon_x + icon_size//2 - 3, icon_y + icon_size//2 - 3), 4)
        elif "叛国" in name:
            # 匕首形状
            pygame.draw.line(surface, base_color,
                           (icon_x + 4, icon_y + icon_size - 4),
                           (icon_x + icon_size - 4, icon_y + 4), 3)
            pygame.draw.circle(surface, base_color, (icon_x + icon_size - 4, icon_y + 4), 4)
        elif "雕" in name:
            # 羽毛形状
            points = [(icon_x + icon_size//2, icon_y),
                     (icon_x + icon_size - 4, icon_y + icon_size),
                     (icon_x + icon_size//2, icon_y + icon_size - 6),
                     (icon_x + 4, icon_y + icon_size)]
            pygame.draw.polygon(surface, base_color, points)
        else:
            # 默认星星
            pygame.draw.circle(surface, base_color, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2 - 2)

        # 按键提示
        font_size = 14
        font = pygame.font.SysFont("arial", font_size, bold=True)
        key_text = font.render(key, True, (255, 255, 255))
        key_rect = key_text.get_rect(center=(x + w - 10, y + h - 10))
        surface.blit(key_text, key_rect)

        # 就绪状态 "RDY" 文字
        if energy >= self.max_energy and not cooling:
            ready_font = pygame.font.SysFont("arial", 10, bold=True)
            ready_text = ready_font.render("RDY", True, (255, 255, 0))
            ready_rect = ready_text.get_rect(center=(x + w//2, y + h - 8))
            surface.blit(ready_text, ready_rect)
