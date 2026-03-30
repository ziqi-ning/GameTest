# Item Drop System - 道具掉落系统

import pygame
import random
import os
import math
from dataclasses import dataclass, field
from typing import Optional, List, Set
from config import GROUND_Y, SCREEN_WIDTH, SCREEN_HEIGHT


# ── 数据类 ────────────────────────────────────────────────────────────────────

@dataclass
class NukeProjectile:
    """核弹投射物"""
    x: float
    y: float
    vel_y: float = 6.0
    active: bool = True
    owner_id: int = 0
    damage: int = 150
    knockback: float = 20.0
    trail_timer: float = 0.0


@dataclass
class GatlingBullet:
    """加特林子弹"""
    x: float
    y: float
    vel_x: float
    vel_y: float
    direction: int
    speed: float = 18.0
    active: bool = True
    owner_id: int = 0
    damage: int = 25
    lifetime: float = 0.0


@dataclass
class StaffEffect:
    """法杖特效"""
    effect_type: str  # "fire" | "wave" | "bomb"
    timer: float = 0.0
    duration: float = 1.5
    active: bool = True
    owner_id: int = 0
    damage: int = 80
    hit_targets: Set = field(default_factory=set)
    # 独立cd字典：key=唯一标识，value=上次命中时间
    hit_targets_cd: dict = field(default_factory=dict)
    screen_flash_timer: float = 0.0
    center_x: float = SCREEN_WIDTH // 2
    center_y: float = GROUND_Y - 80
    # 火焰专用：5根火柱的X坐标（初始化时固定随机一次，全特效期间不变）
    fire_cols: list = field(default_factory=list)


# ── ItemDrop ──────────────────────────────────────────────────────────────────

class ItemDrop:
    """单个掉落道具 - 天上掉落的宝箱"""

    ITEM_TYPES = [
        "coin_bag", "mana_bag", "health_bag",
        "nuke_launcher", "gatling", "staff_red", "staff_blue", "staff_green"
    ]
    WEAPON_TYPES = {"nuke_launcher", "gatling", "staff_red", "staff_blue", "staff_green"}
    ITEM_IMAGES: dict = {}  # class-level cache

    _FALLBACK_COLORS = {
        "coin_bag":      (255, 220, 50),
        "mana_bag":      (80, 80, 255),
        "health_bag":    (50, 220, 80),
        "nuke_launcher": (200, 80, 80),
        "gatling":       (150, 150, 150),
        "staff_red":     (255, 60, 60),
        "staff_blue":    (60, 120, 255),
        "staff_green":   (60, 200, 60),
    }

    # 宝箱颜色配置
    _CHEST_COLORS = {
        "coin_bag":      (255, 220, 50),   # 金色
        "mana_bag":      (80, 80, 255),    # 蓝色
        "health_bag":    (50, 220, 80),    # 绿色
        "nuke_launcher": (200, 80, 80),   # 红色
        "gatling":       (180, 180, 180),  # 银色
        "staff_red":     (255, 60, 60),    # 红色
        "staff_blue":    (60, 120, 255),   # 蓝色
        "staff_green":   (60, 200, 60),    # 绿色
    }

    def __init__(self, item_type: str, x: float):
        self.item_type = item_type
        self.x = x
        self.y = -48          # starts above screen (larger for chest)
        self.vel_y = 4.0      # pixels/frame downward
        self.landed = False
        self.lifetime = 0.0   # seconds since landing
        self.active = True
        self._bob_timer = 0.0
        self._chest_open = False
        self._chest_open_timer = 0.0
        self._sparkle_timer = 0.0

    def get_rect(self):
        """Returns (x, y, w, h) centered on self.x/self.y"""
        return (self.x - 24, self.y - 32, 48, 48)

    def update(self, dt: float, stage) -> None:
        """Apply gravity until landed; count lifetime after landing."""
        if not self.active:
            return

        self._sparkle_timer += dt

        if not self.landed:
            self.y += self.vel_y * 60 * dt

            landed_y = None
            if stage and hasattr(stage, 'platforms') and stage.platforms:
                for px, py, pw, ph in stage.platforms:
                    # 扩大碰撞范围：箱子宽度范围内都可以落到平台上
                    if px - 24 <= self.x <= px + pw + 24 and py - 40 <= self.y <= py + 40:
                        landed_y = py
                        break

            if landed_y is None and self.y >= GROUND_Y:
                landed_y = GROUND_Y

            if landed_y is not None:
                self.y = landed_y
                self.vel_y = 0.0
                self.landed = True
                self._chest_open = True
                self._chest_open_timer = 0.0
        else:
            self.lifetime += dt
            self._bob_timer += dt

    @classmethod
    def load_images(cls) -> None:
        """Load all item PNGs from assets/items/ into ITEM_IMAGES cache."""
        items_dir = os.path.join("assets", "items")
        for item_type in cls.ITEM_TYPES:
            if item_type in cls.ITEM_IMAGES:
                continue
            path = os.path.join(items_dir, f"{item_type}.png")
            try:
                img = pygame.image.load(path).convert_alpha()
                img = pygame.transform.scale(img, (32, 32))
                cls.ITEM_IMAGES[item_type] = img
            except Exception as e:
                print(f"[ItemDrop] Warning: could not load {path}: {e}")
                surf = pygame.Surface((32, 32), pygame.SRCALPHA)
                color = cls._FALLBACK_COLORS.get(item_type, (200, 200, 200))
                pygame.draw.rect(surf, color, (0, 0, 32, 32), border_radius=6)
                pygame.draw.rect(surf, (255, 255, 255), (0, 0, 32, 32), 2, border_radius=6)
                cls.ITEM_IMAGES[item_type] = surf

    def _draw_treasure_chest(self, surface: pygame.Surface, cx: int, cy: int) -> None:
        """绘制一个精美的宝箱"""
        item_color = self._CHEST_COLORS.get(self.item_type, (200, 200, 100))
        bob = math.sin(self._bob_timer * 3.0) * 2.0 if self.landed else 0.0
        chest_y = cy - 24 + bob

        # 浮动光效
        glow_alpha = int(80 + math.sin(self._sparkle_timer * 4) * 40)
        glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
        pygame.draw.ellipse(glow_surf, (*item_color, glow_alpha), (0, 0, 60, 60))
        surface.blit(glow_surf, (cx - 30, chest_y - 10))

        # 宝箱底座阴影
        shadow_surf = pygame.Surface((44, 12), pygame.SRCALPHA)
        pygame.draw.ellipse(shadow_surf, (0, 0, 0, 60), (0, 0, 44, 12))
        surface.blit(shadow_surf, (cx - 22, cy + 2))

        # 宝箱主体（箱身）
        body_color = (180, 120, 60)
        body_top_color = (210, 150, 80)
        pygame.draw.rect(surface, body_color, (cx - 20, chest_y, 40, 22), border_radius=2)
        pygame.draw.rect(surface, body_top_color, (cx - 20, chest_y, 40, 6), border_radius=2)

        # 宝箱盖（打开或关闭）
        if self._chest_open:
            lid_phase = min(self._chest_open_timer * 3, 1.0)
            lid_angle = -lid_phase * 80
            lid_points = [
                (cx - 20, chest_y),
                (cx + 20, chest_y),
                (cx + 18, chest_y - 14),
                (cx - 18, chest_y - 14),
            ]
            lid_surf = pygame.Surface((50, 50), pygame.SRCALPHA)
            lid_color = (160, 100, 50)
            lid_top = (200, 140, 80)
            for dx, dy in [(0, 0), (0, 1), (1, 0), (1, 1)]:
                pygame.draw.line(lid_surf, lid_color,
                               (10 - 18 + dx * 38, 25 - 14 + dy * 14),
                               (10 + 18 + dx * 2, 25 - 14 + dy * 14), 4)
                pygame.draw.line(lid_surf, lid_top,
                               (10 - 18, 25 - 14 + dy * 14),
                               (10 + 18, 25 - 14 + dy * 14), 2)
            pygame.draw.rect(lid_surf, (0, 0, 0, 0), (0, 0, 50, 50))
            surface.blit(lid_surf, (cx - 25, chest_y - 28))

            # 打开的盖子（简单三角形表示）
            open_offset = int(lid_phase * 15)
            pygame.draw.polygon(surface, body_top_color, [
                (cx - 20, chest_y),
                (cx + 20, chest_y),
                (cx + 22, chest_y - 18 + open_offset),
                (cx - 22, chest_y - 18 + open_offset),
            ])
        else:
            pygame.draw.rect(surface, body_top_color, (cx - 20, chest_y - 16, 40, 18), border_radius=3)

        # 金属边框
        pygame.draw.rect(surface, (100, 70, 30), (cx - 20, chest_y, 40, 22), 2, border_radius=2)
        if not self._chest_open:
            pygame.draw.rect(surface, (100, 70, 30), (cx - 20, chest_y - 16, 40, 18), 2, border_radius=3)

        # 锁扣
        lock_color = (220, 180, 50)
        pygame.draw.rect(surface, lock_color, (cx - 5, chest_y + 6, 10, 8), border_radius=1)
        pygame.draw.circle(surface, (180, 140, 30), (cx, chest_y + 12), 3)

        # 装饰铆钉
        rivet_color = (220, 180, 50)
        for rx in [-15, 15]:
            pygame.draw.circle(surface, rivet_color, (cx + rx, chest_y + 4), 2)
            if not self._chest_open:
                pygame.draw.circle(surface, rivet_color, (cx + rx, chest_y - 8), 2)

        # 物品发光（从箱子里发出的光芒）
        if self._chest_open:
            ray_count = 6
            ray_alpha = int(150 * max(0, 1.0 - self._chest_open_timer * 0.5))
            for i in range(ray_count):
                angle = (i / ray_count) * math.pi - math.pi / 2
                ray_len = 20 + math.sin(self._sparkle_timer * 8 + i) * 8
                end_x = cx + math.cos(angle) * ray_len
                end_y = chest_y - 8 + math.sin(angle) * ray_len * 0.5
                ray_surf = pygame.Surface((int(ray_len * 2 + 4), 6), pygame.SRCALPHA)
                pygame.draw.line(ray_surf, (*item_color, ray_alpha), (2, 3), (int(ray_len * 2 + 2), 3), 2)
                surface.blit(ray_surf, (int(cx - ray_len - 2), int(chest_y - 15)))

        # 星星装饰
        star_time = self._sparkle_timer * 3
        for i in range(3):
            sx = cx + math.cos(star_time + i * 2.1) * 16
            sy = chest_y - 20 + math.sin(star_time * 1.3 + i * 2.1) * 8
            star_alpha = int(200 * (0.5 + 0.5 * math.sin(star_time * 2 + i)))
            if star_alpha > 20:
                star_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                pygame.draw.circle(star_surf, (*item_color, star_alpha), (4, 4), 3)
                surface.blit(star_surf, (int(sx - 4), int(sy - 4)))

    def draw(self, surface: pygame.Surface) -> None:
        """Draw the treasure chest sprite."""
        if not self.active:
            return

        cx = int(self.x)
        cy = int(self.y)

        self._draw_treasure_chest(surface, cx, cy)


# ── ItemDropManager ───────────────────────────────────────────────────────────

class ItemDropManager:
    """道具掉落管理器"""

    MAX_ITEMS = 3
    SPAWN_INTERVAL_MIN = 5.0
    SPAWN_INTERVAL_MAX = 15.0
    ITEM_LIFETIME = 10.0
    STAGE_LEFT = 100
    STAGE_RIGHT = 1180

    def __init__(self):
        self.items: List[ItemDrop] = []
        self.spawn_timer: float = random.uniform(self.SPAWN_INTERVAL_MIN, self.SPAWN_INTERVAL_MAX)
        self.active: bool = False

        self.nuke_projectiles: List[NukeProjectile] = []
        self.gatling_bullets: List[GatlingBullet] = []
        self.staff_effects: List[StaffEffect] = []

        # 特效粒子（用于华丽武器特效）
        self.vfx_particles: List[dict] = []
        self.screen_flash: Optional[dict] = None
        self.nuke_explosions: List[dict] = []
        self.gatling_muzzle_flashes: List[dict] = []

        ItemDrop.load_images()

    def start(self) -> None:
        """Called when round enters FIGHT state. Idempotent."""
        self.active = True

    def stop(self) -> None:
        """Called when round ends; clears all items and weapon effects."""
        self.active = False
        self.items.clear()
        self.nuke_projectiles.clear()
        self.gatling_bullets.clear()
        self.staff_effects.clear()
        self.vfx_particles.clear()
        self.screen_flash = None
        self.nuke_explosions.clear()
        self.gatling_muzzle_flashes.clear()

    def _next_spawn_interval(self) -> float:
        return random.uniform(self.SPAWN_INTERVAL_MIN, self.SPAWN_INTERVAL_MAX)

    def _random_item_type(self) -> str:
        return random.choice(ItemDrop.ITEM_TYPES)

    def update(self, dt: float, stage, players: list) -> None:
        """Main update: spawn, physics, pickup, weapon effects."""
        if not self.active:
            return

        # 1. Tick spawn timer
        self.spawn_timer -= dt
        if self.spawn_timer <= 0 and len(self.items) < self.MAX_ITEMS:
            x = random.uniform(self.STAGE_LEFT, self.STAGE_RIGHT)
            item_type = self._random_item_type()
            self.items.append(ItemDrop(item_type, x))
            self.spawn_timer = self._next_spawn_interval()
        elif self.spawn_timer <= 0:
            self.spawn_timer = self._next_spawn_interval()

        # 2. Update each item
        for item in self.items:
            item.update(dt, stage)

        # 3. Remove expired or inactive items
        self.items = [i for i in self.items if i.active and i.lifetime < self.ITEM_LIFETIME]

        # 4. Check pickups
        self.check_pickups(players)

        # 5. Update weapon attack projectiles/effects
        self._update_weapon_effects(dt, stage, players)

        # 6. Update VFX particles
        self._update_vfx(dt)

        # 7. Update chest open animation
        for item in self.items:
            if item.landed and item._chest_open:
                item._chest_open_timer += dt

    def check_pickups(self, players: list) -> None:
        """For each landed item, find overlapping Players and award to closest."""
        from entities.player import Player

        for item in list(self.items):
            if not item.active or not item.landed:
                continue

            item_rect = item.get_rect()
            overlapping = []

            for p in players:
                if not isinstance(p, Player):
                    continue
                p_rect = p.get_rect()
                if self._rects_overlap(item_rect, p_rect):
                    overlapping.append(p)

            if not overlapping:
                continue

            winner = min(overlapping, key=lambda p: abs(p.x - item.x))
            self.apply_item(winner, item)
            item.active = False

    def _rects_overlap(self, r1, r2) -> bool:
        """AABB overlap check."""
        return (r1[0] < r2[0] + r2[2] and r1[0] + r1[2] > r2[0] and
                r1[1] < r2[1] + r2[3] and r1[1] + r1[3] > r2[1])

    def apply_item(self, player, item: ItemDrop) -> None:
        """Apply consumable effect or equip weapon."""
        t = item.item_type

        if t == "coin_bag":
            mm = getattr(player, 'minion_manager', None)
            if mm is not None:
                mm.coins += 50
            player.effect_manager.add_text("+50G", player.x, player.y - 160, (255, 220, 50), 32, 1.5)

        elif t == "mana_bag":
            player.special_energy = player.max_special
            player.effect_manager.add_text("MANA FULL", player.x, player.y - 160, (80, 150, 255), 32, 1.5)

        elif t == "health_bag":
            player.health = player.max_health
            player.effect_manager.add_text("HP FULL", player.x, player.y - 160, (50, 220, 80), 32, 1.5)

        elif t in ItemDrop.WEAPON_TYPES:
            player.equipped_weapon = t
            player.weapon_uses = 3
            weapon_names = {
                "nuke_launcher": "核弹发射器",
                "gatling":       "加特林",
                "staff_red":     "火焰法杖",
                "staff_blue":    "海浪法杖",
                "staff_green":   "炸弹法杖",
            }
            name = weapon_names.get(t, t)
            player.effect_manager.add_text(f"装备: {name}", player.x, player.y - 160, (255, 200, 80), 32, 1.5)

        # Pickup particle burst
        player.effect_manager.add_particle_burst(item.x, item.y - 16, 12, (255, 255, 150), 5.0, 1.5)

    def execute_weapon_attack(self, fighter, stage) -> None:
        """Dispatch weapon attack based on fighter.equipped_weapon."""
        if not getattr(fighter, 'equipped_weapon', None):
            return
        if getattr(fighter, 'weapon_uses', 0) <= 0:
            fighter.equipped_weapon = None
            return

        weapon = fighter.equipped_weapon
        fighter.weapon_uses -= 1

        if weapon == "nuke_launcher":
            self._fire_nuke(fighter, stage)
        elif weapon == "gatling":
            self._fire_gatling(fighter)
        elif weapon == "staff_red":
            self._fire_staff(fighter, "fire", 30)
        elif weapon == "staff_blue":
            self._fire_staff(fighter, "wave", 30)
        elif weapon == "staff_green":
            self._fire_staff(fighter, "bomb", 35)

        if fighter.weapon_uses <= 0:
            fighter.equipped_weapon = None
            fighter.effect_manager.add_text("武器耗尽!", fighter.x, fighter.y - 180, (200, 200, 200), 28, 1.2)

    def _fire_nuke(self, fighter, stage) -> None:
        """Spawn exactly 3 NukeProjectile at distinct random x positions."""
        positions = []
        attempts = 0
        while len(positions) < 3 and attempts < 50:
            x = random.uniform(self.STAGE_LEFT, self.STAGE_RIGHT)
            if all(abs(x - px) >= 50 for px in positions):
                positions.append(x)
            attempts += 1
        while len(positions) < 3:
            positions.append(self.STAGE_LEFT + (self.STAGE_RIGHT - self.STAGE_LEFT) * len(positions) / 3)

        for x in positions:
            self.nuke_projectiles.append(NukeProjectile(
                x=x, y=-32, vel_y=6.0, active=True,
                owner_id=fighter.player_id, damage=150, knockback=20.0, trail_timer=0.0
            ))

        # 华丽预告特效：巨大红色警告标记 + 文字
        fighter.effect_manager.add_text("核弹来袭!", fighter.x, fighter.y - 200, (255, 50, 50), 52, 2.5)
        fighter.effect_manager.add_text("警告!", fighter.x, fighter.y - 150, (255, 220, 50), 36, 2.0)
        fighter.effect_manager.add_particle_burst(fighter.x, fighter.y - 60, 50, (255, 150, 50), 15.0, 12.0)
        fighter.effect_manager.add_ring(fighter.x, fighter.y - 60, 80, (255, 100, 50), 1.2)

        # 强烈屏幕预警（红色闪烁 + 震动）
        self.screen_flash = {"timer": 0.5, "color": (255, 30, 0), "alpha": 120, "type": "nuke"}
        # 存储预警数据用于绘制红色危险区
        self.nuke_warning_zones = [{"x": px, "timer": 0.0} for px in positions]

    def _fire_gatling(self, fighter) -> None:
        """Spawn 3 parallel lanes of gatling bullets for focused firepower."""
        direction = 1 if fighter.facing_right else -1

        # 三路平行弹幕（上路、中路、下路）
        lanes = [
            {"offset_y": -50, "speed": 22.0},   #上路
            {"offset_y": 0, "speed": 25.0},      #中路（最快最中间）
            {"offset_y": 50, "speed": 22.0},    #下路
        ]

        bullets_per_lane = 35
        for lane in lanes:
            for i in range(bullets_per_lane):
                # 子弹之间有微小散布，模拟连续射击
                offset_y = lane["offset_y"] + random.uniform(-8, 8)
                offset_x = random.uniform(-5, 15) * direction
                speed = lane["speed"] + random.uniform(-2, 2)

                self.gatling_bullets.append(GatlingBullet(
                    x=fighter.x + direction * 30 + offset_x,
                    y=fighter.y - 80 + offset_y,
                    vel_x=direction * speed,
                    vel_y=random.uniform(-0.5, 0.5),
                    direction=direction,
                    speed=speed,
                    active=True,
                    owner_id=fighter.player_id,
                    damage=25,
                    lifetime=0.0
                ))

        # 枪口闪光（三路各几个）
        for lane in lanes:
            for i in range(8):
                flash_offset_y = lane["offset_y"] + random.uniform(-5, 5)
                self.gatling_muzzle_flashes.append({
                    "x": fighter.x + direction * 30,
                    "y": fighter.y - 80 + flash_offset_y,
                    "timer": 0.1,
                    "direction": direction
                })

        # 华丽特效
        fighter.effect_manager.add_text("加特林!", fighter.x, fighter.y - 200, (255, 220, 80), 48, 2.0)
        fighter.effect_manager.add_particle_burst(
            fighter.x + direction * 50, fighter.y - 80,
            40, (255, 200, 80), 15.0, 10.0
        )
        fighter.effect_manager.add_ring(
            fighter.x + direction * 40, fighter.y - 80,
            80, (255, 220, 80), 1.0
        )

        # 屏幕闪黄光
        self.screen_flash = {"timer": 0.2, "color": (255, 200, 50), "alpha": 80, "type": "gatling"}

    def _fire_staff(self, fighter, effect_type: str, damage: int) -> None:
        """Spawn staff effect at random position."""
        # 随机位置（不在屏幕边缘）
        cx = random.uniform(SCREEN_WIDTH * 0.2, SCREEN_WIDTH * 0.8)
        cy = random.uniform(GROUND_Y - 200, GROUND_Y - 50)

        # 火焰法杖：5根火柱固定随机位置（特效创建时一次性决定，不随时间变化）
        fire_cols = [random.uniform(SCREEN_WIDTH * 0.08, SCREEN_WIDTH * 0.92) for _ in range(5)] if effect_type == "fire" else []

        # 全屏攻击：一个大的特效覆盖整个场景
        self.staff_effects.append(StaffEffect(
            effect_type=effect_type,
            timer=0.0, duration=1.5,
            active=True,
            owner_id=fighter.player_id,
            damage=damage,
            hit_targets=set(),
            hit_targets_cd={},
            screen_flash_timer=0.0,
            center_x=cx,
            center_y=cy,
            fire_cols=fire_cols
        ))

        # 华丽特效
        colors = {"fire": (255, 100, 50), "wave": (50, 150, 255), "bomb": (100, 220, 80)}
        color = colors.get(effect_type, (255, 255, 255))
        fighter.effect_manager.add_text("法杖攻击!", fighter.x, fighter.y - 180, color, 40, 2.0)
        fighter.effect_manager.add_particle_burst(fighter.x, fighter.y - 60, 40, color, 12.0, 8.0)
        fighter.effect_manager.add_ring(fighter.x, fighter.y - 60, 100, color, 1.0)

        # 屏幕闪光
        flash_colors = {"fire": (255, 50, 0), "wave": (0, 100, 255), "bomb": (50, 200, 50)}
        flash_color = flash_colors.get(effect_type, (200, 200, 200))
        self.screen_flash = {"timer": 0.25, "color": flash_color, "alpha": 60, "type": "staff"}

    def _apply_staff_hit(self, target, effect, hit_x: float, color: tuple, damage: int):
        """统一处理法杖命中效果（fighter和小兵通用）"""
        if hasattr(target, 'health'):
            # Fighter 路径
            target.health = max(0, target.health - damage)
            target.vel_x = 6 * (1 if target.x > hit_x else -1)
            if hasattr(target, 'effect_manager') and target.effect_manager:
                target.effect_manager.add_text(
                    f"-{damage}", target.x, target.y - 120,
                    color, 50, 1.5
                )
                target.effect_manager.add_particle_burst(
                    target.x, target.y - 80, 15, color, 10.0, 6.0
                )
            if hasattr(target, 'screen_shake'):
                shake_map = {"fire": 10, "wave": 8, "bomb": 6}
                target.screen_shake = shake_map.get(effect.effect_type, 8)
        elif hasattr(target, 'take_damage'):
            # 小兵路径
            target.take_damage(damage)

    def _add_nuke_explosion(self, x: float, y: float, owner_id: int) -> None:
        """Add华丽的核爆特效"""
        self.nuke_explosions.append({
            "x": x, "y": y,
            "timer": 0.0,
            "duration": 1.2,
            "owner_id": owner_id,
            "particles": []
        })
        # 添加爆炸粒子
        for _ in range(60):
            angle = random.uniform(0, math.pi * 2)
            speed = random.uniform(3.0, 15.0)
            color = random.choice([
                (255, 200, 50), (255, 100, 20), (255, 50, 0),
                (255, 255, 100), (200, 80, 20)
            ])
            self.vfx_particles.append({
                "x": x, "y": y,
                "vx": math.cos(angle) * speed,
                "vy": math.sin(angle) * speed,
                "color": color,
                "size": random.uniform(4.0, 12.0),
                "lifetime": random.uniform(0.5, 1.5),
                "gravity": 2.0
            })

    def _spawn_gatling_trail(self, x: float, y: float, color: tuple) -> None:
        """Add枪口轨迹特效"""
        self.vfx_particles.append({
            "x": x, "y": y,
            "vx": random.uniform(-1.0, 1.0),
            "vy": random.uniform(-1.0, 1.0),
            "color": color,
            "size": random.uniform(2.0, 5.0),
            "lifetime": 0.3,
            "gravity": 0.0
        })

    def _update_vfx(self, dt: float) -> None:
        """Update visual effect particles and flashes."""
        # Update VFX particles
        for p in list(self.vfx_particles):
            p["lifetime"] -= dt
            if p["lifetime"] <= 0:
                self.vfx_particles.remove(p)
                continue
            p["x"] += p["vx"] * 60 * dt
            p["y"] += p["vy"] * 60 * dt
            if "gravity" in p:
                p["vy"] += p["gravity"] * 60 * dt

        # Update muzzle flashes
        for mf in list(self.gatling_muzzle_flashes):
            mf["timer"] -= dt
            if mf["timer"] <= 0:
                self.gatling_muzzle_flashes.remove(mf)

        # Update screen flash
        if self.screen_flash:
            self.screen_flash["timer"] -= dt
            if self.screen_flash["timer"] <= 0:
                self.screen_flash = None

    def _update_weapon_effects(self, dt: float, stage, players: list) -> None:
        """Update nuke projectiles, gatling bullets, and staff effects."""
        all_fighters = list(players)
        all_minions = []
        for p in players:
            mm = getattr(p, 'minion_manager', None)
            if mm:
                all_minions.extend([m for m in mm.minions if m.alive])

        # ── Nuke projectiles ──
        for nuke in list(self.nuke_projectiles):
            if not nuke.active:
                continue
            nuke.y += nuke.vel_y * 60 * dt
            nuke.trail_timer += dt

            # 添加尾迹粒子
            if nuke.trail_timer > 0.03:
                nuke.trail_timer = 0.0
                self.vfx_particles.append({
                    "x": nuke.x + random.uniform(-4, 4),
                    "y": nuke.y,
                    "vx": random.uniform(-1.0, 1.0),
                    "vy": -random.uniform(0.5, 2.0),
                    "color": (255, 150, 50),
                    "size": random.uniform(3.0, 7.0),
                    "lifetime": 0.4,
                    "gravity": -1.0
                })

            landed = False
            land_y = None

            if stage and hasattr(stage, 'platforms') and stage.platforms:
                for px, py, pw, ph in stage.platforms:
                    if px <= nuke.x <= px + pw and nuke.y >= py - 8 and nuke.y <= py + 20:
                        land_y = py
                        landed = True
                        break

            if not landed and nuke.y >= GROUND_Y:
                land_y = GROUND_Y
                landed = True

            if landed:
                nuke.active = False
                self._add_nuke_explosion(nuke.x, land_y, nuke.owner_id)

                for fighter in all_fighters:
                    if fighter.player_id == nuke.owner_id:
                        continue
                    dist = ((fighter.x - nuke.x) ** 2 + (fighter.y - nuke.y) ** 2) ** 0.5
                    if dist <= 120:
                        dmg = int(nuke.damage * (1.0 - dist / 200))
                        fighter.health = max(0, fighter.health - dmg)
                        fighter.vel_x = nuke.knockback * (1 if fighter.x > nuke.x else -1)
                        fighter.effect_manager.add_text(
                            f"-{dmg}", fighter.x, fighter.y - 120,
                            (255, 80, 80), 52, 1.8
                        )
                        fighter.screen_shake = 15
                        # 核弹命中特效
                        if hasattr(fighter, 'screen_effects'):
                            fighter.screen_effects.weapon_nuke_impact()

                for minion in all_minions:
                    if minion.owner_id == nuke.owner_id:
                        continue
                    dist = ((minion.x - nuke.x) ** 2 + (minion.y - nuke.y) ** 2) ** 0.5
                    if dist <= 120:
                        minion.take_damage(int(nuke.damage * (1.0 - dist / 200)))

        self.nuke_projectiles = [n for n in self.nuke_projectiles if n.active]

        # ── Gatling bullets (continuous fire, hit every frame while in range) ──
        gatling_color = (255, 220, 80)
        for bullet in list(self.gatling_bullets):
            if not bullet.active:
                continue
            bullet.lifetime += dt
            bullet.x += bullet.vel_x * 60 * dt
            bullet.y += bullet.vel_y * 60 * 60 * dt

            # 添加子弹轨迹
            if random.random() < 0.4:
                self.vfx_particles.append({
                    "x": bullet.x, "y": bullet.y,
                    "vx": -bullet.vel_x * 0.3 + random.uniform(-0.5, 0.5),
                    "vy": random.uniform(-0.5, 0.5),
                    "color": (255, 180, 50),
                    "size": random.uniform(2.0, 4.0),
                    "lifetime": 0.15,
                    "gravity": 0.0
                })

            # Out of bounds
            if bullet.x < self.STAGE_LEFT - 50 or bullet.x > self.STAGE_RIGHT + 50:
                bullet.active = False
                continue

            # Hit check against opponents
            bullet_rect = (bullet.x - 8, bullet.y - 8, 16, 16)
            for fighter in all_fighters:
                if fighter.player_id == bullet.owner_id:
                    continue
                hurtbox = fighter.get_hurtbox_rect()
                if self._rects_overlap(bullet_rect, hurtbox):
                    fighter.health = max(0, fighter.health - bullet.damage)
                    fighter.vel_x = 4 * bullet.direction
                    fighter.effect_manager.add_text(
                        f"-{bullet.damage}", fighter.x, fighter.y - 120,
                        (255, 180, 50), 30, 0.8
                    )
                    fighter.screen_shake = 2
                    # 命中粒子
                    for _ in range(4):
                        self.vfx_particles.append({
                            "x": bullet.x, "y": bullet.y,
                            "vx": random.uniform(-3.0, 3.0),
                            "vy": random.uniform(-3.0, 1.0),
                            "color": gatling_color,
                            "size": random.uniform(2.0, 4.0),
                            "lifetime": 0.2,
                            "gravity": 2.0
                        })
                    bullet.active = False
                    break

        self.gatling_bullets = [b for b in self.gatling_bullets if b.active]

        # ── Staff effects: 特效在哪里，伤害就在哪里 ────────────────────────────
        for effect in list(self.staff_effects):
            if not effect.active:
                continue
            effect.timer += dt
            effect.screen_flash_timer += dt
            t = effect.timer

            staff_colors = {"fire": (255, 80, 20), "wave": (50, 150, 255), "bomb": (80, 220, 60)}
            color = staff_colors.get(effect.effect_type, (255, 255, 255))
            cx, cy = effect.center_x, effect.center_y

            # ══ 火焰法杖：固定5根火柱，伤害区域与视觉完全一致 ══════════════
            # 视觉：base_x = col_x + sin(t*3+i*0.8)*20，外层火焰宽24px+oscill，中层16px
            #       火焰底部在 GROUND_Y-80，向上覆盖约80px（角色大腿以下区域）
            #       角色hurtbox站立时：GROUND_Y-150（头）到 GROUND_Y（脚）
            #       有效重叠区：GROUND_Y-150 到 GROUND_Y-80
            if effect.effect_type == "fire":
                if t < 0.3:
                    pass  # 预警阶段不造成伤害
                else:
                    for target in all_fighters + all_minions:
                        target_pid = getattr(target, 'player_id', getattr(target, 'owner_id', None))
                        if target_pid == effect.owner_id:
                            continue
                        target_id = target.player_id if hasattr(target, 'player_id') else id(target)
                        # 火焰覆盖角色下半身：GROUND_Y-160 到 GROUND_Y-20
                        if target.y < GROUND_Y - 160 or target.y > GROUND_Y - 20:
                            continue
                        for i, col_x in enumerate(effect.fire_cols):
                            base_x = col_x + math.sin(t * 3 + i * 0.8) * 20
                            # 外层火焰宽24px+oscill±5，中层16px，角色半宽~20px
                            if abs(target.x - base_x) < 38:
                                # 用索引i作为key（避免浮点col_x精度问题），每柱独立冷却
                                cd_key = f"col{i}_{target_id}"
                                last = effect.hit_targets_cd.get(cd_key, -999.0)
                                if t - last >= 1.5:  # 每柱每1.5s只命中一次
                                    effect.hit_targets_cd[cd_key] = t
                                    effect.hit_targets.add(target_id)
                                    self._apply_staff_hit(target, effect, base_x, color, effect.damage)
                    if t >= effect.duration:
                        effect.active = False
                    continue

            # ══ 海啸法杖：波浪横扫伤害区域与视觉完全一致 ══════════════════
            # 视觉公式：wave_x = SCREEN_WIDTH+100 - (t-0.3)*(SCREEN_WIDTH+400)/1.2
            #       5层波浪每层60px，共覆盖 wave_x-240 到 wave_x（向后延伸）
            #       波浪从 GROUND_Y-80 画到屏幕底部
            elif effect.effect_type == "wave":
                if t < 0.3:
                    pass  # 预警阶段不造成伤害（与视觉预警一致）
                else:
                    # 波前公式与绘制完全一致
                    wave_x = (SCREEN_WIDTH + 100) - (t - 0.3) * (SCREEN_WIDTH + 400) / 1.2
                    # 波浪向右横扫区域：wave_x-350（尾巴）到 wave_x+40（波峰）
                    wave_right = wave_x + 40
                    wave_left = wave_x - 350

                    for target in all_fighters + all_minions:
                        target_pid = getattr(target, 'player_id', getattr(target, 'owner_id', None))
                        if target_pid == effect.owner_id:
                            continue
                        target_id = target.player_id if hasattr(target, 'player_id') else id(target)
                        last_hit = effect.hit_targets_cd.get(target_id, -999.0)
                        if t - last_hit < 0.4:
                            continue
                        # Y轴：波浪从 GROUND_Y-80 涌起，向下覆盖约300px
                        if wave_left < target.x < wave_right and GROUND_Y - 80 < target.y < GROUND_Y + 350:
                            effect.hit_targets_cd[target_id] = t
                            effect.hit_targets.add(target_id)
                            self._apply_staff_hit(target, effect, target.x, color, effect.damage)
                    if t >= effect.duration:
                        effect.active = False
                    continue

            # ── 毒雾法杖：圆形扩散范围，精确跟随视觉半径 ──────────────────
            else:  # bomb
                if t < 0.2:
                    pass  # 初始展开期不造成伤害
                else:
                    progress = min((t - 0.2) / (effect.duration - 0.2), 1.0)
                    # 毒雾半径：40 → 250像素（视觉扩散速度）
                    mist_radius = 40 + progress * 210
                    for target in all_fighters + all_minions:
                        target_pid = getattr(target, 'player_id', getattr(target, 'owner_id', None))
                        if target_pid == effect.owner_id:
                            continue
                        target_id = target.player_id if hasattr(target, 'player_id') else id(target)

                        dist = math.hypot(target.x - cx, target.y - cy)
                        if dist < mist_radius:
                            # 目标在毒雾内时才设置cd，离开后cd清零（可重新被击中）
                            last_hit = effect.hit_targets_cd.get(target_id, -999.0)
                            if t - last_hit >= 0.5:
                                effect.hit_targets_cd[target_id] = t
                                effect.hit_targets.add(target_id)
                                self._apply_staff_hit(target, effect, cx, color, effect.damage)
                        else:
                            # 目标离开毒雾范围后清除cd，允许下次重新命中
                            effect.hit_targets_cd.pop(target_id, None)

                    if t >= effect.duration:
                        effect.active = False
                    continue

            if t >= effect.duration:
                effect.active = False

        self.staff_effects = [e for e in self.staff_effects if e.active]

    def draw(self, surface: pygame.Surface) -> None:
        """Draw all active items and weapon attack visuals."""
        # Draw items (treasure chests)
        for item in self.items:
            if item.active:
                item.draw(surface)

        # Draw nuke warning zones (danger indicators on ground)
        if hasattr(self, 'nuke_warning_zones'):
            for zone in list(self.nuke_warning_zones):
                zone["timer"] += 0.016
                if zone["timer"] > 1.5:
                    self.nuke_warning_zones.remove(zone)
                    continue
                # 危险区域标记（地面上的红色警告圈）
                pulse = abs(math.sin(zone["timer"] * 15))
                warn_radius = 100 + pulse * 20
                warn_alpha = int(150 * (1.0 - zone["timer"] / 1.5))
                # 地面危险圆圈
                pygame.draw.circle(surface, (255, 50, 0, warn_alpha // 2),
                                 (int(zone["x"]), int(GROUND_Y)), int(warn_radius), 3)
                pygame.draw.circle(surface, (255, 100, 0, warn_alpha // 3),
                                 (int(zone["x"]), int(GROUND_Y)), int(warn_radius * 0.6), 2)
                # 警告三角
                warning_surf = pygame.Surface((40, 35), pygame.SRCALPHA)
                pygame.draw.polygon(warning_surf, (255, 200, 0, warn_alpha),
                                  [(20, 0), (0, 35), (40, 35)])
                surface.blit(warning_surf, (int(zone["x"] - 20), int(GROUND_Y - 100 + pulse * 5)))

        # Draw nuke projectiles
        for nuke in self.nuke_projectiles:
            if nuke.active:
                # 核弹主体（更大更醒目）
                pygame.draw.circle(surface, (200, 60, 20), (int(nuke.x), int(nuke.y)), 16)
                pygame.draw.circle(surface, (255, 80, 40), (int(nuke.x), int(nuke.y)), 12)
                pygame.draw.circle(surface, (255, 220, 80), (int(nuke.x), int(nuke.y)), 7)
                pygame.draw.circle(surface, (255, 255, 200), (int(nuke.x), int(nuke.y)), 3)
                # 危险标记
                pygame.draw.circle(surface, (255, 255, 255), (int(nuke.x), int(nuke.y)), 16, 2)

        # Draw gatling bullets
        for bullet in self.gatling_bullets:
            if bullet.active:
                # 子弹主体
                pygame.draw.circle(surface, (255, 220, 80), (int(bullet.x), int(bullet.y)), 5)
                pygame.draw.circle(surface, (255, 255, 200), (int(bullet.x), int(bullet.y)), 3)
                # 发光尾迹
                glow_surf = pygame.Surface((14, 14), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 180, 50, 100), (7, 7), 7)
                surface.blit(glow_surf, (int(bullet.x - 7), int(bullet.y - 7)))

        # Draw staff effects (full screen overlay)
        for effect in self.staff_effects:
            if not effect.active:
                continue

            progress = effect.timer / effect.duration
            pulse = abs(math.sin(effect.timer * 8)) * 0.3 + 0.7
            alpha = int(120 * pulse * (1.0 - progress * 0.5))

            if effect.effect_type == "fire":
                self._draw_fire_storm(surface, effect, progress, pulse, alpha)

            elif effect.effect_type == "wave":
                self._draw_tsunami_wave(surface, effect, progress, pulse, alpha)

            elif effect.effect_type == "bomb":
                self._draw_poison_mist(surface, effect, progress, pulse, alpha)

        # Draw VFX particles
        for p in self.vfx_particles:
            alpha = int(255 * (p["lifetime"] / 1.5)) if p["lifetime"] < 1.5 else 255
            size = int(p["size"] * min(1.0, p["lifetime"] / 0.3))
            if size > 0 and alpha > 0:
                temp_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
                pygame.draw.circle(temp_surf, (*p["color"], min(255, alpha)), (size, size), size)
                surface.blit(temp_surf, (int(p["x"] - size), int(p["y"] - size)))

        # Draw muzzle flashes
        for mf in self.gatling_muzzle_flashes:
            ratio = max(0.0, mf["timer"] / 0.08)
            flash_alpha = max(0, min(255, int(255 * ratio)))
            flash_size = max(1, int(15 * ratio))
            surf_sz = flash_size * 2 + 4
            flash_surf = pygame.Surface((surf_sz, surf_sz), pygame.SRCALPHA)
            pygame.draw.circle(flash_surf, (255, 220, 100, flash_alpha), (flash_size + 2, flash_size + 2), flash_size)
            pygame.draw.circle(flash_surf, (255, 255, 200, flash_alpha), (flash_size + 2, flash_size + 2), max(1, flash_size // 2))
            surface.blit(flash_surf, (int(mf["x"] - flash_size - 2), int(mf["y"] - flash_size - 2)))

        # Draw nuke explosions
        for exp in list(self.nuke_explosions):
            exp["timer"] += 0.016
            progress = exp["timer"] / exp["duration"]
            if progress >= 1.0:
                self.nuke_explosions.remove(exp)
                continue

            self._draw_nuke_mushroom_cloud(surface, exp, progress)

        # Draw gatling bullets (enhanced: dense bullets with shell casings)
        for bullet in self.gatling_bullets:
            if bullet.active:
                # 子弹主体（黄橙发光弹）
                pygame.draw.circle(surface, (255, 220, 80), (int(bullet.x), int(bullet.y)), 6)
                pygame.draw.circle(surface, (255, 255, 200), (int(bullet.x), int(bullet.y)), 4)
                pygame.draw.circle(surface, (255, 255, 255), (int(bullet.x), int(bullet.y)), 2)
                # 发光尾迹
                glow_surf = pygame.Surface((18, 18), pygame.SRCALPHA)
                pygame.draw.circle(glow_surf, (255, 180, 50, 120), (9, 9), 9)
                surface.blit(glow_surf, (int(bullet.x - 9), int(bullet.y - 9)))

        # Draw muzzle flashes (enhanced: big gun fire)
        for mf in self.gatling_muzzle_flashes:
            ratio = max(0.0, mf["timer"] / 0.08)
            flash_alpha = max(0, min(255, int(255 * ratio)))
            flash_size = max(1, int(20 * ratio))
            surf_sz = flash_size * 4 + 10
            flash_surf = pygame.Surface((surf_sz, surf_sz), pygame.SRCALPHA)
            # 外层火焰（红色）
            pygame.draw.circle(flash_surf, (255, 100, 0, flash_alpha), (flash_size * 2 + 5, flash_size * 2 + 5), flash_size * 2)
            # 中层火焰（橙色）
            pygame.draw.circle(flash_surf, (255, 180, 50, flash_alpha), (flash_size * 2 + 5, flash_size * 2 + 5), flash_size)
            # 内层火焰（白色）
            pygame.draw.circle(flash_surf, (255, 255, 200, flash_alpha), (flash_size * 2 + 5, flash_size * 2 + 5), max(1, flash_size // 2))
            surface.blit(flash_surf, (int(mf["x"] - flash_size * 2 - 5), int(mf["y"] - flash_size * 2 - 5)))

            # 枪口火花（spark_alpha 避免负数）
            spark_alpha = max(0, int(flash_alpha * 0.5))
            for _ in range(3):
                spark_x = mf["x"] + random.randint(-15, 15) * mf["direction"]
                spark_y = mf["y"] + random.randint(-10, 10)
                pygame.draw.circle(surface, (255, 200, 100, spark_alpha),
                                 (int(spark_x), int(spark_y)), random.randint(2, 4))

    # ════════════════════════════════════════════════════════════════════════
    # 武器专属华丽特效绘制方法
    # ════════════════════════════════════════════════════════════════════════

    def _draw_fire_storm(self, surface, effect, progress, pulse, alpha):
        """红色法杖 - 火焰风暴：从天而降的火柱 + 火焰漩涡"""
        t = effect.timer
        cx, cy = effect.center_x, effect.center_y

        # 淡化版背景（只在底部有微弱的橙光）
        for y in range(int(GROUND_Y), SCREEN_HEIGHT, 15):
            wave_offset = math.sin(t * 4 + y * 0.05) * 10
            fade = max(0, 1.0 - y / SCREEN_HEIGHT) * 0.3
            alpha_y = int(40 * fade)
            if alpha_y > 3:
                pygame.draw.rect(surface, (100, 30, 0, alpha_y),
                               (int(wave_offset), y, SCREEN_WIDTH, 10))

        # 火焰光柱从天而降（5根，各自有独立的随机X坐标）
        col_xs = effect.fire_cols
        for i in range(5):
            x = col_xs[i]
            base_x = x + math.sin(t * 3 + i * 0.8) * 20
            phase = (t + i * 0.15) % 1.2
            if phase < 0.4:
                flame_y = GROUND_Y - 50 - phase * 1.5 * 200
                flame_h = int(80 + math.sin(t * 10 + i) * 20)
            else:
                flame_y = GROUND_Y - 80
                flame_h = int(60 + math.sin(t * 8 + i) * 15)

            # 外层火焰（暗红，半透明）
            pygame.draw.rect(surface, (150, 20, 0, int(alpha * 0.4)),
                           (int(base_x - 12 + math.sin(t * 6 + i) * 5),
                            int(flame_y), 24, flame_h))
            # 中层火焰（橙色）
            pygame.draw.rect(surface, (200, 50, 0, int(alpha * 0.5)),
                           (int(base_x - 8), int(flame_y + 5), 16, flame_h - 15))
            # 核心火焰（亮黄）
            pygame.draw.rect(surface, (255, 150, 30, int(alpha * 0.4)),
                           (int(base_x - 4), int(flame_y + 10), 8, flame_h - 25))

        # 中心火焰漩涡
        for i in range(12):
            angle = t * 3 + i * (math.pi / 6)
            radius = 40 + i * 8
            px = cx + math.cos(angle) * radius
            py = cy + math.sin(angle) * radius * 0.3
            size = int(5 + i * 0.3)
            color_choice = [(255, 180, 30), (200, 80, 0), (150, 40, 0)]
            color = color_choice[i % 3]
            pygame.draw.circle(surface, (*color, int(alpha * 0.35)),
                             (int(px), int(py)), size)

        # 少量火星（只在火焰区域）
        for _ in range(5):
            spark_x = cx + random.randint(-150, 150)
            spark_y = random.randint(int(GROUND_Y - 200), int(GROUND_Y))
            spark_size = random.randint(1, 3)
            pygame.draw.circle(surface, (255, 150, 30, int(alpha * 0.3)),
                             (spark_x, spark_y), spark_size)

    def _draw_tsunami_wave(self, surface, effect, progress, pulse, alpha):
        """蓝色法杖 - 海啸波浪：巨浪从左向右推进"""
        t = effect.timer
        cx, cy = effect.center_x, effect.center_y

        # 预警闪烁（海啸来临前）
        if t < 0.3:
            flash_alpha = int(80 * (0.3 - t) / 0.3)
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((0, 50, 150, flash_alpha))
            surface.blit(flash_surf, (0, 0))

        # 波前从右向左横扫，波前实时x坐标（与伤害逻辑完全一致）
        wave_x = SCREEN_WIDTH + 100 - (t - 0.3) * (SCREEN_WIDTH + 400) / 1.2

        # 多层海浪（从后到前依次推进）
        for wave_i in range(5):
            wave_depth = wave_i * 60
            wave_front_x = wave_x - wave_depth
            wave_alpha = int(alpha * (1.0 - wave_i * 0.15))

            if wave_front_x > SCREEN_WIDTH + 100:
                continue

            # 波浪曲线（用多个矩形模拟曲线）
            for y in range(int(GROUND_Y - 80), SCREEN_HEIGHT, 12):
                wave_height = 60 + math.sin(t * 6 + y * 0.1 + wave_i) * 20
                wave_top = y - wave_height

                # 波浪颜色渐变（深处蓝色，表面亮蓝）
                depth_ratio = (y - (GROUND_Y - 80)) / (SCREEN_HEIGHT - GROUND_Y + 80)
                r = int(20 + 40 * depth_ratio)
                g = int(120 + 80 * depth_ratio)
                b = int(200 + 55 * depth_ratio)

                # 波浪主体
                points = []
                for wx in range(max(0, int(wave_front_x) - 50), min(SCREEN_WIDTH, int(wave_front_x) + 300), 8):
                    wy = wave_top + math.sin(wx * 0.02 + t * 4 + y * 0.05) * 15
                    points.append((wx, wy))

                if len(points) > 2:
                    alpha_mult = int(wave_alpha * (1.0 - depth_ratio * 0.5))
                    # 画波浪带
                    for j in range(len(points) - 1):
                        pygame.draw.line(surface, (r, g, b, alpha_mult),
                                       points[j], points[j + 1], 6)

            # 浪花飞溅
            if wave_i == 0 and wave_front_x > 0 and wave_front_x < SCREEN_WIDTH:
                for _ in range(5):
                    splash_x = int(wave_front_x + random.randint(-20, 50))
                    splash_y = int(GROUND_Y - 50 - random.randint(0, 100))
                    splash_size = random.randint(3, 8)
                    pygame.draw.circle(surface, (150, 200, 255, int(alpha * 0.4)),
                                     (splash_x, splash_y), splash_size)

        # 背景海面
        bg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        bg_surf.fill((0, 30, 100, int(30 * pulse)))
        for y in range(int(GROUND_Y - 50), SCREEN_HEIGHT, 20):
            wave_offset = math.sin(t * 2 + y * 0.05) * 15
            pygame.draw.rect(bg_surf, (0, 50, 150, int(40 * pulse)),
                           (int(wave_offset), y, SCREEN_WIDTH, 15))
        surface.blit(bg_surf, (0, 0))

        # 前进的水滴
        for _ in range(15):
            drop_x = int(wave_x - random.randint(0, 200))
            drop_y = int(GROUND_Y - 100 - random.randint(0, 200))
            if 0 < drop_x < SCREEN_WIDTH:
                pygame.draw.circle(surface, (100, 180, 255, int(alpha * 0.3)),
                                 (drop_x, drop_y), random.randint(4, 10))

    def _draw_poison_mist(self, surface, effect, progress, pulse, alpha):
        """绿色法杖 - 毒雾弥漫：从中心向外扩散的有毒烟雾"""
        t = effect.timer
        cx, cy = effect.center_x, effect.center_y

        # 多层毒雾环向外扩散
        for ring_i in range(8):
            ring_radius = 50 + ring_i * 100 * (0.2 + progress * 0.8)
            ring_alpha = int(80 * (1.0 - ring_i / 8) * pulse)
            if ring_alpha > 5:
                # 绘制毒雾环形带
                for angle in range(0, 360, 10):
                    rad = math.radians(angle + t * 20 + ring_i * 15)
                    blob_x = cx + math.cos(rad) * ring_radius
                    blob_y = cy + math.sin(rad) * ring_radius * 0.5

                    blob_size = 30 + math.sin(t * 5 + angle * 0.1) * 15
                    color_g = int(200 + 55 * (1.0 - ring_i / 8))

                    # 绘制毒雾团
                    mist_surf = pygame.Surface((int(blob_size * 2 + 4), int(blob_size + 4)), pygame.SRCALPHA)
                    pygame.draw.ellipse(mist_surf, (50, color_g, 50, ring_alpha),
                                      (2, 2, int(blob_size * 2), int(blob_size)))
                    surface.blit(mist_surf, (int(blob_x - blob_size - 2), int(blob_y - blob_size // 2 - 2)))

        # 中心毒雾核心
        core_radius = int(60 + math.sin(t * 8) * 20)
        for r in range(core_radius, 0, -10):
            a = int(30 * (1.0 - r / core_radius))
            pygame.draw.circle(surface, (30, 180, 30, a),
                             (cx, cy), r)

        # 毒气泡上升
        for _ in range(20):
            bubble_x = cx + random.randint(-200, 200)
            bubble_y = int(GROUND_Y - random.randint(0, 400) - t * 100)
            if 0 < bubble_y < GROUND_Y:
                bubble_size = random.randint(5, 15)
                pygame.draw.circle(surface, (80, 220, 80, int(alpha * 0.4)),
                                 (bubble_x, bubble_y), bubble_size)
                # 小气泡
                pygame.draw.circle(surface, (150, 255, 150, int(alpha * 0.3)),
                                 (bubble_x - 3, bubble_y - 3), bubble_size // 3)

        # 全屏毒雾覆盖
        mist_overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for y in range(0, SCREEN_HEIGHT, 20):
            for x in range(0, SCREEN_WIDTH, 30):
                dist = math.sqrt((x - cx) ** 2 + (y - cy) ** 2)
                if dist < 400 + t * 100:
                    noise = math.sin(x * 0.05 + t * 2) * math.cos(y * 0.05 + t * 3)
                    if noise > 0.2:
                        mist_surf = pygame.Surface((40, 30), pygame.SRCALPHA)
                        pygame.draw.ellipse(mist_surf, (40, 180, 40, int(30 * pulse)),
                                          (0, 0, 40, 30))
                        surface.blit(mist_surf, (x, y))

    def _draw_nuke_mushroom_cloud(self, surface, exp, progress):
        """核弹 - 壮观蘑菇云爆炸特效"""
        x, y = exp["x"], exp["y"]
        t = exp["timer"]

        # 多层冲击波光环向外扩散
        for ring_i in range(4):
            ring_radius = int(30 + progress * 200 * (1 + ring_i * 0.3))
            ring_alpha = int(180 * (1.0 - progress) * (1 - ring_i * 0.2))
            if ring_alpha > 5:
                ring_surf = pygame.Surface((ring_radius * 2 + 20, ring_radius * 2 + 20), pygame.SRCALPHA)
                # 外层光环
                pygame.draw.circle(ring_surf, (255, 150, 50, ring_alpha),
                                 (ring_radius + 10, ring_radius + 10), ring_radius, 8)
                # 内层光环
                pygame.draw.circle(ring_surf, (255, 220, 100, int(ring_alpha * 0.6)),
                                 (ring_radius + 10, ring_radius + 10), int(ring_radius * 0.6), 5)
                surface.blit(ring_surf, (int(x - ring_radius - 10), int(y - ring_radius - 10)))

        # 地面火焰
        if progress < 0.6:
            fire_alpha = int(200 * (1.0 - progress / 0.6))
            for i in range(15):
                fx = x + (i - 7) * 30
                fh = int(40 + math.sin(t * 10 + i) * 20)
                pygame.draw.rect(surface, (255, 100, 0, fire_alpha), (int(fx), int(y - fh), 20, fh))
                pygame.draw.rect(surface, (255, 200, 50, int(fire_alpha * 0.8)), (int(fx + 5), int(y - fh // 2), 10, fh // 2))

        # 蘑菇云主体（分阶段绘制）
        if progress < 0.8:
            cloud_progress = min(1.0, progress / 0.5)

            # 烟柱（从爆炸点向上延伸）
            pillar_h = int(150 * cloud_progress)
            pillar_w = int(30 + 40 * cloud_progress)
            pillar_x = x - pillar_w // 2
            pillar_y = y - pillar_h

            # 烟柱渐变
            for py in range(0, pillar_h, 8):
                fade = 1.0 - py / pillar_h
                alpha = int(150 * fade * (1.0 - progress))
                smoke_color = (80, 80, 80)
                offset_x = int(math.sin(py * 0.1 + t * 3) * 10 * fade)
                pygame.draw.rect(surface, (*smoke_color, alpha),
                               (int(pillar_x + offset_x), int(pillar_y + py), pillar_w, 10))

            # 蘑菇云顶部（扩散的大云团）
            if cloud_progress > 0.3:
                cap_y = y - pillar_h - 20
                cap_radius = int(50 + 80 * (cloud_progress - 0.3) / 0.7)

                # 多层云朵
                for layer in range(5):
                    layer_radius = int(cap_radius * (1 - layer * 0.15))
                    layer_y = cap_y - layer * 15
                    layer_alpha = int(180 * (1.0 - layer * 0.15) * (1.0 - progress))

                    cloud_surf = pygame.Surface((layer_radius * 2 + 30, layer_radius + 30), pygame.SRCALPHA)
                    # 主云团
                    pygame.draw.ellipse(cloud_surf, (100, 100, 100, layer_alpha),
                                      (15, 15, layer_radius * 2, layer_radius))
                    # 云朵凸起
                    for bump_i in range(4):
                        bump_x = 15 + bump_i * (layer_radius // 2)
                        bump_r = layer_radius // 3
                        pygame.draw.circle(cloud_surf, (120, 120, 120, layer_alpha),
                                         (int(bump_x + bump_r * 0.5), 15 + bump_r // 2), bump_r)

                    surface.blit(cloud_surf, (int(x - layer_radius - 15), int(layer_y - 15)))

                # 蘑菇云顶部发光的火球核心
                core_alpha = int(255 * (1.0 - progress * 1.5))
                if core_alpha > 0:
                    pygame.draw.circle(surface, (255, 200, 100, core_alpha),
                                     (int(x), int(cap_y - cap_radius // 2)), int(cap_radius * 0.3))
                    pygame.draw.circle(surface, (255, 255, 200, int(core_alpha * 0.8)),
                                     (int(x), int(cap_y - cap_radius // 2)), int(cap_radius * 0.15))

        # 碎片飞溅
        if progress < 0.7:
            debris_alpha = int(150 * (1.0 - progress / 0.7))
            for i in range(12):
                angle = (i / 12) * math.pi * 2
                dist = 50 + progress * 150
                dx = x + math.cos(angle) * dist
                dy = y + math.sin(angle) * dist * 0.5 - progress * 80
                pygame.draw.circle(surface, (200, 100, 50, debris_alpha),
                                 (int(dx), int(dy)), random.randint(3, 8))
