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

register_character(0, create_player_a)  # 角色A - 力量型
register_character(1, create_player_b)  # 角色B - 速度型
register_character(2, create_player_c)  # 角色C - 均衡型
register_character(3, create_player_d)  # 角色D - 技巧型

# 角色列表（用于UI显示）
CHARACTER_LIST = [
    {"id": 0, "name": "大力", "type": "力量型", "color": (220, 50, 50)},
    {"id": 1, "name": "快手", "type": "速度型", "color": (50, 180, 220)},
    {"id": 2, "name": "全能", "type": "均衡型", "color": (50, 200, 100)},
    {"id": 3, "name": "技巧", "type": "技巧型", "color": (200, 100, 220)},
]
