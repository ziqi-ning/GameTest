# 输入管理模块

import pygame
from typing import Dict, List, Set

class InputManager:
    """统一的输入管理器，处理键盘和手柄输入"""

    def __init__(self):
        pygame.joystick.init()
        self.joysticks = [pygame.joystick.Joystick(i) for i in range(pygame.joystick.get_count())]

        # 键盘状态
        self.keys_pressed = []  # pygame.key.get_pressed() 的结果
        self.prev_keys_pressed = []

    def update(self):
        """每帧更新输入状态"""
        # 保存上一帧状态
        self.prev_keys_pressed = self.keys_pressed.copy()

        # 获取当前按键状态
        self.keys_pressed = list(pygame.key.get_pressed())

    def is_key_pressed(self, key: int) -> bool:
        """检测按键是否刚刚按下"""
        current = self.keys_pressed[key] if key < len(self.keys_pressed) else 0
        previous = self.prev_keys_pressed[key] if key < len(self.prev_keys_pressed) else 0
        return bool(current) and not bool(previous)

    def is_key_held(self, key: int) -> bool:
        """检测按键是否按住"""
        return bool(self.keys_pressed[key]) if key < len(self.keys_pressed) else False

    def is_key_released(self, key: int) -> bool:
        """检测按键是否刚刚释放"""
        current = self.keys_pressed[key] if key < len(self.keys_pressed) else 0
        previous = self.prev_keys_pressed[key] if key < len(self.prev_keys_pressed) else 0
        return not bool(current) and bool(previous)

    def get_axis(self, joystick_id: int, axis: int) -> float:
        """获取手柄轴值"""
        # 手柄支持（暂未实现）
        return 0.0


class ControlScheme:
    """控制方案定义"""

    # 玩家1 - WASD + JKL
    PLAYER_1 = {
        'left': pygame.K_a,
        'right': pygame.K_d,
        'up': pygame.K_w,
        'down': pygame.K_s,
        'light_attack': pygame.K_j,
        'heavy_attack': pygame.K_k,
        'special': pygame.K_l,
        'block': pygame.K_u,
    }

    # 玩家2 - 方向键 + 数字键盘
    PLAYER_2 = {
        'left': pygame.K_LEFT,
        'right': pygame.K_RIGHT,
        'up': pygame.K_UP,
        'down': pygame.K_DOWN,
        'light_attack': pygame.K_KP1,
        'heavy_attack': pygame.K_KP2,
        'special': pygame.K_KP3,
        'block': pygame.K_KP0,
    }


class FighterInput:
    """角色输入状态"""

    def __init__(self, controls: Dict[str, int]):
        self.controls = controls
        self.left = False
        self.right = False
        self.up = False
        self.down = False
        self.light_attack = False
        self.heavy_attack = False
        self.special = False
        self.block = False
        self.jump_pressed = False
        self.light_pressed = False
        self.heavy_pressed = False
        self.special_pressed = False
        self.block_pressed = False

    def update(self, input_manager: InputManager, is_player1: bool = True):
        """从InputManager更新输入状态"""
        c = self.controls

        # 移动
        self.left = input_manager.is_key_held(c['left'])
        self.right = input_manager.is_key_held(c['right'])
        self.up = input_manager.is_key_held(c['up'])
        self.down = input_manager.is_key_held(c['down'])

        # 攻击（边缘触发）
        self.light_pressed = input_manager.is_key_pressed(c['light_attack'])
        self.heavy_pressed = input_manager.is_key_pressed(c['heavy_attack'])
        self.special_pressed = input_manager.is_key_pressed(c['special'])
        self.block_pressed = input_manager.is_key_pressed(c['block'])

        self.light_attack = input_manager.is_key_held(c['light_attack'])
        self.heavy_attack = input_manager.is_key_held(c['heavy_attack'])
        self.special = input_manager.is_key_held(c['special'])
        self.block = input_manager.is_key_held(c['block'])
