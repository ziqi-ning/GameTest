# 游戏常量定义

# 角色状态
class FighterState:
    IDLE = "idle"
    WALK = "walk"
    JUMP = "jump"
    CROUCH = "crouch"
    ATTACK_LIGHT = "light_attack"
    ATTACK_HEAVY = "heavy_attack"
    ATTACK_SPECIAL = "special"
    HIT = "hit"
    BLOCK = "block"
    KO = "ko"

# 移动方向
class Direction:
    LEFT = -1
    RIGHT = 1

# 攻击类型
class AttackType:
    LIGHT = "light"
    HEAVY = "heavy"
    SPECIAL = "special"

# 游戏状态
class GameState:
    MENU = "menu"
    CHARACTER_SELECT = "character_select"
    FIGHTING = "fighting"
    ROUND_START = "round_start"
    ROUND_END = "round_end"
    MATCH_END = "match_end"
    PAUSED = "paused"

# 帧数据常量
class FrameData:
    # 轻攻击帧数据（相对值）
    LIGHT_ATTACK_START = 3
    LIGHT_ATTACK_ACTIVE = 3
    LIGHT_ATTACK_RECOVERY = 4
    LIGHT_ATTACK_TOTAL = 10

    # 重攻击帧数据
    HEAVY_ATTACK_START = 4
    HEAVY_ATTACK_ACTIVE = 4
    HEAVY_ATTACK_RECOVERY = 6
    HEAVY_ATTACK_TOTAL = 14

    # 必杀技帧数据
    SPECIAL_START = 5
    SPECIAL_ACTIVE = 10
    SPECIAL_RECOVERY = 8
    SPECIAL_TOTAL = 23

    # 跳跃帧数
    JUMP_TOTAL = 30

    # 受击帧数
    HIT_STUN = 15
    BLOCK_STUN = 10

# 伤害倍率
class DamageMultiplier:
    LIGHT = 0.8
    HEAVY = 1.5
    SPECIAL = 2.5

# 击退力度
class Knockback:
    LIGHT = 5
    HEAVY = 15
    SPECIAL = 30
    HIT_STUN = 8
