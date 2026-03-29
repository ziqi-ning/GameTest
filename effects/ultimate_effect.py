# 终极必杀技特效系统 — 每个角色有独特视觉风格
#
# 龚大哥：爱国火焰 — 红旗飘扬 + 星形冲击波 + 火焰粒子
# 军师：实验室能量 — 激光环 + 电弧 + 能量球螺旋
# 神秘人：叛国暗影 — 多重斩击轨迹 + 残影 + 暗红粒子
# 籽桐：雕之自然 — 藤蔓缠绕 + 树叶飞舞 + 绿光螺旋

import pygame
import math
import random


class UltimateEffect:
    """终极必杀技华丽特效 — 差异化设计"""

    def __init__(self, screen_width: int, screen_height: int,
                 character: str, effect_type: str, direction: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.character = character
        self.effect_type = effect_type
        self.direction = direction

        self.timer = 0.0
        self.duration = 2.5
        self.is_active = True
        self.particles = []

        # 角色专属配置
        self.cfg = self._get_config()
        self._init_particles()

    # ── 角色专属配置 ───────────────────────────────────────────────────

    def _get_config(self) -> dict:
        configs = {
            "龚大哥": {
                "primary": (255, 50, 50),
                "secondary": (255, 200, 50),
                "glow": (255, 100, 100),
                "particles": [(255, 200, 50), (255, 100, 50), (255, 255, 100)],
                "name": "爱国之心",
                "style": "fire",
            },
            "军师": {
                "primary": (100, 50, 255),
                "secondary": (50, 200, 255),
                "glow": (150, 100, 255),
                "particles": [(50, 200, 255), (100, 100, 255), (200, 150, 255)],
                "name": "实验室终极射线",
                "style": "tech",
            },
            "神秘人": {
                "primary": (200, 50, 200),
                "secondary": (100, 50, 100),
                "glow": (255, 100, 255),
                "particles": [(200, 50, 200), (150, 50, 150), (255, 150, 255)],
                "name": "叛国瞬斩",
                "style": "shadow",
            },
            "籽桐": {
                "primary": (50, 200, 100),
                "secondary": (100, 255, 150),
                "glow": (150, 255, 180),
                "particles": [(100, 255, 150), (50, 200, 100), (200, 255, 200)],
                "name": "雕之领域",
                "style": "nature",
            },
        }
        return configs.get(self.character, configs["龚大哥"])

    def _init_particles(self):
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        style = self.cfg["style"]
        cfg_colors = self.cfg["particles"]
        self.particles = []

        if style == "fire":
            # 龚大哥：火焰喷射粒子 + 红旗粒子
            for _ in range(80):
                angle = random.uniform(-math.pi/3, math.pi/3)
                speed = random.uniform(200, 600)
                self.particles.append({
                    "type": "fire",
                    "x": cx,
                    "y": cy,
                    "vx": math.cos(angle) * speed * self.direction,
                    "vy": math.sin(angle) * speed - random.uniform(50, 150),
                    "life": 1.0,
                    "size": random.uniform(3, 10),
                    "color": random.choice(cfg_colors),
                })
            # 红旗粒子
            for _ in range(30):
                angle = random.uniform(-math.pi/4, math.pi/4)
                self.particles.append({
                    "type": "flag",
                    "x": cx + random.uniform(-20, 20),
                    "y": cy - 150,
                    "vx": math.cos(angle) * random.uniform(50, 150) * self.direction,
                    "vy": random.uniform(-20, 20),
                    "life": 1.0,
                    "size": random.uniform(5, 12),
                    "color": random.choice(cfg_colors),
                    "wave": random.uniform(0, math.pi * 2),
                })
            # 星形粒子
            for _ in range(20):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(100, 300)
                self.particles.append({
                    "type": "star",
                    "x": cx,
                    "y": cy,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": 1.0,
                    "size": random.uniform(8, 15),
                    "color": random.choice(cfg_colors),
                    "rot": random.uniform(0, 360),
                    "rot_speed": random.uniform(-200, 200),
                })

        elif style == "tech":
            # 军师：能量球螺旋 + 电弧
            for i in range(60):
                angle = (i / 60) * math.pi * 8
                self.particles.append({
                    "type": "orbit",
                    "angle": angle,
                    "radius": 0,
                    "cx": cx,
                    "cy": cy,
                    "life": 1.0,
                    "size": random.uniform(4, 10),
                    "color": random.choice(cfg_colors),
                    "orbit_speed": 3.0,
                })
            for _ in range(25):
                self.particles.append({
                    "type": "arc",
                    "start_x": cx + random.randint(-300, 300),
                    "start_y": cy - 200 + random.randint(-100, 100),
                    "end_x": cx + random.randint(-100, 100),
                    "end_y": cy + 100,
                    "life": 1.0,
                    "segments": [],
                })
            for _ in range(40):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(50, 200)
                self.particles.append({
                    "type": "spark",
                    "x": cx,
                    "y": cy,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": 1.0,
                    "size": random.uniform(2, 6),
                    "color": random.choice(cfg_colors),
                })

        elif style == "shadow":
            # 神秘人：多重斜向斩击 + 暗影粒子
            for _ in range(8):
                base_x = cx + random.uniform(-100, 100)
                base_y = cy + random.uniform(-80, 80)
                for i in range(15):
                    t = i / 15.0
                    self.particles.append({
                        "type": "slash_trail",
                        "x": base_x + t * 300 * self.direction,
                        "y": base_y + (i % 3 - 1) * 40,
                        "life": 1.0 - t,
                        "size": random.uniform(3, 8),
                        "color": random.choice(cfg_colors),
                    })
            for _ in range(60):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(80, 250)
                self.particles.append({
                    "type": "shadow",
                    "x": cx,
                    "y": cy,
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed,
                    "life": 1.0,
                    "size": random.uniform(2, 7),
                    "color": random.choice(cfg_colors),
                    "fade_rate": random.uniform(0.3, 0.8),
                })

        elif style == "nature":
            # 籽桐：藤蔓 + 树叶螺旋 + 地面冲击
            for i in range(50):
                angle = (i / 50) * math.pi * 2
                self.particles.append({
                    "type": "vine",
                    "x": cx + math.cos(angle) * 20,
                    "y": cy + math.sin(angle) * 20,
                    "angle": angle,
                    "life": 1.0,
                    "size": random.uniform(5, 12),
                    "color": random.choice(cfg_colors),
                    "grow": 0.0,
                })
            for _ in range(40):
                angle = random.uniform(0, math.pi * 2)
                speed = random.uniform(100, 300)
                self.particles.append({
                    "type": "leaf",
                    "x": cx + random.uniform(-100, 100),
                    "y": cy - 100 + random.uniform(-50, 50),
                    "vx": math.cos(angle) * speed,
                    "vy": math.sin(angle) * speed - random.uniform(50, 150),
                    "life": 1.0,
                    "size": random.uniform(4, 9),
                    "color": random.choice(cfg_colors),
                    "rot": random.uniform(0, 360),
                    "rot_speed": random.uniform(-180, 180),
                })
            # 地面冲击波
            for i in range(20):
                self.particles.append({
                    "type": "ground_wave",
                    "x": cx - 200 + i * 20,
                    "y": cy + 80,
                    "life": 1.0 - i * 0.04,
                    "size": random.uniform(6, 12),
                    "color": random.choice(cfg_colors),
                })

    def update(self, dt: float):
        if not self.is_active:
            return

        self.timer += dt
        if self.timer >= self.duration:
            self.is_active = False
            return

        style = self.cfg["style"]
        cx = self.screen_width // 2
        cy = self.screen_height // 2

        for p in self.particles:
            ptype = p["type"]

            if style == "fire":
                if ptype == "fire":
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vy"] += 200 * dt
                    p["vx"] *= 0.97
                    p["life"] -= dt * 0.6
                elif ptype == "flag":
                    p["wave"] += dt * 5
                    p["x"] += p["vx"] * dt + math.sin(p["wave"]) * 3
                    p["y"] += p["vy"] * dt
                    p["life"] -= dt * 0.4
                elif ptype == "star":
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["rot"] += p["rot_speed"] * dt
                    p["life"] -= dt * 0.5

            elif style == "tech":
                if ptype == "orbit":
                    p["radius"] += dt * 200 * (p["life"])
                    p["life"] -= dt * 0.4
                    p["angle"] += p["orbit_speed"] * dt
                elif ptype == "arc":
                    p["life"] -= dt * 2
                    p["segments"] = self._generate_lightning(
                        p["start_x"], p["start_y"], p["end_x"], p["end_y"], 4)
                elif ptype == "spark":
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vx"] *= 0.95
                    p["vy"] *= 0.95
                    p["life"] -= dt * 0.7

            elif style == "shadow":
                if ptype == "slash_trail":
                    p["x"] += p.get("life", 1) * 300 * self.direction * dt
                    p["y"] += random.uniform(-20, 20) * dt
                elif ptype == "shadow":
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vx"] *= 0.96
                    p["vy"] *= 0.96
                    p["life"] -= dt * p["fade_rate"]

            elif style == "nature":
                if ptype == "vine":
                    p["grow"] = min(1.0, p["grow"] + dt * 0.8)
                    p["angle"] += dt * 1.5
                    p["x"] = cx + math.cos(p["angle"]) * 20 * p["grow"]
                    p["y"] = cy + math.sin(p["angle"]) * 20 * p["grow"]
                    p["life"] -= dt * 0.3
                elif ptype == "leaf":
                    p["x"] += p["vx"] * dt
                    p["y"] += p["vy"] * dt
                    p["vy"] += 100 * dt
                    p["rot"] += p["rot_speed"] * dt
                    p["life"] -= dt * 0.5
                elif ptype == "ground_wave":
                    p["life"] -= dt * 0.5

        self.particles = [p for p in self.particles if p.get("life", 0) > 0]

    def _generate_lightning(self, x1: int, y1: int, x2: int, y2: int, depth: int) -> list:
        if depth == 0:
            return [(x1, y1), (x2, y2)]
        mid_x = (x1 + x2) // 2 + random.randint(-25, 25)
        mid_y = (y1 + y2) // 2
        return (self._generate_lightning(x1, y1, mid_x, mid_y, depth - 1) +
                self._generate_lightning(mid_x, mid_y, x2, y2, depth - 1)[1:])

    def draw(self, surface: pygame.Surface):
        if not self.is_active:
            return

        progress = self.timer / self.duration

        if progress < 0.25:
            self._draw_phase_charge(surface, progress / 0.25)
        elif progress < 0.7:
            self._draw_phase_burst(surface, (progress - 0.25) / 0.45)
        else:
            self._draw_phase_fade(surface, (progress - 0.7) / 0.3)

    # ── 蓄力阶段 ──────────────────────────────────────────────────────

    def _draw_phase_charge(self, surface: pygame.Surface, t: float):
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        style = self.cfg["style"]

        if style == "fire":
            # 龚大哥：旋转红旗 + 星形缩放
            for i in range(5):
                angle = t * math.pi * 3 + i * (math.pi * 2 / 5)
                r = 40 + t * 80
                x = cx + math.cos(angle) * r * 0.5
                y = cy - 80 + math.sin(angle) * r * 0.3
                alpha = int(200 * (0.5 + 0.5 * math.sin(t * math.pi * 4)))
                self._draw_glow_circle(surface, int(x), int(y),
                                       int(15 + t * 25), self.cfg["glow"], alpha)
            # 中心火焰核心
            size = int(20 + t * 40)
            self._draw_glow_circle(surface, cx, cy, size, self.cfg["primary"], int(200 * t))
            self._draw_glow_circle(surface, cx, cy, size // 2, self.cfg["secondary"], int(255 * t))

        elif style == "tech":
            # 军师：能量环不断扩张
            for i in range(4):
                ring_t = (t + i * 0.25) % 1.0
                r = int(30 + ring_t * 120)
                alpha = int(200 * (1 - ring_t))
                if alpha > 0:
                    pygame.draw.circle(surface, (*self.cfg["secondary"], alpha),
                                     (cx, cy), r, 2)
            # 中心能量点
            self._draw_glow_circle(surface, cx, cy, int(15 + t * 20), self.cfg["primary"], int(255 * t))

        elif style == "shadow":
            # 神秘人：暗影快速闪烁
            alpha = int(100 + 100 * abs(math.sin(t * math.pi * 6)))
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((50, 0, 50, alpha))
            surface.blit(overlay, (0, 0))
            # 斩击轮廓预演
            for i in range(3):
                sx = cx - 100 * self.direction + i * 60 * self.direction
                self._draw_slash(surface, sx, cy - 60 + i * 50, self.direction,
                                alpha=alpha // 3)

        elif style == "nature":
            # 籽桐：地面藤蔓缓慢生长
            for i in range(8):
                vine_t = min(1.0, t * 2 - i * 0.1)
                if vine_t > 0:
                    vx = cx - 150 + i * 40
                    vy = cy + 80
                    for j in range(int(vine_t * 20)):
                        wx = vx + j * 8 * self.direction
                        wy = vy - j * 4
                        alpha = int(150 * vine_t)
                        self._draw_glow_circle(surface, int(wx), int(wy), 4,
                                              self.cfg["primary"], alpha)
            # 顶部能量聚合
            self._draw_glow_circle(surface, cx, cy - 50, int(10 + t * 20),
                                  self.cfg["glow"], int(200 * t))

    # ── 爆发阶段（角色差异化核心）─────────────────────────────────────

    def _draw_phase_burst(self, surface: pygame.Surface, t: float):
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        style = self.cfg["style"]

        if style == "fire":
            self._draw_gongdage_burst(surface, cx, cy, t)
        elif style == "tech":
            self._draw_junshi_burst(surface, cx, cy, t)
        elif style == "shadow":
            self._draw_shenmiren_burst(surface, cx, cy, t)
        elif style == "nature":
            self._draw_zitong_burst(surface, cx, cy, t)

        # 全角色：文字公告
        self._draw_announcement(surface, cx, cy - 200, t)

    # 龚大哥爆发：火焰海啸 + 红旗 + 星形冲击波
    def _draw_gongdage_burst(self, surface, cx, cy, t):
        # 大型火焰冲击波（向前推进）
        wave_x = cx - 300 * self.direction + 600 * t * self.direction
        for i in range(20):
            wy = cy - 150 + i * 15
            alpha = int(200 * (1 - abs(t - 0.5) * 2))
            size = int(20 + 10 * math.sin(i * 0.5 + t * 5))
            if alpha > 0:
                pygame.draw.ellipse(surface, (*self.cfg["primary"], alpha),
                                  (int(wave_x) - 200, wy, 400, size))

        # 星形爆发
        for i in range(6):
            angle = t * math.pi * 2 + i * (math.pi / 3)
            dist = 50 + t * 300
            sx = cx + math.cos(angle) * dist * self.direction
            sy = cy + math.sin(angle) * dist * 0.6
            alpha = int(255 * (1 - t))
            rot = t * 360 + i * 60
            self._draw_star(surface, int(sx), int(sy), int(15 + 20 * (1 - t)),
                           rot, self.cfg["particles"][i % 3], alpha)

        # 粒子
        for p in self.particles:
            if p["type"] == "fire" and p["life"] > 0:
                alpha = int(255 * p["life"])
                size = int(p["size"] * (0.5 + 0.5 * p["life"]))
                if size > 0:
                    self._draw_glow_circle(surface, int(p["x"]), int(p["y"]),
                                          size, p["color"], alpha)
            elif p["type"] == "flag" and p["life"] > 0:
                alpha = int(200 * p["life"])
                pygame.draw.rect(surface, (*p["color"], alpha),
                               (int(p["x"] - 8), int(p["y"] - 5), 16, 10))

    # 军师爆发：能量同心圆爆炸 + 电弧
    def _draw_junshi_burst(self, surface, cx, cy, t):
        # 多层同心圆向外扩散
        for ring_i in range(5):
            ring_t = (t + ring_i * 0.15) % 1.0
            r = int(20 + ring_t * 350)
            alpha = int(200 * (1 - ring_t))
            if alpha > 0:
                pygame.draw.circle(surface, (*self.cfg["secondary"], alpha),
                                 (cx, cy), r, 3)
                pygame.draw.circle(surface, (*self.cfg["primary"], alpha // 2),
                                 (cx, cy), int(r * 0.7), 2)

        # 旋转能量线条
        for i in range(12):
            angle = t * math.pi * 5 + i * (math.pi / 6)
            length = 80 + t * 280
            ex = cx + math.cos(angle) * length
            ey = cy + math.sin(angle) * length
            alpha = int(150 * (1 - t))
            if alpha > 0:
                self._draw_glow_line(surface, cx, cy, int(ex), int(ey),
                                     self.cfg["glow"], alpha, width=2)

        # 粒子（轨道粒子）
        for p in self.particles:
            if p["type"] == "orbit" and p["life"] > 0:
                px = int(p["cx"] + math.cos(p["angle"]) * p["radius"])
                py = int(p["cy"] + math.sin(p["angle"]) * p["radius"])
                alpha = int(255 * p["life"])
                self._draw_glow_circle(surface, px, py, int(p["size"] * p["life"]),
                                      p["color"], alpha)
            elif p["type"] == "arc" and p["life"] > 0 and p["segments"]:
                alpha = int(255 * p["life"])
                for i in range(len(p["segments"]) - 1):
                    pygame.draw.line(surface, (*self.cfg["secondary"], alpha),
                                   p["segments"][i], p["segments"][i + 1], 2)

    # 神秘人爆发：多重斩击 + 暗影轨迹
    def _draw_shenmiren_burst(self, surface, cx, cy, t):
        # 多条斜向斩击
        for i in range(6):
            sx = cx - 250 * self.direction + i * 80 * self.direction
            sy = cy - 100 + i * 40
            alpha = int(200 * (1 - t * 0.7))
            if alpha > 0:
                self._draw_slash(surface, sx, sy, self.direction, alpha, width=8)
                self._draw_slash(surface, sx + 20 * self.direction, sy - 20,
                                self.direction, alpha // 2, width=4)

        # 暗影粒子
        for p in self.particles:
            if p["type"] == "shadow" and p["life"] > 0:
                alpha = int(200 * p["life"])
                size = int(p["size"] * p["life"])
                if size > 0:
                    self._draw_glow_circle(surface, int(p["x"]), int(p["y"]),
                                          size, p["color"], alpha)

        # 斩击轨迹
        for p in self.particles:
            if p["type"] == "slash_trail" and p["life"] > 0:
                alpha = int(255 * p["life"])
                self._draw_glow_circle(surface, int(p["x"]), int(p["y"]),
                                       int(p["size"] * p["life"]),
                                       p["color"], alpha)

    # 籽桐爆发：藤蔓螺旋 + 树叶乱舞
    def _draw_zitong_burst(self, surface, cx, cy, t):
        # 地面藤蔓冲击
        for i in range(15):
            wx = cx - 200 + i * 30
            wy = cy + 80
            alpha = int(150 * (1 - t * 0.8))
            for j in range(int((1 - t) * 5)):
                jx = wx + j * 5
                jy = wy - j * 4
                if alpha > 0:
                    pygame.draw.circle(surface, (*self.cfg["primary"], alpha),
                                    (int(jx), int(jy)), 4)

        # 树叶
        for p in self.particles:
            if p["type"] == "leaf" and p["life"] > 0:
                alpha = int(200 * p["life"])
                size = int(p["size"] * p["life"])
                if size > 0:
                    self._draw_glow_circle(surface, int(p["x"]), int(p["y"]),
                                          size, p["color"], alpha)
            elif p["type"] == "vine" and p["life"] > 0:
                alpha = int(180 * p["life"])
                size = int(p["size"] * p["life"])
                if size > 0:
                    self._draw_glow_circle(surface, int(p["x"]), int(p["y"]),
                                          size, p["color"], alpha)

        # 地面波纹
        for p in self.particles:
            if p["type"] == "ground_wave" and p["life"] > 0:
                alpha = int(150 * p["life"])
                pygame.draw.circle(surface, (*p["color"], alpha),
                                 (int(p["x"]), int(p["y"])), int(p["size"]))

        # 绿色螺旋能量
        for i in range(8):
            angle = t * math.pi * 4 + i * (math.pi / 4)
            r = 30 + t * 250
            sx = cx + math.cos(angle) * r
            sy = cy + math.sin(angle) * r * 0.5
            alpha = int(180 * (1 - t))
            if alpha > 0:
                self._draw_glow_circle(surface, int(sx), int(sy), 6, self.cfg["glow"], alpha)

    # ── 消散阶段 ──────────────────────────────────────────────────────

    def _draw_phase_fade(self, surface: pygame.Surface, t: float):
        cx = self.screen_width // 2
        cy = self.screen_height // 2
        alpha = int(200 * (1 - t))
        style = self.cfg["style"]

        if alpha <= 0:
            return

        if style == "fire":
            for i in range(3):
                r = 50 + i * 40 + int(50 * (1 - t))
                self._draw_glow_circle(surface, cx, cy, r,
                                      self.cfg["primary"], int(alpha * 0.2 * (1 - i / 3)))
        elif style == "tech":
            for i in range(4):
                r = 30 + i * 50 + int(80 * (1 - t))
                self._draw_glow_circle(surface, cx, cy, r,
                                      self.cfg["secondary"], int(alpha * 0.15))
        elif style == "shadow":
            overlay = pygame.Surface((self.screen_width, self.screen_height), pygame.SRCALPHA)
            overlay.fill((30, 0, 30, int(alpha * 0.3)))
            surface.blit(overlay, (0, 0))
        elif style == "nature":
            for i in range(5):
                y = cy + 80 + i * 20
                pygame.draw.line(surface, (*self.cfg["primary"], int(alpha * 0.5)),
                               (cx - 150, y), (cx + 150, y), 2)

    # ── 辅助绘制函数 ───────────────────────────────────────────────────

    def _draw_glow_circle(self, surface, x, y, radius, color, alpha):
        if radius <= 0 or alpha <= 0:
            return
        size = radius * 2
        glow = pygame.Surface((size, size), pygame.SRCALPHA)
        for r in range(radius, 0, -1):
            a = int(alpha * (1 - r / radius) * 0.5)
            if a > 0:
                pygame.draw.circle(glow, (*color, a), (radius, radius), r)
        surface.blit(glow, (x - radius, y - radius))

    def _draw_glow_line(self, surface, x1, y1, x2, y2, color, alpha, width=2):
        if alpha <= 0:
            return
        length = int(math.hypot(x2 - x1, y2 - y1)) + width * 2
        if length <= 0:
            return
        glow = pygame.Surface((length, width * 4), pygame.SRCALPHA)
        for w in range(width, 0, -1):
            a = int(alpha * (w / width))
            if a > 0:
                pygame.draw.line(glow, (*color, a), (width, width * 2), (length - width, width * 2), w)
        angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
        rotated = pygame.transform.rotate(glow, -angle)
        rect = rotated.get_rect(center=(x1, y1))
        surface.blit(rotated, rect)

    def _draw_slash(self, surface, x, y, direction, alpha, width=6):
        if alpha <= 0:
            return
        length = 120
        # 斜向斩击
        points = [
            (x, y - width),
            (x + length * direction, y + width // 2),
            (x + length * direction, y + width),
            (x, y - width // 2),
        ]
        s = pygame.Surface((length + 10, width * 3), pygame.SRCALPHA)
        pygame.draw.polygon(s, (*self.cfg["primary"], alpha), [
            (5, width), (length + 5, width * 1.5), (length + 5, width * 2)
        ])
        surface.blit(s, (x - 5, y - width * 1.5))

    def _draw_star(self, surface, x, y, size, rotation, color, alpha):
        if alpha <= 0 or size <= 0:
            return
        points = []
        for i in range(10):
            angle = math.radians(rotation + i * 36 - 90)
            r = size if i % 2 == 0 else size // 2
            points.append((x + math.cos(angle) * r, y + math.sin(angle) * r))
        s = pygame.Surface((size * 3, size * 3), pygame.SRCALPHA)
        if len(points) >= 3:
            pygame.draw.polygon(s, (*color, alpha), [
                (size * 1.5 + p[0] - x, size * 1.5 + p[1] - y)
                for p in points
            ])
        surface.blit(s, (x - size * 1.5, y - size * 1.5))

    def _draw_announcement(self, surface, cx, cy, t):
        alpha = int(255 * min(1, t * 4) * max(0, 1 - (t - 0.8) / 0.2))
        if alpha <= 0:
            return

        font_name = "microsoftyahei"
        font_large = pygame.font.SysFont(font_name, 52, bold=True)
        font_small = pygame.font.SysFont(font_name, 28)

        name_text = font_large.render(self.cfg["name"], True, self.cfg["primary"])
        sub_text = font_small.render("ULTIMATE SKILL!", True, self.cfg["secondary"])

        # 描边
        for dx in [-3, 0, 3]:
            for dy in [-3, 0, 3]:
                if dx != 0 or dy != 0:
                    outline = font_large.render(self.cfg["name"], True, (0, 0, 0))
                    outline.set_alpha(alpha // 2)
                    surface.blit(outline, (cx - name_text.get_width() // 2 + dx,
                                           cy + dy))
        name_text.set_alpha(alpha)
        sub_text.set_alpha(alpha)
        surface.blit(name_text, (cx - name_text.get_width() // 2, cy))
        surface.blit(sub_text, (cx - sub_text.get_width() // 2, cy + 55))


class UltimateEffectManager:
    """终极必杀技特效管理器"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.effects = []
        self.is_paused = False
        self.pause_timer = 0.0
        self.pause_duration = 0.0

    def trigger(self, character: str, effect_type: str, direction: int):
        effect = UltimateEffect(self.screen_width, self.screen_height,
                              character, effect_type, direction)
        self.effects.append(effect)
        self.is_paused = True
        self.pause_duration = 2.5
        self.pause_timer = 0.0

    def update(self, dt: float):
        if self.is_paused:
            self.pause_timer += dt
            if self.pause_timer >= self.pause_duration:
                self.is_paused = False

        for effect in self.effects[:]:
            effect.update(dt)
            if not effect.is_active:
                self.effects.remove(effect)

    def draw(self, surface: pygame.Surface):
        for effect in self.effects:
            effect.draw(surface)

    def is_playing(self) -> bool:
        return len(self.effects) > 0 and self.is_paused
