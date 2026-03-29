# 游戏全局配置
# DormFight - 寝室风云

SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720
FPS = 60
TITLE = "DormFight - 寝室风云"

# 地面位置
GROUND_Y = 580

# 角色尺寸
CHARACTER_WIDTH = 80
CHARACTER_HEIGHT = 160

# 初始生命值
MAX_HEALTH = 1000
MAX_SPECIAL = 100

# 倒计时
MATCH_TIME = 99  # 秒

# 重力（调低让跳跃更舒适，低力角色也能跳上中低平台）
GRAVITY = 0.5

# 颜色定义
class Colors:
    # UI 颜色
    WHITE = (255, 255, 255)
    BLACK = (0, 0, 0)
    RED = (220, 50, 50)
    BLUE = (50, 100, 220)
    YELLOW = (255, 220, 50)
    GREEN = (50, 200, 100)
    ORANGE = (255, 150, 50)
    PURPLE = (150, 50, 200)
    GRAY = (100, 100, 100)
    DARK_GRAY = (50, 50, 50)

    # UI 背景
    UI_BG = (30, 30, 40)
    UI_BORDER = (80, 80, 100)
    HEALTH_BG = (40, 40, 50)
    HEALTH_LOW = (200, 30, 30)
    HEALTH_MED = (220, 180, 30)
    HEALTH_HIGH = (50, 200, 80)
    SPECIAL_BG = (50, 50, 60)
    SPECIAL_FILLED = (100, 200, 255)

    # 角色配色
    PLAYER_A_COLOR = (220, 50, 50)      # 红色 - 力量型
    PLAYER_B_COLOR = (50, 180, 220)    # 蓝色 - 速度型
    PLAYER_C_COLOR = (50, 200, 100)     # 绿色 - 均衡型
    PLAYER_D_COLOR = (200, 100, 220)    # 紫色 - 技巧型

# 攻击判定颜色（调试用）
HITBOX_COLOR = (255, 0, 0, 100)
HURTBOX_COLOR = (0, 255, 0, 100)
