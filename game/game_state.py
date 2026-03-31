# 游戏状态枚举

from enum import Enum, auto

class GameState(Enum):
    """游戏状态"""
    MENU = auto()
    CHARACTER_SELECT = auto()
    MAP_SELECT = auto()
    LOADING = auto()
    FIGHTING = auto()
    ROUND_START = auto()
    ROUND_END = auto()
    MATCH_END = auto()
    PAUSED = auto()

    def __str__(self):
        return self.name

class RoundState(Enum):
    """回合状态"""
    READY = auto()
    FIGHT = auto()
    KO = auto()
    TIMEOUT = auto()
    VICTORY = auto()

class MatchResult(Enum):
    """比赛结果"""
    P1_WIN = "Player 1 Wins!"
    P2_WIN = "Player 2 Wins!"
    DRAW = "Time Out - Draw!"
    NONE = "None"
