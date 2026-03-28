# 辅助工具函数

import random
import math

def clamp(value: float, min_val: float, max_val: float) -> float:
    """将值限制在指定范围内"""
    return max(min_val, min(max_val, value))

def lerp(start: float, end: float, t: float) -> float:
    """线性插值"""
    return start + (end - start) * clamp(t, 0, 1)

def inverse_lerp(start: float, end: float, value: float) -> float:
    """反向线性插值"""
    if end - start == 0:
        return 0
    return clamp((value - start) / (end - start), 0, 1)

def map_range(value: float, in_min: float, in_max: float, out_min: float, out_max: float) -> float:
    """将一个范围内的值映射到另一个范围"""
    return lerp(out_min, out_max, inverse_lerp(in_min, in_max, value))

def random_range(min_val: float, max_val: float) -> float:
    """在指定范围内生成随机数"""
    return random.uniform(min_val, max_val)

def random_int(min_val: int, max_val: int) -> int:
    """在指定范围内生成随机整数"""
    return random.randint(min_val, max_val)

def sign(value: float) -> int:
    """返回数值的符号（-1, 0, 1）"""
    if value < 0:
        return -1
    elif value > 0:
        return 1
    return 0

def angle_diff(from_angle: float, to_angle: float) -> float:
    """计算两个角度之间的最小差值（度）"""
    diff = (to_angle - from_angle) % 360
    if diff > 180:
        diff -= 360
    return diff

def smooth_damp(current: float, target: float, velocity: list, smooth_time: float, delta_time: float, max_speed: float = float('inf')) -> float:
    """平滑阻尼（类似Unity的SmoothDamp）"""
    omega = 2.0 / smooth_time
    x = omega * delta_time
    exp_x = 1.0 / (1.0 + x + 0.48 * x * x + 0.235 * x * x * x)
    change = current - target
    max_change = max_speed * smooth_time
    change = clamp(change, -max_change, max_change)
    target = current - change
    temp = (velocity[0] + omega * change) * delta_time
    velocity[0] = (velocity[0] - omega * temp) * exp_x
    output = target + (change + temp) * exp_x
    return output

def rect_intersects(r1: tuple, r2: tuple) -> bool:
    """检测两个矩形是否相交
    矩形格式: (x, y, width, height)
    """
    x1, y1, w1, h1 = r1
    x2, y2, w2, h2 = r2
    return x1 < x2 + w2 and x1 + w1 > x2 and y1 < y2 + h2 and y1 + h1 > y2

def point_in_rect(px: float, py: float, rect: tuple) -> bool:
    """检测点是否在矩形内"""
    x, y, w, h = rect
    return x <= px <= x + w and y <= py <= y + h
