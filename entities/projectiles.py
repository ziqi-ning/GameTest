# 投射物模块

import pygame
from typing import List, Tuple, Optional
from combat.special_moves import Projectile, ProjectileManager

class Projectiles:
    """投射物管理类（兼容旧接口）"""

    def __init__(self):
        self.manager = ProjectileManager()

    def spawn(self, x: float, y: float, direction: int,
              speed: float = 10, damage: int = 80,
              owner_id: int = 0) -> Projectile:
        """生成投射物"""
        return self.manager.spawn(x, y, direction, speed, damage, owner_id)

    def update(self, dt: float):
        """更新投射物"""
        self.manager.update(dt)

    def draw(self, surface: pygame.Surface, camera_offset: Tuple[int, int] = (0, 0)):
        """绘制投射物"""
        self.manager.draw(surface, camera_offset)

    def clear(self):
        """清除所有投射物"""
        self.manager.clear()
