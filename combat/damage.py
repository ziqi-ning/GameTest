# 伤害计算模块

from typing import Tuple

def calculate_damage(attacker_power: int, defender_defense: float,
                     move_multiplier: float = 1.0, combo_multiplier: float = 1.0,
                     combo_count: int = 0) -> int:
    """
    计算伤害值

    参数:
        attacker_power: 攻击方攻击力
        defender_defense: 防御方防御力（0-1之间）
        move_multiplier: 技能倍率
        combo_multiplier: 连击倍率
        combo_count: 当前连击数

    返回:
        最终伤害值
    """
    # 基础伤害
    base_damage = attacker_power * move_multiplier

    # 防御减伤
    reduced_damage = base_damage * (1 - defender_defense)

    # 连击衰减（连击数越多，后续伤害递减）
    combo_penalty = max(0.5, 1.0 - combo_count * 0.03)

    # 最终伤害
    final_damage = int(reduced_damage * combo_penalty * combo_multiplier)

    return max(1, final_damage)  # 至少造成1点伤害


def calculate_knockback(base_knockback: float, knockback_up: float,
                        is_airborne: bool = False, combo_count: int = 0) -> Tuple[float, float]:
    """
    计算击退力度

    返回: (水平击退, 垂直击退)
    """
    # 连击增加击退
    knockback_mult = 1.0 + combo_count * 0.05

    horizontal = base_knockback * knockback_mult
    vertical = knockback_up

    # 空中受击增加垂直击退
    if is_airborne:
        vertical *= 1.5

    return (horizontal, vertical)


def calculate_hitstun(base_hitstun: int, is_blocking: bool = False) -> int:
    """计算受击硬直时间"""
    if is_blocking:
        return int(base_hitstun * 0.6)  # 防御减少60%硬直
    return base_hitstun


def calculate_special_energy_gain(damage: int, attack_type: str) -> int:
    """计算必杀技能量获取"""
    energy_gains = {
        'light': 12,      # 轻攻击获得12能量
        'heavy': 20,      # 重攻击获得20能量
        'special': 0,    # 必杀技不获取能量
        'hit_received': 8,  # 受击获得能量
        'ko': 30,         # KO获得能量
    }
    return energy_gains.get(attack_type, 5)


def get_attack_multiplier(attack_type: str) -> float:
    """获取攻击类型倍率"""
    multipliers = {
        'light': 0.8,
        'heavy': 1.5,
        'special': 2.5,
    }
    return multipliers.get(attack_type, 1.0)


def check_critical_hit(attack_type: str, combo_count: int = 0) -> bool:
    """判定是否暴击"""
    import random

    # 基础暴击率
    crit_chance = 0.0

    # 重攻击有更高暴击率
    if attack_type == 'heavy':
        crit_chance = 0.1
    elif attack_type == 'special':
        crit_chance = 0.3

    # 高连击增加暴击率
    if combo_count >= 5:
        crit_chance += 0.05

    return random.random() < crit_chance


def calculate_critical_damage(damage: int, is_critical: bool) -> int:
    """计算暴击伤害"""
    if is_critical:
        return int(damage * 1.5)
    return damage
