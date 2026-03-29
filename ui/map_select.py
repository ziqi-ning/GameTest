# 地图选择界面

import pygame
import math
from typing import Optional
from stages.dorm_stage import DormStage
from stages.castle_stage import CastleStage
from stages.trench_stage import TrenchStage


MAPS = [
    {'name': '寝室风云', 'desc': '四人寝室，上下铺对决！', 'stage_class': DormStage,
     'bg_color': (90, 70, 55), 'accent': (200, 160, 100)},
    {'name': '天空城堡', 'desc': '云端之上，城堡对决！', 'stage_class': CastleStage,
     'bg_color': (20, 30, 60), 'accent': (100, 180, 255)},
    {'name': '战壕对垒', 'desc': '双方战壕对峙，借助掩体主动出击！', 'stage_class': TrenchStage,
     'bg_color': (60, 50, 35), 'accent': (180, 140, 60)},
]


class MapSelect:
    """地图选择界面"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height

        self.selection = 0
        self.confirm_timer = 0.0
        self.is_transitioning = False

        # 动画
        self.cursor_flash = 0.0
        self.bounce_offset = 0.0
        self.title_y = 0.0

        # 字体
        self.title_font = None
        self.name_font = None
        self.desc_font = None
        self.info_font = None
        self._init_fonts()

        # 预览缩放
        self.map_preview_scale = 0.0  # 淡入动画

    def _init_fonts(self):
        """初始化字体"""
        chinese_fonts = ["microsoftyahei", "simsun", "simhei", "sans-serif"]

        for font_name in chinese_fonts:
            try:
                self.title_font = pygame.font.SysFont(font_name, 52, bold=True)
                self.name_font = pygame.font.SysFont(font_name, 36, bold=True)
                self.desc_font = pygame.font.SysFont(font_name, 24)
                self.info_font = pygame.font.SysFont(font_name, 22)
                return
            except Exception:
                continue

        self.title_font = pygame.font.Font(None, 52)
        self.name_font = pygame.font.Font(None, 36)
        self.desc_font = pygame.font.Font(None, 24)
        self.info_font = pygame.font.Font(None, 22)

    def handle_input(self, event: pygame.event.Event) -> Optional[int]:
        """处理输入，返回选中的地图索引，None表示未选定"""
        if event.type == pygame.KEYDOWN:
            if self.is_transitioning:
                return None

            if event.key == pygame.K_LEFT:
                self.selection = (self.selection - 1) % len(MAPS)
                self.confirm_timer = 0.0
            elif event.key == pygame.K_RIGHT:
                self.selection = (self.selection + 1) % len(MAPS)
                self.confirm_timer = 0.0
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.confirm_timer <= 0:
                    self.confirm_timer = 0.8
            elif event.key == pygame.K_ESCAPE:
                return -1  # -1 表示返回角色选择

        if self.confirm_timer > 0:
            self.confirm_timer -= 1.0 / 60.0
            if self.confirm_timer <= 0:
                self.is_transitioning = True
                return self.selection

        return None

    def update(self, dt: float):
        """更新界面状态"""
        self.cursor_flash += dt * 5
        self.bounce_offset = abs(math.sin(self.cursor_flash)) * 8
        self.title_y = math.sin(self.cursor_flash * 0.5) * 3

        # 预览淡入
        if self.map_preview_scale < 1.0:
            self.map_preview_scale = min(1.0, self.map_preview_scale + dt * 3)

    def draw(self, surface: pygame.Surface):
        """绘制地图选择界面"""
        # 深色背景
        surface.fill((12, 12, 20))

        # 顶部装饰线
        pygame.draw.line(surface, (60, 60, 90), (0, 0), (self.screen_width, 0), 4)

        # 标题
        title = self.title_font.render("选择地图", True, (255, 255, 255))
        title_rect = title.get_rect(center=(self.screen_width // 2, 55 + int(self.title_y)))
        surface.blit(title, title_rect)

        # 绘制地图卡片（横向排列）
        card_w = 300
        card_h = 380
        total_w = len(MAPS) * card_w + (len(MAPS) - 1) * 30
        start_x = (self.screen_width - total_w) // 2
        start_y = 110

        for i, map_info in enumerate(MAPS):
            cx = start_x + i * (card_w + 30)
            cy = start_y

            is_selected = i == self.selection

            # 卡片背景
            bg_color = map_info['bg_color']
            card_bg = (bg_color[0] + 20, bg_color[1] + 15, bg_color[2] + 20)
            pygame.draw.rect(surface, card_bg, (cx, cy, card_w, card_h), border_radius=12)

            # 选中边框
            border_color = map_info['accent'] if is_selected else (50, 50, 70)
            border_w = 4 if is_selected else 2
            pygame.draw.rect(surface, border_color, (cx, cy, card_w, card_h),
                           border_w, border_radius=12)

            # 地图预览区
            preview_x = cx + 20
            preview_y = cy + 20
            preview_w = card_w - 40
            preview_h = 200

            # 预览背景
            prev_bg = (bg_color[0] - 10, bg_color[1] - 10, bg_color[2] - 10)
            pygame.draw.rect(surface, prev_bg, (preview_x, preview_y, preview_w, preview_h),
                           border_radius=8)

            # 绘制微缩预览
            self._draw_mini_preview(surface, preview_x, preview_y, preview_w, preview_h, i)

            # 地图名称
            name_text = self.name_font.render(map_info['name'], True, (255, 255, 255))
            name_rect = name_text.get_rect(center=(cx + card_w // 2, cy + 248))
            surface.blit(name_text, name_rect)

            # 地图描述
            desc_text = self.desc_font.render(map_info['desc'], True, (160, 160, 180))
            desc_rect = desc_text.get_rect(center=(cx + card_w // 2, cy + 280))
            surface.blit(desc_text, desc_rect)

            # 平台数量标签
            stage_class = map_info['stage_class']
            plat_count = len(stage_class.platforms) if hasattr(stage_class, 'platforms') else 0
            plat_text = self.info_font.render(f"平台数: {plat_count}", True, (120, 120, 140))
            surface.blit(plat_text, (cx + 20, cy + card_h - 50))

            # 选中指示器
            if is_selected:
                bounce = self.bounce_offset
                # 底部指示箭头
                arrow_y = cy + card_h + 8 + int(bounce)
                arrow_points = [
                    (cx + card_w // 2 - 15, arrow_y + 12),
                    (cx + card_w // 2 + 15, arrow_y + 12),
                    (cx + card_w // 2, arrow_y),
                ]
                pygame.draw.polygon(surface, map_info['accent'], arrow_points)
                # 外发光
                glow_surf = pygame.Surface((card_w + 20, card_h + 40), pygame.SRCALPHA)
                pygame.draw.rect(glow_surf, (*map_info['accent'], 20),
                               (10, 10, card_w, card_h), 4, border_radius=14)
                surface.blit(glow_surf, (cx - 10, cy - 10))

        # 已选标记
        if self.selection == 0:
            marker = self.info_font.render("← → 切换地图", True, (120, 120, 140))
        else:
            marker = self.info_font.render("← → 切换地图", True, (120, 120, 140))
        marker_rect = marker.get_rect(center=(self.screen_width // 2, 520))
        surface.blit(marker, marker_rect)

        # 确认提示
        if self.confirm_timer > 0:
            confirm_text = self.title_font.render("确认地图", True, (255, 220, 50))
            confirm_rect = confirm_text.get_rect(center=(self.screen_width // 2, 560))
            surface.blit(confirm_text, confirm_rect)
        else:
            hint_text = self.info_font.render("Enter 确认地图  |  Esc 返回角色选择", True, (100, 100, 130))
            hint_rect = hint_text.get_rect(center=(self.screen_width // 2, 560))
            surface.blit(hint_text, hint_rect)

        # 底部装饰线
        pygame.draw.line(surface, (60, 60, 90), (0, self.screen_height - 4),
                       (self.screen_width, self.screen_height - 4), 4)

    def _draw_mini_preview(self, surface: pygame.Surface,
                           px: int, py: int, pw: int, ph: int, map_index: int):
        """绘制微缩地图预览"""
        scale_x = pw / 1280.0
        scale_y = ph / 720.0

        if map_index == 0:
            # 寝室预览
            # 墙面
            for y in range(ph):
                ratio = y / ph
                r = int(90 * (1 - ratio * 0.3) + 70 * ratio)
                g = int(70 * (1 - ratio * 0.3) + 55 * ratio)
                b = int(55 * (1 - ratio * 0.3) + 42 * ratio)
                pygame.draw.line(surface, (r, g, b), (px, py + y), (px + pw, py + y))

            # 地面
            ground_y = py + int(580 * scale_y)
            pygame.draw.rect(surface, (100, 75, 50), (px, ground_y, pw, ph - ground_y + py))

            # 床（简化）
            beds_preview = [
                (60, 480, 160), (260, 400, 150), (1060, 480, 160), (870, 400, 150),
            ]
            for bx, by, bw in beds_preview:
                rx = px + int(bx * scale_x)
                ry = py + int(by * scale_y)
                rw = int(bw * scale_x)
                rh = int(20 * scale_y)
                pygame.draw.rect(surface, (130, 95, 60), (rx, ry, rw, rh))
                # 上铺
                upper_y = py + int((by - 180) * scale_y)
                pygame.draw.rect(surface, (130, 95, 60), (rx, upper_y, rw, rh))

        elif map_index == 1:
            # 城堡预览
            # 天空渐变
            for y in range(ph):
                ratio = y / ph
                if ratio < 0.5:
                    t = ratio / 0.5
                    r = int(20 + t * 30)
                    g = int(10 + t * 40)
                    b = int(50 + t * 50)
                else:
                    t = (ratio - 0.5) / 0.5
                    r = int(50 + t * 150)
                    g = int(50 + t * 30)
                    b = int(100 - t * 30)
                pygame.draw.line(surface, (r, g, b), (px, py + y), (px + pw, py + y))

            # 月亮
            mx = px + int(1050 * scale_x)
            my = py + int(80 * scale_y)
            mr = int(35 * scale_x)
            pygame.draw.circle(surface, (255, 248, 220), (mx, my), max(mr, 4))

            # 云海
            ground_y = py + int(580 * scale_y)
            pygame.draw.rect(surface, (80, 90, 140), (px, ground_y, pw, ph - ground_y + py))

            # 城堡剪影
            pygame.draw.rect(surface, (15, 12, 30), (px, py + int(100 * scale_y),
                           int(150 * scale_x), int(480 * scale_y)))
            pygame.draw.rect(surface, (15, 12, 30), (px + pw - int(150 * scale_x),
                           py + int(200 * scale_y), int(150 * scale_x), int(380 * scale_y)))

            # 云平台（简化点）
            platforms_preview = [
                (50, 440, 200), (100, 280, 150),
                (530, 310, 220), (580, 180, 150),
                (1030, 440, 200), (1030, 280, 150),
            ]
            for bx, by, bw in platforms_preview:
                rx = px + int(bx * scale_x)
                ry = py + int(by * scale_y)
                rw = int(bw * scale_x)
                rh = int(10 * scale_y)
                pygame.draw.ellipse(surface, (220, 230, 250), (rx, ry, rw, max(rh * 3, 6)))

        elif map_index == 2:
            # 战壕预览
            for y in range(ph):
                ratio = y / ph
                r = int(80 + ratio * 60)
                g = int(70 + ratio * 50)
                b = int(50 + ratio * 30)
                pygame.draw.line(surface, (r, g, b), (px, py + y), (px + pw, py + y))

            # 地面
            ground_y = py + int(580 * scale_y)
            pygame.draw.rect(surface, (85, 68, 45), (px, ground_y, pw, ph - ground_y + py))

            # 左右战壕高墙
            pygame.draw.rect(surface, (80, 65, 48),
                             (px, py + int(310 * scale_y), int(200 * scale_x), int(270 * scale_y)))
            pygame.draw.rect(surface, (80, 65, 48),
                             (px + int(1050 * scale_x), py + int(310 * scale_y),
                              int(200 * scale_x), int(270 * scale_y)))

            # 中间掩体平台
            for bx, by, bw in [(380, 490, 140), (760, 490, 140),
                                (480, 380, 120), (680, 380, 120), (570, 270, 140)]:
                rx = px + int(bx * scale_x)
                ry = py + int(by * scale_y)
                rw = max(int(bw * scale_x), 4)
                pygame.draw.rect(surface, (110, 85, 55), (rx, ry, rw, max(int(8 * scale_y), 3)))
