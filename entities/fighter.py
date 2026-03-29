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

    def __init__(self, player_id: int, char_data: CharacterData, x: float, y: float, char_index: int = 0):
        self.player_id = player_id
        self.char_data = char_data
        self.stats = char_data.stats
        self.char_index = char_index  # 角色索引（用于加载正确精灵）

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

    def handle_input(self, left: bool, right: bool, up: bool, down: bool,
                   light_attack: bool, heavy_attack: bool, special: bool, block: bool):
        """处理输入（由子类或AI实现）"""
        pass

    def update(self, dt: float, opponent: Optional['Fighter'] = None):
        """更新角色状态"""
        # 更新特效系统
        self.effect_manager.update(dt)

        # 更新投射物系统
        if opponent:
            self._update_projectiles(dt, opponent)

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
                                      self.special_energy + 8 * dt)  # 每秒回复8点能量（够快）

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

            # 远程攻击：立即发射投射物
            if move.is_ranged:
                self._fire_ranged_attack(move)

    def attack_special(self, move_index: int = 0):
        """发动必杀技（move_index=0为第一个，=1为第二个）"""
        if move_index >= len(self.char_data.special):
            return  # 没有第二个必杀技

        move = self.char_data.special[move_index]
        if self.special_energy < move.energy_cost:
            return
        if self.is_attacking or self.hitstun_timer > 0:
            return

        self.special_energy -= move.energy_cost
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

        # 触发必杀技特效（按技能索引区分）
        effect_func = CharacterEffects.get_effect_function(self._char_effect_name, move_index)
        if effect_func:
            effect_x = self.x + (50 if self.facing_right else -50)
            effect_func(self.effect_manager, effect_x, self.y - 50, move.name_cn)

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
            # 检测命中
            if opponent:
                self.check_hit(opponent)

        # 攻击结束
        if self.attack_frame >= move.total_frames:
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
                elif not opponent.is_invincible:
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

    def _draw_attack_range(self, surface: pygame.Surface, camera_x: int):
        """绘制攻击范围判定框可视化"""
        hitbox_rect = None
        move_name = ""

        if self.is_special_attacking and self.current_special:
            hitbox_rect = self.get_special_hitbox_rect()
            if hitbox_rect:
                move_name = self.current_special.name_cn
                color = (255, 200, 50, 120)   # 金色 - 必杀技
                border_color = (255, 220, 80)
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
        from animation.animator import Animator

        # 获取当前动画帧
        pose = self.animator.get_pose_name()
        anim_frame = self.animator.get_current_frame()

        # 获取精灵帧
        sprite = get_sprite(
            self.char_index,
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

            # 绘制武器
            self._draw_weapon(surface, draw_x, draw_y, camera_x)

        # 绘制受击特效
        if self.hit_effect_timer > 0:
            pygame.draw.circle(surface, (255, 200, 50),
                             (int(self.x - camera_x), int(self.y - 80)), 20, 3)

        # 绘制攻击范围判定框（hitbox可视化）
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

    def _draw_weapon(self, surface: pygame.Surface, draw_x: float, draw_y: float, camera_x: int):
        """绘制角色武器（sprite形式，定位在手中）"""
        import math

        char_name = self._char_effect_name
        facing = 1 if self.facing_right else -1
        char_cx = self.x - camera_x   # 角色屏幕中心x
        char_cy = self.y               # 角色脚部y

        # === 武器在手中的基准偏移 ===
        # 手部位置：朝向前方的一侧，y在角色上半身
        HAND_X_OFFSET = 38   # 朝前方向手部距角色中心的横向偏移
        HAND_Y_OFFSET = -50  # 手部距脚部的纵向偏移（负数=上方）
        ATK_X_OFFSET = 55    # 攻击时手部前伸量

        is_attacking = self.is_attacking and not self.is_special_attacking
        attack_anim_frac = 0.0
        if is_attacking and self.current_attack:
            total = max(self.current_attack.total_frames, 1)
            attack_anim_frac = self.attack_frame / total

        # 手部位置：攻击时武器前伸（轻攻击前伸少，重攻击前伸多）
        x_offset = HAND_X_OFFSET
        y_offset = HAND_Y_OFFSET
        if is_attacking and self.state == FighterState.ATTACK_LIGHT:
            # 轻攻击：前伸30%
            x_offset = HAND_X_OFFSET + ATK_X_OFFSET * 0.3 * facing
            y_offset = HAND_Y_OFFSET - 5
        elif is_attacking and self.state == FighterState.ATTACK_HEAVY:
            # 重攻击：武器在手中准备发射（不需要太前伸，投射物会飞出去）
            x_offset = HAND_X_OFFSET + ATK_X_OFFSET * 0.15 * facing
            y_offset = HAND_Y_OFFSET - 8

        wx = char_cx + x_offset        # 武器中心x（屏幕坐标）
        wy = char_cy + y_offset        # 武器中心y

        # ── 绘制武器精灵 ────────────────────────────────────────
        if "龚大哥" in char_name:
            self._draw_flag_weapon(surface, wx, wy, facing, is_attacking)
        elif "军师" in char_name:
            self._draw_laser_gun_weapon(surface, wx, wy, facing, is_attacking)
        elif "神秘人" in char_name:
            self._draw_dagger_weapon(surface, wx, wy, facing, is_attacking)
        elif "籽桐" in char_name:
            self._draw_eagle_weapon(surface, wx, wy, facing, is_attacking)

    def _draw_flag_weapon(self, surface, wx, wy, facing, is_attacking):
        """龚大哥：五星红旗（旗帜在手中握持）"""
        import math
        # 挥动动画
        wave = math.sin(pygame.time.get_ticks() * 0.006) * 5
        if is_attacking:
            wave *= 1.5

        # 握柄：金色旗杆从手部向下/斜伸
        pole_x1 = wx
        pole_y1 = wy
        pole_len = 40
        pole_x2 = wx + 6 * facing
        pole_y2 = wy + pole_len
        pygame.draw.line(surface, (210, 170, 50), (int(pole_x1), int(pole_y1)), (int(pole_x2), int(pole_y2)), 4)
        pygame.draw.line(surface, (255, 220, 0), (int(pole_x1) + 1, int(pole_y1)), (int(pole_x2) + 1, int(pole_y2)), 1)

        # 红旗：旗面在旗杆顶端，朝外飘扬
        flag_w, flag_h = 30, 20
        fx = pole_x2 + wave * facing
        fy = pole_y2 - flag_h - 2

        # 旗面主体（红色）
        pygame.draw.rect(surface, (220, 30, 30), (int(fx), int(fy), int(flag_w * facing), flag_h))
        # 暗红描边
        pygame.draw.rect(surface, (160, 20, 20), (int(fx), int(fy), int(flag_w * facing), flag_h), 1)

        # 飘动波纹（用折线模拟风吹）
        for i in range(1, 4):
            bx = fx + i * 8 * facing
            by = fy + flag_h // 2
            pygame.draw.arc(surface, (180, 15, 15), (int(bx - 4 * facing), int(by - 4), int(8 * facing), 8), 0, math.pi, 1)

        # 五角星（黄色）
        star_cx = fx + 9 * facing
        star_cy = fy + flag_h // 2
        star_r = 6
        points = []
        for i in range(5):
            outer_angle = math.radians(90 + i * 72)
            inner_angle = math.radians(90 + i * 72 + 36)
            points.append((star_cx + math.cos(outer_angle) * star_r,
                          star_cy - math.sin(outer_angle) * star_r))
            points.append((star_cx + math.cos(inner_angle) * (star_r * 0.38),
                          star_cy - math.sin(inner_angle) * (star_r * 0.38)))
        if len(points) >= 10:
            pygame.draw.polygon(surface, (255, 220, 0), points)

    def _draw_laser_gun_weapon(self, surface, wx, wy, facing, is_attacking):
        """军师：激光枪（科幻枪械，握持在手）"""
        import math
        glow = abs(math.sin(pygame.time.get_ticks() * 0.015)) * 0.6 + 0.4

        # 枪身主体（横向持枪，朝前）
        gun_cx = wx
        gun_cy = wy
        gun_w = 34
        gun_h = 12

        # 外壳（深蓝灰）
        pygame.draw.rect(surface, (60, 70, 110), (int(gun_cx - 8), int(gun_cy - 7), int(gun_w * facing), gun_h), border_radius=3)
        # 高光面（枪身上半部）
        pygame.draw.rect(surface, (80, 95, 140), (int(gun_cx - 8), int(gun_cy - 7), int(gun_w * facing), 5), border_radius=2)

        # 枪管（突出前端）
        barrel_cx = gun_cx + 12 * facing
        pygame.draw.rect(surface, (40, 50, 90), (int(barrel_cx), int(gun_cy - 3), int(16 * facing), 6), border_radius=2)
        # 枪口圆环
        pygame.draw.circle(surface, (0, 180, 255), (int(barrel_cx + 16 * facing), int(gun_cy)), 4)
        # 枪口能量发光
        if is_attacking:
            glow_c = (int(100 * glow), int(200 * glow), 255)
        else:
            glow_c = (int(30 * glow), int(100 * glow), 200)
        pygame.draw.circle(surface, glow_c, (int(barrel_cx + 16 * facing), int(gun_cy)), int(3 + glow * 2))

        # 能量指示条
        bar_x = gun_cx - 4
        bar_y = gun_cy + 2
        pygame.draw.rect(surface, (30, 30, 60), (int(bar_x), int(bar_y), int(20 * facing), 4), border_radius=1)
        fill_w = int(20 * glow * facing)
        if fill_w != 0:
            pygame.draw.rect(surface, (0, 200, 255), (int(bar_x), int(bar_y), fill_w, 3), border_radius=1)

        # 握把（向下）
        pygame.draw.rect(surface, (50, 55, 90), (int(gun_cx - 6), int(gun_cy + 5), int(10 * facing), 10), border_radius=2)
        # 扳机护圈
        pygame.draw.arc(surface, (80, 100, 150), (int(gun_cx - 4), int(gun_cy + 4), int(12 * facing), 10), 0, math.pi, 2)

    def _draw_dagger_weapon(self, surface, wx, wy, facing, is_attacking):
        """神秘人：军用匕首（短刀在手）"""
        import math
        bob = math.sin(pygame.time.get_ticks() * 0.008) * 1.5

        # 匕首整体倾斜（45度角）
        knife_cx = wx + bob * facing
        knife_cy = wy

        # 刀柄（深灰/黑色）
        handle_len = 14
        hx1 = knife_cx - 4 * facing
        hy1 = knife_cy
        hx2 = knife_cx + handle_len * facing
        hy2 = knife_cy + 4
        pygame.draw.line(surface, (50, 50, 55), (int(hx1), int(hy1)), (int(hx2), int(hy2)), 5)
        pygame.draw.line(surface, (70, 70, 75), (int(hx1), int(hy1)), (int(hx2), int(hy2)), 2)

        # 护手（十字护手，银色横条）
        guard_x = knife_cx + 2 * facing
        pygame.draw.rect(surface, (180, 180, 200), (int(guard_x - 3), int(knife_cy - 6), 6, 12), border_radius=2)
        pygame.draw.rect(surface, (220, 220, 240), (int(guard_x - 2), int(knife_cy - 5), 4, 10), border_radius=1)

        # 刀刃（银白色三角形，朝前）
        blade_len = 24
        blade_tip_x = guard_x + blade_len * facing
        blade_tip_y = knife_cy + 2
        # 刀刃主体
        pygame.draw.polygon(surface, (180, 185, 195), [
            (int(guard_x), int(knife_cy - 4)),
            (int(blade_tip_x), int(blade_tip_y)),
            (int(guard_x), int(knife_cy + 4))
        ])
        # 高光（刃面中间一条亮线）
        pygame.draw.line(surface, (230, 235, 245), (int(guard_x + 3 * facing), int(knife_cy)),
                        (int(blade_tip_x - 4 * facing), int(blade_tip_y)), 1)
        # 刀尖
        pygame.draw.circle(surface, (200, 205, 220), (int(blade_tip_x), int(blade_tip_y)), 2)

        # 攻击时反光
        if is_attacking:
            glow_surf = pygame.Surface((int(blade_len + 10), 16), pygame.SRCALPHA)
            pygame.draw.polygon(glow_surf, (150, 180, 220, 80), [
                (0, 8 - 6), (int(blade_len + 10), 8),
                (0, 8 + 6)
            ])
            surface.blit(glow_surf, (int(guard_x - 5), int(knife_cy - 8)))

    def _draw_eagle_weapon(self, surface, wx, wy, facing, is_attacking):
        """籽桐：老鹰（站在手臂上）"""
        import math
        flap = math.sin(pygame.time.get_ticks() * 0.018) * 4
        if is_attacking:
            flap *= 1.8

        bird_cx = wx + 5 * facing
        bird_cy = wy - 5

        # 身体（棕色椭圆形）
        pygame.draw.ellipse(surface, (130, 80, 35), (int(bird_cx - 10), int(bird_cy - 5), 20, 12))
        pygame.draw.ellipse(surface, (155, 105, 55), (int(bird_cx - 7), int(bird_cy - 3), 14, 8))
        # 胸部浅色
        pygame.draw.ellipse(surface, (170, 120, 70), (int(bird_cx - 4), int(bird_cy - 1), 8, 6))

        # 头（朝向前方）
        head_x = bird_cx + 10 * facing
        head_y = bird_cy - 4
        pygame.draw.ellipse(surface, (130, 80, 35), (int(head_x - 5), int(head_y - 5), 11, 10))
        # 羽冠（头顶一簇羽毛）
        for i in range(-1, 2):
            pygame.draw.line(surface, (110, 65, 25),
                           (int(head_x + i * 2), int(head_y - 5)),
                           (int(head_x + i * 2 - 3 * facing), int(head_y - 10)), 2)

        # 喙（黄色，尖锐）
        beak_tip_x = head_x + 10 * facing
        pygame.draw.polygon(surface, (255, 190, 0), [
            (int(head_x + 5 * facing), int(head_y - 2)),
            (int(beak_tip_x), int(head_y)),
            (int(head_x + 5 * facing), int(head_y + 2))
        ])
        # 喙缝
        pygame.draw.line(surface, (200, 150, 0), (int(head_x + 5 * facing), int(head_y)),
                        (int(beak_tip_x - 2 * facing), int(head_y)), 1)

        # 眼睛（凶狠的红眼）
        eye_x = head_x + 3 * facing
        pygame.draw.circle(surface, (0, 0, 0), (int(eye_x), int(head_y - 2)), 3)
        pygame.draw.circle(surface, (200, 40, 0), (int(eye_x), int(head_y - 2)), 2)
        pygame.draw.circle(surface, (255, 80, 0), (int(eye_x), int(head_y - 2)), 1)

        # 翅膀（展开，上下两片）
        wing_c = (110, 70, 30)
        # 上翼（左上伸展）
        wx1 = bird_cx - 5
        wy1 = bird_cy - 3
        wtip1_x = bird_cx - 22 - int(flap)
        wtip1_y = bird_cy - 16 + int(abs(flap) * 0.5)
        pygame.draw.line(surface, wing_c, (int(wx1), int(wy1)), (int(wtip1_x), int(wtip1_y)), 3)
        pygame.draw.line(surface, (130, 85, 40), (int(wx1), int(wy1)), (int(wtip1_x + 6), int(wtip1_y + 4)), 2)
        # 翼尖羽毛
        for j in range(2):
            pygame.draw.line(surface, (95, 60, 25), (int(wtip1_x + j * 4), int(wtip1_y)),
                           (int(wtip1_x + j * 4 - 6), int(wtip1_y - 5)), 2)

        # 下翼（左下伸展）
        wtip2_x = bird_cx - 22 - int(flap * 0.8)
        wtip2_y = bird_cy + 6 - int(abs(flap) * 0.3)
        pygame.draw.line(surface, wing_c, (int(wx1), int(wy1 + 4)), (int(wtip2_x), int(wtip2_y)), 3)
        pygame.draw.line(surface, (130, 85, 40), (int(wx1), int(wy1 + 4)), (int(wtip2_x + 5), int(wtip2_y + 3)), 2)

        # 右翼（朝后）
        rtip_x = bird_cx + 12
        rtip_y = bird_cy - 8 - int(flap * 0.6)
        pygame.draw.line(surface, wing_c, (int(bird_cx + 8), int(wy1)), (int(rtip_x), int(rtip_y)), 2)

        # 尾羽（向后伸出）
        tail_x = bird_cx - 14
        pygame.draw.line(surface, (100, 65, 25), (int(bird_cx - 10), int(bird_cy)),
                        (int(tail_x), int(bird_cy + 2)), 3)
        pygame.draw.line(surface, (120, 80, 35), (int(bird_cx - 9), int(bird_cy - 2)),
                        (int(tail_x - 3), int(bird_cy - 4)), 2)
        """绘制投射物"""
        import math

        for proj in self.projectile_manager.projectiles:
            if not proj.active:
                continue

            screen_x = proj.x - camera_x
            screen_y = proj.y
            dir_sign = proj.direction

            char_name = getattr(proj, 'char_name', '龚大哥')

            # 龚大哥 - 红旗（旋转飞行）
            if "龚大哥" in char_name:
                angle = math.radians(10 if dir_sign > 0 else -10)
                flag_w, flag_h = 30, 20
                # 旗杆
                pole_x1 = screen_x - 12 * dir_sign
                pole_y1 = screen_y - 5
                pole_x2 = screen_x + 8 * dir_sign
                pole_y2 = screen_y - 20
                pygame.draw.line(surface, (200, 160, 50), (int(pole_x1), int(pole_y1)),
                               (int(pole_x2), int(pole_y2)), 2)
                # 旗面
                pygame.draw.rect(surface, (220, 30, 30),
                               (int(pole_x2), int(pole_y2), int(flag_w * dir_sign), flag_h))
                # 五角星
                star_cx = pole_x2 + 7 * dir_sign
                star_cy = pole_y2 + flag_h // 2
                star_r = 5
                points = []
                for i in range(5):
                    outer_angle = math.radians(90 + i * 72)
                    inner_angle = math.radians(90 + i * 72 + 36)
                    points.append((star_cx + math.cos(outer_angle) * star_r,
                                  star_cy - math.sin(outer_angle) * star_r))
                    points.append((star_cx + math.cos(inner_angle) * (star_r * 0.4),
                                  star_cy - math.sin(inner_angle) * (star_r * 0.4)))
                if len(points) >= 10:
                    pygame.draw.polygon(surface, (255, 220, 0), points)
                # 拖尾光效
                for i in range(3):
                    alpha = 100 - i * 30
                    trail_x = screen_x - 15 * dir_sign * (i + 1)
                    trail_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surf, (255, 100, 50, alpha), (5, 5), 4)
                    surface.blit(trail_surf, (int(trail_x - 5), int(screen_y - 5)))

            # 军师 - 激光束
            elif "军师" in char_name:
                # 主光束
                beam_len = 50 * dir_sign
                # 外层光晕
                pygame.draw.line(surface, (50, 100, 255, 100),
                               (int(screen_x), int(screen_y - 5)),
                               (int(screen_x + beam_len), int(screen_y - 5)), 8)
                pygame.draw.line(surface, (80, 130, 255, 150),
                               (int(screen_x), int(screen_y)),
                               (int(screen_x + beam_len), int(screen_y)), 5)
                # 核心
                pygame.draw.line(surface, (200, 220, 255),
                               (int(screen_x), int(screen_y)),
                               (int(screen_x + beam_len), int(screen_y)), 2)
                # 能量粒子
                for i in range(5):
                    px = screen_x + (i * 12 + (pygame.time.get_ticks() // 30) % 12) * dir_sign
                    if 0 < px < 1280:
                        pygame.draw.circle(surface, (150, 200, 255),
                                         (int(px), int(screen_y + (i % 3 - 1) * 4)), 2)
                # 枪口火焰
                muzzle_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                pygame.draw.circle(muzzle_surf, (100, 200, 255, 200), (8, 8), 7)
                pygame.draw.circle(muzzle_surf, (200, 240, 255, 150), (8, 8), 4)
                surface.blit(muzzle_surf, (int(screen_x - 8), int(screen_y - 8)))

            # 神秘人 - 星条旗（旋转飞行）
            elif "神秘人" in char_name:
                flag_w, flag_h = 24, 16
                fx = screen_x - 10 * dir_sign
                fy = screen_y - 8
                # 蓝色区域
                pygame.draw.rect(surface, (30, 50, 150), (int(fx), int(fy), int(10 * dir_sign), 8))
                # 白条
                for i in range(1, 7, 2):
                    pygame.draw.line(surface, (240, 240, 240),
                                   (fx, fy + i), (fx + flag_w * dir_sign, fy + i), 2)
                # 红条
                for i in range(0, 7, 2):
                    if i > 0:
                        pygame.draw.line(surface, (180, 20, 20),
                                      (fx, fy + i), (fx + flag_w * dir_sign, fy + i), 2)
                # 边框
                pygame.draw.rect(surface, (240, 240, 240), (int(fx), int(fy), int(flag_w * dir_sign), flag_h), 1)
                # 拖尾（暗色）
                for i in range(3):
                    trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surf, (80, 80, 100, 80 - i * 25), (4, 4), 3)
                    surface.blit(trail_surf, (int(screen_x - 12 * dir_sign * (i + 1)), int(screen_y - 4)))

            # 籽桐 - 老鹰
            elif "籽桐" in char_name:
                # 简化飞行老鹰
                body_cx = screen_x
                body_cy = screen_y
                # 翅膀扑动动画
                flap = math.sin(pygame.time.get_ticks() * 0.02) * 8

                # 身体
                pygame.draw.ellipse(surface, (139, 90, 43), (int(body_cx - 10), int(body_cy - 6), 20, 12))
                # 翅膀（左+右展开）
                wing_color = (120, 80, 35)
                # 左翼
                pygame.draw.line(surface, wing_color, (body_cx - 5, body_cy - 2),
                               (body_cx - 25 - int(flap), body_cy - 15 + int(abs(flap) * 0.5)), 3)
                pygame.draw.line(surface, wing_color, (body_cx - 5, body_cy + 2),
                               (body_cx - 25 - int(flap), body_cy + 10 - int(abs(flap) * 0.5)), 3)
                # 右翼
                pygame.draw.line(surface, wing_color, (body_cx + 5, body_cy - 2),
                               (body_cx + 25 + int(flap), body_cy - 15 + int(abs(flap) * 0.5)), 3)
                pygame.draw.line(surface, wing_color, (body_cx + 5, body_cy + 2),
                               (body_cx + 25 + int(flap), body_cy + 10 - int(abs(flap) * 0.5)), 3)
                # 头+喙（朝飞行方向）
                head_x = body_cx + 10 * dir_sign
                pygame.draw.ellipse(surface, (139, 90, 43), (int(head_x - 5), int(body_cy - 8), 10, 10))
                pygame.draw.polygon(surface, (255, 200, 0), [
                    (head_x + 5 * dir_sign, body_cy - 5),
                    (head_x + 12 * dir_sign, body_cy - 3),
                    (head_x + 5 * dir_sign, body_cy - 1)
                ])
                # 尾羽
                pygame.draw.line(surface, (100, 70, 30), (body_cx - 10, body_cy),
                               (body_cx - 20 * dir_sign, body_cy + 2), 3)
                # 眼睛
                eye_x = head_x + 3 * dir_sign
                pygame.draw.circle(surface, (0, 0, 0), (int(eye_x), int(body_cy - 5)), 2)
                # 飞行拖尾（羽毛粒子）
                for i in range(4):
                    trail_x = body_cx - 15 * dir_sign * (i + 1)
                    trail_y = body_cy + (i % 3 - 1) * 6
                    ts = pygame.Surface((6, 6), pygame.SRCALPHA)
                    pygame.draw.ellipse(ts, (80, 160, 60, 120 - i * 25), (0, 0, 6, 6))
                    surface.blit(ts, (int(trail_x - 3), int(trail_y - 3)))

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
        self.last_hit_by = 0
