# -*- coding: utf-8 -*-
# 血条UI组件 - 格斗游戏风格
# 统一配色方案，角色主题色驱动，格斗游戏像素风边框
#
# 精灵来源: Streets of Fight (Luis Zuno @ansimuz)
# 许可证: Free for any use, credit appreciated

import math
import pygame
from typing import Tuple
from config import Colors


class HealthBar:
    """血条组件 - 格斗游戏风格，双层边框 + 角色主题色渐变"""

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

        # 护盾值
        self.current_shield = 0
        self.max_shield = 300
        self.display_shield = 0

        # 角色主题色
        self.character_color = character_color
        self.secondary_color = secondary_color
        self.health_high = character_color
        self.health_med = secondary_color
        self.health_low = Colors.HEALTH_LOW

        # 像素边框
        self.bg_color = Colors.HEALTH_BG
        self.shield_color = (100, 200, 255)
        self.border_dark = (20, 20, 30)
        self.border_light = Colors.UI_BORDER

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
        self.current_health = max(0, min(health, self.max_health))

    def set_shield(self, shield: int, max_shield: int = 300):
        self.current_shield = max(0, shield)
        self.max_shield = max(1, max_shield)

    def update(self, dt: float):
        """平滑过渡"""
        if self.display_health > self.current_health:
            self.display_health -= self.smooth_speed * dt * 100
            if self.display_health < self.current_health:
                self.display_health = self.current_health
        elif self.display_health < self.current_health:
            self.display_health += self.smooth_speed * dt * 100
            if self.display_health > self.current_health:
                self.display_health = self.current_health

        if self.display_shield > self.current_shield:
            self.display_shield -= self.smooth_speed * dt * 150
            if self.display_shield < self.current_shield:
                self.display_shield = self.current_shield
        elif self.display_shield < self.current_shield:
            self.display_shield += self.smooth_speed * dt * 150
            if self.display_shield > self.current_shield:
                self.display_shield = self.current_shield

    def get_health_color(self) -> Tuple[int, int, int]:
        ratio = self.display_health / self.max_health
        if ratio > 0.5:
            return self.health_high
        elif ratio > 0.25:
            return self.health_med
        else:
            return self.health_low

    def draw(self, surface: pygame.Surface):
        """绘制血条 - 格斗游戏风格"""
        # ── 双层外边框（像素深色）───────────────────────────────────
        outer_pad = 2
        pygame.draw.rect(surface, self.border_dark,
                       (self.x - outer_pad, self.y - outer_pad,
                        self.width + outer_pad * 2, self.height + outer_pad * 2),
                       border_radius=3)

        # ── 血条背景 ───────────────────────────────────────────────
        pygame.draw.rect(surface, self.bg_color,
                       (self.x, self.y, self.width, self.height))

        # ── 护盾条（血条上方）───────────────────────────────────────
        if self.display_shield > 0:
            shield_height = max(4, self.height // 5)
            shield_y = self.y - shield_height - 2
            shield_ratio = self.display_shield / self.max_shield
            shield_width = int(self.width * shield_ratio)

            if shield_width > 0:
                if self.is_player1:
                    pygame.draw.rect(surface, self.shield_color,
                                  (self.x, shield_y, shield_width, shield_height))
                    # 高光
                    pygame.draw.rect(surface, (150, 220, 255),
                                  (self.x, shield_y, shield_width, 2))
                else:
                    pygame.draw.rect(surface, self.shield_color,
                                  (self.x + self.width - shield_width, shield_y,
                                   shield_width, shield_height))
                    pygame.draw.rect(surface, (150, 220, 255),
                                  (self.x + self.width - shield_width, shield_y,
                                   shield_width, 2))

                pygame.draw.rect(surface, (80, 160, 200),
                              (self.x, shield_y, self.width, shield_height), 1)

        # ── 血量条 + 渐变效果 ───────────────────────────────────────
        health_ratio = self.display_health / self.max_health
        health_width = int(self.width * health_ratio)
        health_color = self.get_health_color()

        if health_width > 0:
            # 主血量
            if self.is_player1:
                pygame.draw.rect(surface, health_color,
                               (self.x, self.y, health_width, self.height))
            else:
                pygame.draw.rect(surface, health_color,
                               (self.x + self.width - health_width, self.y,
                                health_width, self.height))

            # 顶部高光条（角色主题色）
            highlight_height = max(2, self.height // 4)
            highlight_color = tuple(min(255, c + 50) for c in health_color)
            if self.is_player1:
                pygame.draw.rect(surface, highlight_color,
                               (self.x, self.y, health_width, highlight_height))
            else:
                pygame.draw.rect(surface, highlight_color,
                               (self.x + self.width - health_width, self.y,
                                health_width, highlight_height))

            # 低血量脉冲警告效果
            if health_ratio <= 0.25 and health_ratio > 0:
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.008)) * 0.4
                flash_color = tuple(
                    min(255, int(c + (255 - c) * pulse))
                    for c in self.health_low
                )
                flash_surf = pygame.Surface((health_width, self.height), pygame.SRCALPHA)
                flash_surf.fill((flash_color[0], flash_color[1], flash_color[2],
                                int(80 * pulse)))
                if self.is_player1:
                    surface.blit(flash_surf, (self.x, self.y))
                else:
                    surface.blit(flash_surf, (self.x + self.width - health_width, self.y))

        # ── 像素边框（格斗游戏风格）────────────────────────────────
        pygame.draw.rect(surface, self.border_light,
                        (self.x, self.y, self.width, self.height), 2, border_radius=2)
        # 内阴影
        inner_color = tuple(max(0, c - 15) for c in self.border_light)
        pygame.draw.rect(surface, inner_color,
                        (self.x + 1, self.y + 1, self.width - 2, self.height - 2), 1)

    def draw_name(self, surface: pygame.Surface, name: str, font: pygame.font.Font = None):
        """绘制角色名"""
        if font is None:
            font = self.font
        if self.is_player1:
            # 角色名 + 描边效果
            shadow = font.render(name, True, self.border_dark)
            text = font.render(name, True, (255, 255, 255))
            surface.blit(shadow, (self.x + 1, self.y - 24))
            surface.blit(shadow, (self.x - 1, self.y - 24))
            surface.blit(text, (self.x, self.y - 25))
        else:
            shadow = font.render(name, True, self.border_dark)
            text = font.render(name, True, (255, 255, 255))
            text_rect = text.get_rect()
            text_rect.right = self.x + self.width
            surface.blit(shadow, (text_rect.right - text.get_width() + 1, self.y - 24))
            surface.blit(shadow, (text_rect.right - text.get_width() - 1, self.y - 24))
            surface.blit(text, (text_rect.right - text.get_width(), self.y - 25))


class SpecialBar:
    """能量槽 - 格斗游戏风格"""

    def __init__(self, x: int, y: int, width: int, height: int,
                 is_player1: bool = True):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.is_player1 = is_player1

        self.current_energy = 0
        self.max_energy = 100

        self.bg_color = Colors.SPECIAL_BG
        self.energy_color = Colors.SPECIAL_FILLED
        self.energy_ready_color = Colors.YELLOW
        self.border_color = Colors.UI_BORDER

    def set_energy(self, energy: int):
        self.current_energy = max(0, min(energy, self.max_energy))

    def update(self, dt: float):
        pass

    def draw(self, surface: pygame.Surface):
        """绘制能量槽 - 像素边框风格"""
        # 外边框
        pygame.draw.rect(surface, Colors.DARK_GRAY,
                       (self.x - 1, self.y - 1, self.width + 2, self.height + 2),
                       border_radius=2)
        # 背景
        pygame.draw.rect(surface, self.bg_color,
                       (self.x, self.y, self.width, self.height))

        energy_ratio = self.current_energy / self.max_energy
        energy_width = int(self.width * energy_ratio)

        if energy_width > 0:
            if energy_ratio >= 1.0:
                # 满能量时脉动金色
                pulse = abs(math.sin(pygame.time.get_ticks() * 0.006))
                c = self.energy_ready_color
                energy_color = tuple(min(255, int(c[i] + (255 - c[i]) * pulse * 0.4)) for i in range(3))
            else:
                energy_color = self.energy_color

            if self.is_player1:
                pygame.draw.rect(surface, energy_color,
                               (self.x, self.y, energy_width, self.height))
            else:
                pygame.draw.rect(surface, energy_color,
                               (self.x + self.width - energy_width, self.y,
                                energy_width, self.height))

        pygame.draw.rect(surface, self.border_color,
                        (self.x, self.y, self.width, self.height), 1, border_radius=1)


class ComboDisplay:
    """连击显示 - 格斗游戏风格"""

    def __init__(self):
        self.combo_count = 0
        self.timer = 0.0
        self.font = None
        self._init_font()

    def _init_font(self):
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.font = pygame.font.SysFont(font_name, 36, bold=True)
                return
            except:
                continue
        self.font = pygame.font.Font(None, 36)

    def set_combo(self, count: int):
        if count > self.combo_count:
            self.combo_count = count
            self.timer = 2.0

    def update(self, dt: float):
        if self.timer > 0:
            self.timer -= dt

    def draw(self, surface: pygame.Surface, x: int, y: int):
        if self.timer <= 0 or self.combo_count <= 1:
            return

        alpha = int(255 * min(1.0, self.timer))
        if alpha <= 0:
            return

        combo_text = f"{self.combo_count} 连击!"
        # 连击数越大颜色越亮
        intensity = min(1.0, 0.5 + self.combo_count * 0.05)
        r = int(255 * intensity)
        g = int(220 * intensity)
        b = int(50 * intensity)
        combo_color = (r, g, b)
        text = self.font.render(combo_text, True, combo_color)
        shadow = self.font.render(combo_text, True, (0, 0, 0))

        shadow.set_alpha(alpha)
        text.set_alpha(alpha)
        surface.blit(shadow, (x + 2, y + 2))
        surface.blit(text, (x, y))


class SkillBar:
    """双技能槽UI - 格斗游戏华丽版"""

    def __init__(self, x: int, y: int, is_player1: bool = True,
                 skill1_color: Tuple[int, int, int] = (255, 100, 100),
                 skill2_color: Tuple[int, int, int] = (100, 200, 255)):
        self.x = x
        self.y = y
        self.is_player1 = is_player1
        self.skill1_color = skill1_color
        self.skill2_color = skill2_color

        self.slot_width = 50
        self.slot_height = 50
        self.slot_spacing = 8

        self.skill1_energy = 0
        self.skill2_energy = 0
        self.max_energy = 100

        self.slot1_glow = 0.0
        self.slot2_glow = 0.0
        self.pulse_time = 0.0

        self.skill1_cooling = False
        self.skill2_cooling = False
        self.cooldown_timer = 0.0

    def set_energy(self, skill1: int, skill2: int):
        self.skill1_energy = max(0, min(skill1, self.max_energy))
        self.skill2_energy = max(0, min(skill2, self.max_energy))

    def trigger_cooldown(self, skill_index: int, duration: float):
        if skill_index == 0:
            self.skill1_cooling = True
            self.skill1_energy = 0
        else:
            self.skill2_cooling = True
            self.skill2_energy = 0
        self.cooldown_timer = duration

    def update(self, dt: float):
        self.pulse_time += dt

        if self.skill1_energy >= self.max_energy:
            self.slot1_glow = 0.5 + 0.5 * abs(math.sin(self.pulse_time * 4))
        else:
            self.slot1_glow = 0.0

        if self.skill2_energy >= self.max_energy:
            self.slot2_glow = 0.5 + 0.5 * abs(math.sin(self.pulse_time * 4 + math.pi))
        else:
            self.slot2_glow = 0.0

        if self.cooldown_timer > 0:
            self.cooldown_timer -= dt
            if self.cooldown_timer <= 0:
                self.skill1_cooling = False
                self.skill2_cooling = False

    def draw(self, surface: pygame.Surface, skill1_name: str = "必杀1", skill2_name: str = "必杀2"):
        if self.is_player1:
            x1 = self.x
            x2 = self.x + self.slot_width + self.slot_spacing
        else:
            x1 = self.x - self.slot_width - self.slot_spacing
            x2 = self.x

        self._draw_skill_slot(surface, x1, self.y, self.slot_width, self.slot_height,
                             self.skill1_energy, self.skill1_color, self.slot1_glow,
                             skill1_name, "1", self.skill1_cooling, self.cooldown_timer)

        self._draw_skill_slot(surface, x2, self.y, self.slot_width, self.slot_height,
                             self.skill2_energy, self.skill2_color, self.slot2_glow,
                             skill2_name, "2", self.skill2_cooling, self.cooldown_timer)

    def _draw_skill_slot(self, surface: pygame.Surface, x: int, y: int, w: int, h: int,
                        energy: int, base_color: Tuple[int, int, int], glow: float,
                        name: str, key: str, cooling: bool, cooldown_time: float):
        # ── 外发光 ─────────────────────────────────────────────────
        if glow > 0:
            glow_radius = int(8 + 6 * glow)
            glow_surf = pygame.Surface((w + glow_radius * 2, h + glow_radius * 2), pygame.SRCALPHA)
            glow_color = (*base_color, int(80 * glow))
            pygame.draw.rect(glow_surf, glow_color,
                            (glow_radius - 2, glow_radius - 2, w + 4, h + 4),
                            border_radius=8)
            surface.blit(glow_surf, (x - glow_radius, y - glow_radius))

        # ── 背景框 ────────────────────────────────────────────────
        bg_color = (25, 25, 35) if not cooling else (50, 30, 30)
        pygame.draw.rect(surface, bg_color, (x, y, w, h), border_radius=5)

        # ── 能量填充（从下往上渐变）───────────────────────────────
        energy_ratio = energy / self.max_energy
        fill_height = int(h * energy_ratio)
        if fill_height > 0:
            for i in range(fill_height):
                ratio = i / h
                r = int(base_color[0] * (1 - ratio * 0.4))
                g = int(base_color[1] * (1 - ratio * 0.4))
                b = int(base_color[2] * (1 - ratio * 0.4))
                pygame.draw.line(surface, (r, g, b), (x + 2, y + h - i - 1), (x + w - 2, y + h - i - 1))

        # ── 冷却遮罩 ────────────────────────────────────────────
        if cooling and cooldown_time > 0:
            cover_height = int(h * (cooldown_time / 2.0))
            cover = pygame.Surface((w, cover_height), pygame.SRCALPHA)
            cover.fill((0, 0, 0, 180))
            surface.blit(cover, (x, y))

        # ── 边框（格斗游戏像素风格）───────────────────────────────
        if energy >= self.max_energy and not cooling:
            border_color = base_color
            pulse = abs(math.sin(self.pulse_time * 6))
            border_width = 2 + int(pulse * 2)
        else:
            border_color = Colors.UI_BORDER
            border_width = 2

        pygame.draw.rect(surface, border_color, (x, y, w, h), border_width, border_radius=5)
        inner = tuple(max(0, c - 20) for c in border_color)
        pygame.draw.rect(surface, inner, (x + 1, y + 1, w - 2, h - 2), 1)

        # ── 技能图标 ─────────────────────────────────────────────
        icon_size = 20
        icon_x = x + (w - icon_size) // 2
        icon_y = y + 6

        if "爱国" in name or "护盾" in name:
            # 盾牌
            pts = [(icon_x + icon_size//2, icon_y),
                   (icon_x + icon_size - 2, icon_y + 4),
                   (icon_x + icon_size - 2, icon_y + icon_size - 6),
                   (icon_x + icon_size//2, icon_y + icon_size - 2),
                   (icon_x + 2, icon_y + icon_size - 6),
                   (icon_x + 2, icon_y + 4)]
            pygame.draw.polygon(surface, base_color, pts)
        elif "实验室" in name:
            pygame.draw.circle(surface, base_color, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2 - 2)
            pygame.draw.circle(surface, (255, 255, 255), (icon_x + icon_size//2 - 3, icon_y + icon_size//2 - 3), 4)
        elif "叛国" in name:
            pygame.draw.line(surface, base_color, (icon_x + 4, icon_y + icon_size - 4), (icon_x + icon_size - 4, icon_y + 4), 3)
            pygame.draw.circle(surface, base_color, (icon_x + icon_size - 4, icon_y + 4), 4)
        elif "雕" in name or "鹰" in name:
            pts = [(icon_x + icon_size//2, icon_y),
                   (icon_x + icon_size - 4, icon_y + icon_size),
                   (icon_x + icon_size//2, icon_y + icon_size - 6),
                   (icon_x + 4, icon_y + icon_size)]
            pygame.draw.polygon(surface, base_color, pts)
        else:
            pygame.draw.circle(surface, base_color, (icon_x + icon_size//2, icon_y + icon_size//2), icon_size//2 - 2)

        # ── 按键提示 ─────────────────────────────────────────────
        font_size = 13
        font = pygame.font.SysFont("arial", font_size, bold=True)
        key_text = font.render(key, True, (255, 255, 255))
        key_rect = key_text.get_rect(center=(x + w - 10, y + h - 10))
        surface.blit(key_text, key_rect)

        # ── RDY 就绪提示 ──────────────────────────────────────────
        if energy >= self.max_energy and not cooling:
            pulse = abs(math.sin(self.pulse_time * 5))
            ready_alpha = int(200 + 55 * pulse)
            ready_font = pygame.font.SysFont("arial", 9, bold=True)
            ready_text = ready_font.render("RDY", True, (255, 220, 0))
            ready_text.set_alpha(ready_alpha)
            ready_rect = ready_text.get_rect(center=(x + w//2, y + h - 8))
            surface.blit(ready_text, ready_rect)
