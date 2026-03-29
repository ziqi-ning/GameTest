# AI Fighter - AI控制的角色

import random
import math
from typing import Optional
from entities.fighter import Fighter
from config import GROUND_Y
from constants import FighterState, Direction
from game.state_machine import AnimationState

# 边界安全区域（距离边缘多少像素内视为危险）
EDGE_DANGER_ZONE = 150
SCREEN_LEFT = 60
SCREEN_RIGHT = 1220

class AIFighter(Fighter):
    """AI控制的角色"""

    def __init__(self, player_id: int, char_data, x: float, y: float,
                 char_index: int = 0, difficulty: str = "normal", stage=None):
        super().__init__(player_id, char_data, x, y, char_index, stage=stage)

        self.is_human = False
        self.difficulty = difficulty

        # AI行为参数
        self.aggression = 0.7  # 进攻性提高
        self.reaction_time = 0.15  # 反应更快
        self.reaction_timer = 0.0

        # 行为状态
        self.ai_state = "idle"
        self.target_x = x
        self.jump_chance = 0.015   # 每次决策有1.5%跳跃（决策频率约6Hz，约每11秒跳一次）
        self.attack_chance = 0.8   # 在攻击范围内80%概率出手
        self.block_chance = 0.35

        # 主动出击计时器：防止AI一直被动
        self.passive_timer = 0.0
        self.passive_threshold = 2.0  # 超过2秒没有进攻则强制出击

        # 记忆
        self.opponent_last_attack_time = 0
        self.opponent_attack_pattern = []

        # 保存对手引用
        self._opponent_ref = None

    def update_ai(self, dt: float, opponent: Fighter):
        """更新AI行为"""
        if opponent is None:
            return

        self.reaction_timer -= dt
        self.passive_timer += dt

        # 更新朝向
        self.update_direction(opponent.x)

        # 计算与对手的距离
        distance = abs(self.x - opponent.x)

        # ── 跳跃判断（独立于反应延迟，每帧都检查）──────────────────────
        if self.on_ground and not self.is_attacking and self.hitstun_timer <= 0:
            height_diff = self.y - opponent.y  # 正值=对手在上方
            # 对手在高处超过60px，主动跳上去（提高概率）
            if height_diff > 60 and random.random() < 0.04:
                self._do_jump()
            # 随机跳跃（提高到每秒约1次）
            elif random.random() < 0.016:
                self._do_jump()

        # 反应延迟
        if self.reaction_timer > 0:
            return

        self.reaction_timer = self.reaction_time * (1.0 - self.aggression * 0.5)

        # 检查是否需要防御（靠近边缘时降低防御意愿，优先脱离边缘）
        if not self._is_near_edge() and self.should_block(opponent, distance):
            self.apply_movement(False, False, False, False, True)
            return

        # 解除防御
        self.is_blocking = False

        # 边缘逃脱优先级最高：靠近边缘时强制向中央移动
        if self._is_near_edge():
            move = self._edge_escape_direction(opponent.x)
            self.apply_movement(*move)
            if distance < 120 and self.attack_cooldown <= 0:
                self.attack_light()
            return

        # ── 检测附近的敌方小兵威胁，优先攻击 ──────────────────────────
        nearest_minion = self._find_nearest_enemy_minion(opponent)
        if nearest_minion is not None:
            minion_dist = abs(self.x - nearest_minion.x)
            if minion_dist < 100:
                # 转向小兵并攻击
                self.update_direction(nearest_minion.x)
                if minion_dist > 80:
                    self.ai_approach(minion_dist, nearest_minion)
                elif self.attack_cooldown <= 0:
                    self.attack_light()
                return

        # 被动超时：强制出击
        if self.passive_timer > self.passive_threshold:
            self.passive_timer = 0.0
            self.ai_approach(distance, opponent)
            if distance < 150 and self.attack_cooldown <= 0:
                self.attack_light()
            return

        # AI行为决策
        if distance > 200:
            self.ai_approach(distance, opponent)
        elif distance > 80:
            # 中距离：大概率进攻
            if random.random() < min(self.aggression + 0.2, 0.85):
                self.ai_attack(distance, opponent)
                self.passive_timer = 0.0
            else:
                self._safe_retreat(distance, opponent)
        else:
            # 近距离：直接打
            self.ai_combat(distance, opponent)
            self.passive_timer = 0.0

    def _do_jump(self):
        """执行跳跃"""
        self.vel_y = -self.stats.jump_force
        self.on_ground = False
        self.y -= 5  # 立刻脱离地面，避免下一帧平台碰撞把角色拉回
        self.state = FighterState.JUMP
        self.animator.set_state(AnimationState.JUMP)

    def _find_nearest_enemy_minion(self, opponent: Fighter):
        """找最近的敌方小兵（玩家的小兵）"""
        enemy_manager = getattr(opponent, 'minion_manager', None)
        if not enemy_manager:
            return None
        alive = [m for m in enemy_manager.minions if m.alive]
        if not alive:
            return None
        return min(alive, key=lambda m: abs(self.x - m.x))

    def should_block(self, opponent: Fighter, distance: float) -> bool:
        """判断是否应该防御"""
        if opponent.is_attacking and distance < 150:
            block_prob = self.block_chance
            if self.difficulty == "hard":
                block_prob += 0.3
            elif self.difficulty == "easy":
                block_prob -= 0.2
            return random.random() < block_prob
        return False

    def _is_near_edge(self) -> bool:
        """检测自身是否靠近边缘"""
        return self.x < SCREEN_LEFT + EDGE_DANGER_ZONE or self.x > SCREEN_RIGHT - EDGE_DANGER_ZONE

    def _edge_escape_direction(self, opponent_x: float) -> tuple:
        """靠近边缘时，向场地中央移动"""
        center = (SCREEN_LEFT + SCREEN_RIGHT) / 2
        if self.x < center:
            return (False, True, False, False, False)  # 向右（朝中央）
        else:
            return (True, False, False, False, False)  # 向左（朝中央）

    def _safe_retreat(self, distance: float, opponent: Fighter):
        """安全后撤：后撤方向不能是边缘方向"""
        if opponent.x > self.x:
            retreat_x = self.x - 50
        else:
            retreat_x = self.x + 50

        if retreat_x < SCREEN_LEFT + EDGE_DANGER_ZONE or retreat_x > SCREEN_RIGHT - EDGE_DANGER_ZONE:
            # 后撤会进入危险区，改为向中央移动
            move = self._edge_escape_direction(opponent.x)
            self.apply_movement(*move)
        else:
            self.ai_retreat(distance, opponent)

    def ai_approach(self, distance: float, opponent):
        """接近目标（支持Fighter和Minion）"""
        target_x = opponent.x if hasattr(opponent, 'x') else opponent
        if target_x > self.x:
            self.apply_movement(True, False, False, False, False)
        else:
            self.apply_movement(False, True, False, False, False)

    def ai_attack(self, distance: float, opponent: Fighter):
        """进攻"""
        if distance < 120:
            # 直接出手，不再套双重随机
            if self.attack_cooldown <= 0:
                if random.random() < 0.6:
                    self.attack_light()
                else:
                    self.attack_heavy()
        else:
            self.ai_approach(distance, opponent)

    def ai_retreat(self, distance: float, opponent: Fighter):
        """后撤"""
        if opponent.x > self.x:
            self.apply_movement(False, True, False, False, False)
        else:
            self.apply_movement(True, False, False, False, False)

    def ai_combat(self, distance: float, opponent: Fighter):
        """近身战斗 - 直接出手，不后退"""
        if self.attack_cooldown <= 0:
            r = random.random()
            if r < 0.55:
                self.attack_light()
            elif r < 0.8:
                self.attack_heavy()
            elif (self.special_energy >= self.char_data.stats.special_cost and r < 0.9):
                self.attack_special()
        # 只有太近才稍微后退，避免重叠
        if distance < 40:
            self._safe_retreat(distance, opponent)
        elif distance > 120:
            self.ai_approach(distance, opponent)

    def update(self, dt: float, opponent: Fighter = None):
        """更新AI角色"""
        # 保存对手引用
        self._opponent_ref = opponent

        # 更新AI
        if opponent:
            self.update_ai(dt, opponent)

        # 更新基础逻辑
        super().update(dt, opponent)

    def get_opponent(self):
        """获取对手引用"""
        return self._opponent_ref
