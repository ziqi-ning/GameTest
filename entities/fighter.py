# Fighter - 战斗角色基类

import pygame
import random
import math
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
from entities.weapon_data import WeaponType, get_weapon, WeaponData
from assets.weapon_assets import WeaponAssets

# 全局终极实体管理器（所有角色共享同一个实例）
_global_ultimate_entity_manager = None

def get_ultimate_entity_manager(screen_width: int = 1280, screen_height: int = 720):
    """获取全局终极实体管理器（单例）"""
    global _global_ultimate_entity_manager
    if _global_ultimate_entity_manager is None:
        from entities.ultimate_entities import UltimateEntityManager
        _global_ultimate_entity_manager = UltimateEntityManager(screen_width, screen_height)
    return _global_ultimate_entity_manager

def reset_ultimate_entity_manager():
    """重置全局终极实体管理器（换局时调用）"""
    global _global_ultimate_entity_manager
    _global_ultimate_entity_manager = None


class Fighter:
    """战斗角色基类"""

    def __init__(self, player_id: int, char_data: CharacterData, x: float, y: float,
                 char_index: int = 0, stage=None):
        self.player_id = player_id
        self.char_data = char_data
        self.stats = char_data.stats
        self.char_index = char_index  # 角色索引（用于加载正确精灵）
        self.stage = stage  # 场景引用（用于平台碰撞）

        # 位置和移动
        self.x = x
        self.y = y
        self.vel_x = 0.0
        self.vel_y = 0.0
        self.direction = Direction.RIGHT if player_id == 1 else Direction.LEFT
        self.on_ground = True
        self.drop_through = False  # 穿台标志

        # 战斗属性
        self.health = self.stats.max_health
        self.max_health = self.stats.max_health
        self.special_energy = 0
        self.max_special = 100
        self.ultimate_pending_trigger: bool = False  # 必杀技已发动，等待触发终极特效

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
        self._char_effect_name = self.stats.name_cn

        # 武器系统（始终以拳头开始，武器通过道具掉落获得）
        self.weapon_data: WeaponData = get_weapon(WeaponType.FIST)

        # 道具掉落武器状态
        self.equipped_weapon: Optional[str] = None   # e.g. "nuke_launcher"
        self.weapon_uses: int = 0
        self.weapon_attack_pending: bool = False

        # 攻击状态
        self.current_attack: Optional[MoveData] = None
        self.current_special: Optional[SpecialMoveData] = None
        self.current_special_index: int = -1
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
        self.last_hit_by = 0  # 被谁命中了（0=无, 1=P1, 2=P2）用于触发VFX

        # 特殊效果状态
        self.slow_timer = 0.0  # 减速效果
        self.stun_timer = 0.0  # 眩晕效果
        self.curse_timer = 0.0  # 诅咒效果（降低攻击）
        self.shield_value = 0  # 护盾值
        self.max_shield = 300  # 最大护盾值（龚大哥）

        # 增益效果状态（I键必杀技产生）
        self.lifesteal_timer = 0.0  # 吸血效果持续时间
        self.lifesteal_active = False  # 吸血是否激活
        self.lifesteal_duration = 10.0  # 吸血持续时间
        self.freeze_timer = 0.0  # 冻结敌人效果
        self.freeze_target_id = 0  # 被冻结的目标ID

        # 军师增益状态
        self.junshi_multi_shot = 0  # 连发是否激活（0=未激活，1=激活）
        self.junshi_multi_shot_timer = 0.0  # 连发倒计时

        # 终极必杀技实体管理器（使用全局单例，所有角色共享）
        self.ultimate_entity_manager = get_ultimate_entity_manager()

        # 装备必杀技
        if char_data.special:
            self.special_manager.set_special_moves(char_data.special)

        # 小兵管理器（金币 + 随从系统）
        from entities.minion_manager import MinionManager
        self.minion_manager = MinionManager(player_id, self.stats.name_cn)

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

        move = self.current_attack
        dir_sign = 1 if self.facing_right else -1

        if move.active_start <= self.attack_frame < move.active_start + move.active_frames:
            hitbox_x = self.x + move.hitbox_offset[0] * dir_sign - move.hitbox_size[0] // 2
            hitbox_y = self.y - 120 + move.hitbox_offset[1]
            return (hitbox_x, hitbox_y, move.hitbox_size[0], move.hitbox_size[1])

        return None

    def get_special_hitbox_rect(self) -> Optional[Tuple[float, float, float, float]]:
        """获取当前必杀技攻击判定框"""
        if not self.is_special_attacking or not self.current_special:
            return None

        move = self.current_special
        dir_sign = 1 if self.facing_right else -1

        if not (move.active_start <= self.attack_frame < move.active_start + move.active_frames):
            return None

        hitbox_x = self.x + move.hitbox_offset[0] * dir_sign - move.hitbox_size[0] // 2
        hitbox_y = self.y - 120 + move.hitbox_offset[1]

        if self.direction == Direction.LEFT:
            hitbox_x = self.x - move.hitbox_offset[0] * dir_sign - move.hitbox_size[0] // 2

        return (hitbox_x, hitbox_y, move.hitbox_size[0], move.hitbox_size[1])

    def attack_weapon(self) -> bool:
        """
        Called by Player.handle_input() when heavy-attack key pressed.
        Returns True if a weapon attack was dispatched, False if unarmed.
        """
        if self.equipped_weapon and self.weapon_uses > 0:
            self.weapon_attack_pending = True
            return True
        return False

    def handle_input(self, left: bool, right: bool, up: bool, down: bool,
                   light_attack: bool, heavy_attack: bool, special: bool, block: bool):
        """处理输入（由子类或AI实现）"""
        pass

    def update(self, dt: float, opponent: Optional['Fighter'] = None):
        """更新角色状态"""
        # 更新特效系统
        self.effect_manager.update(dt)

        # 更新终极必杀技实体（P1国旗/P2激光/P3黑影/P4鸡蛋）
        # 注：实体在 Fighter.attack_special() 中生成，伤害由 main.py 统一处理
        # 这里仅被动更新实体timer以驱动动画

        # 更新投射物系统
        if opponent:
            self._update_projectiles(dt, opponent)

        # 更新特殊状态效果
        if self.freeze_timer > 0:
            self.freeze_timer -= dt
            self.stun_timer = 0  # 冻结时清除眩晕
        if self.stun_timer > 0:
            self.stun_timer -= dt

        # 更新无敌时间（必须在所有状态检查之前，因为被攻击后也要能结束无敌）
        if self.invincible_timer > 0:
            self.invincible_timer -= dt
            if self.invincible_timer <= 0:
                self.is_invincible = False

        # 如果被冻结或眩晕，不能继续移动
        if self.freeze_timer > 0 or self.stun_timer > 0:
            return  # 冻结/眩晕时不能动
        if self.slow_timer > 0:
            self.slow_timer -= dt
        if self.curse_timer > 0:
            self.curse_timer -= dt

        # 更新增益效果
        # 神秘人吸血效果
        if self.lifesteal_timer > 0:
            self.lifesteal_timer -= dt
            if self.lifesteal_timer <= 0:
                self.lifesteal_active = False

        # 军师连发效果
        if self.junshi_multi_shot_timer > 0:
            self.junshi_multi_shot_timer -= dt
            if self.junshi_multi_shot_timer <= 0:
                self.junshi_multi_shot = 0

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
                                      self.special_energy + 8 * dt)  # 每秒回复8点能量（够快）

        # 重力
        if not self.on_ground:
            self.vel_y += GRAVITY * 60 * dt

        # 移动
        self.x += self.vel_x * 60 * dt
        self.y += self.vel_y * 60 * dt

        # 平台碰撞
        self.on_ground = False
        if self.stage and self.stage.platforms and self.vel_y >= 0:
            feet_y = self.y
            for px, py, pw, ph in self.stage.platforms:
                if (px <= self.x <= px + pw and
                        py - 15 <= feet_y <= py + 8):
                    # 穿台模式：跳过此平台
                    if getattr(self, 'drop_through', False):
                        continue
                    self.y = py
                    self.vel_y = 0
                    self.on_ground = True
                    break
        # 落地后清除穿台标志
        if self.on_ground or self.y >= GROUND_Y:
            self.drop_through = False

        # 地面碰撞（兜底）
        if not self.on_ground and self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.vel_y = 0
            self.on_ground = True

        # 边界限制
        self.x = clamp(self.x, 60, 1220)

        # 攻击冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

    def _is_on_platform(self) -> bool:
        """判断是否站在平台上（非地面）"""
        if not self.stage or not self.stage.platforms:
            return False
        feet_y = self.y
        for px, py, pw, ph in self.stage.platforms:
            if (px <= self.x <= px + pw and abs(feet_y - py) < 5):
                return True
        return False

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

        # 下键：在平台上时穿台，否则下蹲
        if down and self.on_ground:
            # 检查是否站在平台上（非地面）
            if self._is_on_platform():
                self.drop_through = True
                self.on_ground = False
                self.vel_y = 1.0  # 给一个向下的初速度，脱离平台
            else:
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

        # 左右移动（朝向由 update_direction 根据对手位置统一控制，不要在这里设置）
        if left:
            self.vel_x = -self.stats.walk_speed
            if self.on_ground and self.state != FighterState.JUMP:
                self.state = FighterState.WALK
                self.animator.set_state(AnimationState.WALK)
        elif right:
            self.vel_x = self.stats.walk_speed
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
        """重攻击（远程投射，消耗蓝量）"""
        if self.attack_cooldown > 0 or self.is_attacking or self.hitstun_timer > 0:
            return

        if len(self.char_data.moves) > 1:
            move = self.char_data.moves[1]

            # 远程攻击需要消耗蓝量
            if move.is_ranged:
                mana_cost = getattr(move, 'mana_cost', 0)
                if self.special_energy < mana_cost:
                    return  # 蓝量不足，不发动
                self.special_energy -= mana_cost

            self.current_attack = move
            self.is_attacking = True
            self.attack_frame = 0
            self.state = FighterState.ATTACK_HEAVY
            self.animator.set_state(AnimationState.ATTACK_HEAVY)
            self.vel_x = 0

            # 军师增益：5连发效果 - 7秒内每次K键都发射5颗
            if "军师" in self._char_effect_name and self.junshi_multi_shot_timer > 0:
                # 连续发射5颗子弹
                from combat.special_moves import Projectile
                move = self.char_data.moves[1]
                dir_sign = 1 if self.facing_right else -1
                for i in range(5):
                    proj_x = self.x + 30 * dir_sign
                    proj_y = self.y - 80 - i * 5  # 稍微偏移
                    proj = Projectile(
                        x=proj_x, y=proj_y,
                        direction=dir_sign,
                        speed=move.projectile_speed,
                        damage=move.damage,
                        owner_id=self.player_id,
                        size=(60, 40)
                    )
                    proj.effect_type = move.effect_type
                    proj.hitstun = move.hitstun
                    proj.knockback = move.knockback
                    proj.knockback_up = move.knockback_up
                    proj.char_name = self._char_effect_name
                    proj.ignore_invincible = True  # 忽略无敌，连发才能全中
                    self.projectile_manager.projectiles.append(proj)
                # 显示连发提示
                self.effect_manager.add_text("5连发!", self.x, self.y - 200, (100, 200, 255), 32, 0.8)
            elif move.is_ranged:
                # 非军师或无连发buff时，发射正常投射物
                self._fire_ranged_attack(move)

    def attack_special(self, dt: float, move_index: int = 0):
        """发动必杀技（L键=0伤害，I键=1增益）"""
        if move_index >= len(self.char_data.special):
            return  # 没有第二个必杀技

        move = self.char_data.special[move_index]
        if self.special_energy < move.energy_cost:
            return
        if self.is_attacking or self.hitstun_timer > 0:
            return

        self.special_energy -= move.energy_cost

        # ── I键增益效果（move_index=1）─────────────────────
        if move_index == 1:
            # 尝试从Player获取opponent引用
            opponent_ref = None
            if hasattr(self, '_opponent_ref'):
                opponent_ref = self._opponent_ref
            if opponent_ref is None and opponent is not None:
                opponent_ref = opponent
            self._activate_buff_effect(move, opponent_ref)

            # 增益不需要动画帧，直接结束
            self.state = FighterState.IDLE
            self.animator.set_state(AnimationState.IDLE)
            self.is_attacking = False
            self.is_special_attacking = False
            self.current_special = None
            self.attack_cooldown = 0.3
            return

        # ── L键伤害必杀技（move_index=0）─────────────────────
        self.is_attacking = True
        self.is_special_attacking = True
        self.attack_frame = 0
        self.current_special = move
        self.current_special_index = move_index
        self.state = FighterState.ATTACK_SPECIAL
        self.animator.set_state(AnimationState.ATTACK_SPECIAL)
        self.vel_x = 0
        self.special_hit_count = 0
        self.ultimate_pending_trigger = True  # 通知 main.py 触发终极特效

        # 初始化攻击帧（由 Fighter.update() 的 update_attack() 统一推进）
        self.attack_frame = 0

        # 根据 effect_type 触发不同的终极实体
        effect_type = move.effect_type
        char_name = self._char_effect_name
        opponent_ref = None
        if hasattr(self, '_opponent_ref'):
            opponent_ref = self._opponent_ref

        if effect_type == "national_flag":
            # P1龚大哥：全屏五星红旗
            owner_is_p1 = (self.player_id == 1)
            self.ultimate_entity_manager.spawn_p1_flag(
                self.x, self.y, self.player_id, owner_is_p1
            )
            self.effect_manager.add_text(
                "五星红旗!", self.x, self.y - 180, (255, 220, 0), 48, 2.0
            )
            self.effect_manager.add_particle_burst(self.x, self.y - 100, 40,
                                                 (255, 200, 50), 15.0, 10.0)
            self.effect_manager.add_ring(self.x, self.y - 80, 100,
                                       (255, 50, 50), 1.5)
            self.screen_shake = 10

        elif effect_type == "laser_beam":
            # P2军师：高能激光对同一行
            self.ultimate_entity_manager.spawn_p2_laser(
                self.x, self.y, self.player_id,
                direction=(1 if self.facing_right else -1),
                owner=self
            )
            self.effect_manager.add_text(
                "高能激光!", self.x, self.y - 200, (50, 150, 255), 52, 2.0
            )
            self.effect_manager.add_particle_burst(self.x, self.y - 90, 50,
                                                 (50, 100, 255), 18.0, 12.0)
            self.effect_manager.add_ring(self.x, self.y - 90, 80,
                                       (50, 200, 255), 1.2)
            self.screen_shake = 15

        elif effect_type == "shadow_clone":
            # P3神秘人：黑影瞬移到敌人身后
            if opponent_ref:
                self.ultimate_entity_manager.spawn_p3_shadow(
                    self.x, self.y, self.player_id,
                    max_health=self.max_health,
                    target_x=opponent_ref.x,
                    target_facing_right=opponent_ref.facing_right,
                    duration=move.effect_duration
                )
            else:
                self.ultimate_entity_manager.spawn_p3_shadow(
                    self.x, self.y, self.player_id,
                    max_health=self.max_health,
                    target_x=self.x,
                    target_facing_right=self.facing_right,
                    duration=move.effect_duration
                )
            self.effect_manager.add_text(
                "黑影瞬斩!", self.x, self.y - 200, (180, 60, 255), 50, 2.0
            )
            self.effect_manager.add_particle_burst(self.x, self.y - 80, 60,
                                                 (80, 20, 160), 15.0, 10.0)
            self.effect_manager.add_ring(self.x, self.y - 80, 60,
                                       (120, 40, 200), 1.0)
            self.screen_shake = 12

        elif effect_type == "chicken_egg":
            # P4籽桐：召唤大公鸡和鸡蛋
            trapped_id = opponent_ref.player_id if opponent_ref else 2
            self.ultimate_entity_manager.spawn_p4_egg(
                self.x, self.y, self.player_id,
                trapped_target_id=trapped_id,
                trap_duration=move.effect_duration
            )
            self.effect_manager.add_text(
                "雕与蛋!", self.x, self.y - 200, (80, 200, 80), 52, 2.0
            )
            self.effect_manager.add_particle_burst(self.x, self.y - 80, 50,
                                                 (200, 180, 80), 15.0, 10.0)
            self.effect_manager.add_ring(self.x, self.y - 80, 70,
                                       (150, 255, 100), 1.2)
            self.screen_shake = 10

        else:
            # 旧版必杀技（兼容）
            effect_func = CharacterEffects.get_effect_function(char_name, move_index)
            if effect_func:
                effect_x = self.x + (50 if self.facing_right else -50)
                effect_func(self.effect_manager, effect_x, self.y - 50, move.name_cn)

    def _activate_buff_effect(self, move, opponent=None):
        """激活增益效果（I键必杀技）"""
        effect_type = move.effect_type
        duration = move.effect_duration
        value = move.effect_value

        char_name = self._char_effect_name

        # 龚大哥 - 护盾
        if "龚大哥" in char_name and effect_type == "shield":
            self.shield_value = int(value)  # value=300
            self.max_shield = int(value)
            self.effect_manager.add_text(
                f"护盾 +{int(value)}",
                self.x, self.y - 160, (100, 200, 255), 36, 2.0
            )
            self.effect_manager.add_ring(self.x, self.y - 80, 50, (100, 200, 255), 1.0)
            self.effect_manager.add_particle_burst(self.x, self.y - 80, 15, (100, 200, 255), 5.0, 5.0)

        # 军师 - 5连发
        elif "军师" in char_name and effect_type == "multi_shot":
            self.junshi_multi_shot = 1  # 激活连发
            self.junshi_multi_shot_timer = duration  # 7秒
            self.effect_manager.add_text(
                f"5连发! {int(duration)}秒",
                self.x, self.y - 160, (100, 150, 255), 36, 2.0
            )
            self.effect_manager.add_ring(self.x, self.y - 80, 60, (50, 100, 255), 1.2)
            self.effect_manager.add_particle_burst(self.x, self.y - 80, 20, (100, 150, 255), 6.0, 5.0)

        # 神秘人 - 吸血
        elif "神秘人" in char_name and effect_type == "lifesteal":
            self.lifesteal_active = True
            self.lifesteal_timer = duration  # 10秒
            heal_ratio = int(value * 100)  # 33%
            self.effect_manager.add_text(
                f"吸血 {heal_ratio}%! {int(duration)}秒",
                self.x, self.y - 160, (180, 50, 200), 36, 2.0
            )
            self.effect_manager.add_ring(self.x, self.y - 80, 50, (180, 50, 200), 1.0)
            self.effect_manager.add_particle_burst(self.x, self.y - 80, 15, (200, 100, 220), 5.0, 5.0)

        # 籽桐 - 冻结敌人
        elif "籽桐" in char_name and effect_type == "freeze":
            self.effect_manager.add_text(
                f"冰雕凝视! {int(duration)}秒",
                self.x, self.y - 160, (50, 200, 255), 36, 2.0
            )
            self.effect_manager.add_ring(self.x, self.y - 80, 80, (50, 150, 255), 1.5)
            self.effect_manager.add_particle_burst(self.x, self.y - 80, 25, (100, 200, 255), 8.0, 6.0)
            # 冻结敌人
            if opponent:
                opponent.freeze_timer = duration
                opponent.stun_timer = duration  # 冻结等同于眩晕
                self.freeze_target_id = opponent.player_id
                opponent.effect_manager.add_text(
                    "冻结!",
                    opponent.x, opponent.y - 150, (50, 200, 255), 40, 2.0
                )
                # 大范围冰冻特效
                opponent.effect_manager.add_ring(opponent.x, opponent.y - 80, 60, (50, 150, 255), 1.5)
                opponent.effect_manager.add_particle_burst(opponent.x, opponent.y - 80, 20, (100, 180, 255), 6.0, 6.0)

    def update_attack(self, dt: float, opponent: Optional['Fighter'] = None):
        """更新攻击状态"""
        self.attack_frame += 1

        # 必杀技使用 current_special，普通攻击使用 current_attack
        if self.is_special_attacking and self.current_special:
            move = self.current_special
        else:
            move = self.current_attack

        if move is None:
            # 防御性处理：没有攻击数据时结束攻击状态
            self.is_attacking = False
            self.is_special_attacking = False
            self.current_attack = None
            self.current_special = None
            self.attack_cooldown = 0.1
            self.state = FighterState.IDLE
            self.animator.set_state(AnimationState.IDLE)
            return

        # 同步动画帧 (让动画跟着攻击帧走)
        anim_frame = min(self.attack_frame // 3, self.animator.get_frame_count() - 1)
        # 强制设置动画帧
        self.animator.frame = anim_frame

        # 判定帧
        if (move.active_start <= self.attack_frame <
                move.active_start + move.active_frames):
            # 检测命中主角
            if opponent:
                self.check_hit(opponent)
            # 检测命中敌方小兵
            self._check_hit_enemy_minions()

        # 攻击结束（普通攻击用帧数，必杀技用特效时长控制）
        # 必杀技：优先用 animation_lock 控制玩家锁定时长，effect_duration 控制实体存活
        if self.is_special_attacking and self.current_special:
            # 锁定时长阈值（帧数）
            lock_duration = self.current_special.animation_lock
            if lock_duration <= 0:
                lock_duration = self.current_special.effect_duration
            if lock_duration <= 0:
                lock_duration = self.current_special.total_frames / 60.0
            lock_frames = int(lock_duration * 60)

            if self.attack_frame >= lock_frames:
                self.is_attacking = False
                self.is_special_attacking = False
                self.current_attack = None
                self.current_special = None
                self.attack_cooldown = 0.1
                self.state = FighterState.IDLE
                self.animator.set_state(AnimationState.IDLE)
                return
        elif self.attack_frame >= move.total_frames:
            self.is_attacking = False
            self.is_special_attacking = False
            self.current_attack = None
            self.current_special = None
            self.attack_cooldown = 0.1
            self.state = FighterState.IDLE
            self.animator.set_state(AnimationState.IDLE)

    def check_hit(self, opponent: 'Fighter'):
        """检查攻击是否命中"""
        # 必杀技使用 current_special，普通攻击使用 current_attack
        if self.is_special_attacking and self.current_special:
            move_data = self.current_special
        else:
            move_data = self.current_attack

        if not move_data or not opponent:
            return

        # 黑影必杀技（shadow_clone）不需要自身造成伤害，伤害由黑影实体处理
        if hasattr(move_data, 'effect_type') and move_data.effect_type == "shadow_clone":
            return

        # 国旗/激光/鸡蛋必杀技的伤害由实体系统（ultimate_entities）统一处理
        # 不走 hitbox 碰撞，避免双重伤害
        if hasattr(move_data, 'effect_type') and move_data.effect_type in (
            "national_flag", "laser_beam", "chicken_egg"
        ):
            return

        # 构建攻击数据用于命中检测
        class HitMoveData:
            def __init__(self, special_data):
                self.name = special_data.name
                self.knockback = special_data.knockback
                self.knockback_up = special_data.knockback_up
                self.can_block = True  # 必杀技也可被防御
                self.hitbox_offset = special_data.hitbox_offset
                self.hitbox_size = special_data.hitbox_size
                self.active_start = special_data.active_start
                self.active_frames = special_data.active_frames
                self.total_frames = special_data.total_frames

        move = HitMoveData(move_data)

        # 计算判定框位置（统一用 facing_right 处理方向）
        dir_sign = 1 if self.facing_right else -1
        # 只在active帧期间显示判定框
        if not (move.active_start <= self.attack_frame < move.active_start + move.active_frames):
            return

        hitbox_x = self.x + move.hitbox_offset[0] * dir_sign - move.hitbox_size[0] // 2
        hitbox_y = self.y - 120 + move.hitbox_offset[1]

        hitbox_rect = (hitbox_x, hitbox_y, move.hitbox_size[0], move.hitbox_size[1])

        hurtbox_rect = opponent.get_hurtbox_rect()
        original_move = self.current_attack  # 保存普通攻击数据（用于伤害计算）
        attack_move = move  # HitMoveData 对象（用于防御检查）

        # 碰撞检测
        if (hitbox_rect[0] < hurtbox_rect[0] + hurtbox_rect[2] and
            hitbox_rect[0] + hitbox_rect[2] > hurtbox_rect[0] and
            hitbox_rect[1] < hurtbox_rect[1] + hurtbox_rect[3] and
            hitbox_rect[1] + hitbox_rect[3] > hurtbox_rect[1]):

            # 检查防御
            if opponent.is_blocking and attack_move.can_block:
                self.apply_blocked_hit(opponent, move_data)
            elif not opponent.is_invincible:
                self.apply_hit(opponent, move_data)

                # 触发命中特效
                effect_func = CharacterEffects.get_effect_function(self._char_effect_name, -1)
                if effect_func:
                    effect_x = opponent.x
                    effect_func(self.effect_manager, effect_x, opponent.y - 50, move_data.name)

    def _check_hit_enemy_minions(self):
        """检测攻击判定框是否命中敌方小兵"""
        # 获取当前攻击数据
        if self.is_special_attacking and self.current_special:
            move_data = self.current_special
            offset = move_data.hitbox_offset
            size = move_data.hitbox_size
        elif self.current_attack:
            move_data = self.current_attack
            offset = move_data.hitbox_offset
            size = move_data.hitbox_size
        else:
            return

        if size[0] == 0 or size[1] == 0:
            return  # 远程攻击无近战判定框

        dir_sign = 1 if self.facing_right else -1
        hitbox_x = self.x + offset[0] * dir_sign - size[0] // 2
        hitbox_y = self.y - 120 + offset[1]
        # 扩大判定框宽度，更容易命中小兵
        expanded = (hitbox_x - 10, hitbox_y - 10, size[0] + 20, size[1] + 20)
        hitbox = expanded

        # 找对手的小兵管理器（通过 _opponent_ref）
        opponent = getattr(self, '_opponent_ref', None)
        if not opponent:
            return
        enemy_manager = getattr(opponent, 'minion_manager', None)
        if not enemy_manager:
            return

        damage = int(self.stats.attack_power * 0.8)  # 对小兵伤害略低

        for minion in enemy_manager.minions:
            if not minion.alive:
                continue
            mbox = minion.get_hurtbox()
            if (hitbox[0] < mbox[0] + mbox[2] and hitbox[0] + hitbox[2] > mbox[0] and
                    hitbox[1] < mbox[1] + mbox[3] and hitbox[1] + hitbox[3] > mbox[1]):
                minion.take_damage(damage)
                # 击杀奖励金币给攻击方
                if not minion.alive:
                    self.minion_manager.coins += 5
                    self.effect_manager.add_text("+5G", self.x, self.y - 160, (255, 220, 60), 26, 0.8)
                # 命中特效
                self.effect_manager.add_particle_burst(minion.x, minion.y - 20, 4, (255, 150, 50), 3.0, 2.0)

    def apply_hit(self, opponent: 'Fighter', move):
        """应用命中效果"""
        # 根据是否必杀技确定攻击倍率
        if self.is_special_attacking:
            attack_type = 'special'
        elif 'light' in move.name.lower():
            attack_type = 'light'
        elif 'heavy' in move.name.lower():
            attack_type = 'heavy'
        else:
            attack_type = 'light'

        # 计算伤害
        damage = calculate_damage(
            self.stats.attack_power,
            opponent.stats.defense,
            get_attack_multiplier(attack_type),
            1.0,
            self.combat.combo_count
        )

        # 应用伤害
        opponent.take_damage(damage, move.knockback, move.knockback_up, self.direction)

        # 更新连击
        combo_count = self.combat.register_hit(damage, move.name)

        # 更新能量
        self.special_energy = min(self.max_special,
                                  self.special_energy + calculate_special_energy_gain(damage, attack_type))

        # 神秘人吸血效果（攻击伤害的1/3回复生命）
        if self.lifesteal_active and self.lifesteal_timer > 0:
            heal_amount = damage // 3
            if heal_amount > 0:
                old_health = self.health
                self.health = min(self.max_health, self.health + heal_amount)
                actual_heal = self.health - old_health
                if actual_heal > 0:
                    self.effect_manager.add_text(
                        f"+{actual_heal}",
                        self.x, self.y - 150, (100, 255, 150), 28, 1.0
                    )
                    self.effect_manager.add_particle_burst(self.x, self.y - 80, 5, (100, 255, 150), 3.0, 3.0)

        # 视觉效果
        opponent.hit_effect_timer = 0.2
        opponent.last_hit_by = self.player_id  # 标记被谁命中
        self.screen_shake = 5

        # 近战命中斩击特效
        hit_x = opponent.x
        hit_y = opponent.y - 70
        char_name = self._char_effect_name
        if "龚大哥" in char_name:
            opponent.effect_manager.add_slash(hit_x, hit_y, 0.5, (255, 60, 30), 80)
            opponent.effect_manager.add_ring(hit_x, hit_y, 20, (255, 180, 50), 0.3)
        elif "军师" in char_name:
            opponent.effect_manager.add_slash(hit_x, hit_y, -0.3, (50, 120, 255), 70)
            opponent.effect_manager.add_ring(hit_x, hit_y, 25, (100, 200, 255), 0.25)
        elif "神秘人" in char_name:
            opponent.effect_manager.add_slash(hit_x, hit_y, 0.8, (180, 180, 200), 65)
            opponent.effect_manager.add_particle_burst(hit_x, hit_y, 5, (150, 150, 180), 3.0, 3.0)
        elif "籽桐" in char_name:
            opponent.effect_manager.add_slash(hit_x, hit_y, 0.3, (80, 200, 80), 75)
            opponent.effect_manager.add_particle_burst(hit_x, hit_y, 6, (100, 180, 60), 3.5, 3.0)

        # 显示伤害数字
        is_special = self.is_special_attacking
        dmg_color = (255, 200, 50) if is_special else (255, 80, 80)
        dmg_size = 44 if is_special else 36
        dmg_prefix = "★ " if is_special else ""
        opponent.effect_manager.add_text(
            f"{dmg_prefix}{damage}",
            opponent.x, opponent.y - 120, dmg_color, dmg_size, 1.2
        )

    def apply_blocked_hit(self, opponent: 'Fighter', move):
        """应用被防御的命中"""
        hitstun = calculate_hitstun(move.hitstun, is_blocking=True)

        # 击退（较小）
        knockback = move.knockback * 0.3
        opponent.vel_x = knockback * self.direction
        opponent.hitstun_timer = hitstun / 60.0

        # 减少能量
        opponent.special_energy = max(0, opponent.special_energy - 5)

        # 显示被防御的伤害数字
        if self.is_special_attacking:
            attack_type = 'special'
        elif 'light' in move.name.lower():
            attack_type = 'light'
        elif 'heavy' in move.name.lower():
            attack_type = 'heavy'
        else:
            attack_type = 'light'
        damage = calculate_damage(
            self.stats.attack_power,
            opponent.stats.defense,
            get_attack_multiplier(attack_type),
            1.0,
            self.combat.combo_count
        )
        block_damage = int(damage * 0.3)
        opponent.effect_manager.add_text(
            f"{block_damage}",
            opponent.x, opponent.y - 120, (160, 160, 255), 32, 1.0
        )

    def _fire_ranged_attack(self, move):
        """发射远程投射物"""
        from combat.special_moves import Projectile
        dir_sign = 1 if self.facing_right else -1
        # 投射物从角色前方发射，高度在角色上半身
        proj_x = self.x + 30 * dir_sign
        proj_y = self.y - 80

        proj = Projectile(
            x=proj_x,
            y=proj_y,
            direction=dir_sign,
            speed=move.projectile_speed,
            damage=move.damage,
            owner_id=self.player_id,
            size=(60, 40)
        )
        proj.effect_type = move.effect_type
        proj.hitstun = move.hitstun
        proj.knockback = move.knockback
        proj.knockback_up = move.knockback_up
        proj.char_name = self._char_effect_name
        self.projectile_manager.projectiles.append(proj)

        # ── 发射特效（枪口/旗帜挥动闪光）─────────────────────
        char_name = self._char_effect_name
        if "龚大哥" in char_name:
            # 红旗发射光芒（金色冲击波）
            self.effect_manager.add_ring(proj_x, proj_y, 30, (255, 200, 0), 0.3)
            self.effect_manager.add_particle_burst(proj_x, proj_y, 6, (255, 220, 50), 4.0, 3.0)
        elif "军师" in char_name:
            # 激光枪枪口闪光（蓝色）
            self.effect_manager.add_ring(proj_x, proj_y, 25, (50, 150, 255), 0.25)
            self.effect_manager.add_particle_burst(proj_x, proj_y, 8, (0, 200, 255), 3.0, 4.0)
            self.screen_shake = 2
        elif "神秘人" in char_name:
            # 星条旗甩出（暗红闪光）
            self.effect_manager.add_ring(proj_x, proj_y, 25, (100, 100, 180), 0.25)
            self.effect_manager.add_particle_burst(proj_x, proj_y, 5, (80, 80, 150), 3.0, 2.5)
        elif "籽桐" in char_name:
            # 老鹰飞出击羽毛散落
            self.effect_manager.add_particle_burst(proj_x, proj_y, 7, (160, 120, 60), 3.0, 3.5)
            self.effect_manager.add_ring(proj_x, proj_y, 20, (100, 160, 80), 0.2)

    def _schedule_junshi_multi_shot(self):
        """调度军师连发效果：每0.5秒发射一颗额外子弹"""
        # 军师连发效果通过定时器实现，在update中处理
        # 这里设置剩余连发数量，倒计时在update中递减
        pass

    def _fire_junshi_multi_shots(self, shots: int):
        """军师连发：每次K键发射多颗子弹"""
        if shots > 0 and len(self.char_data.moves) > 1:
            move = self.char_data.moves[1]  # K键的远程攻击
            # 发射多颗子弹，稍微改变y位置模拟散射
            for i in range(shots):
                # 稍微偏移y位置
                original_y = self.y
                self.y -= 5  # 向上偏移一点
                self._fire_ranged_attack(move)
                self.y = original_y
            # 显示连发提示
            self.effect_manager.add_text(
                f"5连发!",
                self.x, self.y - 200, (100, 200, 255), 32, 0.8
            )

    def _fire_junshi_bonus_projectile(self):
        """发射军师连发效果的额外投射物（兼容旧代码）"""
        if self.junshi_multi_shot > 0 and len(self.char_data.moves) > 1:
            move = self.char_data.moves[1]  # K键的远程攻击
            self._fire_ranged_attack(move)
            self.junshi_multi_shot -= 1
            # 显示连发提示
            self.effect_manager.add_text(
                f"连发 x{self.junshi_multi_shot + 1}",
                self.x, self.y - 180, (100, 200, 255), 24, 0.8
            )

    def freeze_opponent(self, opponent: 'Fighter', duration: float = 10.0):
        """冻结敌人（籽桐I技能效果）"""
        if opponent:
            opponent.freeze_timer = duration
            opponent.stun_timer = duration  # 冻结等同于长时间眩晕
            self.freeze_target_id = opponent.player_id
            opponent.effect_manager.add_text(
                "冻结!",
                opponent.x, opponent.y - 150, (50, 200, 255), 40, 2.0
            )
            # 大范围冰冻特效
            opponent.effect_manager.add_ring(opponent.x, opponent.y - 80, 60, (50, 150, 255), 1.5)
            opponent.effect_manager.add_ring(opponent.x, opponent.y - 80, 40, (150, 200, 255), 1.2)
            opponent.effect_manager.add_particle_burst(opponent.x, opponent.y - 80, 20, (100, 180, 255), 6.0, 6.0)

    def _update_projectiles(self, dt: float, opponent: 'Fighter'):
        """更新所有投射物（移动 + 碰撞检测）"""
        from utils import clamp
        for proj in list(self.projectile_manager.projectiles):
            if not proj.active:
                continue

            # 移动投射物
            proj.update(dt)

            # 边界检测
            proj_x = proj.x
            if proj_x < 0 or proj_x > 1280:
                proj.deactivate()
                continue

            # 获取投射物碰撞框
            proj_rect = proj.get_rect()
            opp_rect = opponent.get_hurtbox_rect()

            # AABB碰撞检测
            if (proj_rect[0] < opp_rect[0] + opp_rect[2] and
                proj_rect[0] + proj_rect[2] > opp_rect[0] and
                proj_rect[1] < opp_rect[1] + opp_rect[3] and
                proj_rect[1] + proj_rect[3] > opp_rect[1]):

                # 检查防御
                if opponent.is_blocking:
                    opponent.special_energy = max(0, opponent.special_energy - 5)
                    opponent.effect_manager.add_text(
                        "格挡", opponent.x, opponent.y - 100, (160, 160, 255), 28, 0.8
                    )
                elif not opponent.is_invincible or proj.ignore_invincible:
                    # 应用伤害
                    opponent.take_damage(proj.damage, proj.knockback, proj.knockback_up, proj.direction)
                    # 显示伤害数字
                    opponent.effect_manager.add_text(
                        f"{proj.damage}",
                        opponent.x, opponent.y - 120, (255, 80, 80), 36, 1.2
                    )
                    # 命中特效
                    opponent.hit_effect_timer = 0.2
                    opponent.last_hit_by = self.player_id
                    self.screen_shake = 3

                    # 投射物命中时的特效
                    proj_char = getattr(proj, 'char_name', '')
                    hit_x = opponent.x
                    hit_y = opponent.y - 70
                    if "龚大哥" in proj_char:
                        opponent.effect_manager.add_ring(hit_x, hit_y, 30, (255, 200, 0), 0.3)
                        opponent.effect_manager.add_particle_burst(hit_x, hit_y, 6, (255, 220, 50), 4.0, 3.0)
                    elif "军师" in proj_char:
                        opponent.effect_manager.add_ring(hit_x, hit_y, 30, (50, 150, 255), 0.25)
                        opponent.effect_manager.add_particle_burst(hit_x, hit_y, 8, (0, 200, 255), 3.0, 4.0)
                    elif "神秘人" in proj_char:
                        opponent.effect_manager.add_ring(hit_x, hit_y, 25, (100, 100, 180), 0.25)
                        opponent.effect_manager.add_particle_burst(hit_x, hit_y, 5, (80, 80, 150), 3.0, 2.5)
                    elif "籽桐" in proj_char:
                        opponent.effect_manager.add_particle_burst(hit_x, hit_y, 7, (160, 120, 60), 3.0, 3.5)
                        opponent.effect_manager.add_ring(hit_x, hit_y, 20, (100, 160, 80), 0.2)

                    # 投射物命中后消失
                    proj.deactivate()

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

    def take_minion_damage(self, damage: int, attacker_owner_id: int):
        """承受小兵伤害（无击退，轻微硬直）"""
        if self.is_invincible:
            return
        # 护盾吸收
        if self.shield_value > 0:
            absorbed = min(self.shield_value, damage)
            self.shield_value -= absorbed
            damage -= absorbed
            if damage <= 0:
                return
        self.health = max(0, self.health - damage)
        self.hit_effect_timer = 0.1
        self.last_hit_by = attacker_owner_id
        self.effect_manager.add_text(
            f"-{damage}", self.x, self.y - 100, (255, 140, 80), 28, 0.8
        )
        if self.health <= 0:
            self.ko()

    def apply_knockback(self, dt: float):
        """应用击退"""
        self.x += self.knockback_x * 60 * dt
        self.y += self.knockback_y * 60 * dt

        self.knockback_y += GRAVITY * 30 * dt

        # 平台碰撞（击退时也要能站在平台上）
        self.on_ground = False
        if self.stage and self.stage.platforms and self.knockback_y >= 0:
            feet_y = self.y
            for px, py, pw, ph in self.stage.platforms:
                if (px <= self.x <= px + pw and
                        py - 10 <= feet_y <= py + 10):
                    self.y = py
                    self.knockback_y = 0
                    self.on_ground = True
                    break
        if not self.on_ground and self.y >= GROUND_Y:
            self.y = GROUND_Y
            self.knockback_y = 0
            self.on_ground = True

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

    def _draw_attack_range(self, surface: pygame.Surface, camera_x: int):
        """绘制攻击范围判定框可视化"""
        hitbox_rect = None
        move_name = ""

        if self.is_special_attacking and self.current_special:
            # 必杀技hitbox调试框已禁用（全屏技能不需要）
            pass
        elif self.is_attacking and self.current_attack:
            hitbox_rect = self.get_hitbox_rect()
            if hitbox_rect:
                move_name = self.current_attack.name
                # 根据当前攻击状态选择颜色（轻攻击/重攻击）
                state_str = str(self.state)
                if 'light' in state_str:
                    color = (255, 100, 100, 80)     # 红色 - 轻攻击
                    border_color = (255, 150, 150)
                elif 'heavy' in state_str:
                    color = (100, 100, 255, 80)     # 蓝色 - 重攻击
                    border_color = (150, 150, 255)
                else:
                    color = (255, 180, 100, 80)     # 橙色 - 普通
                    border_color = (255, 200, 150)

        if hitbox_rect:
            x, y, w, h = hitbox_rect
            x -= camera_x

            # 创建半透明填充
            s = pygame.Surface((int(w), int(h)), pygame.SRCALPHA)
            s.fill(color)
            surface.blit(s, (int(x), int(y)))

            # 绘制边框
            pygame.draw.rect(surface, border_color, (int(x), int(y), int(w), int(h)), 2)

            # 绘制角标（表示这是攻击判定框）
            corner_size = 6
            # 左上角
            pygame.draw.line(surface, border_color, (x, y + corner_size), (x, y), 3)
            pygame.draw.line(surface, border_color, (x + corner_size, y), (x, y), 3)
            # 右上角
            pygame.draw.line(surface, border_color, (x + w - corner_size, y), (x + w, y), 3)
            pygame.draw.line(surface, border_color, (x + w, y + corner_size), (x + w, y), 3)
            # 左下角
            pygame.draw.line(surface, border_color, (x, y + h - corner_size), (x, y + h), 3)
            pygame.draw.line(surface, border_color, (x + corner_size, y + h), (x, y + h), 3)
            # 右下角
            pygame.draw.line(surface, border_color, (x + w - corner_size, y + h), (x + w, y + h), 3)
            pygame.draw.line(surface, border_color, (x + w, y + h - corner_size), (x + w, y + h), 3)

            # 在判定框上方显示攻击类型
            if move_name:
                try:
                    font = pygame.font.SysFont("microsoftyahei", 14, bold=True)
                except:
                    font = pygame.font.Font(None, 14)
                text_surf = font.render(move_name, True, border_color)
                text_surf.set_alpha(200)
                tx = x + w // 2 - text_surf.get_width() // 2
                ty = y - text_surf.get_height() - 2
                if ty >= 0:
                    surface.blit(text_surf, (int(tx), int(ty)))

    def draw(self, surface: pygame.Surface, camera_x: int = 0):
        """绘制角色"""
        from animation.sprite_loader import get_sprite

        screen_x = self.x - camera_x
        pose = self.animator.get_pose_name()
        anim_frame = self.animator.get_current_frame()

        # 获取精灵帧
        sprite = get_sprite(
            self.char_index,
            pose,
            self.facing_right,
            anim_frame
        )

        # 无敌闪烁
        invincible_blink = (self.is_invincible and int(self.invincible_timer * 20) % 2 == 0)

        # KO倒地效果
        if self.state == FighterState.KO:
            if sprite is not None:
                sprite_copy = pygame.transform.rotate(sprite, -90)
                draw_x = self.x - sprite_copy.get_width() // 2 - camera_x
                draw_y = self.y - 40
                if invincible_blink:
                    sprite_copy.set_alpha(100)
                surface.blit(sprite_copy, (draw_x, draw_y))
            else:
                self._draw_fallback_body(surface, screen_x, "ko")
            self._draw_projectiles(surface, camera_x)
            return

        # 绘制角色身体精灵（或fallback轮廓）
        if sprite is not None:
            draw_x = self.x - 48 - camera_x  # 96/2 = 48
            draw_y = self.y - 63  # 精灵高度
            if invincible_blink:
                sprite.set_alpha(100)
            surface.blit(sprite, (draw_x, draw_y))
        else:
            self._draw_fallback_body(surface, screen_x, pose)

        # 绘制武器（挂在手上）
        self._draw_weapon(surface, screen_x, camera_x)

        # 绘制受击特效
        if self.hit_effect_timer > 0:
            pygame.draw.circle(surface, (255, 200, 50),
                             (int(screen_x), int(self.y - 80)), 20, 3)

        # 绘制攻击范围判定框
        self._draw_attack_range(surface, camera_x)

        # 绘制护盾
        if self.shield_value > 0:
            shield_alpha = min(100, self.shield_value // 3)
            shield_surf = pygame.Surface((80, 120), pygame.SRCALPHA)
            pygame.draw.ellipse(shield_surf, (100, 200, 255, shield_alpha), (0, 0, 80, 120), 3)
            surface.blit(shield_surf, (int(self.x - 40 - camera_x), int(self.y - 120)))

        # 绘制特效
        self.effect_manager.draw(surface)

        # 绘制投射物
        self._draw_projectiles(surface, camera_x)

    def _draw_fallback_body(self, surface: pygame.Surface, screen_x: float, pose: str):
        """当角色精灵文件缺失时，绘制一个彩色的角色轮廓"""
        primary = self.stats.color
        secondary = self.stats.secondary_color
        facing = 1 if self.facing_right else -1

        # 根据姿态调整身体形状
        is_crouching = (pose == 'crouch')
        is_walking = (pose == 'walk')
        is_attacking = 'attack' in pose
        is_hit = pose in ('hit', 'block')

        if is_crouching:
            # 蹲下姿势：身体压低
            body_h = 60
            body_y = self.y - body_h
            # 身体
            pygame.draw.rect(surface, primary,
                           (int(screen_x - 25), int(body_y), 50, body_h))
            pygame.draw.rect(surface, secondary,
                           (int(screen_x - 25), int(body_y), 50, body_h), 2)
            # 头
            pygame.draw.ellipse(surface, (240, 195, 160),
                              (int(screen_x - 12), int(body_y - 20), 24, 24))
            # 脚
            pygame.draw.rect(surface, secondary,
                           (int(screen_x - 28), int(self.y - 8), 20, 8))
            pygame.draw.rect(surface, secondary,
                           (int(screen_x + 8), int(self.y - 8), 20, 8))
        elif is_hit:
            # 受击姿势：身体后仰
            body_h = 80
            body_y = self.y - body_h
            # 身体（带角度）
            pygame.draw.rect(surface, primary,
                           (int(screen_x - 22), int(body_y + 5), 44, body_h - 10))
            pygame.draw.rect(surface, (255, 80, 80),
                           (int(screen_x - 22), int(body_y + 5), 44, body_h - 10), 2)
            # 头
            pygame.draw.ellipse(surface, (240, 195, 160),
                              (int(screen_x - 14 + 5 * facing), int(body_y - 12), 24, 24))
            # 痛苦效果
            pygame.draw.circle(surface, (255, 100, 100, 120),
                             (int(screen_x), int(self.y - 100)), 15)
        elif is_attacking:
            # 攻击姿势：前倾伸手
            body_h = 100
            body_y = self.y - body_h
            # 身体
            pygame.draw.rect(surface, primary,
                           (int(screen_x - 20), int(body_y + 5), 40, body_h - 5))
            pygame.draw.rect(surface, secondary,
                           (int(screen_x - 20), int(body_y + 5), 40, body_h - 5), 2)
            # 攻击手臂（朝前伸出）
            arm_x = screen_x + 15 * facing
            pygame.draw.line(surface, (240, 195, 160),
                           (int(screen_x + 5 * facing), int(body_y + 35)),
                           (int(arm_x), int(body_y + 30)), 6)
            # 另一只手
            pygame.draw.line(surface, (240, 195, 160),
                           (int(screen_x - 5 * facing), int(body_y + 40)),
                           (int(screen_x - 15 * facing), int(body_y + 50)), 5)
            # 头
            pygame.draw.ellipse(surface, (240, 195, 160),
                              (int(screen_x - 12), int(body_y - 8), 24, 24))
            # 腿
            if is_walking:
                leg_offset = int(math.sin(pygame.time.get_ticks() * 0.01) * 10)
            else:
                leg_offset = 0
            pygame.draw.line(surface, secondary,
                           (int(screen_x - 8), int(body_y + body_h - 5)),
                           (int(screen_x - 12 + leg_offset), int(self.y)), 7)
            pygame.draw.line(surface, secondary,
                           (int(screen_x + 8), int(body_y + body_h - 5)),
                           (int(screen_x + 12 - leg_offset), int(self.y)), 7)
        elif is_walking:
            # 走路姿势
            body_h = 110
            body_y = self.y - body_h
            leg_offset = int(math.sin(pygame.time.get_ticks() * 0.01) * 12)
            # 身体
            pygame.draw.rect(surface, primary,
                           (int(screen_x - 20), int(body_y + 10), 40, body_h - 15))
            pygame.draw.rect(surface, secondary,
                           (int(screen_x - 20), int(body_y + 10), 40, body_h - 15), 2)
            # 头
            pygame.draw.ellipse(surface, (240, 195, 160),
                              (int(screen_x - 12), int(body_y), 24, 24))
            # 走路手臂摆动
            pygame.draw.line(surface, (240, 195, 160),
                           (int(screen_x + 5 * facing), int(body_y + 30)),
                           (int(screen_x + 12 * facing + leg_offset), int(body_y + 50)), 6)
            pygame.draw.line(surface, (240, 195, 160),
                           (int(screen_x - 5 * facing), int(body_y + 30)),
                           (int(screen_x - 12 * facing - leg_offset), int(body_y + 50)), 5)
            # 腿
            pygame.draw.line(surface, secondary,
                           (int(screen_x - 8), int(body_y + body_h - 5)),
                           (int(screen_x - 10 + leg_offset), int(self.y)), 7)
            pygame.draw.line(surface, secondary,
                           (int(screen_x + 8), int(body_y + body_h - 5)),
                           (int(screen_x + 10 - leg_offset), int(self.y)), 7)
        else:
            # 默认站立姿势
            body_h = 110
            body_y = self.y - body_h
            # 身体
            pygame.draw.rect(surface, primary,
                           (int(screen_x - 20), int(body_y + 10), 40, body_h - 15))
            pygame.draw.rect(surface, secondary,
                           (int(screen_x - 20), int(body_y + 10), 40, body_h - 15), 2)
            # 头
            pygame.draw.ellipse(surface, (240, 195, 160),
                              (int(screen_x - 12), int(body_y), 24, 24))
            # 手臂自然下垂
            pygame.draw.line(surface, (240, 195, 160),
                           (int(screen_x + 10 * facing), int(body_y + 30)),
                           (int(screen_x + 15 * facing), int(body_y + 60)), 6)
            pygame.draw.line(surface, (240, 195, 160),
                           (int(screen_x - 10 * facing), int(body_y + 30)),
                           (int(screen_x - 15 * facing), int(body_y + 60)), 6)
            # 腿
            pygame.draw.line(surface, secondary,
                           (int(screen_x - 8), int(body_y + body_h - 5)),
                           (int(screen_x - 10), int(self.y)), 7)
            pygame.draw.line(surface, secondary,
                           (int(screen_x + 8), int(body_y + body_h - 5)),
                           (int(screen_x + 10), int(self.y)), 7)

        # 攻击范围发光（如果是攻击状态）
        if 'attack' in pose and self.is_attacking:
            glow_surf = pygame.Surface((120, 140), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_surf, (*primary, 40), (10, 10, 100, 120))
            surface.blit(glow_surf, (int(screen_x - 60), int(self.y - 150)))

    def _draw_weapon(self, surface: pygame.Surface, screen_x: float, camera_x: int):
        """绘制角色武器（定位在角色手中）

        所有坐标均为 screen space (screen_x = world_x - camera_x)。
        武器根据当前姿态(pose)调整手部位置，并按 weapon_type 分发绘制。
        优先绘制装备的掉落道具武器（核弹/加特林/法杖）。
        """

        facing = 1 if self.facing_right else -1
        pose = self.animator.get_pose_name()
        is_attacking = self.is_attacking and not self.is_special_attacking
        is_crouching = (pose == 'crouch')
        is_walking = (pose == 'walk')

        # --- 根据姿态计算手部位置（screen space） ---
        if is_crouching:
            hand_y_offset = -35
        elif is_attacking:
            hand_y_offset = -60
        elif is_walking:
            bob = int(math.sin(pygame.time.get_ticks() * 0.01) * 3)
            hand_y_offset = -52 + bob
        else:
            hand_y_offset = -50

        if is_attacking:
            hand_x = screen_x + 30 * facing
        else:
            hand_x = screen_x + 8 * facing

        hand_y = self.y + hand_y_offset

        # 帧动画索引（老鹰翅膀扑动）
        anim_idx = 0
        if is_attacking and self.current_attack:
            total = max(self.current_attack.total_frames, 1)
            anim_idx = int((self.attack_frame / total) * 7) % 7

        # 优先绘制装备的掉落道具武器（核弹/加特林/法杖）
        if self.equipped_weapon and self.weapon_uses > 0:
            self._draw_equipped_weapon(surface, hand_x, hand_y, facing, is_attacking, screen_x)
            return

        # 按 weapon_type 分发（默认武器）
        weapon_type = self.weapon_data.weapon_type
        if weapon_type == WeaponType.FLAG:
            self._draw_flag_weapon(surface, hand_x, hand_y, facing, is_attacking)
        elif weapon_type == WeaponType.LASER:
            self._draw_gun_weapon(surface, hand_x, hand_y, facing, is_attacking)
        elif weapon_type == WeaponType.DAGGER:
            self._draw_dagger_weapon(surface, hand_x, hand_y, facing, is_attacking)
        elif weapon_type == WeaponType.EAGLE:
            self._draw_eagle_weapon(surface, hand_x, hand_y, facing, is_attacking, anim_idx)
        elif weapon_type == WeaponType.PISTOL:
            self._draw_gun_weapon(surface, hand_x, hand_y, facing, is_attacking)
        elif weapon_type == WeaponType.RIFLE:
            self._draw_rifle_weapon(surface, hand_x, hand_y, facing, is_attacking)
        elif weapon_type == WeaponType.NUNCHAKU:
            self._draw_nunchaku_weapon(surface, hand_x, hand_y, facing, is_attacking)
        elif weapon_type == WeaponType.SHURIKEN:
            self._draw_shuriken_weapon(surface, hand_x, hand_y, facing, is_attacking)
        else:
            self._draw_fist_weapon(surface, hand_x, hand_y, facing, is_attacking)

    def _draw_equipped_weapon(self, surface, hand_x: float, hand_y: float, facing: int,
                              is_attacking: bool, screen_x: float):
        """绘制装备的掉落道具武器（核弹/加特林/法杖）"""
        weapon = self.equipped_weapon
        timer_t = pygame.time.get_ticks() * 0.001

        if weapon == "nuke_launcher":
            # 核弹发射器（肩扛式火箭筒）
            dir_sign = 1 if facing > 0 else -1
            # 筒身角度（肩扛）
            if is_attacking:
                angle = math.radians(30 * facing)
            else:
                angle = math.radians(15 * facing)
            surf_w, surf_h = 70, 30
            rot_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            # 筒身
            pygame.draw.rect(rot_surf, (100, 100, 110), (5, 8, 60, 14), border_radius=3)
            pygame.draw.rect(rot_surf, (140, 140, 150), (5, 8, 60, 6), border_radius=2)
            # 发射口
            pygame.draw.ellipse(rot_surf, (80, 80, 90), (55, 5, 12, 20))
            pygame.draw.ellipse(rot_surf, (60, 60, 70), (55, 8, 12, 14))
            # 把手
            pygame.draw.rect(rot_surf, (120, 80, 40), (15, 18, 10, 12), border_radius=2)
            # 准星
            pygame.draw.circle(rot_surf, (255, 80, 80), (58, 15), 3)
            pygame.draw.circle(rot_surf, (255, 200, 50), (58, 15), 2)
            rot_surf = pygame.transform.rotate(rot_surf, -angle * facing * (180 / math.pi))
            rw, rh = rot_surf.get_size()
            surface.blit(rot_surf, (int(hand_x - rw // 2), int(hand_y - rh // 2 - 10)))
            # 使用次数指示
            for i in range(self.weapon_uses):
                dot_x = hand_x + 15 * facing + i * 8 * facing
                dot_y = hand_y + 15
                pygame.draw.circle(surface, (255, 50, 50), (int(dot_x), int(dot_y)), 3)

        elif weapon == "gatling":
            # 加特林机枪（双手持握的大型机枪）
            dir_sign = 1 if facing > 0 else -1
            surf_w, surf_h = 80, 40
            rot_surf = pygame.Surface((surf_w, surf_h), pygame.SRCALPHA)
            # 枪身主体
            pygame.draw.rect(rot_surf, (120, 120, 130), (5, 15, 70, 12), border_radius=2)
            pygame.draw.rect(rot_surf, (160, 160, 170), (5, 15, 70, 5), border_radius=2)
            # 枪管（多个圆筒表示转管）
            for i in range(6):
                bx = 65 + i * 2
                pygame.draw.circle(rot_surf, (100, 100, 110), (bx, 18), 5)
                pygame.draw.circle(rot_surf, (140, 140, 150), (bx, 18), 4)
            # 供弹带
            pygame.draw.rect(rot_surf, (80, 70, 60), (10, 23, 40, 6), border_radius=1)
            # 把手
            pygame.draw.rect(rot_surf, (80, 60, 40), (20, 22, 8, 14), border_radius=2)
            pygame.draw.rect(rot_surf, (80, 60, 40), (38, 22, 8, 14), border_radius=2)
            # 旋转动画
            rot_angle = timer_t * 20 * facing
            rot_surf = pygame.transform.rotate(rot_surf, 0)
            surface.blit(rot_surf, (int(hand_x - 40), int(hand_y - 25)))
            # 使用次数
            for i in range(self.weapon_uses):
                dot_x = hand_x - 30 * facing + i * 8 * facing
                dot_y = hand_y + 25
                pygame.draw.circle(surface, (255, 220, 80), (int(dot_x), int(dot_y)), 3)

        elif weapon in ("staff_red", "staff_blue", "staff_green"):
            # 法杖
            staff_colors = {
                "staff_red": ((200, 60, 60), (255, 150, 50), (255, 220, 100)),
                "staff_blue": ((50, 100, 220), (100, 180, 255), (180, 230, 255)),
                "staff_green": ((50, 180, 60), (150, 255, 100), (200, 255, 150)),
            }
            body_color, glow_color, tip_color = staff_colors.get(
                weapon, ((200, 200, 200), (255, 255, 200), (255, 255, 255)))
            # 杖身（倾斜的棒子）
            pulse = math.sin(timer_t * 4) * 0.15 + 0.85
            sway = math.sin(timer_t * 2) * 3
            if is_attacking:
                staff_end_x = hand_x + 25 * facing
                staff_end_y = hand_y - 40
            else:
                staff_end_x = hand_x + 15 * facing + sway
                staff_end_y = hand_y + 35
            # 杖身
            pygame.draw.line(surface, body_color, (int(hand_x), int(hand_y)),
                           (int(staff_end_x), int(staff_end_y)), 6)
            pygame.draw.line(surface, glow_color, (int(hand_x), int(hand_y)),
                           (int(staff_end_x), int(staff_end_y)), 3)
            # 杖头（发光球体）
            orb_radius = int(10 * pulse)
            glow_surf = pygame.Surface((orb_radius * 4 + 10, orb_radius * 4 + 10), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*glow_color, 60), (orb_radius * 2 + 5, orb_radius * 2 + 5), orb_radius * 2)
            pygame.draw.circle(glow_surf, (*tip_color, 200), (orb_radius * 2 + 5, orb_radius * 2 + 5), orb_radius)
            pygame.draw.circle(glow_surf, (255, 255, 255), (orb_radius * 2 + 5, orb_radius * 2 + 5), orb_radius // 2)
            surface.blit(glow_surf, (int(staff_end_x - orb_radius * 2 - 5), int(staff_end_y - orb_radius * 2 - 5)))
            pygame.draw.circle(surface, glow_color, (int(staff_end_x), int(staff_end_y)), orb_radius)
            pygame.draw.circle(surface, tip_color, (int(staff_end_x), int(staff_end_y)), orb_radius // 2)
            # 使用次数
            for i in range(self.weapon_uses):
                dot_x = staff_end_x + (i - 1) * 8 * facing
                dot_y = staff_end_y + 15
                pygame.draw.circle(surface, body_color, (int(dot_x), int(dot_y)), 3)

    def _flip(self, surf: pygame.Surface) -> pygame.Surface:
        """左右翻转sprite"""
        return pygame.transform.flip(surf, True, False)

    def _get_weapon_sprite(self, sprite_key: str) -> pygame.Surface:
        """从 WeaponAssets 加载 sprite，失败返回 1x1 placeholder"""
        if not WeaponAssets._loaded:
            WeaponAssets._ensure_loaded()
        return WeaponAssets.get(sprite_key)

    # ------------------------------------------------------------------
    # 各武器绘制方法（screen space）
    # ------------------------------------------------------------------

    def _draw_fist_weapon(self, surface, hand_x, hand_y, facing, is_attacking):
        """拳头（徒手）"""
        fist_w, fist_h = 22, 18
        fx = hand_x - fist_w // 2
        fy = hand_y - fist_h // 2
        # 主体
        pygame.draw.ellipse(surface, (220, 180, 140), (int(fx), int(fy), fist_w, fist_h))
        pygame.draw.ellipse(surface, (240, 200, 160), (int(fx + 2), int(fy + 2), fist_w - 4, fist_h - 6))
        # 指节
        for i in range(3):
            px = fx + 4 + i * 5
            pygame.draw.line(surface, (200, 160, 120), (px, fy + fist_h - 3), (px, fy + fist_h), 2)
        if is_attacking:
            glow_s = pygame.Surface((fist_w + 8, fist_h + 8), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_s, (255, 200, 100, 60), glow_s.get_rect())
            surface.blit(glow_s, (int(fx - 4), int(fy - 4)))

    def _draw_flag_weapon(self, surface, hand_x, hand_y, facing, is_attacking):
        """五星红旗（旗杆握在手中）"""
        wave = math.sin(pygame.time.get_ticks() * 0.006) * 6
        if is_attacking:
            wave *= 2.0
        # 旗杆
        pole_x = hand_x
        pole_top_y = hand_y
        pole_end_x = hand_x + 8 * facing
        pole_end_y = hand_y + 38
        pygame.draw.line(surface, (210, 170, 50), (int(pole_x), int(pole_top_y)),
                       (int(pole_end_x), int(pole_end_y)), 5)
        # 红旗
        fx = pole_end_x + wave * facing
        fy = pole_end_y - 26
        pygame.draw.rect(surface, (220, 30, 30), (int(fx), int(fy), int(34 * facing), 22))
        pygame.draw.rect(surface, (160, 15, 15), (int(fx), int(fy), int(34 * facing), 22), 1)
        # 五角星
        star_x = fx + 12 * facing
        star_y = fy + 11
        pts = []
        for i in range(5):
            oa = math.radians(90 + i * 72)
            ia = math.radians(90 + i * 72 + 36)
            pts.append((star_x + math.cos(oa) * 6, star_y - math.sin(oa) * 6))
            pts.append((star_x + math.cos(ia) * 6 * 0.38, star_y - math.sin(ia) * 6 * 0.38))
        if len(pts) >= 10:
            pygame.draw.polygon(surface, (255, 220, 0), pts)

    def _draw_gun_weapon(self, surface, hand_x, hand_y, facing, is_attacking):
        """激光枪 / 手枪 / 小型枪械（共用渲染）
        优先使用 era_weapons 中的 pistol_gun.png（52x24），
        备用 WeaponData.sprite_key（如 laser_gun）。
        如果所有资源都缺失，则使用程序化绘制。"""
        sprite_key = self.weapon_data.sprite_key
        sprite_loaded = False
        orig_size = (1, 1)
        grip_px = self.weapon_data.grip_px

        # pistol_gun 优先
        sprite = self._get_weapon_sprite('pistol_gun')
        if sprite.get_size() != (1, 1):
            orig_size = sprite.get_size()
            sprite_loaded = True
        elif self._get_weapon_sprite(sprite_key).get_size() != (1, 1):
            sprite = self._get_weapon_sprite(sprite_key)
            orig_size = sprite.get_size()
            sprite_loaded = True
        elif self._get_weapon_sprite('weapon_p_45').get_size() != (1, 1):
            sprite = self._get_weapon_sprite('weapon_p_45')
            orig_size = sprite.get_size()
            sprite_loaded = True

        if sprite_loaded:
            target_h = 28
            scale = target_h / orig_size[1]
            new_w = max(1, int(orig_size[0] * scale))
            new_h = max(1, int(orig_size[1] * scale))
            sprite = pygame.transform.smoothscale(sprite, (new_w, new_h))
            if facing < 0:
                sprite = self._flip(sprite)
            blit_x = hand_x - grip_px
            blit_y = hand_y - new_h // 2
            surface.blit(sprite, (int(blit_x), int(blit_y)))
            tip_x = hand_x + (new_w - grip_px) * facing
        else:
            # 程序化备用：绘制科幻激光枪
            self._draw_laser_gun_procedural(surface, hand_x, hand_y, facing, is_attacking)
            tip_x = hand_x + 22 * facing

        # 能量/枪口光效
        glow = abs(math.sin(pygame.time.get_ticks() * 0.015))
        intensity = 1.0 if is_attacking else (0.5 + 0.5 * glow)
        glow_c = (int(30 * intensity), int(180 * intensity), 255)
        pygame.draw.circle(surface, glow_c, (int(tip_x), int(hand_y)), int(3 + glow * 2))

    def _draw_laser_gun_procedural(self, surface, hand_x, hand_y, facing, is_attacking):
        """程序化绘制科幻激光枪（备用方案）"""
        # 枪身（深蓝灰色矩形）
        gun_color = (60, 60, 90)
        body_x = hand_x - 6
        body_y = hand_y - 10
        pygame.draw.rect(surface, gun_color, (int(body_x), int(body_y), 28, 20))
        pygame.draw.rect(surface, (80, 80, 110), (int(body_x), int(body_y), 28, 20), 1)

        # 枪管
        barrel_x = hand_x + 22 * facing
        pygame.draw.rect(surface, (50, 50, 80), (int(min(body_x, barrel_x)), int(body_y + 5), abs(barrel_x - body_x) + 8, 10))
        pygame.draw.rect(surface, (70, 70, 100), (int(min(body_x, barrel_x)), int(body_y + 5), abs(barrel_x - body_x) + 8, 10), 1)

        # 能量指示灯（蓝色发光条）
        indicator_x = hand_x - 3
        indicator_y = body_y + 3
        pygame.draw.rect(surface, (30, 180, 255), (int(indicator_x), int(indicator_y), 16, 4))
        glow = abs(math.sin(pygame.time.get_ticks() * 0.01))
        pygame.draw.rect(surface, (100, 220, 255), (int(indicator_x), int(indicator_y), int(16 * (0.5 + 0.5 * glow)), 4))

        # 握把
        pygame.draw.rect(surface, (40, 40, 60), (int(body_x + 5), int(body_y + 18), 10, 10))
        pygame.draw.rect(surface, (60, 60, 80), (int(body_x + 5), int(body_y + 18), 10, 10), 1)

        # 攻击时枪口加亮
        if is_attacking:
            glow_s = pygame.Surface((40, 30), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_s, (50, 150, 255, 80), glow_s.get_rect())
            surface.blit(glow_s, (int(hand_x + 20 * facing - 20), int(hand_y - 15)))

    def _draw_rifle_weapon(self, surface, hand_x, hand_y, facing, is_attacking):
        """突击步枪（smg_flag 52x24，缩放到更长）"""
        sprite = self._get_weapon_sprite('smg_flag')
        if sprite.get_size() == (1, 1):
            sprite = self._get_weapon_sprite('weapon_s_01')
        if sprite.get_size() == (1, 1):
            return

        orig_w, orig_h = sprite.get_size()
        target_h = 30
        scale = target_h / orig_h
        new_w = max(1, int(orig_w * scale))
        new_h = max(1, int(orig_h * scale))
        sprite = pygame.transform.smoothscale(sprite, (new_w, new_h))
        if facing < 0:
            sprite = self._flip(sprite)

        grip_px = self.weapon_data.grip_px
        surface.blit(sprite, (int(hand_x - grip_px), int(hand_y - new_h // 2)))

        # 攻击时枪口闪光
        if is_attacking:
            flash = pygame.Surface((12, 12), pygame.SRCALPHA)
            pygame.draw.circle(flash, (255, 200, 50, 200), (6, 6), 5)
            surface.blit(flash, (int(hand_x + (new_w - grip_px) * facing - 6), int(hand_y - 6)))

    def _draw_dagger_weapon(self, surface, hand_x, hand_y, facing, is_attacking):
        """军用匕首（era_weapons/knife.png 48x22，斜向下握持）
        备用：程序化绘制金色匕首"""
        sprite = self._get_weapon_sprite('knife')
        if sprite.get_size() == (1, 1):
            sprite = self._get_weapon_sprite(self.weapon_data.sprite_key)

        if sprite.get_size() != (1, 1):
            orig_w, orig_h = sprite.get_size()
            target_h = 32
            scale = target_h / orig_h
            new_w = max(1, int(orig_w * scale))
            new_h = max(1, int(orig_h * scale))
            sprite = pygame.transform.smoothscale(sprite, (new_w, new_h))
            if facing < 0:
                sprite = self._flip(sprite)
            sprite = pygame.transform.rotate(sprite, 45 * facing)
            rw, rh = sprite.get_size()
            blit_x = hand_x - rw // 2
            blit_y = hand_y - rh // 2
            surface.blit(sprite, (int(blit_x), int(blit_y)))
        else:
            # 程序化备用：绘制金色匕首
            self._draw_dagger_procedural(surface, hand_x, hand_y, facing, is_attacking)

        if is_attacking:
            glow_s = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_s, (180, 200, 240, 60), glow_s.get_rect())
            surface.blit(glow_s, (int(hand_x - 25), int(hand_y - 25)))

    def _draw_dagger_procedural(self, surface, hand_x, hand_y, facing, is_attacking):
        """程序化绘制金色匕首（备用方案）"""
        # 匕首长度
        dagger_len = 35
        # 刀柄颜色（金色）
        handle_color = (160, 130, 80)
        handle_dark = (120, 90, 50)
        # 刀刃颜色（银白色）
        blade_color = (220, 220, 240)
        blade_edge = (180, 180, 200)

        # 计算匕首方向（斜向下45度）
        angle = math.radians(45) if facing > 0 else math.radians(135)
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)

        # 刀柄起点（手部位置）
        hx = hand_x
        hy = hand_y

        # 刀柄末端
        kx = hx + int(cos_a * 12)
        ky = hy + int(sin_a * 12)

        # 刀刃起点
        bx = kx
        by = ky

        # 刀刃末端（刀尖）
        tx = hx + int(cos_a * dagger_len)
        ty = hy + int(sin_a * dagger_len)

        # 绘制刀柄
        pygame.draw.line(surface, handle_color, (int(hx), int(hy)), (int(kx), int(ky)), 6)
        pygame.draw.line(surface, handle_dark, (int(hx), int(hy)), (int(kx), int(ky)), 2)

        # 绘制刀格（护手）
        guard_x = bx
        guard_y = by
        pygame.draw.ellipse(surface, (200, 180, 100), (int(guard_x - 4), int(guard_y - 4), 8, 8))

        # 绘制刀刃（三角形）
        # 刀背
        pygame.draw.line(surface, blade_color, (int(bx), int(by)), (int(tx), int(ty)), 4)
        # 刀刃线
        perp_x = -sin_a * 5
        perp_y = cos_a * 5
        pygame.draw.line(surface, blade_edge, (int(bx + perp_x), int(by + perp_y)), (int(tx + perp_x), int(ty + perp_y)), 2)
        # 刀尖
        tip_x = tx
        tip_y = ty
        pygame.draw.circle(surface, (255, 255, 255), (int(tip_x), int(tip_y)), 2)

        # 刀身光泽效果
        if is_attacking:
            glow_s = pygame.Surface((50, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_s, (200, 220, 255, 80), glow_s.get_rect())
            surface.blit(glow_s, (int(hand_x - 25 + cos_a * 15), int(hand_y - 25 + sin_a * 15)))

    def _draw_eagle_weapon(self, surface, hand_x, hand_y, facing, is_attacking, anim_idx):
        """白头海雕（eagle_flap.png spritesheet，7帧）
        备用：程序化绘制展翅老鹰"""
        sprite = WeaponAssets.get_frame('eagle_frames', anim_idx)
        if sprite.get_size() != (1, 1):
            orig_w, orig_h = sprite.get_size()
            new_w, new_h = 60, max(1, int(orig_h * (60.0 / orig_w)))
            sprite = pygame.transform.smoothscale(sprite, (new_w, new_h))
            if facing < 0:
                sprite = self._flip(sprite)
            surface.blit(sprite, (int(hand_x - new_w // 2), int(hand_y - new_h // 2)))
        else:
            # 程序化备用：绘制一只展翅老鹰
            self._draw_eagle_procedural(surface, hand_x, hand_y, facing, is_attacking, anim_idx)

    def _draw_eagle_procedural(self, surface, hand_x, hand_y, facing, is_attacking, anim_idx):
        """程序化绘制白头海雕（备用方案）"""
        # 翅膀扑动动画
        flap_angle = math.sin(pygame.time.get_ticks() * 0.015) * 0.4
        wing_span = 30 + int(abs(math.sin(pygame.time.get_ticks() * 0.015)) * 10)

        # 身体（椭圆形）
        body_color = (100, 70, 40)
        pygame.draw.ellipse(surface, body_color, (int(hand_x - 8), int(hand_y - 6), 16, 12))

        # 头（白色）
        head_x = hand_x + 6 * facing
        pygame.draw.ellipse(surface, (240, 240, 240), (int(head_x - 5), int(hand_y - 10), 10, 10))

        # 喙（黄色）
        beak_x = hand_x + 10 * facing
        pygame.draw.polygon(surface, (255, 200, 0), [
            (int(beak_x), int(hand_y - 7)),
            (int(beak_x + 6 * facing), int(hand_y - 5)),
            (int(beak_x), int(hand_y - 3)),
        ])

        # 眼睛
        pygame.draw.circle(surface, (0, 0, 0), (int(head_x + 2 * facing), int(hand_y - 8)), 2)

        # 左翅膀
        wx1 = hand_x - 5
        wy1 = hand_y - 4
        wtip_x = hand_x - wing_span - int(flap_angle * 8)
        wtip_y = hand_y - 15 + int(abs(flap_angle) * 5)
        pygame.draw.polygon(surface, (120, 90, 60), [
            (int(wx1), int(wy1)),
            (int(wtip_x), int(wtip_y)),
            (int(wx1 - 5), int(wtip_y + 8)),
        ])

        # 右翅膀
        wx2 = hand_x + 5
        wtip2_x = hand_x + wing_span + int(flap_angle * 8)
        wtip2_y = hand_y - 15 + int(abs(flap_angle) * 5)
        pygame.draw.polygon(surface, (120, 90, 60), [
            (int(wx2), int(wy1)),
            (int(wtip2_x), int(wtip2_y)),
            (int(wx2 + 5), int(wtip2_y + 8)),
        ])

        # 尾巴
        pygame.draw.polygon(surface, (80, 60, 40), [
            (int(hand_x - 6), int(hand_y + 4)),
            (int(hand_x - 15 * facing), int(hand_y + 10)),
            (int(hand_x - 5), int(hand_y + 8)),
        ])

        # 攻击时光效
        if is_attacking:
            glow_s = pygame.Surface((60, 50), pygame.SRCALPHA)
            pygame.draw.ellipse(glow_s, (200, 180, 100, 60), glow_s.get_rect())
            surface.blit(glow_s, (int(hand_x - 30), int(hand_y - 25)))

    def _draw_nunchaku_weapon(self, surface, hand_x, hand_y, facing, is_attacking):
        """双截棍（procedural）"""
        # 动画：双节棍随时间摆动
        t = pygame.time.get_ticks()
        angle1 = math.sin(t * 0.008) * 0.6
        angle2 = math.sin(t * 0.008 + 1.5) * 0.6
        cx, cy = int(hand_x), int(hand_y)

        # 第一截
        end1_x = cx + int(math.cos(angle1) * 16)
        end1_y = cy + int(math.sin(angle1) * 16) + 10
        pygame.draw.line(surface, (180, 140, 80), (cx, cy), (end1_x, end1_y), 4)
        pygame.draw.ellipse(surface, (220, 170, 100), (end1_x - 5, end1_y - 3, 10, 6))

        # 连接链
        pygame.draw.line(surface, (160, 160, 170), (end1_x, end1_y),
                        (end1_x + int(math.cos(angle2) * 6), end1_y + int(math.sin(angle2) * 6)), 2)

        # 第二截
        end2_x = end1_x + int(math.cos(angle1 + angle2) * 16)
        end2_y = end1_y + int(math.sin(angle1 + angle2) * 16) + 10
        pygame.draw.line(surface, (180, 140, 80), (end1_x, end1_y), (end2_x, end2_y), 4)
        pygame.draw.ellipse(surface, (220, 170, 100), (end2_x - 5, end2_y - 3, 10, 6))

        if is_attacking:
            glow_s = pygame.Surface((40, 40), pygame.SRCALPHA)
            pygame.draw.circle(glow_s, (255, 220, 100, 60), (20, 20), 16)
            surface.blit(glow_s, (int(end2_x - 20), int(end2_y - 20)))

    def _draw_shuriken_weapon(self, surface, hand_x, hand_y, facing, is_attacking):
        """手里剑（procedural + era_weapons 备用）"""
        t = pygame.time.get_ticks()
        rot = t * 0.01
        cx, cy = int(hand_x), int(hand_y)
        r = 12

        # 尝试从 WeaponAssets 加载手里剑 sprite
        sprite = self._get_weapon_sprite('weapon_s_08')
        if sprite.get_size() != (1, 1):
            sprite = pygame.transform.rotate(sprite, math.degrees(rot))
            sw, sh = sprite.get_size()
            surface.blit(sprite, (int(cx - sw // 2), int(cy - sh // 2)))
        else:
            # Procedural 手里剑
            pts = [(cx, cy - r), (cx + 3, cy - 3), (cx + r, cy),
                   (cx + 3, cy + 3), (cx, cy + r), (cx - 3, cy + 3),
                   (cx - r, cy), (cx - 3, cy - 3)]
            pygame.draw.polygon(surface, (180, 180, 190), pts)
            pygame.draw.circle(surface, (80, 80, 90), (cx, cy), 3)

        if is_attacking:
            for i in range(4):
                tx = cx + int(math.cos(rot + i * math.pi / 2) * (r + 8))
                ty = cy + int(math.sin(rot + i * math.pi / 2) * (r + 8))
                pygame.draw.circle(surface, (200, 200, 220), (tx, ty), 2)

    def _draw_projectiles(self, surface: pygame.Surface, camera_x: int):
        """绘制投射物（按 weapon_type 分发）"""
        weapon_type = self.weapon_data.weapon_type

        for proj in self.projectile_manager.projectiles:
            if not proj.active:
                continue

            screen_x = proj.x - camera_x
            screen_y = proj.y
            dir_sign = proj.direction

            if weapon_type == WeaponType.FLAG:
                self._draw_proj_flag(surface, screen_x, screen_y, dir_sign)
            elif weapon_type in (WeaponType.LASER, WeaponType.PISTOL, WeaponType.RIFLE):
                self._draw_proj_laser(surface, screen_x, screen_y, dir_sign)
            elif weapon_type == WeaponType.DAGGER:
                self._draw_proj_dagger(surface, screen_x, screen_y, dir_sign)
            elif weapon_type == WeaponType.EAGLE:
                self._draw_proj_eagle(surface, screen_x, screen_y, dir_sign)
            elif weapon_type == WeaponType.NUNCHAKU:
                self._draw_proj_nunchaku(surface, screen_x, screen_y, dir_sign)
            elif weapon_type == WeaponType.SHURIKEN:
                self._draw_proj_shuriken(surface, screen_x, screen_y, dir_sign)
            else:
                self._draw_proj_default(surface, screen_x, screen_y, dir_sign)

    def _draw_proj_flag(self, surface, screen_x, screen_y, dir_sign):
        """投射物：红旗"""
        flag_w, flag_h = 30, 20
        pole_x1 = screen_x - 12 * dir_sign
        pole_y1 = screen_y - 5
        pole_x2 = screen_x + 8 * dir_sign
        pole_y2 = screen_y - 20
        pygame.draw.line(surface, (200, 160, 50), (int(pole_x1), int(pole_y1)),
                       (int(pole_x2), int(pole_y2)), 2)
        pygame.draw.rect(surface, (220, 30, 30),
                       (int(pole_x2), int(pole_y2), int(flag_w * dir_sign), flag_h))
        star_cx = pole_x2 + 7 * dir_sign
        star_cy = pole_y2 + flag_h // 2
        points = []
        for i in range(5):
            oa = math.radians(90 + i * 72)
            ia = math.radians(90 + i * 72 + 36)
            points.append((star_cx + math.cos(oa) * 5, star_cy - math.sin(oa) * 5))
            points.append((star_cx + math.cos(ia) * 5 * 0.38, star_cy - math.sin(ia) * 5 * 0.38))
        if len(points) >= 10:
            pygame.draw.polygon(surface, (255, 220, 0), points)
        for i in range(3):
            ts = pygame.Surface((10, 10), pygame.SRCALPHA)
            pygame.draw.circle(ts, (255, 100, 50, 100 - i * 30), (5, 5), 4)
            surface.blit(ts, (int(screen_x - 15 * dir_sign * (i + 1) - 5), int(screen_y - 5)))

    def _draw_proj_laser(self, surface, screen_x, screen_y, dir_sign):
        """投射物：激光束"""
        beam_len = 50 * dir_sign
        pygame.draw.line(surface, (50, 100, 255, 100),
                       (int(screen_x), int(screen_y - 5)),
                       (int(screen_x + beam_len), int(screen_y - 5)), 8)
        pygame.draw.line(surface, (80, 130, 255, 150),
                       (int(screen_x), int(screen_y)),
                       (int(screen_x + beam_len), int(screen_y)), 5)
        pygame.draw.line(surface, (200, 220, 255),
                       (int(screen_x), int(screen_y)),
                       (int(screen_x + beam_len), int(screen_y)), 2)
        for i in range(5):
            px = screen_x + (i * 12 + (pygame.time.get_ticks() // 30) % 12) * dir_sign
            if 0 < px < 1280:
                pygame.draw.circle(surface, (150, 200, 255),
                                 (int(px), int(screen_y + (i % 3 - 1) * 4)), 2)
        muzzle = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.circle(muzzle, (100, 200, 255, 200), (8, 8), 7)
        pygame.draw.circle(muzzle, (200, 240, 255, 150), (8, 8), 4)
        surface.blit(muzzle, (int(screen_x - 8), int(screen_y - 8)))

    def _draw_proj_dagger(self, surface, screen_x, screen_y, dir_sign):
        """投射物：星条旗（匕首投射形态）"""
        flag_w, flag_h = 24, 16
        fx = screen_x - 10 * dir_sign
        fy = screen_y - 8
        pygame.draw.rect(surface, (30, 50, 150), (int(fx), int(fy), int(10 * dir_sign), 8))
        for i in range(1, 7, 2):
            pygame.draw.line(surface, (240, 240, 240), (fx, fy + i), (fx + flag_w * dir_sign, fy + i), 2)
        for i in range(2, 7, 2):
            pygame.draw.line(surface, (180, 20, 20), (fx, fy + i), (fx + flag_w * dir_sign, fy + i), 2)
        pygame.draw.rect(surface, (240, 240, 240), (int(fx), int(fy), int(flag_w * dir_sign), flag_h), 1)
        for i in range(3):
            ts = pygame.Surface((8, 8), pygame.SRCALPHA)
            pygame.draw.circle(ts, (80, 80, 100, 80 - i * 25), (4, 4), 3)
            surface.blit(ts, (int(screen_x - 12 * dir_sign * (i + 1) - 4), int(screen_y - 4)))

    def _draw_proj_eagle(self, surface, screen_x, screen_y, dir_sign):
        """投射物：白头海雕"""
        flap = math.sin(pygame.time.get_ticks() * 0.02) * 8
        body_cx, body_cy = screen_x, screen_y
        pygame.draw.ellipse(surface, (139, 90, 43), (int(body_cx - 10), int(body_cy - 6), 20, 12))
        wing_color = (120, 80, 35)
        wx1, wy1 = body_cx - 5, body_cy - 2
        wtip1_x, wtip1_y = body_cx - 25 - int(flap), body_cy - 15 + int(abs(flap) * 0.5)
        pygame.draw.line(surface, wing_color, (int(wx1), int(wy1)), (int(wtip1_x), int(wtip1_y)), 3)
        pygame.draw.line(surface, wing_color, (int(wx1), int(wy1 + 2)), (int(wtip1_x), int(wtip1_y + 8)), 3)
        wtip2_x, wtip2_y = body_cx + 25 + int(flap), body_cy - 15 + int(abs(flap) * 0.5)
        pygame.draw.line(surface, wing_color, (int(body_cx + 5), int(wy1)), (int(wtip2_x), int(wtip2_y)), 3)
        pygame.draw.line(surface, wing_color, (int(body_cx + 5), int(wy1 + 2)), (int(wtip2_x), int(wtip2_y + 8)), 3)
        head_x, head_y = body_cx + 10 * dir_sign, body_cy - 4
        pygame.draw.ellipse(surface, (139, 90, 43), (int(head_x - 5), int(head_y - 5), 10, 10))
        pygame.draw.polygon(surface, (255, 200, 0), [
            (int(head_x + 5 * dir_sign), int(head_y - 2)),
            (int(head_x + 12 * dir_sign), int(head_y)),
            (int(head_x + 5 * dir_sign), int(head_y + 2))
        ])
        pygame.draw.circle(surface, (0, 0, 0), (int(head_x + 3 * dir_sign), int(head_y - 2)), 2)
        pygame.draw.circle(surface, (200, 50, 0), (int(head_x + 3 * dir_sign), int(head_y - 2)), 1)
        pygame.draw.line(surface, (100, 70, 30), (int(body_cx - 10), int(body_cy)),
                       (int(body_cx - 20 * dir_sign), int(body_cy + 2)), 3)
        for i in range(4):
            tx = body_cx - 15 * dir_sign * (i + 1)
            ty = body_cy + (i % 3 - 1) * 6
            ts = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.ellipse(ts, (80, 160, 60, 120 - i * 25), (0, 0, 6, 6))
            surface.blit(ts, (int(tx - 3), int(ty - 3)))

    def _draw_proj_nunchaku(self, surface, screen_x, screen_y, dir_sign):
        """投射物：双截棍（旋转）"""
        t = pygame.time.get_ticks()
        for i in range(2):
            angle = t * 0.015 + i * math.pi
            ex = screen_x + int(math.cos(angle) * 18) * dir_sign
            ey = screen_y + int(math.sin(angle) * 12)
            pygame.draw.ellipse(surface, (220, 170, 100), (int(ex - 5), int(ey - 3), 10, 6))
            if i == 0:
                sx, sy = screen_x, screen_y
            else:
                prev_angle = angle - 0.4
                sx = screen_x + int(math.cos(prev_angle) * 18) * dir_sign
                sy = screen_y + int(math.sin(prev_angle) * 12)
            pygame.draw.line(surface, (180, 140, 80), (int(sx), int(sy)), (int(ex), int(ey)), 4)

    def _draw_proj_shuriken(self, surface, screen_x, screen_y, dir_sign):
        """投射物：手里剑（旋转飞镖）"""
        rot = pygame.time.get_ticks() * 0.012
        r = 14
        cx, cy = int(screen_x), int(screen_y)
        pts = [(cx, cy - r), (cx + 4, cy - 4), (cx + r, cy),
               (cx + 4, cy + 4), (cx, cy + r), (cx - 4, cy + 4),
               (cx - r, cy), (cx - 4, cy - 4)]
        pygame.draw.polygon(surface, (180, 180, 190), pts)
        pygame.draw.circle(surface, (80, 80, 90), (cx, cy), 4)
        for i in range(3):
            trail_x = cx - 12 * dir_sign * (i + 1)
            trail_y = cy + (i % 3 - 1) * 5
            ts = pygame.Surface((6, 6), pygame.SRCALPHA)
            pygame.draw.circle(ts, (180, 180, 200, 150 - i * 40), (3, 3), 2)
            surface.blit(ts, (int(trail_x - 3), int(trail_y - 3)))

    def _draw_proj_default(self, surface, screen_x, screen_y, dir_sign):
        """投射物：默认能量弹"""
        colors = [(255, 255, 100), (255, 200, 50), (255, 150, 0)]
        t = pygame.time.get_ticks()
        ci = (t // 50) % len(colors)
        pygame.draw.ellipse(surface, colors[ci], (int(screen_x - 30), int(screen_y - 20), 60, 40))
        pygame.draw.ellipse(surface, (255, 255, 255), (int(screen_x - 18), int(screen_y - 12), 36, 24))

    def reset(self, x: float, y: float):
        """重置角色状态"""
        self.x = x
        self.y = y
        self.vel_x = 0
        self.vel_y = 0
        self.health = self.max_health
        self.special_energy = 0
        self.ultimate_pending_trigger = False
        self.state = FighterState.IDLE
        self.is_blocking = False
        self.block_input = False
        self.is_invincible = False
        self.is_attacking = False
        self.is_special_attacking = False
        self.current_attack = None
        self.current_special = None
        self.current_special_index = -1
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
        # 清除投射物
        self.projectile_manager.projectiles.clear()
        # 清除终极必杀技实体（重置全局管理器）
        reset_ultimate_entity_manager()
        self.last_hit_by = 0