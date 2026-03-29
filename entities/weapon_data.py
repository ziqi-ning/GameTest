# Weapon Data System - 武器数据系统
# 支持数据驱动的武器定义，武器作为角色数据的一部分，可以灵活替换

from dataclasses import dataclass, field
from enum import Enum
from typing import Callable, Optional, Tuple, List
import pygame


class WeaponType(Enum):
    FIST = "fist"
    FLAG = "flag"
    PISTOL = "pistol"
    RIFLE = "rifle"
    DAGGER = "dagger"
    EAGLE = "eagle"
    NUNCHAKU = "nunchaku"
    SHURIKEN = "shuriken"
    LASER = "laser"


@dataclass
class WeaponData:
    """武器数据定义"""
    weapon_type: WeaponType
    name_cn: str  # 中文名
    sprite_key: str = ""          # WeaponAssets中的sprite key
    sprite_frames_key: str = ""    # 多帧武器（如老鹰扑翼）
    grip_px: int = 12             # 握柄在sprite中的x像素位置（从sprite左边缘算）
    scale_w: int = 40             # 绘制宽度（像素）
    hand_y_offset: int = -50      # 握柄相对于角色脚部的Y偏移
    atk_forward_extend: int = 18   # 攻击时握柄额外前伸量
    atk_y_offset: int = 0          # 攻击时握柄Y额外偏移
    # 程序化绘制用颜色
    primary_color: Tuple[int,int,int] = (200, 200, 200)
    secondary_color: Tuple[int,int,int] = (150, 150, 150)
    # 武器朝向: 0=水平, 1=斜向下, -1=斜向上
    angle: int = 0
    # 投射物特效用
    projectile_color: Tuple[int,int,int,int] = (255, 100, 50, 180)
    glow_color: Tuple[int,int,int] = (255, 200, 50)
    # 备用程序绘制函数 (sprite加载失败时调用)
    procedural_draw: Optional[Callable] = field(default=None, repr=False)


WEAPON_REGISTRY: dict[WeaponType, WeaponData] = {}

def register_weapon(data: WeaponData):
    WEAPON_REGISTRY[data.weapon_type] = data

def get_weapon(t: WeaponType) -> WeaponData:
    return WEAPON_REGISTRY.get(t, WEAPON_REGISTRY[WeaponType.FIST])


def _register_all_weapons():
    # === 拳头（无武器）===
    register_weapon(WeaponData(
        weapon_type=WeaponType.FIST,
        name_cn="拳头",
        grip_px=0,
        scale_w=0,
        hand_y_offset=-50,
        atk_forward_extend=15,
        primary_color=(220, 180, 140),
        secondary_color=(180, 140, 100),
    ))

    # === 五星红旗 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.FLAG,
        name_cn="五星红旗",
        grip_px=0,
        scale_w=0,
        hand_y_offset=-50,
        atk_forward_extend=20,
        primary_color=(220, 30, 30),
        secondary_color=(255, 220, 0),
        angle=1,
        projectile_color=(220, 30, 30, 200),
        glow_color=(255, 220, 0),
    ))

    # === 激光枪 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.LASER,
        name_cn="激光枪",
        sprite_key="laser_gun",
        sprite_frames_key="laser_gun_frames",
        grip_px=8,
        scale_w=42,
        hand_y_offset=-50,
        atk_forward_extend=18,
        atk_y_offset=0,
        primary_color=(60, 60, 80),
        secondary_color=(30, 180, 255),
        projectile_color=(80, 140, 255, 200),
        glow_color=(30, 180, 255),
    ))

    # === 匕首 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.DAGGER,
        name_cn="军用匕首",
        sprite_key="knife",
        grip_px=6,
        scale_w=30,
        hand_y_offset=-48,
        atk_forward_extend=20,
        atk_y_offset=-5,
        primary_color=(180, 160, 120),
        secondary_color=(220, 220, 240),
        angle=1,
        projectile_color=(200, 180, 100, 200),
        glow_color=(255, 220, 100),
    ))

    # === 老鹰 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.EAGLE,
        name_cn="白头海雕",
        sprite_key="eagle",
        sprite_frames_key="eagle_frames",
        grip_px=0,
        scale_w=60,
        hand_y_offset=-45,
        atk_forward_extend=25,
        atk_y_offset=-10,
        primary_color=(139, 90, 43),
        secondary_color=(255, 200, 0),
        projectile_color=(139, 90, 43, 200),
        glow_color=(255, 220, 50),
    ))

    # === 手枪 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.PISTOL,
        name_cn="沙漠之鹰",
        sprite_key="pistol_gun",
        grip_px=7,
        scale_w=38,
        hand_y_offset=-50,
        atk_forward_extend=15,
        atk_y_offset=0,
        primary_color=(80, 80, 100),
        secondary_color=(200, 50, 50),
        projectile_color=(255, 150, 50, 200),
        glow_color=(255, 100, 50),
    ))

    # === 步枪 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.RIFLE,
        name_cn="突击步枪",
        sprite_key="smg_flag",
        grip_px=7,
        scale_w=50,
        hand_y_offset=-50,
        atk_forward_extend=22,
        atk_y_offset=0,
        primary_color=(60, 60, 80),
        secondary_color=(100, 200, 100),
        projectile_color=(200, 200, 100, 200),
        glow_color=(200, 255, 100),
    ))

    # === 双截棍 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.NUNCHAKU,
        name_cn="双截棍",
        grip_px=0,
        scale_w=0,
        hand_y_offset=-50,
        atk_forward_extend=20,
        atk_y_offset=-5,
        primary_color=(180, 140, 80),
        secondary_color=(220, 180, 120),
        angle=1,
        projectile_color=(220, 180, 80, 180),
        glow_color=(255, 220, 100),
    ))

    # === 手里剑 ===
    register_weapon(WeaponData(
        weapon_type=WeaponType.SHURIKEN,
        name_cn="手里剑",
        grip_px=0,
        scale_w=28,
        hand_y_offset=-48,
        atk_forward_extend=22,
        atk_y_offset=-8,
        primary_color=(180, 180, 190),
        secondary_color=(80, 80, 90),
        projectile_color=(180, 180, 190, 200),
        glow_color=(200, 200, 220),
    ))


_register_all_weapons()
