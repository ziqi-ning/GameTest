# 终极必杀技实体系统
# 管理P1全屏国旗、P2激光、P3黑影、P4鸡/鸡蛋等实体

import pygame
import math
import random
from typing import List, Optional, Tuple
from dataclasses import dataclass, field


# ══════════════════════════════════════════════════════════════
# 实体基类
# ══════════════════════════════════════════════════════════════

class UltimateEntity:
    """终极必杀技实体基类"""

    def __init__(self, x: float, y: float, owner_id: int, screen_width: int, screen_height: int):
        self.x = x
        self.y = y
        self.owner_id = owner_id
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.active = True
        self.timer = 0.0
        self.duration = 2.0

    def update(self, dt: float):
        self.timer += dt
        if self.timer >= self.duration:
            self.active = False

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        pass

    def get_hurtbox_rect(self) -> Tuple[float, float, float, float]:
        """返回受击框（用于碰撞检测）"""
        return (0, 0, 0, 0)


# ══════════════════════════════════════════════════════════════
# P1 五星红旗实体（全屏伤害）
# ══════════════════════════════════════════════════════════════

class P1NationalFlag(UltimateEntity):
    """
    P1龚大哥终极技：全屏范围绘制一幅五星红旗国旗
    全图除了己方阵营外的敌人全部受到中额伤害
    """

    def __init__(self, x: float, y: float, owner_id: int,
                 screen_width: int, screen_height: int,
                 owner_is_p1: bool = True):
        super().__init__(x, y, owner_id, screen_width, screen_height)
        self.duration = 3.0          # 红旗存在3秒（仅用于视觉）
        self.damage = 100            # 一次性中额伤害
        self.has_dealt_damage = False  # 防止重复伤害
        self.owner_is_p1 = owner_is_p1  # True=P1玩家(右侧), False=AI(左侧)
        self.wave_time = 0.0        # 红旗飘动动画

        # 伤害目标集合（player_id列表）
        self._damaged_targets = set()

        # 五角星位置（国旗大星在左上角，4颗小星围绕）
        self._big_star_pos = (140, 170)  # 相对于国旗左上角
        # 4颗小五角星的角度和位置
        self._small_stars = [
            (335, 165, 210),   # (x, y, rotation)
            (405, 215, 240),
            (385, 285, 300),
            (305, 325, 30),
        ]

    def update(self, dt: float):
        super().update(dt)
        self.wave_time += dt

    def can_damage_target(self, target_player_id: int) -> bool:
        """检查是否可以对目标造成伤害（阵营判断）"""
        if target_player_id in self._damaged_targets:
            return False
        # P1玩家发动 → 伤害P2(AI)
        # AI发动 → 伤害P1玩家
        if self.owner_is_p1:
            return target_player_id != self.owner_id
        else:
            return target_player_id != self.owner_id

    def record_damage_to(self, target_player_id: int):
        """记录已对某目标造成过伤害"""
        self._damaged_targets.add(target_player_id)

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        """绘制五星红旗"""
        # 国旗尺寸（放大2.5倍）
        FLAG_W = 600
        FLAG_H = 400
        # 国旗位置：屏幕居中偏上
        base_x = self.screen_width // 2 - FLAG_W // 2 - camera_x
        base_y = self.screen_height // 2 - FLAG_H // 2 - 40

        # 淡入淡出
        progress = self.timer / self.duration
        if progress < 0.1:
            alpha = int(255 * (progress / 0.1))
        elif progress > 0.8:
            alpha = int(255 * ((1.0 - progress) / 0.2))
        else:
            alpha = 255

        # 波动动画（旗帜飘动）
        wave1 = math.sin(self.wave_time * 4) * 8
        wave2 = math.sin(self.wave_time * 4 + 1) * 6

        # 绘制红色背景（带波动）
        flag_surf = pygame.Surface((FLAG_W, FLAG_H), pygame.SRCALPHA)
        for px in range(FLAG_W):
            offset = int(math.sin((px / FLAG_W) * math.pi * 2 + self.wave_time * 5) * 4)
            color = (220, 30, 30, alpha)
            pygame.draw.line(flag_surf, color, (px, 0), (px, FLAG_H))

        # 大五角星（金黄色）
        bsx, bsy = self._big_star_pos
        self._draw_star_on_surface(flag_surf, bsx, bsy + wave1, 60, 0, (255, 220, 0, alpha))

        # 4颗小五角星
        for sx, sy, rot in self._small_stars:
            self._draw_star_on_surface(flag_surf, sx + wave2, sy + wave2, 20, rot, (255, 220, 0, alpha))

        surface.blit(flag_surf, (base_x, base_y))

        # 国旗外发光边框
        glow_surf = pygame.Surface((FLAG_W + 20, FLAG_H + 20), pygame.SRCALPHA)
        pygame.draw.rect(glow_surf, (255, 200, 50, alpha // 3), glow_surf.get_rect(), 8)
        surface.blit(glow_surf, (base_x - 10, base_y - 10))

        # 金色粒子效果（飘散）
        for i in range(20):
            t = (self.timer * 0.3 + i * 0.15) % 1.0
            px = base_x + int(random.uniform(50, FLAG_W - 50) + math.sin(t * 10 + i) * 20)
            py = base_y + int(t * FLAG_H * 0.8)
            size = int(4 + math.sin(i) * 2)
            if alpha > 50:
                glow_p = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(glow_p, (255, 220, 50, alpha // 2), (size, size), size)
                surface.blit(glow_p, (int(px - size), int(py - size)))

    def _draw_star_on_surface(self, surf: pygame.Surface, cx: int, cy: int,
                               radius: int, rotation: float,
                               color: Tuple[int, int, int, int]):
        """在surface上绘制五角星"""
        points = []
        for i in range(10):
            angle = math.radians(rotation + i * 36 - 90)
            r = radius if i % 2 == 0 else radius * 0.382
            px = cx + math.cos(angle) * r
            py = cy + math.sin(angle) * r
            points.append((px, py))
        if len(points) >= 5:
            pygame.draw.polygon(surf, color, points)


# ══════════════════════════════════════════════════════════════
# P2 高能激光实体（同一行巨额伤害）
# ══════════════════════════════════════════════════════════════

class P2LaserBeam(UltimateEntity):
    """
    P2军师终极技：释放蓝色高能激光，对同一行造成巨额伤害
    """

    def __init__(self, x: float, y: float, owner_id: int,
                 screen_width: int, screen_height: int,
                 direction: int = 1,
                 owner: 'Fighter' = None):
        super().__init__(x, y, owner_id, screen_width, screen_height)
        self.owner = owner  # 实时跟随发射者
        self.duration = 2.5
        self.damage = 400            # 巨额伤害
        self.direction = direction   # 1=向右, -1=向左
        self.has_dealt_damage = False
        self.charge_timer = 0.0     # 蓄力时间
        self.charge_duration = 0.5  # 0.5秒蓄力

        # 激光参数（水平发射）
        self.laser_thickness = 50       # 激光上下厚度
        self.laser_length = 0            # 激光水平长度（随时间增长）
        self.max_laser_length = 800     # 激光最大水平长度

        # 特效粒子
        self.particles: List[dict] = []
        self.arc_segments: List[List[Tuple[int, int]]] = []

    def update(self, dt: float):
        super().update(dt)

        # 实时跟随发射者的Y轴
        if self.owner is not None:
            self.y = self.owner.y

        # 蓄力阶段
        if self.timer < self.charge_duration:
            self.charge_timer = self.timer / self.charge_duration
            return

        # 激光展开阶段
        active_timer = self.timer - self.charge_duration
        expand_progress = min(1.0, active_timer / 0.3)

        # 激光长度从0扩展到最大值（水平）
        self.laser_length = int(self.max_laser_length * expand_progress)

        # 生成电弧
        if random.random() < 0.4:
            self._generate_arc()

        # 更新粒子
        self._update_particles(dt)

        # 更新电弧
        for seg in self.arc_segments[:]:
            seg[0] -= dt
            if seg[0] <= 0:
                self.arc_segments.remove(seg)

    def _generate_arc(self):
        """生成闪电电弧"""
        start_x = self.x + self.direction * random.randint(50, 150)
        start_y = self.y - 80 + random.randint(-20, 20)
        end_x = self.x + self.direction * random.randint(200, 600)
        end_y = start_y + random.randint(-40, 40)
        segments = self._generate_lightning(start_x, start_y, end_x, end_y, 3)
        self.arc_segments.append([0.15, segments])

    def _generate_lightning(self, x1: int, y1: int, x2: int, y2: int, depth: int) -> List[Tuple[int, int]]:
        if depth == 0:
            return [(x1, y1), (x2, y2)]
        mid_x = (x1 + x2) // 2 + random.randint(-20, 20)
        mid_y = (y1 + y2) // 2
        left = self._generate_lightning(x1, y1, mid_x, mid_y, depth - 1)
        right = self._generate_lightning(mid_x, mid_y, x2, y2, depth - 1)
        return left + right[1:]

    def _update_particles(self, dt: float):
        # 生成新粒子（水平散布）
        if random.random() < 0.6:
            angle = random.uniform(-0.3, 0.3)  # 接近水平方向
            speed = random.uniform(100, 400)
            dist = random.randint(0, self.laser_length)
            self.particles.append({
                "x": self.x + self.direction * dist,
                "y": self.y - 80 + random.uniform(-25, 25),
                "vx": math.cos(angle) * speed * self.direction,
                "vy": math.sin(angle) * speed,
                "life": 0.3,
                "size": random.uniform(3, 8),
                "color": random.choice([
                    (50, 150, 255), (100, 200, 255), (150, 100, 255), (200, 230, 255)
                ])
            })

        # 更新现有粒子
        for p in self.particles[:]:
            p["x"] += p["vx"] * dt
            p["y"] += p["vy"] * dt
            p["life"] -= dt
            if p["life"] <= 0:
                self.particles.remove(p)

    def is_in_laser_row(self, target_y: float, target_h: float) -> bool:
        """判断目标是否在激光同一行（角色高度范围）"""
        target_top = target_y - target_h
        target_bottom = target_y
        laser_mid = self.y - 75  # 对齐激光视觉中心
        laser_half_thickness = self.laser_thickness // 2
        return (target_top <= laser_mid + laser_half_thickness and
                target_bottom >= laser_mid - laser_half_thickness)

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        # 蓄力阶段：显示蓄力特效
        if self.timer < self.charge_duration:
            self._draw_charging(surface, camera_x)
            return

        # 正式激光
        self._draw_laser(surface, camera_x)
        # 粒子
        self._draw_particles(surface, camera_x)
        # 电弧
        self._draw_arcs(surface, camera_x)

    def _draw_charging(self, surface: pygame.Surface, camera_x: int):
        """蓄力阶段的视觉效果"""
        t = self.charge_timer
        # 能量聚集环
        cx = self.x - camera_x
        cy = self.y - 90
        for i in range(4):
            ring_t = (t + i * 0.2) % 1.0
            r = int(30 + ring_t * 100)
            alpha = int(200 * (1 - ring_t))
            if alpha > 0:
                pygame.draw.circle(surface, (50, 150, 255, alpha), (cx, cy), r, 2)
        # 中心能量球
        glow_r = int(15 + t * 30)
        glow = pygame.Surface((glow_r * 2 + 10, glow_r * 2 + 10), pygame.SRCALPHA)
        pygame.draw.circle(glow, (50, 150, 255, 200), (glow_r + 5, glow_r + 5), glow_r)
        pygame.draw.circle(glow, (150, 220, 255, 255), (glow_r + 5, glow_r + 5), glow_r // 2)
        surface.blit(glow, (int(cx - glow_r - 5), int(cy - glow_r - 5)))

    def _draw_laser(self, surface: pygame.Surface, camera_x: int):
        """绘制主激光束（水平方向）"""
        if self.laser_length <= 0:
            return

        cx = self.x - camera_x
        cy = self.y - 75  # 角色身体中心，对齐实际伤害覆盖层
        thickness = self.laser_thickness
        alpha = 255

        # 计算激光的x范围
        laser_start_x = cx
        laser_end_x = cx + self.direction * self.laser_length

        # 多层光束叠加（外→内，颜色由深到浅）
        layers = [
            (thickness + 30, (50, 100, 200, alpha // 3)),          # 最外层光晕
            (thickness + 15, (50, 150, 255, alpha // 2)),        # 外层
            (thickness,      (80, 180, 255, int(alpha * 0.8))), # 中层
            (thickness // 2, (150, 220, 255, alpha)),           # 内层
            (thickness // 4, (255, 255, 255, alpha)),           # 核心白光
        ]

        for th, color in layers:
            rect_y = cy - th // 2
            rect_h = th
            rect_w = abs(laser_end_x - laser_start_x)
            rect_x = min(laser_start_x, laser_end_x)
            if rect_w > 0 and rect_h > 0:
                pygame.draw.rect(surface, color, (int(rect_x), int(rect_y), int(rect_w), int(rect_h)))

        # 激光发射口能量球
        ball_x = laser_start_x + self.direction * 20
        for r in range(25, 0, -5):
            a = int(150 * (1 - r / 25))
            if a > 0:
                pygame.draw.circle(surface, (100, 180, 255, a), (int(ball_x), int(cy)), r)

    def _draw_particles(self, surface: pygame.Surface, camera_x: int):
        """绘制激光粒子"""
        for p in self.particles:
            a = int(255 * (p["life"] / 0.3))
            if a > 0:
                glow = pygame.Surface((int(p["size"] * 2 + 4), int(p["size"] * 2 + 4)), pygame.SRCALPHA)
                pygame.draw.circle(glow, (*p["color"], a), (int(p["size"] + 2), int(p["size"] + 2)), int(p["size"]))
                surface.blit(glow, (int(p["x"] - camera_x - p["size"] - 2), int(p["y"] - p["size"] - 2)))

    def _draw_arcs(self, surface: pygame.Surface, camera_x: int):
        """绘制闪电电弧"""
        for seg_data in self.arc_segments:
            remaining, segments = seg_data
            alpha = int(255 * (remaining / 0.15))
            if alpha <= 0 or len(segments) < 2:
                continue
            # 缩放segments到camera space
            scaled = [(x - camera_x, y) for x, y in segments]
            for i in range(len(scaled) - 1):
                pygame.draw.line(surface, (100, 200, 255, alpha), scaled[i], scaled[i + 1], 2)


# ══════════════════════════════════════════════════════════════
# P3 黑影实体（瞬移身后持续伤害）
# ══════════════════════════════════════════════════════════════

class P3ShadowClone(UltimateEntity):
    """
    P3神秘人终极技：大号小弟（黑影）
    瞬移到敌人身后，自动攻击敌人，持续一段时间后消失
    """

    def __init__(self, x: float, y: float, owner_id: int,
                 screen_width: int, screen_height: int,
                 max_health: int, target_x: float, target_facing_right: bool,
                 duration: float = 8.0):
        super().__init__(x, y, owner_id, screen_width, screen_height)
        # 黑影瞬移到敌人前面
        if target_facing_right:
            self.x = target_x + 80
        else:
            self.x = target_x - 80

        self.y = y
        self.target_ref = None  # 保存敌人引用用于跟随
        self.duration = duration
        self.max_health = max_health
        self.health = self.max_health
        self.alive = True

        # 小弟属性
        self.ATTACK_DAMAGE = 40     # 每次攻击伤害
        self.ATTACK_RANGE = 100     # 攻击范围（水平距离）
        self.ATTACK_COOLDOWN = 1.0  # 攻击间隔
        self.MOVE_SPEED = 2.0

        self.attack_timer = 0.0
        self.hit_flash = 0.0
        self.facing_right = not target_facing_right
        self.last_damage_time = 0.0  # 上次伤害时间（防止瞬秒）

        # 动画
        self.anim_frame = 0
        self.anim_timer = 0.0

        # 特效
        self.trail_positions: List[Tuple[float, float]] = []

    def set_target(self, enemy):
        """设置追踪目标"""
        self.target_ref = enemy

    def update(self, dt: float, player1, player2):
        super().update(dt)

        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.anim_timer += dt
        if self.anim_timer >= 0.12:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % 4

        # 记录轨迹（只在瞬移初期）
        if self.timer < 0.3:
            self.trail_positions.append((self.x, self.y))
        if len(self.trail_positions) > 6:
            self.trail_positions.pop(0)

        if not self.alive:
            return

        # 根据owner_id确定该打的敌人
        if player1 and player1.player_id == self.owner_id:
            enemy = player2
        elif player2 and player2.player_id == self.owner_id:
            enemy = player1
        else:
            enemy = None

        # 跟随敌人在Y轴上的位置（保持相对高度）
        if enemy and hasattr(enemy, 'y'):
            # 平滑跟随敌人Y坐标
            target_y = enemy.y
            self.y += (target_y - self.y) * 0.1

        # AI行为：追击敌人
        if enemy and hasattr(enemy, 'health') and enemy.health > 0:
            dist = abs(self.x - enemy.x)
            self.facing_right = enemy.x > self.x

            # 保持在敌人前面位置
            behind_offset = 80
            if enemy.x > self.x:
                target_ahead_x = enemy.x - behind_offset
            else:
                target_ahead_x = enemy.x + behind_offset

            # 平滑移动到敌人前面
            self.x += (target_ahead_x - self.x) * 0.05

            # 只有在攻击范围内才能造成伤害
            if dist <= self.ATTACK_RANGE:
                if self.attack_timer <= 0:
                    self._do_attack(enemy)
                    self.attack_timer = self.ATTACK_COOLDOWN

    def _do_attack(self, target):
        """攻击敌人"""
        if hasattr(target, 'take_minion_damage'):
            target.take_minion_damage(self.ATTACK_DAMAGE, self.owner_id)
        elif hasattr(target, 'health'):
            target.health = max(0, target.health - self.ATTACK_DAMAGE)

    def take_damage(self, damage: int):
        """受伤"""
        self.health -= damage
        self.hit_flash = 0.15
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def get_hurtbox(self) -> Tuple[float, float, int, int]:
        """获取受击框"""
        return (self.x - 40, self.y - 160, 80, 160)

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        sx = self.x - camera_x
        sy = self.y

        # 轨迹残影
        for i, (tx, ty) in enumerate(self.trail_positions):
            alpha = int(80 * (i / len(self.trail_positions)))
            if alpha > 0:
                tsx = tx - camera_x
                tsy = ty
                shadow_s = pygame.Surface((70, 150), pygame.SRCALPHA)
                pygame.draw.ellipse(shadow_s, (30, 0, 60, alpha), shadow_s.get_rect())
                surface.blit(shadow_s, (int(tsx - 35), int(tsy - 150)))

        # 受击闪烁
        if self.hit_flash > 0 and int(self.hit_flash * 20) % 2 == 0:
            return

        # 主体黑影（简化绘制）
        shadow_surf = pygame.Surface((80, 160), pygame.SRCALPHA)

        # 身体
        pygame.draw.ellipse(shadow_surf, (40, 0, 80, 200), (10, 40, 60, 100))

        # 头部
        pygame.draw.ellipse(shadow_surf, (50, 10, 100, 200), (20, 10, 40, 40))

        # 眼睛（红色发光）
        pulse = 0.7 + 0.3 * abs(math.sin(self.anim_timer * 8))
        eye_color = (int(255 * pulse), 0, int(50 * pulse))
        pygame.draw.circle(shadow_surf, eye_color, (28, 25), 5)
        pygame.draw.circle(shadow_surf, eye_color, (48, 25), 5)

        # 雾气效果
        for i in range(4):
            cloud_x = 10 + int(math.sin(self.timer * 2 + i) * 10)
            cloud_y = 130 + i * 5
            pygame.draw.ellipse(shadow_surf, (30, 0, 50, 100), (cloud_x, cloud_y, 50, 12))

        surface.blit(shadow_surf, (int(sx - 40), int(sy - 160)))

        # 血条
        bar_w = 60
        bar_h = 5
        bx = int(sx - bar_w // 2)
        by = int(sy - 170)
        ratio = self.health / self.max_health
        pygame.draw.rect(surface, (40, 0, 60), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (200, 50, 150), (bx, by, int(bar_w * ratio), bar_h))


# ══════════════════════════════════════════════════════════════
# P4 鸡和鸡蛋实体（吸入+持续啄击）
# ══════════════════════════════════════════════════════════════

class P4Egg(UltimateEntity):
    """
    P4籽桐终极技：召唤一个鸡蛋，把敌人吸入鸡蛋内
    鸡一直啄造成伤害，持续5秒
    """

    def __init__(self, x: float, y: float, owner_id: int,
                 screen_width: int, screen_height: int,
                 trapped_target_id: int, trap_duration: float = 5.0):
        super().__init__(x, y, owner_id, screen_width, screen_height)
        self.duration = trap_duration
        self.damage = 30             # 每0.5秒伤害
        self.damage_tick = 0.0
        self.damage_interval = 0.5
        self.trapped_target_id = trapped_target_id
        self.trap_duration = trap_duration
        self.egg_radius = 50         # 鸡蛋半径
        self.has_trapped = False     # 是否已吸入目标
        self.egg_scale =0.0          # 鸡蛋缩放（用于吸入会动效）
        self.peck_timer = 0.0        # 啄击计时
        self.peck_count = 0          # 啄击次数
        self.wobble = 0.0            # 鸡蛋晃动

        # 被困目标的位置记录（用于锁定目标）
        self._target_locked_pos: Optional[Tuple[float, float]] = None

    def update(self, dt: float):
        super().update(dt)

        # 吸入会动效（0.3秒）
        if self.timer < 0.3:
            self.egg_scale = self.timer / 0.3
        else:
            self.egg_scale = 1.0

        # 鸡蛋晃动
        self.wobble = math.sin(self.timer * 8) * (5 * (1.0 - self.egg_scale))

        # 啄击计时
        self.peck_timer += dt
        if self.peck_timer >= self.damage_interval and self.active:
            self.peck_timer = 0.0
            self.peck_count += 1

    def can_damage_target(self) -> bool:
        """检查是否可以造成伤害"""
        return self.peck_timer >= self.damage_interval and self.active

    def get_egg_rect(self) -> Tuple[float, float, float, float]:
        """获取鸡蛋碰撞框"""
        r = int(self.egg_radius * self.egg_scale)
        return (self.x - r, self.y - r * 1.3, r * 2, r * 2.6)

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        sx = self.x - camera_x
        sy = self.y

        # 绘制大公鸡（在鸡蛋旁边啄击）
        self._draw_chicken(surface, sx, sy)

        # 绘制鸡蛋（椭圆形）
        self._draw_egg(surface, sx, sy)

    def _draw_egg(self, surface: pygame.Surface, sx: float, sy: float):
        """绘制鸡蛋"""
        r = int(self.egg_radius * self.egg_scale)
        wobble_x = int(self.wobble)

        # 鸡蛋外壳（白色椭圆）
        egg_surf = pygame.Surface((r * 2 + 20, int(r * 2.6) + 20), pygame.SRCALPHA)
        cx = r + 10
        cy = int(r * 1.3) + 10

        # 外壳渐变效果
        pygame.draw.ellipse(egg_surf, (240, 235, 220), (10, 10, r * 2, int(r * 2.6)))
        pygame.draw.ellipse(egg_surf, (255, 252, 245), (15, 15, r * 2 - 10, int(r * 2.6) - 15))

        # 裂纹效果（鸡蛋内部有什么东西要出来）
        if self.timer > self.duration * 0.5:
            crack_alpha = int(150 * ((self.timer - self.duration * 0.5) / (self.duration * 0.5)))
            crack_surf = pygame.Surface((r * 2 + 20, int(r * 2.6) + 20), pygame.SRCALPHA)
            for i in range(3):
                crack_x = cx + int(math.sin(i * 2.5) * r * 0.4)
                crack_y = cy + int(i * r * 0.25)
                pygame.draw.circle(crack_surf, (80, 200, 80, crack_alpha),
                                 (crack_x, crack_y), 3 + i * 2)

        # 内部隐隐透出绿色（困住的敌人）
        inner_alpha = int(80 + math.sin(self.timer * 6) * 30)
        pygame.draw.ellipse(egg_surf, (50, 200, 80, inner_alpha),
                          (20, 25, r * 2 - 20, int(r * 2.6) - 35))

        surface.blit(egg_surf, (int(sx - cx + wobble_x), int(sy - cy)))

    def _draw_chicken(self, surface: pygame.Surface, sx: float, sy: float):
        """绘制大公鸡（在鸡蛋旁边啄击）"""
        # 啄击动画
        peck_extend = 0.0
        if self.peck_timer < 0.1:
            peck_extend = math.sin(self.peck_timer / 0.1 * math.pi) * 15
        wing_flap = math.sin(self.timer * 15) * 10

        # 鸡身体（棕色椭圆形）
        body_x = sx + 60
        body_y = sy - 20
        pygame.draw.ellipse(surface, (180, 120, 60),  # 棕色身体
                           (int(body_x - 25), int(body_y - 20), 50, 40))
        pygame.draw.ellipse(surface, (200, 140, 80),
                           (int(body_x - 22), int(body_y - 18), 44, 36))

        # 鸡头
        head_x = body_x - 20 - peck_extend
        head_y = body_y - 25
        pygame.draw.ellipse(surface, (200, 140, 80), (int(head_x - 12), int(head_y - 12), 24, 24))

        # 鸡冠（红色）
        pygame.draw.polygon(surface, (220, 30, 30), [
            (head_x - 5, head_y - 12),
            (head_x, head_y - 22),
            (head_x + 5, head_y - 12),
            (head_x + 3, head_y - 8),
            (head_x - 3, head_y - 8),
        ])
        pygame.draw.polygon(surface, (255, 50, 50), [
            (head_x + 2, head_y - 12),
            (head_x + 7, head_y - 20),
            (head_x + 10, head_y - 10),
        ])

        # 喙（黄色，向鸡蛋方向）
        beak_x = head_x - 12 - peck_extend
        beak_y = head_y + 2
        pygame.draw.polygon(surface, (255, 200, 0), [
            (beak_x - 8, beak_y),
            (beak_x, beak_y - 4),
            (beak_x, beak_y + 4),
        ])

        # 眼睛
        pygame.draw.circle(surface, (0, 0, 0), (int(head_x - 3), int(head_y - 2)), 3)
        pygame.draw.circle(surface, (255, 255, 255), (int(head_x - 4), int(head_y - 3)), 1)

        # 翅膀（扑动动画）
        wing_x = body_x + 5
        wing_y = body_y - 5
        pygame.draw.ellipse(surface, (160, 100, 50),
                           (int(wing_x - 10), int(wing_y - wing_flap - 10), 20, 25))

        # 尾巴（彩色羽毛）
        for i, fc in enumerate([(80, 180, 80), (60, 150, 60), (100, 200, 100)]):
            tail_x = body_x + 20
            tail_y = body_y - 15 + i * 8
            tail_angle = 30 + i * 15
            tail_len = 20 + i * 5
            tx = tail_x + math.cos(math.radians(tail_angle)) * tail_len
            ty = tail_y + math.sin(math.radians(tail_angle)) * tail_len
            pygame.draw.line(surface, fc, (int(tail_x), int(tail_y)), (int(tx), int(ty)), 3)

        # 爪子（站在鸡蛋旁边）
        leg_x1 = body_x - 10
        leg_x2 = body_x + 5
        leg_y = body_y + 18
        pygame.draw.line(surface, (255, 200, 0), (int(leg_x1), int(leg_y)), (int(leg_x1), int(leg_y + 15)), 2)
        pygame.draw.line(surface, (255, 200, 0), (int(leg_x2), int(leg_y)), (int(leg_x2), int(leg_y + 15)), 2)

        # 啄击粒子效果（每次啄击喷出羽毛/能量）
        if self.peck_timer < 0.1:
            for i in range(3):
                px = head_x - 5 + random.uniform(-5, 5)
                py = beak_y + random.uniform(-5, 5)
                puff = pygame.Surface((10, 10), pygame.SRCALPHA)
                pygame.draw.circle(puff, (200, 150, 50, 200), (5, 5), 4)
                surface.blit(puff, (int(px - 5), int(py - 5)))


# ══════════════════════════════════════════════════════════════
# 终极必杀技实体管理器
# ══════════════════════════════════════════════════════════════

class UltimateEntityManager:
    """终极必杀技实体管理器"""

    def __init__(self, screen_width: int, screen_height: int):
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.entities: List[UltimateEntity] = []

        # P1国旗（通常只有一个）
        self.p1_flags: List[P1NationalFlag] = []

        # P2激光（通常只有一个）
        self.p2_lasers: List[P2LaserBeam] = []

        # P3黑影（无上限）
        self.p3_shadows: List[P3ShadowClone] = []

        # P4鸡/鸡蛋（每使用一次召唤一个）
        self.p4_entities: List[P4Egg] = []

    # ── 实体创建 ────────────────────────────────────────────────

    def spawn_p1_flag(self, x: float, y: float, owner_id: int,
                     owner_is_p1: bool = True) -> P1NationalFlag:
        """生成P1五星红旗"""
        flag = P1NationalFlag(x, y, owner_id, self.screen_width, self.screen_height, owner_is_p1)
        self.entities.append(flag)
        self.p1_flags.append(flag)
        return flag

    def spawn_p2_laser(self, x: float, y: float, owner_id: int,
                       direction: int = 1,
                       owner: 'Fighter' = None) -> P2LaserBeam:
        """生成P2高能激光"""
        laser = P2LaserBeam(x, y, owner_id, self.screen_width, self.screen_height, direction, owner)
        self.entities.append(laser)
        self.p2_lasers.append(laser)
        return laser

    def spawn_p3_shadow(self, x: float, y: float, owner_id: int,
                        max_health: int, target_x: float,
                        target_facing_right: bool,
                        duration: float = 8.0) -> P3ShadowClone:
        """生成P3黑影（无上限）"""
        shadow = P3ShadowClone(x, y, owner_id, self.screen_width, self.screen_height,
                               max_health, target_x, target_facing_right, duration)
        self.entities.append(shadow)
        self.p3_shadows.append(shadow)
        return shadow

    def spawn_p4_egg(self, x: float, y: float, owner_id: int,
                     trapped_target_id: int, trap_duration: float = 5.0) -> P4Egg:
        """生成P4鸡蛋（召唤鸡+鸡蛋）"""
        egg = P4Egg(x, y, owner_id, self.screen_width, self.screen_height,
                    trapped_target_id, trap_duration)
        self.entities.append(egg)
        self.p4_entities.append(egg)
        return egg

    # ── 更新 ────────────────────────────────────────────────────

    def update(self, dt: float, player1: 'Fighter' = None, player2: 'Fighter' = None):
        """更新所有实体"""
        for entity in self.entities[:]:
            # 黑影需要传入两个玩家，自己判断谁该打
            if isinstance(entity, P3ShadowClone):
                entity.update(dt, player1, player2)
            else:
                entity.update(dt)

            # 检查是否存活（P3黑影用alive属性，其他用active）
            if isinstance(entity, P3ShadowClone):
                if not entity.alive:
                    self.entities.remove(entity)
                    if entity in self.p3_shadows:
                        self.p3_shadows.remove(entity)
            else:
                if not entity.active:
                    self.entities.remove(entity)
                    if isinstance(entity, P1NationalFlag):
                        if entity in self.p1_flags:
                            self.p1_flags.remove(entity)
                    elif isinstance(entity, P2LaserBeam):
                        if entity in self.p2_lasers:
                            self.p2_lasers.remove(entity)
                    elif isinstance(entity, P4Egg):
                        if entity in self.p4_entities:
                            self.p4_entities.remove(entity)

    def update_target_position(self, target_x: float, target_facing_right: bool):
        """更新所有P3黑影在目标前面的位置"""
        for shadow in self.p3_shadows:
            if target_facing_right:
                shadow.x = target_x + 80
            else:
                shadow.x = target_x - 80

    # ── 绘制 ────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        """绘制所有实体（按Z顺序）"""
        # 先绘制国旗（P1，在最底层）
        for flag in self.p1_flags:
            flag.draw(surface, camera_x)

        # 绘制激光（P2）
        for laser in self.p2_lasers:
            laser.draw(surface, camera_x)

        # 绘制鸡蛋（P4，在角色层下方）
        for egg in self.p4_entities:
            egg.draw(surface, camera_x)

        # 绘制黑影（P3，在角色层上方）
        for shadow in self.p3_shadows:
            shadow.draw(surface, camera_x)

    # ── 碰撞检测 ────────────────────────────────────────────────

    def check_p1_flag_damage(self, target_player_id: int,
                             target_x: float, target_y: float,
                             target_h: float) -> Tuple[bool, int]:
        """
        检查P1国旗是否命中目标
        返回: (是否命中, 伤害值)
        """
        for flag in self.p1_flags:
            if not flag.active:
                continue
            if not flag.can_damage_target(target_player_id):
                continue
            # 国旗全屏范围，只需要确认目标存在
            flag.record_damage_to(target_player_id)
            return (True, flag.damage)
        return (False, 0)

    def check_p2_laser_damage(self, target_player_id: int,
                              target_x: float, target_y: float,
                              target_h: float) -> Tuple[bool, int]:
        """
        检查P2激光是否命中目标
        返回: (是否命中, 伤害值)
        """
        for laser in self.p2_lasers:
            if not laser.active:
                continue
            if laser.timer < laser.charge_duration:
                continue  # 还在蓄力阶段
            if not laser.has_dealt_damage and laser.is_in_laser_row(target_y, target_h):
                laser.has_dealt_damage = True
                return (True, laser.damage)
        return (False, 0)

    # P3黑影的伤害由黑影实体自己在update()中直接处理，不需要额外的碰撞检测

    def check_p4_trap(self, target_player_id: int,
                       target_x: float, target_y: float,
                       target_h: float) -> Tuple[bool, int, Optional[P4Egg]]:
        """
        检查P4鸡蛋是否困住目标
        返回: (是否命中, 伤害值, 鸡蛋实例)
        """
        for egg in self.p4_entities:
            if not egg.active:
                continue
            egg_rect = egg.get_egg_rect()
            target_rect = (target_x - 35, target_y - target_h, 70, target_h)
            if (egg_rect[0] < target_rect[0] + target_rect[2] and
                egg_rect[0] + egg_rect[2] > target_rect[0] and
                egg_rect[1] < target_rect[1] + target_rect[3] and
                egg_rect[1] + egg_rect[3] > target_rect[1]):
                if egg.can_damage_target():
                    return (True, egg.damage, egg)
        return (False, 0, None)

    def apply_damage_to_shadow(self, shadow: P3ShadowClone, damage: int,
                               attacker_owner_id: int) -> bool:
        """对P3黑影造成伤害，返回是否死亡"""
        return shadow.take_damage(damage)

    def get_trapped_target_pos(self, egg: P4Egg) -> Optional[Tuple[float, float]]:
        """获取被困目标在鸡蛋中的位置"""
        return (egg.x, egg.y)

    def clear(self):
        """清除所有实体"""
        self.entities.clear()
        self.p1_flags.clear()
        self.p2_lasers.clear()
        self.p3_shadows.clear()
        self.p4_entities.clear()
