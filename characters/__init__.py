# 角色注册表

from typing import Dict, Callable
from characters.character_base import CharacterData


# 角色创建函数注册
CHARACTER_REGISTRY: Dict[int, Callable[[], CharacterData]] = {}


def register_character(char_id: int, creator: Callable[[], CharacterData]):
    """注册角色"""
    CHARACTER_REGISTRY[char_id] = creator


def get_character(char_id: int) -> CharacterData:
    """获取角色数据"""
    if char_id in CHARACTER_REGISTRY:
        return CHARACTER_REGISTRY[char_id]()
    raise ValueError(f"Unknown character ID: {char_id}")


def get_all_characters() -> Dict[int, CharacterData]:
    """获取所有角色"""
    return {char_id: creator() for char_id, creator in CHARACTER_REGISTRY.items()}


# 注册所有角色
from characters.player_a import create_player_a
from characters.player_b import create_player_b
from characters.player_c import create_player_c
from characters.player_d import create_player_d

register_character(0, create_player_a)  # 龚大哥 - 力量型
register_character(1, create_player_b)  # 军师 - 远程型
register_character(2, create_player_c)  # 神秘人 - 技巧型
register_character(3, create_player_d)  # 籽桐 - 控制型

# 角色列表（用于UI显示）
CHARACTER_LIST = [
    {"id": 0, "name": "龚大哥", "type": "力量·爱国", "color": (220, 50, 50)},
    {"id": 1, "name": "军师", "type": "远程·实验室", "color": (100, 50, 220)},
    {"id": 2, "name": "神秘人", "type": "技巧·叛国", "color": (50, 50, 50)},
    {"id": 3, "name": "籽桐", "type": "控制·雕", "color": (80, 180, 80)},
]
