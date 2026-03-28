# 角色数据基类

from dataclasses import dataclass
from typing import List, Tuple
import pygame

@dataclass
class CharacterStats:
    """角色属性"""
    name: str
    name_cn: str  # 中文名
    description: str  # 角色描述
    max_health: int = 1000  # 最大生命值
    walk_speed: float = 5.0  # 移动速度
    jump_force: float = 15.0  # 跳跃力度
    attack_power: int = 80  # 基础攻击力
    defense: float = 0.15  # 防御力（减伤比）
    special_cost: int = 100  # 必杀技能量需求
    color: Tuple[int, int, int] = (255, 255, 255)  # 角色主色
    secondary_color: Tuple[int, int, int] = (200, 200, 200)  # 角色次色


@dataclass
class MoveData:
    """攻击动作数据"""
    name: str
    damage: int
    hitbox_offset: Tuple[int, int]  # 相对角色的偏移
    hitbox_size: Tuple[int, int]  # 判定盒大小
    active_start: int  # 开始判定帧
    active_frames: int  # 判定持续帧数
    recovery_frames: int  # 收招帧数
    total_frames: int  # 总帧数
    hitstun: int  # 命中硬直
    knockback: float  # 击退力度
    knockback_up: float = 0  # 向上击退
    can_block: bool = True  # 能否被防御


@dataclass
class SpecialMoveData:
    """必杀技数据"""
    name: str
    name_cn: str  # 中文名
    damage: int
    energy_cost: int  # 能量消耗
    hitbox_offset: Tuple[int, int]
    hitbox_size: Tuple[int, int]
    active_start: int
    active_frames: int
    total_frames: int
    hitstun: int
    knockback: float
    knockback_up: float = 5
    projectile: bool = False  # 是否产生投射物
    projectile_speed: float = 10  # 投射物速度


class CharacterData:
    """角色数据类"""

    def __init__(self, stats: CharacterStats, moves: List[MoveData], special: SpecialMoveData):
        self.stats = stats
        self.moves = moves
        self.special = special

    @staticmethod
    def create_power_type() -> CharacterStats:
        """力量型角色属性"""
        return CharacterStats(
            name="Power",
            name_cn="大力",
            description="力量型角色，攻击力高但速度慢",
            max_health=1100,
            walk_speed=4.0,
            jump_force=14.0,
            attack_power=100,
            defense=0.20,
            special_cost=100,
            color=(220, 50, 50),
            secondary_color=(150, 30, 30)
        )

    @staticmethod
    def create_speed_type() -> CharacterStats:
        """速度型角色属性"""
        return CharacterStats(
            name="Speed",
            name_cn="快手",
            description="速度型角色，攻速快但伤害低",
            max_health=850,
            walk_speed=6.5,
            jump_force=16.0,
            attack_power=60,
            defense=0.10,
            special_cost=100,
            color=(50, 180, 220),
            secondary_color=(30, 120, 160)
        )

    @staticmethod
    def create_balanced_type() -> CharacterStats:
        """均衡型角色属性"""
        return CharacterStats(
            name="Balance",
            name_cn="全能",
            description="均衡型角色，各项能力平衡",
            max_health=1000,
            walk_speed=5.0,
            jump_force=15.0,
            attack_power=80,
            defense=0.15,
            special_cost=100,
            color=(50, 200, 100),
            secondary_color=(30, 140, 70)
        )

    @staticmethod
    def create_technical_type() -> CharacterStats:
        """技巧型角色属性"""
        return CharacterStats(
            name="Technical",
            name_cn="技巧",
            description="技巧型角色，擅长远程牵制",
            max_health=900,
            walk_speed=5.5,
            jump_force=15.5,
            attack_power=70,
            defense=0.12,
            special_cost=100,
            color=(200, 100, 220),
            secondary_color=(140, 60, 170)
        )


def get_default_moves(stats: CharacterStats) -> List[MoveData]:
    """获取默认攻击动作"""
    power_mult = stats.attack_power / 80.0  # 根据攻击力调整

    return [
        MoveData(
            name="light_punch",
            damage=int(40 * power_mult),
            hitbox_offset=(40, 30),
            hitbox_size=(60, 40),
            active_start=3,
            active_frames=3,
            recovery_frames=4,
            total_frames=10,
            hitstun=12,
            knockback=4,
            knockback_up=0
        ),
        MoveData(
            name="heavy_punch",
            damage=int(70 * power_mult),
            hitbox_offset=(45, 25),
            hitbox_size=(70, 50),
            active_start=4,
            active_frames=4,
            recovery_frames=6,
            total_frames=14,
            hitstun=18,
            knockback=10,
            knockback_up=3
        ),
    ]


def get_default_special(stats: CharacterStats) -> SpecialMoveData:
    """获取默认必杀技"""
    power_mult = stats.attack_power / 80.0

    return SpecialMoveData(
        name="special_attack",
        name_cn="必杀技",
        damage=int(150 * power_mult),
        energy_cost=100,
        hitbox_offset=(50, 10),
        hitbox_size=(100, 100),
        active_start=5,
        active_frames=10,
        total_frames=23,
        hitstun=25,
        knockback=20,
        knockback_up=8,
        projectile=False
    )
