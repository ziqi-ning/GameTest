# 状态机模块

from typing import Callable, Dict, List, Optional, Any
from enum import Enum

class State:
    """状态基类"""

    def __init__(self, name: str):
        self.name = name
        self.timer = 0.0
        self.transitions: Dict[str, Callable[[], Optional[str]]] = {}

    def enter(self, owner: Any) -> None:
        """进入状态时调用"""
        self.timer = 0.0

    def exit(self, owner: Any) -> None:
        """离开状态时调用"""
        pass

    def update(self, owner: Any, dt: float) -> None:
        """每帧更新"""
        self.timer += dt

    def add_transition(self, target_state: str, condition: Callable[[], bool]) -> 'State':
        """添加状态转换条件"""
        self.transitions[target_state] = condition
        return self

    def check_transition(self, owner: Any) -> Optional[str]:
        """检查是否满足转换条件"""
        for target, condition in self.transitions.items():
            if condition():
                return target
        return None


class StateMachine:
    """状态机"""

    def __init__(self, initial_state: Optional[str] = None):
        self.states: Dict[str, State] = {}
        self.current_state: Optional[State] = None
        self.current_state_name: Optional[str] = None
        self.initial_state = initial_state

    def add_state(self, state: State) -> 'StateMachine':
        """添加状态"""
        self.states[state.name] = state
        if self.initial_state is None:
            self.initial_state = state.name
        return self

    def set_state(self, state_name: str) -> None:
        """设置当前状态"""
        if state_name not in self.states:
            raise ValueError(f"State '{state_name}' not found")

        if self.current_state is not None:
            self.current_state.exit(self)

        self.current_state = self.states[state_name]
        self.current_state_name = state_name
        self.current_state.enter(self)

    def update(self, owner: Any, dt: float) -> None:
        """更新状态机"""
        if self.current_state is None:
            return

        # 更新当前状态
        self.current_state.update(owner, dt)

        # 检查转换条件
        next_state = self.current_state.check_transition(owner)
        if next_state:
            self.set_state(next_state)

    def get_state_name(self) -> Optional[str]:
        """获取当前状态名"""
        return self.current_state_name

    def is_state(self, state_name: str) -> bool:
        """检查是否在指定状态"""
        return self.current_state_name == state_name

    def time_in_state(self) -> float:
        """获取当前状态持续时间"""
        if self.current_state:
            return self.current_state.timer
        return 0.0


class AnimationState(Enum):
    """动画状态"""
    IDLE = "idle"
    WALK = "walk"
    JUMP = "jump"
    FALL = "fall"
    CROUCH = "crouch"
    ATTACK_LIGHT = "light_attack"
    ATTACK_HEAVY = "heavy_attack"
    ATTACK_SPECIAL = "special_attack"
    HIT = "hit"
    BLOCK = "block"
    KO = "ko"
    LAND = "land"
