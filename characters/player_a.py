# 角色A - 力量型（红色）
from characters.character_base import CharacterData, get_default_moves, get_default_special

def create_player_a() -> CharacterData:
    stats = CharacterData.create_power_type()
    stats.name = "大力"
    stats.name_cn = "大力"
    stats.description = "力量型角色，攻击力高但速度慢，适合近身肉搏"
    return CharacterData(stats, get_default_moves(stats), get_default_special(stats))
