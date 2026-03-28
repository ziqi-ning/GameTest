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
    dodge_chance: float = 0.0  # 闪避几率 (神秘人用)


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
    effect_type: str = "none"  # 效果类型: none, burn, slow, poison


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
    effect_type: str = "none"  # 特殊效果
    effect_duration: float = 0.0  # 效果持续时间
    effect_value: float = 0.0  # 效果数值


class CharacterData:
    """角色数据类"""

    def __init__(self, stats: CharacterStats, moves: List[MoveData], special: List[SpecialMoveData]):
        self.stats = stats
        self.moves = moves
        self.special = special

    @staticmethod
    def create_gong_dage() -> CharacterStats:
        """龚大哥 - 力量型，血量厚，速度慢，主题：爱国"""
        return CharacterStats(
            name="GongDaGe",
            name_cn="龚大哥",
            description="力量型角色，血量深厚但速度慢，技能围绕「爱国」展开",
            max_health=1500,
            walk_speed=3.5,
            jump_force=12.0,
            attack_power=120,
            defense=0.25,
            special_cost=100,
            color=(220, 50, 50),
            secondary_color=(180, 30, 30)
        )

    @staticmethod
    def create_junshi() -> CharacterStats:
        """军师 - 远程型，伤害爆炸，主题：实验室"""
        return CharacterStats(
            name="JunShi",
            name_cn="军师",
            description="远程型角色，擅长波动攻击，技能围绕「实验室」展开",
            max_health=900,
            walk_speed=5.0,
            jump_force=14.0,
            attack_power=100,
            defense=0.10,
            special_cost=100,
            color=(100, 50, 220),
            secondary_color=(70, 30, 180)
        )

    @staticmethod
    def create_shenmiren() -> CharacterStats:
        """神秘人 - 被动闪避，技能围绕「叛国」"""
        return CharacterStats(
            name="ShenMiRen",
            name_cn="神秘人",
            description="技巧型角色，被动随机闪避攻击，技能围绕「叛国」展开",
            max_health=1000,
            walk_speed=6.0,
            jump_force=16.0,
            attack_power=85,
            defense=0.12,
            special_cost=100,
            color=(50, 50, 50),
            secondary_color=(100, 100, 100),
            dodge_chance=0.25  # 25% 闪避几率
        )

    @staticmethod
    def create_zitong() -> CharacterStats:
        """籽桐 - 负面增益，减速控制，主题：雕"""
        return CharacterStats(
            name="ZiTong",
            name_cn="籽桐",
            description="控制型角色，擅长负面增益和减速控制，技能围绕「雕」展开",
            max_health=950,
            walk_speed=5.5,
            jump_force=15.0,
            attack_power=75,
            defense=0.15,
            special_cost=100,
            color=(80, 180, 80),
            secondary_color=(50, 140, 50)
        )


def get_gong_dage_moves(stats: CharacterStats) -> List[MoveData]:
    """龚大哥的普通攻击"""
    power_mult = stats.attack_power / 80.0
    return [
        MoveData(
            name="爱国重拳",
            damage=int(50 * power_mult),
            hitbox_offset=(50, 30),
            hitbox_size=(70, 45),
            active_start=4,
            active_frames=3,
            recovery_frames=5,
            total_frames=12,
            hitstun=14,
            knockback=6,
            knockback_up=0,
            effect_type="none"
        ),
        MoveData(
            name="爱国连击",
            damage=int(80 * power_mult),
            hitbox_offset=(55, 25),
            hitbox_size=(80, 55),
            active_start=5,
            active_frames=4,
            recovery_frames=7,
            total_frames=16,
            hitstun=20,
            knockback=12,
            knockback_up=4,
            effect_type="none"
        ),
    ]


def get_junshi_moves(stats: CharacterStats) -> List[MoveData]:
    """军师的普通攻击"""
    power_mult = stats.attack_power / 80.0
    return [
        MoveData(
            name="实验室冲击波",
            damage=int(35 * power_mult),
            hitbox_offset=(60, 25),
            hitbox_size=(80, 35),
            active_start=3,
            active_frames=4,
            recovery_frames=4,
            total_frames=11,
            hitstun=10,
            knockback=5,
            knockback_up=0,
            effect_type="none"
        ),
        MoveData(
            name="实验室射线",
            damage=int(60 * power_mult),
            hitbox_offset=(70, 20),
            hitbox_size=(100, 40),
            active_start=4,
            active_frames=5,
            recovery_frames=6,
            total_frames=15,
            hitstun=16,
            knockback=8,
            knockback_up=2,
            effect_type="burn"
        ),
    ]


def get_shenmiren_moves(stats: CharacterStats) -> List[MoveData]:
    """神秘人的普通攻击"""
    power_mult = stats.attack_power / 80.0
    return [
        MoveData(
            name="叛国暗刺",
            damage=int(40 * power_mult),
            hitbox_offset=(45, 30),
            hitbox_size=(55, 40),
            active_start=2,
            active_frames=3,
            recovery_frames=3,
            total_frames=8,
            hitstun=8,
            knockback=3,
            knockback_up=0,
            effect_type="none"
        ),
        MoveData(
            name="叛国匕首",
            damage=int(70 * power_mult),
            hitbox_offset=(50, 25),
            hitbox_size=(65, 45),
            active_start=3,
            active_frames=4,
            recovery_frames=5,
            total_frames=12,
            hitstun=12,
            knockback=6,
            knockback_up=2,
            effect_type="poison"
        ),
    ]


def get_zitong_moves(stats: CharacterStats) -> List[MoveData]:
    """籽桐的普通攻击"""
    power_mult = stats.attack_power / 80.0
    return [
        MoveData(
            name="雕羽攻击",
            damage=int(35 * power_mult),
            hitbox_offset=(45, 30),
            hitbox_size=(55, 40),
            active_start=3,
            active_frames=3,
            recovery_frames=4,
            total_frames=10,
            hitstun=10,
            knockback=4,
            knockback_up=0,
            effect_type="slow"
        ),
        MoveData(
            name="雕羽连斩",
            damage=int(55 * power_mult),
            hitbox_offset=(50, 25),
            hitbox_size=(70, 45),
            active_start=4,
            active_frames=4,
            recovery_frames=5,
            total_frames=13,
            hitstun=14,
            knockback=5,
            knockback_up=1,
            effect_type="slow"
        ),
    ]


def get_gong_dage_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """龚大哥的必杀技 - 爱国系列"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="爱国之心",
            name_cn="爱国之心",
            damage=int(180 * power_mult),
            energy_cost=100,
            hitbox_offset=(60, 0),
            hitbox_size=(150, 120),
            active_start=6,
            active_frames=12,
            total_frames=25,
            hitstun=30,
            knockback=25,
            knockback_up=10,
            effect_type="stun",
            effect_duration=1.5,
            effect_value=0
        ),
        SpecialMoveData(
            name="爱国护盾",
            name_cn="爱国护盾",
            damage=0,
            energy_cost=80,
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=0,
            active_frames=0,
            total_frames=30,
            hitstun=0,
            knockback=0,
            effect_type="shield",
            effect_duration=3.0,
            effect_value=300
        ),
    ]


def get_junshi_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """军师的必杀技 - 实验室系列"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="实验室终极射线",
            name_cn="实验室终极射线",
            damage=int(200 * power_mult),
            energy_cost=100,
            hitbox_offset=(80, 10),
            hitbox_size=(150, 60),
            active_start=5,
            active_frames=15,
            total_frames=28,
            hitstun=35,
            knockback=20,
            knockback_up=8,
            effect_type="burn",
            effect_duration=3.0,
            effect_value=30
        ),
        SpecialMoveData(
            name="实验室召唤",
            name_cn="实验室召唤",
            damage=int(150 * power_mult),
            energy_cost=80,
            hitbox_offset=(100, 0),
            hitbox_size=(200, 100),
            active_start=8,
            active_frames=10,
            total_frames=25,
            hitstun=25,
            knockback=18,
            knockback_up=6,
            projectile=True,
            projectile_speed=15,
            effect_type="burn"
        ),
    ]


def get_shenmiren_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """神秘人的必杀技 - 叛国系列"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="叛国瞬斩",
            name_cn="叛国瞬斩",
            damage=int(160 * power_mult),
            energy_cost=100,
            hitbox_offset=(0, 0),
            hitbox_size=(200, 150),
            active_start=3,
            active_frames=8,
            total_frames=20,
            hitstun=20,
            knockback=15,
            knockback_up=5,
            effect_type="teleport",
            effect_duration=0.5
        ),
        SpecialMoveData(
            name="叛国诅咒",
            name_cn="叛国诅咒",
            damage=int(120 * power_mult),
            energy_cost=80,
            hitbox_offset=(60, 20),
            hitbox_size=(100, 80),
            active_start=5,
            active_frames=10,
            total_frames=22,
            hitstun=18,
            knockback=12,
            knockback_up=3,
            effect_type="curse",
            effect_duration=5.0,
            effect_value=0.5  # 降低50%攻击
        ),
    ]


def get_zitong_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """籽桐的必杀技 - 雕系列"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="雕之领域",
            name_cn="雕之领域",
            damage=int(140 * power_mult),
            energy_cost=100,
            hitbox_offset=(50, 0),
            hitbox_size=(250, 150),
            active_start=6,
            active_frames=12,
            total_frames=26,
            hitstun=22,
            knockback=10,
            knockback_up=3,
            effect_type="slow_field",
            effect_duration=4.0,
            effect_value=0.5  # 减速50%
        ),
        SpecialMoveData(
            name="雕羽风暴",
            name_cn="雕羽风暴",
            damage=int(100 * power_mult),
            energy_cost=80,
            hitbox_offset=(80, 0),
            hitbox_size=(180, 120),
            active_start=5,
            active_frames=15,
            total_frames=30,
            hitstun=16,
            knockback=8,
            knockback_up=2,
            effect_type="multi_hit",
            effect_duration=0,
            effect_value=5  # 多次打击
        ),
    ]
