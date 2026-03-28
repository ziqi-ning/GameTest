# 角色D - 技巧型（紫色）
from characters.character_base import CharacterData, get_default_moves, get_default_special

def create_player_d() -> CharacterData:
    stats = CharacterData.create_technical_type()
    stats.name = "技巧"
    stats.name_cn = "技巧"
    stats.description = "技巧型角色，擅长中距离牵制，必杀技带投射物"
    return CharacterData(stats, get_default_moves(stats), get_default_special(stats))
