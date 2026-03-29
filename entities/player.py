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

    def __init__(self, player_id: int, char_data, x: float, y: float,
                 char_index: int = 0, stage=None):
        super().__init__(player_id, char_data, x, y, char_index, stage=stage)

        # 获取控制方案
        if player_id == 1:
            self.input = FighterInput(PLAYER_1)
        else:
            self.input = FighterInput(PLAYER_2)

        self.is_human = True
        self._opponent_ref = None  # 保存对手引用用于必杀技

    def handle_input(self, left: bool, right: bool, up: bool, down: bool,
                   light_attack: bool, heavy_attack: bool,
                   special: bool, special_2: bool, block: bool,
                   summon_minion: bool = False, toggle_minion: bool = False):
        """处理输入"""
        # 应用移动
        self.apply_movement(left, right, up, down, block)

        # 攻击输入 (优先级: 必杀技2 > 必杀技1 > 重攻击 > 轻攻击)
        if special_2:
            self.attack_special(move_index=1)
        elif special:
            self.attack_special(move_index=0)
        elif heavy_attack and self.attack_cooldown <= 0:
            self.attack_heavy()
        elif light_attack and self.attack_cooldown <= 0:
            self.attack_light()

        # U键：召唤小兵
        if summon_minion:
            success = self.minion_manager.try_summon(self.x, self.y)
            if success:
                self.effect_manager.add_text(
                    "召唤!", self.x, self.y - 180, (255, 220, 60), 32, 1.0
                )
            else:
                self.effect_manager.add_text(
                    f"金币不足({self.minion_manager.coin_int}/20)",
                    self.x, self.y - 180, (255, 80, 80), 26, 1.0
                )

        # O键：切换小兵模式
        if toggle_minion and self.minion_manager.minions:
            mode = self.minion_manager.toggle_mode()
            mode_cn = "冲锋!" if mode == "charge" else "跟随!"
            self.effect_manager.add_text(
                mode_cn, self.x, self.y - 200, (200, 200, 255), 30, 1.0
            )

    def update(self, dt: float, opponent: Optional[Fighter] = None):
        """更新玩家状态"""
        # 保存对手引用
        self._opponent_ref = opponent

        # 更新朝向
        if opponent:
            self.update_direction(opponent.x)

        # 更新攻击冷却
        if self.attack_cooldown > 0:
            self.attack_cooldown -= dt

        # 调用父类更新
        super().update(dt, opponent)

    def get_opponent(self):
        """获取对手引用"""
        return self._opponent_ref
