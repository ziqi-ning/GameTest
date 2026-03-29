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
        from assets.weapon_assets import WeaponAssets

        char_name = self._char_effect_name
        facing = 1 if self.facing_right else -1
        char_cx = self.x - camera_x
        char_cy = self.y

        is_attacking = self.is_attacking and not self.is_special_attacking

        # 帧动画索引（用于老鹰翅膀扑动）
        anim_idx = 0
        if is_attacking and self.current_attack:
            total = max(self.current_attack.total_frames, 1)
            anim_idx = int((self.attack_frame / total) * 7) % 7

        # 手部基准偏移（朝向侧）
        HAND_X = 38    # 朝前方向距角色中心的横向偏移
        HAND_Y = -52   # 手部距脚部的纵向偏移
        ATK_EXTRA = 18 # 攻击时额外前伸量

        wx = char_cx + HAND_X * facing
        wy = char_cy + HAND_Y
        if is_attacking:
            wx += ATK_EXTRA * facing

        if "龚大哥" in char_name:
            self._draw_flag_weapon(surface, wx, wy, facing, is_attacking)
        elif "军师" in char_name:
            self._draw_laser_gun_weapon(surface, wx, wy, facing, is_attacking)
        elif "神秘人" in char_name:
            self._draw_dagger_weapon(surface, wx, wy, facing, is_attacking)
        elif "籽桐" in char_name:
            self._draw_eagle_weapon(surface, wx, wy, facing, is_attacking, anim_idx)

    def _flip(self, surf: pygame.Surface) -> pygame.Surface:
        """左右翻转sprite"""
        return pygame.transform.flip(surf, True, False)

    def _draw_flag_weapon(self, surface, wx, wy, facing, is_attacking):
        """龚大哥：五星红旗（五星红旗握在手中）"""
        import math
        wave = math.sin(pygame.time.get_ticks() * 0.006) * 6
        if is_attacking:
            wave *= 2.0
        # 旗杆（金色）
        pygame.draw.line(surface, (210, 170, 50), (int(wx), int(wy)),
                       (int(wx + 8 * facing), int(wy + 36)), 5)
        # 红旗（红色）
        fx = wx + 8 * facing + wave * facing
        fy = wy + 36 - 24
        pygame.draw.rect(surface, (220, 30, 30), (int(fx), int(fy), int(32 * facing), 22))
        pygame.draw.rect(surface, (160, 15, 15), (int(fx), int(fy), int(32 * facing), 22), 1)
        # 五角星
        star_x = fx + 10 * facing
        star_y = fy + 11
        sr = 6
        pts = []
        for i in range(5):
            oa = math.radians(90 + i * 72)
            ia = math.radians(90 + i * 72 + 36)
            pts.append((star_x + math.cos(oa) * sr, star_y - math.sin(oa) * sr))
            pts.append((star_x + math.cos(ia) * sr * 0.38, star_y - math.sin(ia) * sr * 0.38))
        if len(pts) >= 10:
            pygame.draw.polygon(surface, (255, 220, 0), pts)

    def _draw_laser_gun_weapon(self, surface, wx, wy, facing, is_attacking):
        """军师：激光枪（Eradication Wars CC0 sprite）"""
        from assets.weapon_assets import WeaponAssets
        sprite = WeaponAssets.get('laser_gun')
        if sprite.get_size() == (1, 1):
            return  # 未加载成功则跳过
        # 缩小到合适大小（约56px宽）
        w, h = sprite.get_size()
        scale = min(56.0 / w, 28.0 / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        sprite = pygame.transform.smoothscale(sprite, (new_w, new_h))
        if facing < 0:
            sprite = self._flip(sprite)
        # 枪柄朝下，枪口朝前
        rx = wx - sprite.get_width() // 2
        ry = wy - sprite.get_height() // 2
        surface.blit(sprite, (int(rx), int(ry)))
        # 能量指示灯（如果角色在攻击则更亮）
        glow = abs(math.sin(pygame.time.get_ticks() * 0.015))
        intensity = 0.5 + 0.5 * glow
        if is_attacking:
            intensity = 1.0
        glow_c = (int(30 * intensity), int(180 * intensity), 255)
        pygame.draw.circle(surface, glow_c, (int(wx + (new_w // 2 - 4) * facing), int(wy)), int(3 + glow * 2))

    def _draw_dagger_weapon(self, surface, wx, wy, facing, is_attacking):
        """神秘人：军用匕首（64x64 CC0 sprite）"""
        from assets.weapon_assets import WeaponAssets
        sprite = WeaponAssets.get('dagger')
        if sprite.get_size() == (1, 1):
            return
        # 缩小到约48px宽
        w, h = sprite.get_size()
        scale = min(48.0 / w, 24.0 / h)
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        sprite = pygame.transform.smoothscale(sprite, (new_w, new_h))
        if facing < 0:
            sprite = self._flip(sprite)
        rx = wx - sprite.get_width() // 2
        ry = wy - sprite.get_height() // 2
        surface.blit(sprite, (int(rx), int(ry)))
        # 攻击时加个反光
        if is_attacking:
            glow_surf = pygame.Surface((sprite.get_width() + 8, sprite.get_height() + 8), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (180, 200, 240, 60), glow_surf.get_rect(), border_radius=4)
            surface.blit(glow_surf, (int(rx - 4), int(ry - 4)))

    def _draw_eagle_weapon(self, surface, wx, wy, facing, is_attacking, anim_idx):
        """籽桐：老鹰（287x21 spritesheet，7帧 CC0 sprite）"""
        from assets.weapon_assets import WeaponAssets
        sprite = WeaponAssets.get_frame('eagle_frames', anim_idx)
        if sprite.get_size() == (1, 1):
            return
        # 放大到约80px宽
        w, h = sprite.get_size()
        scale = 80.0 / w
        new_w = max(1, int(w * scale))
        new_h = max(1, int(h * scale))
        sprite = pygame.transform.smoothscale(sprite, (new_w, new_h))
        if facing < 0:
            sprite = self._flip(sprite)
        rx = wx - sprite.get_width() // 2
        ry = wy - sprite.get_height() // 2
        surface.blit(sprite, (int(rx), int(ry)))

    def _draw_projectiles(self, surface: pygame.Surface, camera_x: int):
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
                    points.append((star_cx + math.cos(inner_angle) * (star_r * 0.38),
                                  star_cy - math.sin(inner_angle) * (star_r * 0.38)))
                if len(points) >= 10:
                    pygame.draw.polygon(surface, (255, 220, 0), points)
                # 拖尾
                for i in range(3):
                    trail_surf = pygame.Surface((10, 10), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surf, (255, 100, 50, 100 - i * 30), (5, 5), 4)
                    surface.blit(trail_surf, (int(screen_x - 15 * dir_sign * (i + 1) - 5), int(screen_y - 5)))

            # 军师 - 激光束
            elif "军师" in char_name:
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

            # 神秘人 - 星条旗
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
                for i in range(2, 7, 2):
                    pygame.draw.line(surface, (180, 20, 20),
                                  (fx, fy + i), (fx + flag_w * dir_sign, fy + i), 2)
                # 边框
                pygame.draw.rect(surface, (240, 240, 240), (int(fx), int(fy), int(flag_w * dir_sign), flag_h), 1)
                # 拖尾
                for i in range(3):
                    trail_surf = pygame.Surface((8, 8), pygame.SRCALPHA)
                    pygame.draw.circle(trail_surf, (80, 80, 100, 80 - i * 25), (4, 4), 3)
                    surface.blit(trail_surf, (int(screen_x - 12 * dir_sign * (i + 1) - 4), int(screen_y - 4)))

            # 籽桐 - 老鹰
            elif "籽桐" in char_name:
                flap = math.sin(pygame.time.get_ticks() * 0.02) * 8
                body_cx = screen_x
                body_cy = screen_y
                # 身体
                pygame.draw.ellipse(surface, (139, 90, 43), (int(body_cx - 10), int(body_cy - 6), 20, 12))
                # 翅膀（左+右展开）
                wing_color = (120, 80, 35)
                # 左翼
                wx1 = body_cx - 5
                wy1 = body_cy - 2
                wtip1_x = body_cx - 25 - int(flap)
                wtip1_y = body_cy - 15 + int(abs(flap) * 0.5)
                pygame.draw.line(surface, wing_color, (int(wx1), int(wy1)), (int(wtip1_x), int(wtip1_y)), 3)
                pygame.draw.line(surface, wing_color, (int(wx1), int(wy1 + 2)), (int(wtip1_x), int(wtip1_y + 8)), 3)
                # 右翼
                wtip2_x = body_cx + 25 + int(flap)
                wtip2_y = body_cy - 15 + int(abs(flap) * 0.5)
                pygame.draw.line(surface, wing_color, (int(body_cx + 5), int(wy1)), (int(wtip2_x), int(wtip2_y)), 3)
                pygame.draw.line(surface, wing_color, (int(body_cx + 5), int(wy1 + 2)), (int(wtip2_x), int(wtip2_y + 8)), 3)
                # 头+喙
                head_x = body_cx + 10 * dir_sign
                head_y = body_cy - 4
                pygame.draw.ellipse(surface, (139, 90, 43), (int(head_x - 5), int(head_y - 5), 10, 10))
                pygame.draw.polygon(surface, (255, 200, 0), [
                    (int(head_x + 5 * dir_sign), int(head_y - 2)),
                    (int(head_x + 12 * dir_sign), int(head_y)),
                    (int(head_x + 5 * dir_sign), int(head_y + 2))
                ])
                # 眼睛
                eye_x = head_x + 3 * dir_sign
                pygame.draw.circle(surface, (0, 0, 0), (int(eye_x), int(head_y - 2)), 2)
                pygame.draw.circle(surface, (200, 50, 0), (int(eye_x), int(head_y - 2)), 1)
                # 尾羽
                pygame.draw.line(surface, (100, 70, 30), (int(body_cx - 10), int(body_cy)),
                               (int(body_cx - 20 * dir_sign), int(body_cy + 2)), 3)
                # 羽毛拖尾
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
