# 主菜单界面

import pygame
import math
from typing import Optional, Callable

class Menu:
    """主菜单"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.selected_index = 0
        self.menu_items = ["普通模式", "双人模式", "调试模式", "退出"]
        self.item_height = 60

        self.title_font = None
        self.menu_font = None
        self.hint_font = None
        self._init_fonts()

        # 动画
        self.title_y = 150
        self.animation_timer = 0.0

    def _init_fonts(self):
        """初始化字体 - 使用支持中文的字体"""
        # 尝试使用支持中文的字体
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]

        for font_name in chinese_fonts:
            try:
                self.title_font = pygame.font.SysFont(font_name, 72, bold=True)
                self.menu_font = pygame.font.SysFont(font_name, 36)
                self.hint_font = pygame.font.SysFont(font_name, 24)
                print(f"Font loaded: {font_name}")
                return
            except:
                continue

        # 如果都失败，使用默认字体
        self.title_font = pygame.font.Font(None, 72)
        self.menu_font = pygame.font.Font(None, 36)
        self.hint_font = pygame.font.Font(None, 24)

    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        """处理输入，返回选中的菜单项"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
            elif event.key == pygame.K_DOWN:
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
            elif event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return self.menu_items[self.selected_index]
        return None

    def update(self, dt: float):
        """更新菜单动画"""
        self.animation_timer += dt
        self.title_y = 150 + math.sin(self.animation_timer * 2) * 5

    def draw(self, surface: pygame.Surface):
        """绘制菜单"""
        surface.fill((20, 20, 30))

        # 标题
        title = self.title_font.render("寝室风云", True, (255, 220, 50))
        title_rect = title.get_rect(center=(self.screen_width // 2, int(self.title_y)))
        surface.blit(title, title_rect)

        # 副标题
        subtitle = self.menu_font.render("DormFight", True, (200, 200, 200))
        subtitle_rect = subtitle.get_rect(center=(self.screen_width // 2, int(self.title_y) + 50))
        surface.blit(subtitle, subtitle_rect)

        # 菜单项
        start_y = 350
        for i, item in enumerate(self.menu_items):
            # 选中效果
            if i == self.selected_index:
                color = (255, 220, 50)
                # 箭头
                arrow = self.menu_font.render(">> ", True, (255, 220, 50))
                surface.blit(arrow, (self.screen_width // 2 - 100, start_y + i * self.item_height))
            else:
                color = (150, 150, 150)

            text = self.menu_font.render(item, True, color)
            text_rect = text.get_rect(center=(self.screen_width // 2 + 30, start_y + i * self.item_height))
            surface.blit(text, text_rect)

        # 操作提示
        hint = self.hint_font.render("使用上下选择，Enter确认", True, (100, 100, 100))
        hint_rect = hint.get_rect(center=(self.screen_width // 2, self.screen_height - 50))
        surface.blit(hint, hint_rect)
