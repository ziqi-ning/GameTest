# Player - 玩家控制的角色

import pygame
from typing import Optional
from config import GRAVITY
from constants import FighterState
from entities.fighter import Fighter
from input.input_manager import FighterInput
from input.control_scheme import PLAYER_1, PLAYER_2

class Player(Fighter):
    """玩家控制的角色"""

    def __init__(self, player_id: int, char_data, x: float, y: float, char_index: int = 0):
        super().__init__(player_id, char_data, x, y, char_index)

        # 获取控制方案
        if player_id == 1:
            self.input = FighterInput(PLAYER_1)
        else:
            self.input = FighterInput(PLAYER_2)

        self.is_human = True

    def handle_input(self, left: bool, right: bool, up: bool, down: bool,
                   light_attack: bool, heavy_attack: bool, special: bool, block: bool):
        """处理输入"""
        # 应用移动
        self.apply_movement(left, right, up, down, block)

        # 攻击输入 (优先级: 必杀技 > 重攻击 > 轻攻击)
        if special:
            self.attack_special()
        elif heavy_attack and self.attack_cooldown <= 0:
            self.attack_heavy()
        elif light_attack and self.attack_cooldown <= 0:
            self.attack_light()

    def update(self, dt: float, opponent: Optional[Fighter] = None):
        """更新玩家状态"""
        # 更新朝向
        if opponent:
            self.update_direction(opponent.x)

        # 更新攻击冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # 调用父类更新
        super().update(dt, opponent)
