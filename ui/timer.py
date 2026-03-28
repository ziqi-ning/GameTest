# 倒计时器组件

import pygame

class Timer:
    """对战倒计时器"""

    def __init__(self, x: int, y: int, max_time: int = 99):
        self.x = x
        self.y = y
        self.max_time = max_time
        self.current_time = max_time
        self.is_paused = False
        self.is_finished = False

        self.font = None
        self._init_font()

    def _init_font(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.font = pygame.font.SysFont(font_name, 48, bold=True)
                return
            except:
                continue
        self.font = pygame.font.Font(None, 48)

    def update(self, dt: float):
        """更新计时器"""
        if self.is_paused or self.is_finished:
            return

        self.current_time -= dt

        if self.current_time <= 0:
            self.current_time = 0
            self.is_finished = True

    def reset(self, time: int = None):
        """重置计时器"""
        if time is None:
            time = self.max_time
        self.current_time = time
        self.is_finished = False
        self.is_paused = False

    def pause(self):
        """暂停计时器"""
        self.is_paused = True

    def resume(self):
        """恢复计时器"""
        self.is_paused = False

    def draw(self, surface: pygame.Surface):
        """绘制计时器"""
        time_text = f"{int(self.current_time):02d}"

        # 根据时间显示不同颜色
        if self.current_time <= 10:
            color = (255, 50, 50)  # 红色警告
        elif self.current_time <= 30:
            color = (255, 200, 50)  # 黄色
        else:
            color = (255, 255, 255)  # 白色

        # 绘制文字
        text = self.font.render(time_text, True, color)

        # 绘制阴影
        shadow = self.font.render(time_text, True, (50, 50, 50))

        # 居中显示
        text_rect = text.get_rect(center=(self.x, self.y))
        shadow_rect = shadow.get_rect(center=(self.x + 2, self.y + 2))

        surface.blit(shadow, shadow_rect)
        surface.blit(text, text_rect)


class RoundDisplay:
    """回合显示"""

    def __init__(self, x: int, y: int):
        self.x = x
        self.y = y
        self.p1_wins = 0
        self.p2_wins = 0
        self.max_wins = 2  # 先赢2局

        self.font = None
        self._init_font()

    def _init_font(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.font = pygame.font.SysFont(font_name, 24)
                return
            except:
                continue
        self.font = pygame.font.Font(None, 24)

    def set_wins(self, p1: int, p2: int):
        """设置获胜数"""
        self.p1_wins = p1
        self.p2_wins = p2

    def add_win(self, player: int):
        """添加获胜"""
        if player == 1:
            self.p1_wins += 1
        else:
            self.p2_wins += 1

    def reset(self):
        """重置"""
        self.p1_wins = 0
        self.p2_wins = 0

    def draw(self, surface: pygame.Surface):
        """绘制回合指示"""
        # P1 胜利图标
        p1_x = self.x - 100
        for i in range(self.max_wins):
            color = (255, 220, 50) if i < self.p1_wins else (60, 60, 70)
            pygame.draw.circle(surface, color, (p1_x + i * 30, self.y), 10)

        # P2 胜利图标
        p2_x = self.x + 100
        for i in range(self.max_wins):
            color = (255, 220, 50) if i < self.p2_wins else (60, 60, 70)
            pygame.draw.circle(surface, color, (p2_x + i * 30, self.y), 10)


class Announcement:
    """公告显示（如 FIGHT! KO! 等）"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.text = ""
        self.timer = 0.0
        self.duration = 2.0
        self.font = None
        self._init_font()

    def _init_font(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]
        for font_name in chinese_fonts:
            try:
                self.font = pygame.font.SysFont(font_name, 72, bold=True)
                return
            except:
                continue
        self.font = pygame.font.Font(None, 72)

    def show(self, text: str, duration: float = 2.0):
        """显示公告"""
        self.text = text
        self.timer = duration
        self.duration = duration

    def update(self, dt: float):
        """更新公告"""
        if self.timer > 0:
            self.timer -= dt

    def is_active(self) -> bool:
        """检查公告是否在显示"""
        return self.timer > 0

    def draw(self, surface: pygame.Surface):
        """绘制公告"""
        if self.timer <= 0:
            return

        # 计算透明度（淡入淡出）
        fade_time = 0.3
        if self.timer > self.duration - fade_time:
            # 淡入
            alpha = int(255 * (self.duration - self.timer) / fade_time)
        elif self.timer < fade_time:
            # 淡出
            alpha = int(255 * self.timer / fade_time)
        else:
            alpha = 255

        if alpha <= 0:
            return

        # 创建表面
        text_surface = self.font.render(self.text, True, (255, 255, 255))
        text_surface.set_alpha(alpha)

        # 阴影
        shadow_surface = self.font.render(self.text, True, (50, 50, 50))
        shadow_surface.set_alpha(alpha)

        # 居中
        rect = text_surface.get_rect(center=(self.screen_width // 2, self.screen_height // 2 - 50))

        # 绘制阴影
        shadow_rect = rect.copy()
        shadow_rect.x += 4
        shadow_rect.y += 4
        surface.blit(shadow_surface, shadow_rect)

        # 绘制文字
        surface.blit(text_surface, rect)
