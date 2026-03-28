# 角色B - 军师（远程型，主题：实验室）
from characters.character_base import (
    CharacterData, get_junshi_moves, get_junshi_special
)


def create_player_b() -> CharacterData:
    stats = CharacterData.create_junshi()
    return CharacterData(stats, get_junshi_moves(stats), get_junshi_special(stats))
