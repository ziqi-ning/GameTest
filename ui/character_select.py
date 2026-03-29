# 角色选择界面

import pygame
import math
from typing import Tuple, Optional
from characters import CHARACTER_LIST
from animation.sprite_loader import sprite_loader

class CharacterSelect:
    """角色选择界面"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.p1_selection = 0
        self.p2_selection = 1
        self.phase = "p1_select"  # p1_select, p2_select, confirmed
        self.confirm_timer = 0.0
        self.transition_timer = 0.0
        self.is_transitioning = False

        # 动画
        self.cursor_flash = 0.0
        self.bounce_offset = 0.0

        # 字体
        self.title_font = None
        self.name_font = None
        self.info_font = None
        self._init_fonts()

    def _init_fonts(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]

        for font_name in chinese_fonts:
            try:
                self.title_font = pygame.font.SysFont(font_name, 48, bold=True)
                self.name_font = pygame.font.SysFont(font_name, 32, bold=True)
                self.info_font = pygame.font.SysFont(font_name, 24)
                return
            except:
                continue

        self.title_font = pygame.font.Font(None, 48)
        self.name_font = pygame.font.Font(None, 32)
        self.info_font = pygame.font.Font(None, 24)

    def handle_input(self, event: pygame.event.Event) -> Optional[Tuple[int, int]]:
        """处理输入，返回选中的角色ID (p1_id, p2_id)"""
        if event.type == pygame.KEYDOWN:
            if self.phase == "p1_select":
                if event.key == pygame.K_LEFT:
                    self.p1_selection = (self.p1_selection - 1) % 4
                elif event.key == pygame.K_RIGHT:
                    self.p1_selection = (self.p1_selection + 1) % 4
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.phase = "p2_select"
                elif event.key == pygame.K_ESCAPE:
                    return None  # 返回主菜单
            elif self.phase == "p2_select":
                if event.key == pygame.K_LEFT:
                    self.p2_selection = (self.p2_selection - 1) % 4
                elif event.key == pygame.K_RIGHT:
                    self.p2_selection = (self.p2_selection + 1) % 4
                elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                    self.phase = "confirmed"
                    self.confirm_timer = 1.0
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "p1_select"
            elif self.phase == "confirmed":
                if self.confirm_timer <= 0:
                    return (self.p1_selection, self.p2_selection)
        return None

    def update(self, dt: float):
        """更新界面状态"""
        self.cursor_flash += dt * 5
        self.bounce_offset = abs(math.sin(self.cursor_flash)) * 10

        if self.phase == "confirmed":
            self.confirm_timer -= dt
            if self.confirm_timer <= 0:
                self.is_transitioning = True

    def draw(self, surface: pygame.Surface):
        """绘制角色选择界面"""
        surface.fill((15, 15, 25))

        # 标题
        if self.phase == "p1_select":
            title_text = "Player 1 - 选择角色"
        elif self.phase == "p2_select":
            title_text = "Player 2 - 选择角色"
        else:
            title_text = "确认选择"

        title = self.title_font.render(title_text, True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, 50))
        surface.blit(title, title_rect)

        # 绘制角色选择格子
        char_width = 200
        char_height = 280
        spacing = 50
        total_width = 4 * char_width + 3 * spacing
        start_x = (self.screen_width - total_width) // 2
        start_y = 120

        for i, char_info in enumerate(CHARACTER_LIST):
            x = start_x + i * (char_width + spacing)
            y = start_y

            # 选中框
            is_p1_selected = i == self.p1_selection
            is_p2_selected = i == self.p2_selection

            if is_p1_selected and self.phase in ["p1_select", "confirmed"]:
                border_color = (255, 100, 100)  # P1红色
                border_width = 4
            elif is_p2_selected and self.phase == "confirmed":
                border_color = (100, 100, 255)  # P2蓝色
                border_width = 4
            elif is_p2_selected and self.phase == "p2_select":
                border_color = (100, 100, 255)
                border_width = 4
            else:
                border_color = (50, 50, 80)
                border_width = 2

            # 背景框
            pygame.draw.rect(surface, (30, 30, 50), (x, y, char_width, char_height))
            pygame.draw.rect(surface, border_color, (x, y, char_width, char_height), border_width)

            # 角色头像（使用真实精灵）
            self._draw_character_preview(surface, x + char_width // 2, y + 100,
                                       char_info['id'], char_info['color'],
                                       is_p1_selected or is_p2_selected)

            # 角色名
            name = self.name_font.render(char_info['name'], True, (255, 255, 255))
            name_rect = name.get_rect(center=(x + char_width // 2, y + 200))
            surface.blit(name, name_rect)

            # 角色类型
            char_type = self.info_font.render(char_info['type'], True, (180, 180, 180))
            type_rect = char_type.get_rect(center=(x + char_width // 2, y + 230))
            surface.blit(char_type, type_rect)

            # P1/P2 标记
            if is_p1_selected:
                p1_mark = self.info_font.render("P1", True, (255, 100, 100))
                surface.blit(p1_mark, (x + 10, y + 10))
            if is_p2_selected:
                p2_mark = self.info_font.render("P2", True, (100, 100, 255))
                surface.blit(p2_mark, (x + char_width - 40, y + 10))

        # 角色详情面板
        self._draw_character_details(surface, CHARACTER_LIST[self.p1_selection], 100, 450, True)
        self._draw_character_details(surface, CHARACTER_LIST[self.p2_selection], self.screen_width - 350, 450, False)

        # VS 标志
        vs = self.title_font.render("VS", True, (255, 220, 50))
        vs_rect = vs.get_rect(center=(self.screen_width // 2, 520))
        surface.blit(vs, vs_rect)

        # 操作提示
        if self.phase == "p1_select":
            hint = "使用左右选择角色，Enter确认，Esc返回"
        elif self.phase == "p2_select":
            hint = "Player 2: 左右选择，Enter确认，Esc重新选择"
        else:
            hint = "准备开始对战..."

        hint_text = self.info_font.render(hint, True, (120, 120, 120))
        hint_rect = hint_text.get_rect(center=(self.screen_width // 2, self.screen_height - 30))
        surface.blit(hint_text, hint_rect)

    def _draw_character_preview(self, surface: pygame.Surface, cx: int, cy: int,
                               char_index: int, color: Tuple[int, int, int], selected: bool):
        """绘制角色预览（使用真实精灵）"""
        bounce = self.bounce_offset if selected else 0

        # 尝试加载真实精灵帧
        sprite = sprite_loader.get_sprite_frame(char_index, 'idle', 0, True)
        if sprite:
            # 翻转角色朝向（面向中心）
            sprite_flipped = pygame.transform.flip(sprite, True, False)
            # 上下弹跳效果
            draw_y = cy - sprite_flipped.get_height() // 2 + int(bounce)
            surface.blit(sprite_flipped, (cx - sprite_flipped.get_width() // 2, draw_y))
        else:
            # 降级：绘制简单几何图形
            pygame.draw.circle(surface, color, (cx, cy - 40 + bounce), 30)
            pygame.draw.circle(surface, (240, 220, 200), (cx, cy - 40 + bounce), 25)
            body_rect = (cx - 25, cy - 10 + bounce, 50, 60)
            pygame.draw.ellipse(surface, color, body_rect)
            if selected:
                angle = math.sin(self.cursor_flash) * 0.3
                pygame.draw.line(surface, color, (cx - 25, cy + bounce), (cx - 45, cy - 20 + int(20 * angle) + bounce), 10)
                pygame.draw.line(surface, color, (cx + 25, cy + bounce), (cx + 45, cy - 20 + int(-20 * angle) + bounce), 10)
            else:
                pygame.draw.line(surface, color, (cx - 25, cy + bounce), (cx - 40, cy + 30 + bounce), 10)
                pygame.draw.line(surface, color, (cx + 25, cy + bounce), (cx + 40, cy + 30 + bounce), 10)
            pygame.draw.line(surface, (50, 50, 80), (cx - 15, cy + 50 + bounce), (cx - 15, cy + 90 + bounce), 12)
            pygame.draw.line(surface, (50, 50, 80), (cx + 15, cy + 50 + bounce), (cx + 15, cy + 90 + bounce), 12)

    def _draw_character_details(self, surface: pygame.Surface, char_info: dict,
                               x: int, y: int, is_p1: bool):
        """绘制角色详细信息"""
        # 背景
        pygame.draw.rect(surface, (25, 25, 40), (x, y, 250, 150))
        pygame.draw.rect(surface, (80, 80, 100), (x, y, 250, 150), 2)

        # 玩家标记
        player_label = "P1" if is_p1 else "P2"
        color = (255, 100, 100) if is_p1 else (100, 100, 255)
        label = self.info_font.render(player_label, True, color)
        surface.blit(label, (x + 10, y + 10))

        # 角色名
        name = self.name_font.render(char_info['name'], True, (255, 255, 255))
        surface.blit(name, (x + 10, y + 40))

        # 角色类型
        char_type = self.info_font.render(char_info['type'], True, (180, 180, 180))
        surface.blit(char_type, (x + 10, y + 75))

        # 属性条
        stats = self._get_character_stats(char_info['id'])
        bar_width = 100
        bar_height = 12

        # 攻击力
        atk_label = self.info_font.render("攻击", True, (200, 200, 200))
        surface.blit(atk_label, (x + 10, y + 105))
        pygame.draw.rect(surface, (40, 40, 50), (x + 60, y + 107, bar_width, bar_height))
        pygame.draw.rect(surface, (255, 100, 100), (x + 60, y + 107, int(bar_width * stats['atk']), bar_height))

        # 防御力
        def_label = self.info_font.render("防御", True, (200, 200, 200))
        surface.blit(def_label, (x + 10, y + 125))
        pygame.draw.rect(surface, (40, 40, 50), (x + 60, y + 127, bar_width, bar_height))
        pygame.draw.rect(surface, (100, 100, 255), (x + 60, y + 127, int(bar_width * stats['def']), bar_height))

    def _get_character_stats(self, char_id: int) -> dict:
        """获取角色属性"""
        stats = {
            0: {'atk': 0.9, 'def': 0.8},  # 大力
            1: {'atk': 0.6, 'def': 0.5},  # 快手
            2: {'atk': 0.7, 'def': 0.7},  # 全能
            3: {'atk': 0.65, 'def': 0.55},  # 技巧
        }
        return stats.get(char_id, {'atk': 0.5, 'def': 0.5})
