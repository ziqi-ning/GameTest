# Fighter - 战斗角色基类

import pygame
import random
from typing import Optional, Tuple, List
from config import GROUND_Y, GRAVITY, Colors
from constants import FighterState, Direction, FrameData, DamageMultiplier
from utils import Vector2, Rect, clamp, sign
from animation.animator import Animator, AnimationState
from combat import (
    ComboSystem, HitboxManager, ProjectileManager,
    calculate_damage, calculate_knockback, calculate_hitstun,
    calculate_special_energy_gain, get_attack_multiplier,
    SpecialMoveManager, EffectManager, CharacterEffects
)
from characters.character_base import CharacterData, MoveData, SpecialMoveData


class Fighter:
    """战斗角色基类"""

    def __init__(self, player_id: int, char_data: CharacterData, x: float, y: float):
        self.player_id = player_id
        self.char_data = char_data
        self.stats = char_data.stats

        # 位置和移动
        self.x = x
        self.y = y
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.direction = Direction.RIGHT if player_id == 1 else Direction.LEFT
        self.on_ground = True

        # 战斗属性
        self.health = self.stats.max_health
        self.max_health = self.stats.max_health
        self.special_energy = 0
        self.max_special = 100

        # 状态
        self.state = FighterState.IDLE
        self.is_blocking = False
        self.block_input = False  # 保存防御输入
        self.is_invincible = False
        self.invincible_timer = 0.0

        # 动画
        self.animator = Animator(owner_id=player_id)

        # 攻击系统
        self.combat = ComboSystem()
        self.hitbox_manager = HitboxManager()
        self.special_manager = SpecialMoveManager()
        self.projectile_manager = ProjectileManager()

        # 特效系统
        self.effect_manager = EffectManager()
        self.effect_func = CharacterEffects.get_effect_function(self.stats.name_cn)

        # 攻击状态
        self.current_attack: Optional[MoveData] = None
        self.current_special: Optional[SpecialMoveData] = None
        self.attack_frame = 0
        self.attack_cooldown = 0.0
        self.is_attacking = False
        self.is_special_attacking = False
        self.special_hit_count = 0  # 必杀技命中计数

        # 受击状态
        self.hitstun_timer = 0.0
        self.knockback_x = 0.0
        self.knockback_y = 0.0

        # 连击显示
        self.combo_display_count = 0
        self.combo_display_timer = 0.0

        # 视觉特效
        self.hit_effect_timer = 0.0
        self.screen_shake = 0.0

        # 特殊效果状态
        self.slow_timer = 0.0  # 减速效果
        self.stun_timer = 0.0  # 眩晕效果
        self.curse_timer = 0.0  # 诅咒效果（降低攻击）
        self.shield_value = 0  # 护盾值

        # 装备必杀技
        if char_data.special:
            self.special_manager.set_special_moves(char_data.special)

    @property
    def facing_right(self) -> bool:
        return self.direction == Direction.RIGHT

    @property
    def center_x(self) -> float:
        return self.x

    @property
    def center_y(self) -> float:
        return self.y

    def get_rect(self) -> Tuple[float, float, float, float]:
        """获取角色碰撞框"""
        return (self.x - 40, self.y - 160, 80, 160)

    def get_hurtbox_rect(self) -> Tuple[float, float, float, float]:
        """获取受击判定框"""
        if self.state == FighterState.CROUCH:
            return (self.x - 35, self.y - 100, 70, 100)
        return (self.x - 35, self.y - 150, 70, 150)

    def get_hitbox_rect(self) -> Optional[Tuple[float, float, float, float]]:
        """获取当前攻击判定框"""
        if not self.is_attacking or not self.current_attack:
            return None

        # 计算判定框位置
        move = self.current_attack
        dir = self.direction

        # 只在active帧期间显示判定框
        if move.active_start <= self.attack_frame < move.active_start + move.active_frames:
            hitbox_x = self.x + move.hitbox_offset[0] * dir - move.hitbox_size[0] // 2
            hitbox_y = self.y - 120 + move.hitbox_offset[1]

            # 翻转x坐标
            if dir == Direction.LEFT:
                hitbox_x = self.x - move.hitbox_offset[0] * dir - move.hitbox_size[0] // 2

            return (hitbox_x, hitbox_y, move.hitbox_size[0], move.hitbox_size[1])

        return None

    def handle_input(self, left: bool, right: bool, up: bool, down: bool,
                   light_attack: bool, heavy_attack: bool, special: bool, block: bool):
        """处理输入（由子类或AI实现）"""
        pass

    def update(self, dt: float, opponent: Optional['Fighter'] = None):
        """更新角色状态"""
        # 更新特效系统
        self.effect_manager.update(dt)

        # 更新特殊状态效果
        if self.slow_timer > 0:
            self.slow_timer -= dt
        if self.stun_timer > 0:
            self.stun_timer -= dt
            return  # 眩晕时不能动
        if self.curse_timer > 0:
            self.curse_timer -= dt

        # 更新无敌时间
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.is_invincible = False

        # 更新动画
        self.animator.update(dt)

        # 更新受击硬直
        if self.hitstun_timer > 0:
            self.hitstun_timer -= dt
            self.apply_knockback(dt)
            return

        # 更新攻击
        if self.is_attacking:
            self.update_attack(dt, opponent)
            return

        # 更新防御状态
        if not self.block_input and self.is_blocking:
            self.is_blocking = False
            if self.state != FighterState.IDLE:
                self.state = FighterState.IDLE
                self.animator.set_state(AnimationState.IDLE)

        # HIT状态结束后恢复IDLE
        if self.state == FighterState.HIT:
            self.state = FighterState.IDLE
            self.animator.set_state(AnimationState.IDLE)

        # 更新连击显示
        if self.combo_display_timer > 0:
            self.combo_display_timer -= dt

        # 更新特殊效果
        if self.hit_effect_timer > 0:
            self.hit_effect_timer -= dt

        # 被动能量回复 (战斗中缓慢回复)
        if self.special_energy < self.max_special:
            self.special_energy = min(self.max_special,
                                      self.special_energy + 3 * dt)  # 每秒回复3点能量

        # 重力
        if not self.on_ground:
            self.vel_y += GRAVITY * 60 * dt

        # 移动
        self.x += self.vel_x * 60 * dt
        self.y += self.vel_y * 60 * dt

        # 地面碰撞
        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

        # 边界限制
        self.x = clamp(self.x, 60, 1220)

        # 攻击冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

    def apply_movement(self, left: bool, right: bool, up: bool, down: bool, block: bool):
        """应用移动输入"""
        self.block_input = block  # 保存防御输入状态

        if self.hitstun_timer > 0 or self.is_attacking:
            return

        # 防御
        if block and self.on_ground:
            self.is_blocking = True
            self.state = FighterState.BLOCK
            self.animator.set_state(AnimationState.BLOCK)
            return

        # 防御时不能移动
        if self.is_blocking:
            self.vel_x = 0
            return

        # 下蹲
        if down and self.on_ground:
            self.state = FighterState.CROUCH
            self.animator.set_state(AnimationState.CROUCH)
            self.vel_x = 0
            return

        # 跳跃
        if up and self.on_ground:
            self.vel_y = -self.stats.jump_force
            self.on_ground = False
            self.state = FighterState.JUMP
            self.animator.set_state(AnimationState.JUMP)

        # 左右移动
        if left:
            self.vel_x = -self.stats.walk_speed
            self.direction = Direction.LEFT
            if self.on_ground and self.state != FighterState.JUMP:
                self.state = FighterState.WALK
                self.animator.set_state(AnimationState.WALK)
        elif right:
            self.vel_x = self.stats.walk_speed
            self.direction = Direction.RIGHT
            if self.on_ground and self.state != FighterState.JUMP:
                self.state = FighterState.WALK
                self.animator.set_state(AnimationState.WALK)
        else:
            self.vel_x = 0
            if self.on_ground and self.state not in [FighterState.ATTACK_LIGHT, FighterState.ATTACK_HEAVY]:
                self.state = FighterState.IDLE
                self.animator.set_state(AnimationState.IDLE)

    def attack_light(self):
        """轻攻击"""
        if self.attack_cooldown > 0 or self.is_attacking or self.hitstun_timer > 0:
            return

        if len(self.char_data.moves) > 0:
            self.current_attack = self.char_data.moves[0]
            self.is_attacking = True
            self.attack_frame = 0
            self.state = FighterState.ATTACK_LIGHT
            self.animator.set_state(AnimationState.ATTACK_LIGHT)
            self.vel_x = 0

    def attack_heavy(self):
        """重攻击"""
        if self.attack_cooldown > 0 or self.is_attacking or self.hitstun_timer > 0:
            return

        if len(self.char_data.moves) > 1:
            self.current_attack = self.char_data.moves[1]
            self.is_attacking = True
            self.attack_frame = 0
            self.state = FighterState.ATTACK_HEAVY
            self.animator.set_state(AnimationState.ATTACK_HEAVY)
            self.vel_x = 0

    def attack_special(self):
        """必杀技"""
        if self.special_energy < self.char_data.stats.special_cost:
            return
        if self.is_attacking or self.hitstun_timer > 0:
            return

        self.special_energy -= self.char_data.stats.special_cost
        self.is_attacking = True
        self.is_special_attacking = True
        self.attack_frame = 0
        self.current_special = self.char_data.special[0]  # 使用第一个必杀技
        self.state = FighterState.ATTACK_SPECIAL
        self.animator.set_state(AnimationState.ATTACK_SPECIAL)
        self.vel_x = 0
        self.special_hit_count = 0

        # 触发必杀技特效
        if self.effect_func:
            effect_x = self.x + (50 if self.facing_right else -50)
            self.effect_func(self.effect_manager, effect_x, self.y - 50, self.current_special.name_cn)

    def update_attack(self, dt: float, opponent: Optional['Fighter'] = None):
        """更新攻击状态"""
        self.attack_frame += 1

        move = self.current_attack

        # 同步动画帧 (让动画跟着攻击帧走)
        anim_frame = min(self.attack_frame // 3, self.animator.get_frame_count() - 1)
        # 强制设置动画帧
        self.animator.frame = anim_frame

        # 判定帧
        if (move.active_start <= self.attack_frame <
                move.active_start + move.active_frames):
            # 检测命中
            if opponent:
                self.check_hit(opponent)

        # 攻击结束
        if self.attack_frame >= move.total_frames:
            self.is_attacking = False
            self.is_special_attacking = False
            self.current_attack = None
            self.attack_cooldown = 0.1
            self.state = FighterState.IDLE
            self.animator.set_state(AnimationState.IDLE)

    def check_hit(self, opponent: 'Fighter'):
        """检查攻击是否命中"""
        if not self.current_attack or not opponent:
            return

        hitbox_rect = self.get_hitbox_rect()
        if not hitbox_rect:
            return

        hurtbox_rect = opponent.get_hurtbox_rect()
        move = self.current_attack

        # 碰撞检测
        if (hitbox_rect[0] < hurtbox_rect[0] + hurtbox_rect[2] and
            hitbox_rect[0] + hitbox_rect[2] > hurtbox_rect[0] and
            hitbox_rect[1] < hurtbox_rect[1] + hurtbox_rect[3] and
            hitbox_rect[1] + hitbox_rect[3] > hurtbox_rect[1]):

            # 检查防御
            if opponent.is_blocking and move.can_block:
                self.apply_blocked_hit(opponent, move)
            elif not opponent.is_invincible:
                self.apply_hit(opponent, move)

                # 触发命中特效
                if self.effect_func:
                    effect_x = opponent.x
                    self.effect_func(self.effect_manager, effect_x, opponent.y - 50, move.name)

    def apply_hit(self, opponent: 'Fighter', move):
        """应用命中效果"""
        # 计算伤害
        damage = calculate_damage(
            self.stats.attack_power,
            opponent.stats.defense,
            get_attack_multiplier(move.name.split('_')[0]),
            1.0,
            self.combat.combo_count
        )

        # 应用伤害
        opponent.take_damage(damage, move.knockback, move.knockback_up, self.direction)

        # 更新连击
        combo_count = self.combat.register_hit(damage, move.name)

        # 更新能量 (根据攻击类型)
        if 'light' in move.name:
            energy_type = 'light'
        elif 'heavy' in move.name:
            energy_type = 'heavy'
        else:
            energy_type = 'light'
        self.special_energy = min(self.max_special,
                                  self.special_energy + calculate_special_energy_gain(damage, energy_type))

        # 视觉效果
        opponent.hit_effect_timer = 0.2
        self.screen_shake = 5

    def apply_blocked_hit(self, opponent: 'Fighter', move):
        """应用被防御的命中"""
        hitstun = calculate_hitstun(move.hitstun, is_blocking=True)

        # 击退（较小）
        knockback = move.knockback * 0.3
        opponent.vel_x = knockback * self.direction
        opponent.hitstun_timer = hitstun / 60.0

        # 减少能量
        opponent.special_energy = max(0, opponent.special_energy - 5)

    def take_damage(self, damage: int, knockback: float, knockback_up: float, direction: int):
        """承受伤害"""
        # 神秘人被动闪避检查
        if hasattr(self.stats, 'dodge_chance') and self.stats.dodge_chance > 0:
            if random.random() < self.stats.dodge_chance:
                # 闪避成功！
                self.effect_manager.add_text("闪避!", self.x, self.y - 80, (255, 255, 100), 36, 1.0)
                self.effect_manager.add_particle_burst(self.x, self.y - 50, 8, (255, 255, 200), 5.0, 4.0)
                return

        # 护盾吸收伤害
        if self.shield_value > 0:
            absorbed = min(self.shield_value, damage)
            self.shield_value -= absorbed
            damage -= absorbed
            if damage <= 0:
                self.effect_manager.add_text("护盾!", self.x, self.y - 80, (100, 200, 255), 32, 1.0)
                return

        self.health = max(0, self.health - damage)
        self.is_invincible = True
        self.invincible_timer = 0.3

        # 击退
        self.knockback_x = knockback * direction
        self.knockback_y = -knockback_up

        # 状态
        self.state = FighterState.HIT
        self.animator.set_state(AnimationState.HIT)
        self.hitstun_timer = 0.3

        # 检查KO
        if self.health <= 0:
            self.ko()

    def apply_knockback(self, dt: float):
        """应用击退"""
        self.x += self.knockback_x * 60 * dt
        self.y += self.knockback_y * 60 * dt

        self.knockback_y += GRAVITY * 30 * dt

        if self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.knockback_y = 0

        self.x = clamp(self.x, 60, 1220)

    def ko(self):
        """KO状态"""
        self.state = FighterState.KO
        self.animator.set_state(AnimationState.KO)
        self.health = 0

    def update_direction(self, opponent_x: float):
        """更新朝向（面向对手）"""
        if opponent_x > self.x:
            self.direction = Direction.RIGHT
        else:
            self.direction = Direction.LEFT

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        """绘制角色"""
        from animation.sprite_loader import get_sprite
        from animation.animator import Animator

        # 获取当前动画帧
        pose = self.animator.get_pose_name()
        anim_frame = self.animator.get_current_frame()

        # 获取精灵帧
        sprite = get_sprite(
            self.player_id - 1,
            pose,
            self.facing_right,
            anim_frame
        )

        if sprite is None:
            return

        # 位置调整 (精灵高度偏移)
        draw_x = self.x - 48 - camera_x  # 96/2 = 48
        draw_y = self.y - 63  # 精灵高度

        # 无敌闪烁
        if self.is_invincible and int(self.invincible_timer * 20) % 2 == 0:
            sprite.set_alpha(100)

        # KO倒地效果 - 旋转倒地
        if self.state == FighterState.KO:
            sprite_copy = pygame.transform.rotate(sprite, -90)
            draw_x = self.x - sprite_copy.get_width() // 2 - camera_x
            draw_y = self.y - 40
            surface.blit(sprite_copy, (draw_x, draw_y))
        else:
            # 绘制精灵
            surface.blit(sprite, (draw_x, draw_y))

        # 绘制受击特效
        if self.hit_effect_timer > 0:
            pygame.draw.circle(surface, (255, 200, 50),
                             (int(self.x - camera_x), int(self.y - 80)), 20, 3)

        # 绘制护盾
        if self.shield_value > 0:
            shield_alpha = min(100, self.shield_value // 3)
            shield_surf = pygame.Surface((80, 120), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surf, (100, 200, 255, shield_alpha), (0, 0, 80, 120), 3)
            surface.blit(shield_surf, (int(self.x - 40 - camera_x), int(self.y - 120)))

        # 绘制特效
        self.effect_manager.draw(surface)

    def reset(self, x: float, y: float):
        """重置角色状态"""
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.health = self.max_health
        self.special_energy = 0
        self.state = FighterState.IDLE
        self.is_blocking = False
        self.block_input = False
        self.is_invincible = False
        self.is_attacking = False
        self.is_special_attacking = False
        self.current_attack = None
        self.current_special = None
        self.hitstun_timer = 0
        self.combat.reset()
        self.animator.reset()
        self.hit_effect_timer = 0
        self.slow_timer = 0
        self.stun_timer = 0
        self.curse_timer = 0
        self.shield_value = 0
        # 清除特效
        self.effect_manager.effect_texts.clear()
        self.effect_manager.particles.clear()
        self.effect_manager.effect_rings.clear()
        self.effect_manager.slash_effects.clear()
