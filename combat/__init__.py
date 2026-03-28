# 战斗系统初始化

from combat.combo_system import ComboSystem, HitboxManager
from combat.damage import (
    calculate_damage,
    calculate_knockback,
    calculate_hitstun,
    calculate_special_energy_gain,
    get_attack_multiplier
)
from combat.special_moves import SpecialMoveManager, Projectile, ProjectileManager

__all__ = [
    'ComboSystem',
    'HitboxManager',
    'calculate_damage',
    'calculate_knockback',
    'calculate_hitstun',
    'calculate_special_energy_gain',
    'get_attack_multiplier',
    'SpecialMoveManager',
    'Projectile',
    'ProjectileManager',
]
