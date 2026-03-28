# 角色A - 龚大哥（力量型，主题：爱国）
from characters.character_base import (
    CharacterData, get_gong_dage_moves, get_gong_dage_special
)


def create_player_a() -> CharacterData:
    stats = CharacterData.create_gong_dage()
    return CharacterData(stats, get_gong_dage_moves(stats), get_gong_dage_special(stats))
