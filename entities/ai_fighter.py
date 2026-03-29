# AI Fighter - AI控制的角色

import random
import math
from typing import Optional
from entities.fighter import Fighter
from config import GROUND_Y
from constants import FighterState, Direction
from game.state_machine import AnimationState

class AIFighter(Fighter):
    """AI控制的角色"""

    def __init__(self, player_id: int, char_data, x: float, y: float,
                 char_index: int = 0, difficulty: str = "normal"):
        super().__init__(player_id, char_data, x, y, char_index)

        self.is_human = False
        self.difficulty = difficulty

        # AI行为参数
        self.aggression = 0.5  # 进攻性 0-1
        self.reaction_time = 0.2  # 反应时间（秒）
        self.reaction_timer = 0.0

        # 行为状态
        self.ai_state = "idle"
        self.target_x = x
        self.jump_chance = 0.02
        self.attack_chance = 0.03
        self.block_chance = 0.4

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

        # 更新朝向
        self.update_direction(opponent.x)

        # 计算与对手的距离
        distance = abs(self.x - opponent.x)

        # 反应延迟
        if self.reaction_timer > 0:
            return

        self.reaction_timer = self.reaction_time * (1.0 - self.aggression * 0.5)

        # 检查是否需要防御
        if self.should_block(opponent, distance):
            self.apply_movement(False, False, False, False, True)
            return

        # 解除防御
        self.is_blocking = False

        # AI行为决策
        if distance > 200:
            # 远距离：接近对手
            self.ai_approach(distance, opponent)
        elif distance > 100:
            # 中距离：判断进攻或后退
            if random.random() < self.aggression:
                self.ai_attack(distance, opponent)
            else:
                self.ai_retreat(distance, opponent)
        else:
            # 近距离：进攻
            self.ai_combat(distance, opponent)

        # 随机跳跃
        if self.on_ground and random.random() < self.jump_chance:
            self.vel_y = -self.stats.jump_force
            self.on_ground = False
            self.state = FighterState.JUMP
            self.animator.set_state(AnimationState.JUMP)

    def should_block(self, opponent: Fighter, distance: float) -> bool:
        """判断是否应该防御"""
        # 简单判断：对手在攻击且距离近
        if opponent.is_attacking and distance < 150:
            # 高难度AI更容易防御
            block_prob = self.block_chance
            if self.difficulty == "hard":
                block_prob += 0.3
            elif self.difficulty == "easy":
                block_prob -= 0.2
            return random.random() < block_prob
        return False

    def ai_approach(self, distance: float, opponent: Fighter):
        """接近对手"""
        if opponent.x > self.x:
            self.apply_movement(True, False, False, False, False)
        else:
            self.apply_movement(False, True, False, False, False)

    def ai_attack(self, distance: float, opponent: Fighter):
        """进攻"""
        # 判断是否在攻击范围
        if distance < 120:
            # 随机攻击
            if random.random() < self.attack_chance:
                if random.random() < 0.6:
                    self.attack_light()
                else:
                    self.attack_heavy()
        else:
            # 接近
            self.ai_approach(distance, opponent)

    def ai_retreat(self, distance: float, opponent: Fighter):
        """后撤"""
        if opponent.x > self.x:
            self.apply_movement(False, True, False, False, False)
        else:
            self.apply_movement(True, False, False, False, False)

    def ai_combat(self, distance: float, opponent: Fighter):
        """近身战斗"""
        # 连击或打断
        if self.attack_cooldown <= 0:
            # 高连击机会
            if random.random() < 0.5:
                self.attack_light()
            elif random.random() < 0.3:
                self.attack_heavy()
            # 必杀技
            elif (self.special_energy >= self.char_data.stats.special_cost and
                  random.random() < self.aggression * 0.2):
                self.attack_special()

        # 保持距离
        if distance < 60:
            self.ai_retreat(distance, opponent)
        elif distance > 100:
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
