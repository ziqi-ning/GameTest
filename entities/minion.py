# 小兵系统 - 各角色专属随从

import pygame
import math
import random
import os
from typing import Optional, List, Tuple, Dict
from config import GROUND_Y, GRAVITY

MINION_DIR = os.path.join("assets", "sprites", "minions")
SPRITE_W = 96   # 每帧宽度（与角色一致）
SPRITE_H = 63   # 每帧高度
MINION_DRAW_W = 64  # 小兵渲染宽度（缩小以区分主角）
MINION_DRAW_H = 42  # 小兵渲染高度


def _load_spritesheet(filename: str, frame_count: int) -> List[pygame.Surface]:
    """加载 spritesheet，返回帧列表；失败返回空列表"""
    path = os.path.join(MINION_DIR, filename)
    if not os.path.exists(path):
        return []
    try:
        sheet = pygame.image.load(path).convert_alpha()
        frames = []
        for i in range(frame_count):
            f = pygame.Surface((SPRITE_W, SPRITE_H), pygame.SRCALPHA)
            f.blit(sheet, (0, 0), (i * SPRITE_W, 0, SPRITE_W, SPRITE_H))
            frames.append(f)
        return frames
    except Exception as e:
        print(f"[Minion] Failed to load {filename}: {e}")
        return []


# ── 小兵基类 ──────────────────────────────────────────────────────────────────

class Minion:
    """小兵基类"""

    SIZE = (32, 48)          # 默认碰撞尺寸
    MAX_HEALTH = 60
    MOVE_SPEED = 2.5
    ATTACK_RANGE = 60
    ATTACK_DAMAGE = 15
    ATTACK_COOLDOWN = 1.2    # 秒
    COIN_REWARD = 5          # 击杀奖励金币
    CAN_FLY = False          # 是否可飞行

    def __init__(self, x: float, y: float, owner_id: int, owner_char: str):
        self.x = x
        self.y = y
        self.owner_id = owner_id        # 1 or 2
        self.owner_char = owner_char    # 角色名（用于区分小兵类型）

        self.vel_x = 0.0
        self.vel_y = 0.0
        self.on_ground = True
        self.health = self.MAX_HEALTH
        self.max_health = self.MAX_HEALTH
        self.alive = True

        self.attack_timer = 0.0         # 攻击冷却计时
        self.mode = "charge"            # "charge" 冲锋 | "follow" 跟随
        self.stage = None               # 场景引用（平台碰撞）

        # 朝向
        self.facing_right = (owner_id == 1)

        # 动画（spritesheet）
        self.anim_timer = 0.0
        self.anim_frame = 0
        self.anim_speed = 0.12
        self.sprites: Dict[str, List[pygame.Surface]] = {}  # 子类填充
        self.current_anim = "idle"

        # 图片（子类加载）
        self.image: Optional[pygame.Surface] = None
        self.image_left: Optional[pygame.Surface] = None
        self.image_right: Optional[pygame.Surface] = None

        # 受击闪烁
        self.hit_flash = 0.0

        # 投射物列表（远程小兵用）
        self.projectiles: List['MinionProjectile'] = []

        # 分散偏移：每个小兵有独立的目标偏移，避免扎堆
        self.spread_offset = random.uniform(-80, 80)
        # 行为延迟：随机错开决策时机
        self.behavior_timer = random.uniform(0, 0.5)

    # ── 状态更新 ──────────────────────────────────────────────────────────────

    def update(self, dt: float, owner_x: float, owner_y: float,
               enemy: 'Fighter', enemy_minions: List['Minion']):
        """每帧更新"""
        if not self.alive:
            return

        self.attack_timer = max(0.0, self.attack_timer - dt)
        self.hit_flash = max(0.0, self.hit_flash - dt)
        self.anim_timer += dt
        if self.anim_timer >= self.anim_speed:
            self.anim_timer = 0.0
            frames = self.sprites.get(self.current_anim, [])
            if frames:
                self.anim_frame = (self.anim_frame + 1) % len(frames)
            else:
                self.anim_frame = (self.anim_frame + 1) % 4

        # 更新投射物
        for proj in self.projectiles[:]:
            proj.update(dt)
            if not proj.alive:
                self.projectiles.remove(proj)

        # 行为决策
        if self.mode == "charge":
            self._behavior_charge(dt, enemy, enemy_minions)
        else:
            self._behavior_follow(dt, owner_x, owner_y)

        # 物理
        self._apply_physics(dt)

    def _behavior_charge(self, dt: float, enemy, enemy_minions: List['Minion']):
        """冲锋：优先攻击敌方小兵，再攻击主角，保持分散"""
        # 行为延迟：错开决策时机，避免同步扎堆
        self.behavior_timer = max(0.0, self.behavior_timer - dt)
        if self.behavior_timer > 0:
            self.vel_x = 0
            self.current_anim = "idle"
            return

        target = self._find_nearest_target(enemy, enemy_minions)
        if target is None:
            return

        tx = target.x if hasattr(target, 'x') else target[0]
        ty = target.y if hasattr(target, 'y') else target[1]

        # 应用分散偏移：每个小兵的目标位置略有不同
        target_x = tx + self.spread_offset
        dist_x = abs(self.x - target_x)
        dist_y = self.y - ty

        self.facing_right = tx > self.x

        # 与同阵营小兵保持间距（避免重叠）
        same_side = [m for m in enemy_minions if m is not self and m.alive and m.owner_id == self.owner_id]
        for ally in same_side:
            ally_dist = abs(self.x - ally.x)
            if ally_dist < 40:
                # 太近了，往反方向推一点
                push = 1 if self.x > ally.x else -1
                self.vel_x = self.MOVE_SPEED * push
                self.current_anim = "walk"
                return

        # 目标在高处（超过40px），尝试跳跃
        if dist_y > 40 and self.on_ground and self.vel_y == 0:
            self.vel_y = -12.0
            self.on_ground = False

        if dist_x > self.ATTACK_RANGE or abs(dist_y) > 80:
            self.vel_x = self.MOVE_SPEED * (1 if target_x > self.x else -1)
            self.current_anim = "walk"
        else:
            self.vel_x = 0
            if self.attack_timer <= 0 and abs(dist_y) <= 80:
                self._do_attack(target)
                self.attack_timer = self.ATTACK_COOLDOWN
                # 攻击后随机重置偏移，下次攻击位置不同
                self.spread_offset = random.uniform(-80, 80)
                self.current_anim = "attack"
                self.anim_frame = 0
            elif self.current_anim == "attack":
                frames = self.sprites.get("attack", [])
                if frames and self.anim_frame >= len(frames) - 1:
                    self.current_anim = "idle"

    def _behavior_follow(self, dt: float, owner_x: float, owner_y: float):
        """跟随主人，保持一定距离"""
        dist = abs(self.x - owner_x)
        follow_dist = 80  # 跟随距离
        if dist > follow_dist:
            self.facing_right = owner_x > self.x
            self.vel_x = self.MOVE_SPEED * (1 if owner_x > self.x else -1)
            self.current_anim = "walk"
        else:
            self.vel_x = 0
            self.current_anim = "idle"

    def _find_nearest_target(self, enemy, enemy_minions: List['Minion']):
        """找最近的敌方目标（优先小兵）"""
        candidates = [m for m in enemy_minions if m.alive]
        if enemy and hasattr(enemy, 'health') and enemy.health > 0:
            candidates.append(enemy)
        if not candidates:
            return None
        return min(candidates, key=lambda t: abs(self.x - t.x))

    def _do_attack(self, target):
        """执行攻击（子类可重写）"""
        if hasattr(target, 'take_minion_damage'):
            target.take_minion_damage(self.ATTACK_DAMAGE, self.owner_id)
        elif hasattr(target, 'health'):
            target.health = max(0, target.health - self.ATTACK_DAMAGE)

    def _apply_physics(self, dt: float):
        """物理更新（重力、平台碰撞）"""
        if not self.CAN_FLY:
            if not self.on_ground:
                self.vel_y += GRAVITY * 60 * dt

        self.x += self.vel_x * 60 * dt
        self.y += self.vel_y * 60 * dt

        # 平台碰撞
        if not self.CAN_FLY:
            self.on_ground = False
            if self.stage and self.stage.platforms and self.vel_y >= 0:
                for px, py, pw, ph in self.stage.platforms:
                    if px <= self.x <= px + pw and py - 15 <= self.y <= py + 8:
                        self.y = py
                        self.vel_y = 0
                        self.on_ground = True
                        break
            if not self.on_ground and self.y >= GROUND_Y:
                self.y = GROUND_Y
                self.vel_y = 0
                self.on_ground = True

        # 边界
        self.x = max(60, min(1220, self.x))

    def take_damage(self, damage: int):
        """受到伤害"""
        self.health -= damage
        self.hit_flash = 0.15
        if self.health <= 0:
            self.health = 0
            self.alive = False

    def get_hurtbox(self) -> Tuple[float, float, int, int]:
        """获取受击框"""
        w, h = self.SIZE
        return (self.x - w // 2, self.y - h, w, h)

    # ── 绘制 ──────────────────────────────────────────────────────────────────

    def draw(self, surface: pygame.Surface):
        if not self.alive:
            return

        # 绘制投射物
        for proj in self.projectiles:
            proj.draw(surface)

        # 受击闪烁
        if self.hit_flash > 0 and int(self.hit_flash * 20) % 2 == 0:
            return

        self._draw_body(surface)
        self._draw_health_bar(surface)

    def _draw_body(self, surface: pygame.Surface):
        """绘制小兵本体（使用 spritesheet 或占位，缩小渲染）"""
        frames = self.sprites.get(self.current_anim) or self.sprites.get("idle") or []
        if frames:
            idx = self.anim_frame % len(frames)
            frame = frames[idx]
            if not self.facing_right:
                frame = pygame.transform.flip(frame, True, False)
            # 缩小渲染，区分主角
            small = pygame.transform.scale(frame, (MINION_DRAW_W, MINION_DRAW_H))
            surface.blit(small, (int(self.x - MINION_DRAW_W // 2), int(self.y - MINION_DRAW_H)))
        else:
            # 占位方块
            w, h = self.SIZE
            x = int(self.x - w // 2)
            y = int(self.y - h)
            pygame.draw.rect(surface, (200, 200, 200), (x, y, w, h))

    def _tint_sprites(self, color: Tuple[int, int, int], alpha: int = 60):
        """给所有 sprite 帧叠加颜色色调"""
        for anim_name, frames in self.sprites.items():
            tinted = []
            for frame in frames:
                f = frame.copy()
                tint = pygame.Surface(f.get_size(), pygame.SRCALPHA)
                tint.fill((*color, alpha))
                f.blit(tint, (0, 0), special_flags=pygame.BLEND_RGBA_ADD)
                tinted.append(f)
            self.sprites[anim_name] = tinted


# ── 龚大哥小兵：红头巾小子 ───────────────────────────────────────────────────

    def _draw_health_bar(self, surface: pygame.Surface):
        """绘制血条"""
        w, h = self.SIZE
        bar_w = w
        bar_h = 4
        bx = int(self.x - bar_w // 2)
        by = int(self.y - h - 6)
        ratio = self.health / self.max_health
        pygame.draw.rect(surface, (60, 20, 20), (bx, by, bar_w, bar_h))
        pygame.draw.rect(surface, (220, 60, 60), (bx, by, int(bar_w * ratio), bar_h))


# ── 投射物（小兵用）─────────────────────────────────────────────────────────

class MinionProjectile:
    """小兵投射物"""

    def __init__(self, x: float, y: float, direction: int, speed: float,
                 damage: int, owner_id: int, color: Tuple[int, int, int] = (200, 200, 100),
                 size: int = 10, max_range: float = 400):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.owner_id = owner_id
        self.color = color
        self.size = size
        self.max_range = max_range
        self.traveled = 0.0
        self.alive = True
        self.vel_y = 0.0  # 籽桐蛋用

    def update(self, dt: float):
        dx = self.speed * self.direction * 60 * dt
        self.x += dx
        self.y += self.vel_y * 60 * dt
        self.traveled += abs(dx)
        if self.traveled >= self.max_range:
            self.alive = False
        if self.y > GROUND_Y + 50:
            self.alive = False

    def draw(self, surface: pygame.Surface):
        if self.alive:
            pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), self.size)
            # 高光
            pygame.draw.circle(surface, (255, 255, 255),
                               (int(self.x) - self.size // 3, int(self.y) - self.size // 3), 2)

    def get_rect(self) -> Tuple[float, float, int, int]:
        return (self.x - self.size, self.y - self.size, self.size * 2, self.size * 2)


# ── 龚大哥小兵：红头巾小子 ───────────────────────────────────────────────────

class GongMinion(Minion):
    """戴红头巾的小子，攻速快，近战"""
    SIZE = (28, 44)
    MAX_HEALTH = 750
    MOVE_SPEED = 3.2
    ATTACK_RANGE = 55
    ATTACK_DAMAGE = 12
    ATTACK_COOLDOWN = 0.7   # 攻速快

    def __init__(self, x, y, owner_id, owner_char):
        super().__init__(x, y, owner_id, owner_char)
        self.sprites = {
            "idle":   _load_spritesheet("boxer_idle.png", 4),
            "walk":   _load_spritesheet("boxer_walk.png", 6),
            "attack": _load_spritesheet("boxer_attack.png", 4),
            "hurt":   _load_spritesheet("boxer_hurt.png", 2),
        }


# ── 军师小兵：白大褂研究员 ───────────────────────────────────────────────────

class JunshiMinion(Minion):
    """穿白大褂的研究员，远程丢试剂瓶"""
    SIZE = (28, 46)
    MAX_HEALTH = 650
    MOVE_SPEED = 2.0
    ATTACK_RANGE = 250
    ATTACK_DAMAGE = 18
    ATTACK_COOLDOWN = 1.5
    PREFERRED_DIST = 180

    def __init__(self, x, y, owner_id, owner_char):
        super().__init__(x, y, owner_id, owner_char)
        self.sprites = {
            "idle":   _load_spritesheet("scientist_idle.png", 4),
            "walk":   _load_spritesheet("scientist_walk.png", 6),
            "attack": _load_spritesheet("scientist_attack.png", 4),
            "hurt":   _load_spritesheet("scientist_hurt.png", 2),
        }

    def _behavior_charge(self, dt: float, enemy, enemy_minions: List[Minion]):
        """远程：保持距离，在射程内投掷"""
        target = self._find_nearest_target(enemy, enemy_minions)
        if target is None:
            return

        tx = target.x
        dist = abs(self.x - tx)
        self.facing_right = tx > self.x

        if dist > self.ATTACK_RANGE:
            # 超出射程，靠近
            self.vel_x = self.MOVE_SPEED * (1 if tx > self.x else -1)
        elif dist < self.PREFERRED_DIST:
            # 太近，后退
            self.vel_x = self.MOVE_SPEED * (-1 if tx > self.x else 1)
        else:
            self.vel_x = 0
            if self.attack_timer <= 0:
                self._throw_bottle(target)
                self.attack_timer = self.ATTACK_COOLDOWN

    def _throw_bottle(self, target):
        """投掷试剂瓶"""
        dir_sign = 1 if target.x > self.x else -1
        proj = MinionProjectile(
            x=self.x + 15 * dir_sign,
            y=self.y - 30,
            direction=dir_sign,
            speed=5.0,
            damage=self.ATTACK_DAMAGE,
            owner_id=self.owner_id,
            color=(100, 220, 180),
            size=8,
            max_range=300
        )
        self.projectiles.append(proj)


# ── 神秘人小兵：日本武士 ─────────────────────────────────────────────────────

class ShenmirenMinion(Minion):
    """日本武士，伤害高，近战"""
    SIZE = (30, 50)
    MAX_HEALTH = 800
    MOVE_SPEED = 2.8
    ATTACK_RANGE = 65
    ATTACK_DAMAGE = 28      # 高伤害
    ATTACK_COOLDOWN = 1.4

    def __init__(self, x, y, owner_id, owner_char):
        super().__init__(x, y, owner_id, owner_char)
        self.sprites = {
            "idle":   _load_spritesheet("samurai_idle.png", 4),
            "walk":   _load_spritesheet("samurai_walk.png", 6),
            "attack": _load_spritesheet("samurai_attack.png", 4),
            "hurt":   _load_spritesheet("samurai_hurt.png", 2),
        }
        self._tint_sprites((40, 40, 80), alpha=30)
        self.slash_effect = 0.0

    def _do_attack(self, target):
        super()._do_attack(target)
        self.slash_effect = 0.2


# ── 籽桐小兵：飞行的雕 ───────────────────────────────────────────────────────

class ZitongMinion(Minion):
    """飞行的雕，可飞行，啄击+下蛋攻击"""
    SIZE = (36, 28)
    MAX_HEALTH = 600
    MOVE_SPEED = 3.5
    ATTACK_RANGE = 70
    ATTACK_DAMAGE = 14
    ATTACK_COOLDOWN = 1.0
    CAN_FLY = True
    EGG_COOLDOWN = 3.0      # 下蛋冷却

    def __init__(self, x, y, owner_id, owner_char):
        super().__init__(x, y, owner_id, owner_char)
        self.sprites = {
            "idle":   _load_spritesheet("eagle_idle.png", 4),
            "walk":   _load_spritesheet("eagle_walk.png", 4),
            "attack": _load_spritesheet("eagle_attack.png", 2),
            "hurt":   _load_spritesheet("eagle_hurt.png", 2),
        }
        self._tint_sprites((100, 70, 30), alpha=20)
        self.fly_y = y - 80
        self.egg_timer = 0.0
        self.wing_phase = random.uniform(0, math.pi * 2)

    def update(self, dt, owner_x, owner_y, enemy, enemy_minions):
        self.egg_timer = max(0.0, self.egg_timer - dt)
        # 飞行高度跟随主人
        self.fly_y = owner_y - 100
        super().update(dt, owner_x, owner_y, enemy, enemy_minions)

    def _apply_physics(self, dt: float):
        """飞行物理：平滑飞向目标高度"""
        target_y = self.fly_y
        dy = target_y - self.y
        self.vel_y = dy * 5 * dt  # 平滑插值
        self.x += self.vel_x * 60 * dt
        self.y += dy * 0.1  # 缓慢靠近目标高度
        self.x = max(60, min(1220, self.x))

    def _behavior_charge(self, dt, enemy, enemy_minions):
        target = self._find_nearest_target(enemy, enemy_minions)
        if target is None:
            return

        tx = target.x
        ty = target.y - 60  # 飞在目标上方
        dist_x = abs(self.x - tx)
        self.facing_right = tx > self.x
        self.fly_y = ty

        if dist_x > self.ATTACK_RANGE:
            self.vel_x = self.MOVE_SPEED * (1 if tx > self.x else -1)
        else:
            self.vel_x = 0
            # 啄击
            if self.attack_timer <= 0:
                self._do_attack(target)
                self.attack_timer = self.ATTACK_COOLDOWN
            # 下蛋（对地面目标）
            if self.egg_timer <= 0 and hasattr(target, 'y') and target.y > self.y + 30:
                self._drop_egg(target)
                self.egg_timer = self.EGG_COOLDOWN

    def _drop_egg(self, target):
        """向目标下方投蛋"""
        proj = MinionProjectile(
            x=self.x,
            y=self.y,
            direction=0,
            speed=0,
            damage=10,
            owner_id=self.owner_id,
            color=(240, 230, 180),
            size=7,
            max_range=500
        )
        proj.vel_y = 3.0  # 向下落
        self.projectiles.append(proj)


# ── 工厂函数 ──────────────────────────────────────────────────────────────────

MINION_CLASSES = {
    "龚大哥": GongMinion,
    "军师": JunshiMinion,
    "神秘人": ShenmirenMinion,
    "籽桐": ZitongMinion,
}

def create_minion(char_name: str, x: float, y: float, owner_id: int) -> Minion:
    """根据角色名创建对应小兵"""
    cls = MINION_CLASSES.get(char_name, GongMinion)
    return cls(x, y, owner_id, char_name)
