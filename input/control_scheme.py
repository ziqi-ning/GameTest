# 控制方案配置

import pygame

# 导出预定义的控制方案
__all__ = ['PLAYER_1', 'PLAYER_2', 'get_player_controls', 'DEFAULT_CONTROLS']

# 玩家1 - WASD + JKL / I
PLAYER_1 = {
    'left': pygame.K_a,
    'right': pygame.K_d,
    'up': pygame.K_w,
    'down': pygame.K_s,
    'light_attack': pygame.K_j,
    'heavy_attack': pygame.K_k,
    'special': pygame.K_l,       # 必杀技1
    'special_2': pygame.K_i,     # 必杀技2
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
    'special': pygame.K_KP3,        # 必杀技1
    'special_2': pygame.K_PERIOD,  # 必杀技2（小键盘 .）
    'block': pygame.K_KP0,
}

def get_player_controls(player_num: int) -> dict:
    """获取指定玩家的控制方案"""
    if player_num == 1:
        return PLAYER_1.copy()
    elif player_num == 2:
        return PLAYER_2.copy()
    else:
        raise ValueError(f"不支持的玩家编号: {player_num}")

# 默认控制方案
DEFAULT_CONTROLS = {
    1: PLAYER_1,
    2: PLAYER_2,
}
