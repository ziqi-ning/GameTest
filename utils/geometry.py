# 几何计算工具

import math
from typing import Tuple, Optional

class Rect:
    """矩形类，用于碰撞检测"""

    def __init__(self, x: float, y: float, width: float, height: float):
        self.x = x
        self.y = y
        self.width = width
        self.height = height

    @property
    def left(self) -> float:
        return self.x

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def top(self) -> float:
        return self.y

    @property
    def bottom(self) -> float:
        return self.y + self.height

    @property
    def center(self) -> Tuple[float, float]:
        return (self.x + self.width / 2, self.y + self.height / 2)

    @property
    def centerx(self) -> float:
        return self.x + self.width / 2

    @property
    def centery(self) -> float:
        return self.y + self.height / 2

    def intersects(self, other: 'Rect') -> bool:
        """检测与另一个矩形是否相交"""
        return (
            self.x < other.x + other.width and
            self.x + self.width > other.x and
            self.y < other.y + other.height and
            self.y + self.height > other.y
        )

    def colliderect(self, other: 'Rect') -> Optional['Rect']:
        """返回两个矩形的相交区域"""
        if not self.intersects(other):
            return None

        x1 = max(self.x, other.x)
        y1 = max(self.y, other.y)
        x2 = min(self.x + self.width, other.x + other.width)
        y2 = min(self.y + self.height, other.y + other.height)

        return Rect(x1, y1, x2 - x1, y2 - y1)

    def contains_point(self, px: float, py: float) -> bool:
        """检测点是否在矩形内"""
        return self.x <= px <= self.x + self.width and self.y <= py <= self.y + self.height

    def move(self, dx: float, dy: float) -> 'Rect':
        """移动矩形"""
        return Rect(self.x + dx, self.y + dy, self.width, self.height)

    def inflate(self, dw: float, dh: float) -> 'Rect':
        """扩展矩形（正值为扩大，负值为缩小）"""
        return Rect(
            self.x - dw / 2,
            self.y - dh / 2,
            self.width + dw,
            self.height + dh
        )

    def to_tuple(self) -> Tuple[float, float, float, float]:
        """转换为元组格式 (x, y, width, height)"""
        return (self.x, self.y, self.width, self.height)

    def __repr__(self) -> str:
        return f"Rect({self.x}, {self.y}, {self.width}, {self.height})"


class Hitbox(Rect):
    """攻击判定盒"""

    def __init__(self, x: float, y: float, width: float, height: float,
                 damage: int = 50, hitstun: int = 10, knockback: float = 5,
                 attack_type: str = "light"):
        super().__init__(x, y, width, height)
        self.damage = damage
        self.hitstun = hitstun
        self.knockback = knockback
        self.attack_type = attack_type
        self.active = True
        self.hit_list = []  # 已命中的目标列表

    def can_hit(self, target_id: int) -> bool:
        """检查是否可以命中目标（防止同一攻击多次命中）"""
        return target_id not in self.hit_list

    def register_hit(self, target_id: int) -> None:
        """记录命中"""
        self.hit_list.append(target_id)


class Hurtbox(Rect):
    """受击判定盒"""

    def __init__(self, x: float, y: float, width: float, height: float,
                 owner_id: int = 0, can_block: bool = True):
        super().__init__(x, y, width, height)
        self.owner_id = owner_id
        self.can_block = can_block


def circle_collision(x1: float, y1: float, r1: float, x2: float, y2: float, r2: float) -> bool:
    """圆形碰撞检测"""
    dx = x2 - x1
    dy = y2 - y1
    distance_squared = dx * dx + dy * dy
    radius_sum = r1 + r2
    return distance_squared <= radius_sum * radius_sum


def distance(x1: float, y1: float, x2: float, y2: float) -> float:
    """计算两点之间的距离"""
    dx = x2 - x1
    dy = y2 - y1
    return math.sqrt(dx * dx + dy * dy)


def line_intersection(x1: float, y1: float, x2: float, y2: float,
                     x3: float, y3: float, x4: float, y4: float) -> Optional[Tuple[float, float]]:
    """计算两条线的交点"""
    denom = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
    if abs(denom) < 0.0001:
        return None

    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / denom
    u = -((x1 - x2) * (y1 - y3) - (y1 - y2) * (x1 - x3)) / denom

    if 0 <= t <= 1 and 0 <= u <= 1:
        return (x1 + t * (x2 - x1), y1 + t * (y2 - y1))
    return None
