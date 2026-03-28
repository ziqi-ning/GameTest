# 角色C - 神秘人（技巧型，主题：叛国）
from characters.character_base import (
    CharacterData, get_shenmiren_moves, get_shenmiren_special
)


def create_player_c() -> CharacterData:
    stats = CharacterData.create_shenmiren()
    return CharacterData(stats, get_shenmiren_moves(stats), get_shenmiren_special(stats))
