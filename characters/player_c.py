# 角色C - 均衡型（绿色）
from characters.character_base import CharacterData, get_default_moves, get_default_special

def create_player_c() -> CharacterData:
    stats = CharacterData.create_balanced_type()
    stats.name = "全能"
    stats.name_cn = "全能"
    stats.description = "均衡型角色，各项能力平衡，上手容易"
    return CharacterData(stats, get_default_moves(stats), get_default_special(stats))
