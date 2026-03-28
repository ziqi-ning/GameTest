# 角色D - 籽桐（控制型，主题：雕）
from characters.character_base import (
    CharacterData, get_zitong_moves, get_zitong_special
)


def create_player_d() -> CharacterData:
    stats = CharacterData.create_zitong()
    return CharacterData(stats, get_zitong_moves(stats), get_zitong_special(stats))
