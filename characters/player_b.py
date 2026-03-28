# 角色B - 速度型（蓝色）
from characters.character_base import CharacterData, get_default_moves, get_default_special

def create_player_b() -> CharacterData:
    stats = CharacterData.create_speed_type()
    stats.name = "快手"
    stats.name_cn = "快手"
    stats.description = "速度型角色，攻速快但伤害低，适合打连招"
    return CharacterData(stats, get_default_moves(stats), get_default_special(stats))
