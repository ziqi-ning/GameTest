# 角色数据基类

from dataclasses import dataclass
from typing import List, Tuple, Optional
import pygame


@dataclass
class CharacterStats:
    """角色属性"""
    name: str
    name_cn: str  # 中文名
    description: str  # 角色描述
    weapon_type: str = "fist"  # 武器类型: fist, flag, laser, dagger, eagle, pistol, rifle, nunchaku, shuriken
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
    is_ranged: bool = False  # 是否为远程攻击
    projectile_speed: float = 8.0  # 投射物速度（像素/帧）
    mana_cost: int = 0  # 远程攻击消耗蓝量


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
    effect_duration: float = 0.0  # 效果持续时间（实体存活时间）
    animation_lock: float = 0.0   # 玩家动画锁定时间（=0则用effect_duration）
    effect_value: float = 0.0  # 效果数值


class CharacterData:
    """角色数据类"""

    def __init__(self, stats: CharacterStats, moves: List[MoveData], special: List[SpecialMoveData]):
        self.stats = stats
        self.moves = moves
        self.special = special

    @staticmethod
    def create_gong_dage() -> CharacterStats:
        """龚大哥 - 力量型拳击手，拳套，血量厚速度慢"""
        return CharacterStats(
            name="GongDaGe",
            name_cn="龚大哥",
            description="力量型拳击手，血量深厚但速度慢，技能围绕「爱国」展开",
            weapon_type="fist",
            max_health=1500,
            walk_speed=2.5,
            jump_force=13.0,  # 力量型角色，能跳上第一阶平台（约169px高度）
            attack_power=120,
            defense=0.25,
            special_cost=80,
            color=(220, 50, 50),        # 红色主题 - Boxer CC0 拳击手
            secondary_color=(255, 100, 100)
        )

    @staticmethod
    def create_junshi() -> CharacterStats:
        """军师 - 远程型研究员，手枪攻击，波动伤害"""
        return CharacterStats(
            name="JunShi",
            name_cn="军师",
            description="远程型研究员，擅长手枪射击和波动攻击，技能围绕「实验室」展开",
            weapon_type="pistol",
            max_health=900,
            walk_speed=5.0,
            jump_force=14.0,
            attack_power=100,
            defense=0.10,
            special_cost=80,
            color=(150, 100, 60),       # 棕色主题 - LPC Professor 研究员
            secondary_color=(200, 150, 120)
        )

    @staticmethod
    def create_shenmiren() -> CharacterStats:
        """神秘人 - 技巧型忍者，手里剑，被动25%闪避"""
        return CharacterStats(
            name="ShenMiRen",
            name_cn="神秘人",
            description="技巧型忍者，擅长手里剑攻击，被动25%几率闪避所有伤害",
            weapon_type="shuriken",
            max_health=1000,
            walk_speed=6.0,
            jump_force=16.0,
            attack_power=85,
            defense=0.12,
            special_cost=80,
            color=(80, 40, 120),         # 暗紫色 - LPC 忍者
            secondary_color=(255, 150, 100),
            dodge_chance=0.25  # 25% 闪避几率
        )

    @staticmethod
    def create_zitong() -> CharacterStats:
        """籽桐 - 控制型探险家，白头海雕，减速控制"""
        return CharacterStats(
            name="ZiTong",
            name_cn="籽桐",
            description="控制型探险家，擅长白头海雕攻击和减速控制，技能围绕「雕」展开",
            weapon_type="eagle",
            max_health=950,
            walk_speed=5.5,
            jump_force=15.0,
            attack_power=75,
            defense=0.15,
            special_cost=80,
            color=(50, 180, 80),         # 绿色 - Kenney Adventurer 探险家
            secondary_color=(100, 220, 130)
        )


def get_gong_dage_moves(stats: CharacterStats) -> List[MoveData]:
    """龚大哥的普通攻击（轻拳近战 / 重拳远程红旗）"""
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
            name="爱国飞旗",
            damage=int(30 * power_mult),
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=5,
            active_frames=0,
            recovery_frames=10,
            total_frames=20,
            hitstun=18,
            knockback=10,
            knockback_up=2,
            effect_type="none",
            is_ranged=True,
            projectile_speed=6.0,
            mana_cost=16
        ),
    ]


def get_junshi_moves(stats: CharacterStats) -> List[MoveData]:
    """军师的普通攻击（轻拳近战 / 重拳远程激光枪）"""
    power_mult = stats.attack_power / 80.0
    return [
        MoveData(
            name="实验室冲击波",
            damage=int(35 * power_mult),
            hitbox_offset=(55, 25),
            hitbox_size=(65, 45),
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
            name="激光枪射击",
            damage=int(31 * power_mult),
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=4,
            active_frames=0,
            recovery_frames=10,
            total_frames=18,
            hitstun=14,
            knockback=8,
            knockback_up=1,
            effect_type="burn",
            is_ranged=True,
            projectile_speed=14.0,
            mana_cost=16
        ),
    ]


def get_shenmiren_moves(stats: CharacterStats) -> List[MoveData]:
    """神秘人的普通攻击（轻拳近战 / 重拳远程星条旗）"""
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
            name="叛国飞旗",
            damage=int(22 * power_mult),
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=4,
            active_frames=0,
            recovery_frames=8,
            total_frames=16,
            hitstun=12,
            knockback=6,
            knockback_up=1,
            effect_type="poison",
            is_ranged=True,
            projectile_speed=9.0,
            mana_cost=16
        ),
    ]


def get_zitong_moves(stats: CharacterStats) -> List[MoveData]:
    """籽桐的普通攻击（轻拳近战 / 重拳远程老鹰）"""
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
            name="鹰击长空",
            damage=int(18 * power_mult),
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=5,
            active_frames=0,
            recovery_frames=10,
            total_frames=20,
            hitstun=16,
            knockback=7,
            knockback_up=3,
            effect_type="slow",
            is_ranged=True,
            projectile_speed=11.0,
            mana_cost=16
        ),
    ]


def get_gong_dage_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """龚大哥的必杀技 - 爱国系列
    L键(0)：爱国之心 - 全屏五星红旗范围伤害，中额伤害
    I键(1)：爱国护盾 - 增益：生成护盾"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="爱国之心",
            name_cn="爱国之心",
            damage=int(200 * power_mult),  # 中额伤害
            energy_cost=80,
            hitbox_offset=(640, 0),    # 全屏宽度偏移
            hitbox_size=(1280, 720),   # 全屏范围
            active_start=0,
            active_frames=999,         # 持续整局
            total_frames=999,
            hitstun=25,
            knockback=15,
            knockback_up=5,
            effect_type="national_flag",  # 全屏国旗
            effect_duration=3.0,
            effect_value=200,  # damage value
            animation_lock=1.0,  # 玩家动画锁定1秒
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
            effect_value=300  # 护盾值
        ),
    ]


def get_junshi_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """军师的必杀技 - 实验室系列
    L键(0)：高能激光 - 蓝色高能激光对同一行造成巨额伤害
    I键(1)：实验室强化 - 增益：5连发激光枪，持续10秒"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="高能激光",
            name_cn="高能激光",
            damage=int(400 * power_mult),  # 巨额伤害
            energy_cost=80,
            hitbox_offset=(640, 0),   # 半屏宽度偏移
            hitbox_size=(640, 220),  # 激光宽度范围
            active_start=0,
            active_frames=999,
            total_frames=999,
            hitstun=40,
            knockback=30,
            knockback_up=15,
            effect_type="laser_beam",  # 激光束
            effect_duration=2.5,
            effect_value=400  # damage value
        ),
        SpecialMoveData(
            name="实验室强化",
            name_cn="实验室强化",
            damage=0,
            energy_cost=80,
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=0,
            active_frames=0,
            total_frames=20,
            hitstun=0,
            knockback=0,
            effect_type="multi_shot",
            effect_duration=7.0,  # 7秒
            effect_value=5  # 5连发
        ),
    ]


def get_shenmiren_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """神秘人的必杀技 - 叛国系列
    L键(0)：黑影瞬斩 - 分裂黑影瞬移到敌人身后持续伤害，可召唤无上限个
    I键(1)：叛国血脉 - 增益：吸血效果，攻击伤害的1/3回复生命，持续10秒"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="黑影瞬斩",
            name_cn="黑影瞬斩",
            damage=int(160 * power_mult),
            energy_cost=80,
            hitbox_offset=(0, 0),
            hitbox_size=(200, 150),  # 黑影判定范围
            active_start=0,
            active_frames=60,
            total_frames=60,
            hitstun=20,
            knockback=15,
            knockback_up=5,
            effect_type="shadow_clone",  # 黑影瞬移
            effect_duration=8.0,  # 黑影存在8秒
            animation_lock=1.0     # 玩家动画锁定1秒
        ),
        SpecialMoveData(
            name="叛国血脉",
            name_cn="叛国血脉",
            damage=0,
            energy_cost=80,
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=0,
            active_frames=0,
            total_frames=20,
            hitstun=0,
            knockback=0,
            effect_type="lifesteal",
            effect_duration=10.0,
            animation_lock=1.0,  # 玩家锁定1秒
            effect_value=0.33  # 33%吸血
        ),
    ]


def get_zitong_special(stats: CharacterStats) -> List[SpecialMoveData]:
    """籽桐的必杀技 - 雕系列
    L键(0)：雕与蛋 - 召唤大公鸡和鸡蛋，把敌人吸入鸡蛋内持续啄击5秒
    I键(1)：冰雕凝视 - 减益：强制冻结敌人2.5秒（原5秒削弱）"""
    power_mult = stats.attack_power / 80.0
    return [
        SpecialMoveData(
            name="雕与蛋",
            name_cn="雕与蛋",
            damage=int(100 * power_mult),  # 每0.5秒30伤害
            energy_cost=80,
            hitbox_offset=(0, 0),
            hitbox_size=(150, 150),  # 鸡蛋吸入范围
            active_start=0,
            active_frames=999,
            total_frames=999,
            hitstun=16,
            knockback=8,
            knockback_up=2,
            effect_type="chicken_egg",  # 鸡+鸡蛋
            effect_duration=5.0,  # 持续5秒
            animation_lock=1.5     # 玩家锁定1.5秒
        ),
        SpecialMoveData(
            name="冰雕凝视",
            name_cn="冰雕凝视",
            damage=0,
            energy_cost=80,
            hitbox_offset=(0, 0),
            hitbox_size=(0, 0),
            active_start=0,
            active_frames=0,
            total_frames=25,
            hitstun=0,
            knockback=0,
            effect_type="freeze",
            effect_duration=2.5,  # 削弱为2.5秒（原5秒）
            effect_value=0  # 无伤害，只冻结
        ),
    ]
