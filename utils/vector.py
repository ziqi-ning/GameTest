# 2D向量工具类

import math

class Vector2:
    """2D向量类，封装常用向量运算"""

    def __init__(self, x: float = 0, y: float = 0):
        self.x = x
        self.y = y

    @staticmethod
    def from_angle(angle: float, length: float = 1) -> 'Vector2':
        """从角度创建向量（角度以度为单位）"""
        rad = math.radians(angle)
        return Vector2(math.cos(rad) * length, math.sin(rad) * length)

    def copy(self) -> 'Vector2':
        """返回向量的副本"""
        return Vector2(self.x, self.y)

    def length(self) -> float:
        """返回向量的长度"""
        return math.sqrt(self.x * self.x + self.y * self.y)

    def length_squared(self) -> float:
        """返回向量长度的平方（避免开方运算）"""
        return self.x * self.x + self.y * self.y

    def normalize(self) -> 'Vector2':
        """返回归一化后的向量"""
        length = self.length()
        if length > 0:
            return Vector2(self.x / length, self.y / length)
        return Vector2(0, 0)

    def dot(self, other: 'Vector2') -> float:
        """点积"""
        return self.x * other.x + self.y * other.y

    def cross(self, other: 'Vector2') -> float:
        """叉积（2D中返回标量）"""
        return self.x * other.y - self.y * other.x

    def distance_to(self, other: 'Vector2') -> float:
        """到另一个点的距离"""
        return (self - other).length()

    def distance_squared_to(self, other: 'Vector2') -> float:
        """到另一个点距离的平方"""
        return (self - other).length_squared()

    def angle_to(self, other: 'Vector2') -> float:
        """到另一个向量的角度（度）"""
        dx = other.x - self.x
        dy = other.y - self.y
        return math.degrees(math.atan2(dy, dx))

    def rotate(self, angle: float) -> 'Vector2':
        """绕原点旋转（角度以度为单位）"""
        rad = math.radians(angle)
        cos_a = math.cos(rad)
        sin_a = math.sin(rad)
        return Vector2(
            self.x * cos_a - self.y * sin_a,
            self.x * sin_a + self.y * cos_a
        )

    def lerp(self, other: 'Vector2', t: float) -> 'Vector2':
        """线性插值"""
        return Vector2(
            self.x + (other.x - self.x) * t,
            self.y + (other.y - self.y) * t
        )

    def clamp(self, min_val: float, max_val: float) -> 'Vector2':
        """限制向量长度"""
        length = self.length()
        if length > max_val:
            return self.normalize() * max_val
        elif length < min_val and length > 0:
            return self.normalize() * min_val
        return self.copy()

    def __add__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x + other.x, self.y + other.y)

    def __sub__(self, other: 'Vector2') -> 'Vector2':
        return Vector2(self.x - other.x, self.y - other.y)

    def __mul__(self, scalar: float) -> 'Vector2':
        return Vector2(self.x * scalar, self.y * scalar)

    def __rmul__(self, scalar: float) -> 'Vector2':
        return self.__mul__(scalar)

    def __truediv__(self, scalar: float) -> 'Vector2':
        if scalar != 0:
            return Vector2(self.x / scalar, self.y / scalar)
        return Vector2(0, 0)

    def __neg__(self) -> 'Vector2':
        return Vector2(-self.x, -self.y)

    def __eq__(self, other: 'Vector2') -> bool:
        return abs(self.x - other.x) < 0.0001 and abs(self.y - other.y) < 0.0001

    def __repr__(self) -> str:
        return f"Vector2({self.x:.2f}, {self.y:.2f})"
