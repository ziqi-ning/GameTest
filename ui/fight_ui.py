# 战斗界面UI

import pygame
from typing import Optional, Tuple

class FightUI:
    """战斗界面UI管理"""

    def __init__(self, screen_width: int, screen_height: int,
                 p1_color: Tuple[int, int, int] = (50, 200, 80),
                 p1_secondary: Tuple[int, int, int] = (220, 180, 30),
                 p2_color: Tuple[int, int, int] = (100, 50, 220),
                 p2_secondary: Tuple[int, int, int] = (70, 30, 180)):
        self.screen_width = screen_width
        self.screen_height = screen_height

        from ui.health_bar import HealthBar, SpecialBar, ComboDisplay
        from ui.timer import Timer, RoundDisplay, Announcement

        # 血条（传入角色颜色）
        self.p1_health = HealthBar(20, 20, 400, 30, is_player1=True,
                                    character_color=p1_color, secondary_color=p1_secondary)
        self.p2_health = HealthBar(screen_width - 420, 20, 400, 30, is_player1=False,
                                    character_color=p2_color, secondary_color=p2_secondary)

        # 能量槽
        self.p1_special = SpecialBar(20, 55, 200, 15, is_player1=True)
        self.p2_special = SpecialBar(screen_width - 220, 55, 200, 15, is_player1=False)

        # 倒计时
        self.timer = Timer(screen_width // 2, 35)

        # 回合显示
        self.round_display = RoundDisplay(screen_width // 2, 65)

        # 连击显示
        self.p1_combo = ComboDisplay()
        self.p2_combo = ComboDisplay()

        # 公告
        self.announcement = Announcement(screen_width, screen_height)

        # 字体
        self.name_font = None
        self._init_fonts()

    def _init_fonts(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.name_font = pygame.font.SysFont(font_name, 24, bold=True)
                return
            except:
                continue
        self.name_font = pygame.font.Font(None, 24)

    def update(self, dt: float, p1_fighter=None, p2_fighter=None):
        """更新UI"""
        # 更新血条
        if p1_fighter:
            self.p1_health.set_health(p1_fighter.health)
            self.p1_health.update(dt)
            self.p1_special.set_energy(int(p1_fighter.special_energy))
            if p1_fighter.combat.combo_count > 1:
                self.p1_combo.set_combo(p1_fighter.combat.combo_count)

        if p2_fighter:
            self.p2_health.set_health(p2_fighter.health)
            self.p2_health.update(dt)
            self.p2_special.set_energy(int(p2_fighter.special_energy))
            if p2_fighter.combat.combo_count > 1:
                self.p2_combo.set_combo(p2_fighter.combat.combo_count)

        # 更新倒计时
        self.timer.update(dt)

        # 更新连击显示
        self.p1_combo.update(dt)
        self.p2_combo.update(dt)

        # 更新公告
        self.announcement.update(dt)

    def draw(self, surface: pygame.Surface, p1_name: str = "P1", p2_name: str = "P2"):
        """绘制UI"""
        # 绘制血条
        self.p1_health.draw(surface)
        self.p2_health.draw(surface)

        # 绘制血条名称
        self.p1_health.draw_name(surface, p1_name, self.name_font)
        self.p2_health.draw_name(surface, p2_name, self.name_font)

        # 绘制能量槽
        self.p1_special.draw(surface)
        self.p2_special.draw(surface)

        # 绘制倒计时
        self.timer.draw(surface)

        # 绘制回合指示
        self.round_display.draw(surface)

        # 绘制连击
        self.p1_combo.draw(surface, 50, 150)
        self.p2_combo.draw(surface, self.screen_width - 150, 150)

        # 绘制公告
        self.announcement.draw(surface)

    def show_announcement(self, text: str, duration: float = 2.0):
        """显示公告"""
        self.announcement.show(text, duration)

    def set_round_wins(self, p1: int, p2: int):
        """设置回合获胜数"""
        self.round_display.set_wins(p1, p2)


class VictoryScreen:
    """胜利画面"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.winner = 0  # 1 or 2
        self.timer = 0.0
        self.is_active = False

        self.title_font = None
        self.info_font = None
        self._init_fonts()

    def _init_fonts(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.title_font = pygame.font.SysFont(font_name, 72, bold=True)
                self.info_font = pygame.font.SysFont(font_name, 36)
                return
            except:
                continue
        self.title_font = pygame.font.Font(None, 72)
        self.info_font = pygame.font.Font(None, 36)

    def show(self, winner: int):
        """显示胜利画面"""
        self.winner = winner
        self.timer = 0.0
        self.is_active = True

    def update(self, dt: float):
        """更新"""
        if self.is_active:
            self.timer += dt

    def draw(self, surface: pygame.Surface, p1_name: str = "Player 1", p2_name: str = "Player 2"):
        """绘制"""
        if not self.is_active:
            return

        # 渐变背景
        alpha = min(180, int(self.timer * 100))
        overlay = pygame.Surface((self.screen_width, self.screen_height))
        overlay.fill((0, 0, 0))
        overlay.set_alpha(alpha)
        surface.blit(overlay, (0, 0))

        # 胜利文字
        if self.timer > 0.5:
            text_alpha = min(255, int((self.timer - 0.5) * 255))
            winner_name = p1_name if self.winner == 1 else p2_name
            color = (255, 100, 100) if self.winner == 1 else (100, 100, 255)

            victory_text = f"{winner_name} 胜利!"
            text = self.title_font.render(victory_text, True, color)
            text.set_alpha(text_alpha)
            text_rect = text.get_rect(center=(self.screen_width // 2, self.screen_height // 2))
            surface.blit(text, text_rect)

            # KO文字
            if self.timer > 1.0:
                ko_alpha = min(255, int((self.timer - 1.0) * 255))
                ko = self.title_font.render("K.O.", True, (255, 220, 50))
                ko.set_alpha(ko_alpha)
                ko_rect = ko.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 80))
                surface.blit(ko, ko_rect)

        # 继续提示
        if self.timer > 2.0:
            hint_alpha = min(255, int((self.timer - 2.0) * 255))
            hint = self.info_font.render("按 Enter 继续...", True, (200, 200, 200))
            hint.set_alpha(hint_alpha)
            hint_rect = hint.get_rect(center=(self.screen_width // 2, self.screen_height // 2 + 80))
            surface.blit(hint, hint_rect)

    def hide(self):
        """隐藏"""
        self.is_active = False

    def handle_input(self, event: pygame.event.Event) -> Optional[str]:
        """处理输入"""
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN or event.key == pygame.K_SPACE:
                return "continue"
            elif event.key == pygame.K_ESCAPE:
                return "quit"
        return None
