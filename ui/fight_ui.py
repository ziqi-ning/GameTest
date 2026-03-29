# 战斗界面UI

import pygame
from typing import Optional, Tuple

class BuffDisplay:
    """Buff/Debuff 状态显示"""

    def __init__(self, x: int, y: int, is_player1: bool = True):
        self.x = x
        self.y = y
        self.is_player1 = is_player1
        self.buffs = []  # [(name, color, remaining_time, max_time, icon_type)]
        self.font = pygame.font.SysFont("arial", 12, bold=True)

        # Buff类型定义
        self.buff_defs = {
            "shield": {"name": "护盾", "color": (100, 200, 255), "icon": "shield"},
            "burn": {"name": "灼烧", "color": (255, 100, 50), "icon": "fire"},
            "slow": {"name": "减速", "color": (100, 200, 100), "icon": "slow"},
            "poison": {"name": "中毒", "color": (150, 50, 200), "icon": "poison"},
            "curse": {"name": "诅咒", "color": (200, 50, 200), "icon": "skull"},
            "stun": {"name": "眩晕", "color": (255, 255, 100), "icon": "star"},
            "burn_field": {"name": "灼烧", "color": (255, 100, 50), "icon": "fire"},
            "slow_field": {"name": "减速场", "color": (100, 200, 100), "icon": "slow"},
            "damage_up": {"name": "强化", "color": (255, 200, 100), "icon": "sword"},
            "damage_down": {"name": "弱化", "color": (100, 100, 100), "icon": "broken_sword"},
            "teleport": {"name": "瞬移", "color": (200, 100, 255), "icon": "blink"},
        }

    def add_buff(self, buff_type: str, duration: float):
        """添加Buff"""
        if buff_type in self.buff_defs:
            # 检查是否已存在
            for i, buff in enumerate(self.buffs):
                if buff[0] == buff_type:
                    # 刷新时间
                    self.buffs[i] = (buff_type, self.buff_defs[buff_type]["color"], duration, duration, self.buff_defs[buff_type]["icon"])
                    return
            # 新增
            self.buffs.append((buff_type, self.buff_defs[buff_type]["color"], duration, duration, self.buff_defs[buff_type]["icon"]))

    def remove_buff(self, buff_type: str):
        """移除Buff"""
        self.buffs = [b for b in self.buffs if b[0] != buff_type]

    def update(self, dt: float):
        """更新"""
        for buff in self.buffs[:]:
            new_remaining = buff[2] - dt
            if new_remaining <= 0:
                self.buffs.remove(buff)
            else:
                idx = self.buffs.index(buff)
                self.buffs[idx] = (buff[0], buff[1], new_remaining, buff[3], buff[4])

    def draw(self, surface: pygame.Surface):
        """绘制"""
        if not self.buffs:
            return

        slot_width = 40
        slot_height = 35
        spacing = 5

        for i, buff in enumerate(self.buffs):
            buff_type, color, remaining, max_time, icon = buff
            x = self.x + i * (slot_width + spacing)
            y = self.y

            # 背景
            bg = pygame.Surface((slot_width, slot_height), pygame.SRCALPHA)
            pygame.draw.rect(bg, (20, 20, 30, 200), (0, 0, slot_width, slot_height), border_radius=4)
            surface.blit(bg, (x, y))

            # 图标
            self._draw_icon(surface, x + 5, y + 5, 15, icon, color)

            # 进度条
            ratio = remaining / max_time if max_time > 0 else 0
            bar_height = 4
            pygame.draw.rect(surface, (50, 50, 60), (x + 2, y + slot_height - bar_height - 2, slot_width - 4, bar_height))
            pygame.draw.rect(surface, color, (x + 2, y + slot_height - bar_height - 2, int((slot_width - 4) * ratio), bar_height))

            # 名称
            name_text = self.font.render(self.buff_defs[buff_type]["name"], True, color)
            name_rect = name_text.get_rect(center=(x + slot_width // 2, y + 25))
            surface.blit(name_text, name_rect)

    def _draw_icon(self, surface: pygame.Surface, x: int, y: int, size: int, icon_type: str, color: Tuple[int, int, int]):
        """绘制Buff图标"""
        if icon_type == "fire":
            # 火焰
            points = [(x + size//2, y), (x + size, y + size//2), (x + size//2, y + size), (x, y + size//2)]
            pygame.draw.polygon(surface, color, points)
        elif icon_type == "shield":
            # 盾牌
            points = [(x + size//2, y + 2), (x + size - 2, y + 4), (x + size - 2, y + size - 4),
                     (x + size//2, y + size - 2), (x + 2, y + size - 4), (x + 2, y + 4)]
            pygame.draw.polygon(surface, color, points)
        elif icon_type == "slow":
            # 雪花
            pygame.draw.circle(surface, color, (x + size//2, y + size//2), size//2 - 2)
        elif icon_type == "poison":
            # 毒液
            points = [(x + size//4, y + size), (x + size//2, y), (x + size*3//4, y + size)]
            pygame.draw.polygon(surface, color, points)
        elif icon_type == "skull":
            # 骷髅
            pygame.draw.circle(surface, color, (x + size//2, y + size//3), size//3)
            pygame.draw.rect(surface, color, (x + size//4, y + size//2, size//2, size//3))
        elif icon_type == "star":
            # 星星
            points = [(x + size//2, y), (x + size//2 + 3, y + size//2), (x + size, y + size//2),
                     (x + size//2 + 2, y + size//2 + 2), (x + size//2 + 4, y + size), (x + size//2, y + size//2 + 3)]
            pygame.draw.polygon(surface, color, points)
        elif icon_type == "sword":
            # 剑
            pygame.draw.line(surface, color, (x + 2, y + size), (x + size - 2, y), 2)
            pygame.draw.line(surface, color, (x + 2, y + size//2), (x + size - 2, y + size//2), 2)
        elif icon_type == "broken_sword":
            # 断剑
            pygame.draw.line(surface, color, (x + 4, y + size), (x + size//2, y + size//3), 2)
            pygame.draw.line(surface, color, (x + size//2, y + size//3), (x + size - 4, y + size//4), 2)
        elif icon_type == "blink":
            # 闪电
            points = [(x + size//2, y), (x + size//4, y + size//2), (x + size//2, y + size//2),
                     (x + size//4 + 2, y + size), (x + size, y + size//3), (x + size//2 + 2, y + size//3)]
            pygame.draw.polygon(surface, color, points)
        else:
            pygame.draw.circle(surface, color, (x + size//2, y + size//2), size//2)


class FightUI:
    """战斗界面UI管理"""

    def __init__(self, screen_width: int, screen_height: int,
                 p1_color: Tuple[int, int, int] = (50, 200, 80),
                 p1_secondary: Tuple[int, int, int] = (220, 180, 30),
                 p2_color: Tuple[int, int, int] = (100, 50, 220),
                 p2_secondary: Tuple[int, int, int] = (70, 30, 180)):
        self.screen_width = screen_width
        self.screen_height = screen_height

        from ui.health_bar import HealthBar, SpecialBar, ComboDisplay, SkillBar
        from ui.timer import Timer, RoundDisplay, Announcement

        # 血条（传入角色颜色）
        self.p1_health = HealthBar(20, 20, 350, 30, is_player1=True,
                                    character_color=p1_color, secondary_color=p1_secondary)
        self.p2_health = HealthBar(screen_width - 370, 20, 350, 30, is_player1=False,
                                    character_color=p2_color, secondary_color=p2_secondary)

        # 能量槽（保留原版）
        self.p1_special = SpecialBar(20, 55, 170, 15, is_player1=True)
        self.p2_special = SpecialBar(screen_width - 190, 55, 170, 15, is_player1=False)

        # 双技能槽（华丽版）
        self.p1_skills = SkillBar(195, 52, is_player1=True,
                                  skill1_color=p1_color, skill2_color=p1_secondary)
        self.p2_skills = SkillBar(screen_width - 195, 52, is_player1=False,
                                  skill1_color=p2_color, skill2_color=p2_secondary)

        # Buff显示
        self.p1_buffs = BuffDisplay(20, 75, is_player1=True)
        self.p2_buffs = BuffDisplay(screen_width - 180, 75, is_player1=False)

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

        # 技能名称
        self.p1_skill_names = ["必杀1", "必杀2"]
        self.p2_skill_names = ["必杀1", "必杀2"]

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

    def set_skill_names(self, p1_names: list, p2_names: list):
        """设置技能名称"""
        if len(p1_names) >= 2:
            self.p1_skill_names = p1_names[:2]
        if len(p2_names) >= 2:
            self.p2_skill_names = p2_names[:2]

    def update(self, dt: float, p1_fighter=None, p2_fighter=None):
        """更新UI"""
        # 更新血条
        if p1_fighter:
            self.p1_health.set_health(p1_fighter.health)
            self.p1_health.update(dt)
            self.p1_special.set_energy(int(p1_fighter.special_energy))

            # 更新技能槽能量
            energy1 = int(p1_fighter.special_energy)
            energy2 = int(p1_fighter.special_energy * 0.8)  # 第二技能消耗较少
            self.p1_skills.set_energy(energy1, energy2)

            # 更新Buff显示（从 Fighter 的实际状态属性构建）
            self.p1_buffs.buffs = []
            if hasattr(p1_fighter, 'slow_timer') and p1_fighter.slow_timer > 0:
                self.p1_buffs.add_buff('slow', p1_fighter.slow_timer)
            if hasattr(p1_fighter, 'stun_timer') and p1_fighter.stun_timer > 0:
                self.p1_buffs.add_buff('stun', p1_fighter.stun_timer)
            if hasattr(p1_fighter, 'curse_timer') and p1_fighter.curse_timer > 0:
                self.p1_buffs.add_buff('curse', p1_fighter.curse_timer)
            if hasattr(p1_fighter, 'shield_value') and p1_fighter.shield_value > 0:
                self.p1_buffs.add_buff('shield', 999.0)

            if p1_fighter.combat.combo_count > 1:
                self.p1_combo.set_combo(p1_fighter.combat.combo_count)

        if p2_fighter:
            self.p2_health.set_health(p2_fighter.health)
            self.p2_health.update(dt)
            self.p2_special.set_energy(int(p2_fighter.special_energy))

            # 更新技能槽能量
            energy1 = int(p2_fighter.special_energy)
            energy2 = int(p2_fighter.special_energy * 0.8)
            self.p2_skills.set_energy(energy1, energy2)

            # 更新Buff显示（从 Fighter 的实际状态属性构建）
            self.p2_buffs.buffs = []
            if hasattr(p2_fighter, 'slow_timer') and p2_fighter.slow_timer > 0:
                self.p2_buffs.add_buff('slow', p2_fighter.slow_timer)
            if hasattr(p2_fighter, 'stun_timer') and p2_fighter.stun_timer > 0:
                self.p2_buffs.add_buff('stun', p2_fighter.stun_timer)
            if hasattr(p2_fighter, 'curse_timer') and p2_fighter.curse_timer > 0:
                self.p2_buffs.add_buff('curse', p2_fighter.curse_timer)
            if hasattr(p2_fighter, 'shield_value') and p2_fighter.shield_value > 0:
                self.p2_buffs.add_buff('shield', 999.0)

            if p2_fighter.combat.combo_count > 1:
                self.p2_combo.set_combo(p2_fighter.combat.combo_count)

        # 更新倒计时
        self.timer.update(dt)

        # 更新连击显示
        self.p1_combo.update(dt)
        self.p2_combo.update(dt)

        # 更新公告
        self.announcement.update(dt)

        # 更新技能槽动画
        self.p1_skills.update(dt)
        self.p2_skills.update(dt)

        # 更新Buff显示
        self.p1_buffs.update(dt)
        self.p2_buffs.update(dt)

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

        # 绘制技能槽
        self.p1_skills.draw(surface, self.p1_skill_names[0], self.p1_skill_names[1])
        self.p2_skills.draw(surface, self.p2_skill_names[0], self.p2_skill_names[1])

        # 绘制Buff
        self.p1_buffs.draw(surface)
        self.p2_buffs.draw(surface)

        # 绘制倒计时
        self.timer.draw(surface)

        # 绘制回合指示
        self.round_display.draw(surface)

        # 绘制连击
        self.p1_combo.draw(surface, 50, 120)
        self.p2_combo.draw(surface, self.screen_width - 150, 120)

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
