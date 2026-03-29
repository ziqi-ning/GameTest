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
