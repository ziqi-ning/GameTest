# 必杀技系统

from typing import List, Tuple, Callable, Optional
from characters.character_base import SpecialMoveData

class SpecialMoveManager:
    """必杀技管理器"""

    def __init__(self, max_energy: int = 100):
        self.max_energy = max_energy
        self.current_energy = 0
        self.energy_gain_rate = 0.5  # 每秒能量恢复
        self.special_moves: List[SpecialMoveData] = []
        self.is_executing = False
        self.execution_timer = 0.0

        # 特效回调
        self.on_special_start: Optional[Callable] = None
        self.on_special_hit: Optional[Callable] = None
        self.on_special_end: Optional[Callable] = None

    def add_special_move(self, move: SpecialMoveData):
        """添加必杀技"""
        self.special_moves.append(move)

    def set_special_moves(self, moves: List[SpecialMoveData]):
        """设置必杀技列表"""
        self.special_moves = moves

    def can_use_special(self, move_index: int = 0) -> bool:
        """检查是否可以使用必杀技"""
        if move_index >= len(self.special_moves):
            return False

        move = self.special_moves[move_index]
        return (self.current_energy >= move.energy_cost and
                not self.is_executing)

    def use_special(self, move_index: int = 0) -> bool:
        """使用必杀技"""
        if not self.can_use_special(move_index):
            return False

        move = self.special_moves[move_index]
        self.current_energy -= move.energy_cost
        self.is_executing = True
        self.execution_timer = 0.0

        if self.on_special_start:
            self.on_special_start(move)

        return True

    def update(self, dt: float, is_executing: bool = False):
        """更新必杀技状态"""
        self.is_executing = is_executing

        # 能量恢复（不在执行必杀技时）
        if not is_executing:
            self.current_energy = min(
                self.max_energy,
                self.current_energy + self.energy_gain_rate * dt
            )

        if is_executing:
            self.execution_timer += dt

    def add_energy(self, amount: int):
        """增加能量"""
        self.current_energy = min(self.max_energy, self.current_energy + amount)

    def get_energy_percent(self) -> float:
        """获取能量百分比"""
        return self.current_energy / self.max_energy

    def reset(self):
        """重置能量"""
        self.current_energy = 0
        self.is_executing = False
        self.execution_timer = 0.0


class Projectile:
    """投射物（如波动拳）"""

    def __init__(self, x: float, y: float, direction: int,
                 speed: float = 10, damage: int = 80,
                 owner_id: int = 0, size: Tuple[int, int] = (60, 40)):
        self.x = x
        self.y = y
        self.direction = direction
        self.speed = speed
        self.damage = damage
        self.owner_id = owner_id
        self.width, self.height = size
        self.active = True
        self.lifetime = 0.0
        self.max_lifetime = 3.0  # 最大存在时间

        # 视觉效果
        self.anim_frame = 0
        self.anim_timer = 0.0

        # 附加属性（由发射方设置）
        self.effect_type: str = "none"
        self.hitstun: int = 10
        self.knockback: float = 5.0
        self.knockback_up: float = 0.0
        self.char_name: str = ""

    def update(self, dt: float):
        """更新投射物"""
        if not self.active:
            return

        self.x += self.speed * self.direction * 60 * dt
        self.lifetime += dt

        # 更新动画
        self.anim_timer += dt
        if self.anim_timer >= 0.05:
            self.anim_timer = 0.0
            self.anim_frame = (self.anim_frame + 1) % 4

        # 检查是否过期
        if self.lifetime >= self.max_lifetime:
            self.active = False

    def get_rect(self) -> Tuple[float, float, float, float]:
        """获取投射物碰撞框"""
        return (self.x - self.width / 2, self.y - self.height / 2,
                self.width, self.height)

    def deactivate(self):
        """停用投射物"""
        self.active = False


class ProjectileManager:
    """投射物管理器"""

    def __init__(self):
        self.projectiles: List[Projectile] = []

    def spawn(self, x: float, y: float, direction: int,
              speed: float = 10, damage: int = 80,
              owner_id: int = 0) -> Projectile:
        """生成投射物"""
        projectile = Projectile(x, y, direction, speed, damage, owner_id)
        self.projectiles.append(projectile)
        return projectile

    def update(self, dt: float):
        """更新所有投射物"""
        for proj in self.projectiles:
            proj.update(dt)

        # 移除已停用的投射物
        self.projectiles = [p for p in self.projectiles if p.active]

    def get_projectiles_for_owner(self, owner_id: int) -> List[Projectile]:
        """获取属于指定所有者的投射物"""
        return [p for p in self.projectiles if p.owner_id == owner_id]

    def clear(self):
        """清除所有投射物"""
        self.projectiles.clear()

    def draw(self, surface, camera_offset: Tuple[int, int] = (0, 0)):
        """绘制所有投射物"""
        import pygame
        from config import Colors

        for proj in self.projectiles:
            if not proj.active:
                continue

            screen_x = proj.x - camera_offset[0]
            screen_y = proj.y - camera_offset[1]

            # 绘制投射物光效
            colors = [(255, 255, 100), (255, 200, 50), (255, 150, 0)]
            color_idx = proj.anim_frame % len(colors)

            # 外层光晕
            pygame.draw.ellipse(surface, colors[color_idx],
                             (screen_x - 35, screen_y - 25, 70, 50))
            # 内层核心
            pygame.draw.ellipse(surface, (255, 255, 255),
                             (screen_x - 20, screen_y - 15, 40, 30))
