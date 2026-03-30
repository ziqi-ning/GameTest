# 动画控制器

import pygame
from typing import Dict, Callable, Optional, List
from game.state_machine import AnimationState

class Animator:
    """动画控制器，管理角色动画状态和过渡"""

    def __init__(self, owner_id: int = 0):
        self.owner_id = owner_id
        self.current_state = AnimationState.IDLE
        self.frame = 0
        self.frame_time = 0.0
        self.fps = 12
        self.animations: Dict[AnimationState, Dict] = {}

        # 动画完成回调
        self.on_complete: Optional[Callable] = None
        self.on_frame_change: Optional[Callable[[int], None]] = None

        self._setup_default_animations()

    def _setup_default_animations(self):
        """设置默认动画配置"""
        # 每个状态的帧数配置 (与精灵帧数匹配)
        frame_counts = {
            AnimationState.IDLE: 4,
            AnimationState.WALK: 6,
            AnimationState.JUMP: 4,
            AnimationState.FALL: 4,
            AnimationState.CROUCH: 1,
            AnimationState.ATTACK_LIGHT: 3,
            AnimationState.ATTACK_HEAVY: 5,
            AnimationState.ATTACK_SPECIAL: 5,
            AnimationState.HIT: 2,
            AnimationState.BLOCK: 2,
            AnimationState.KO: 2,
            AnimationState.LAND: 4,
        }

        for state, count in frame_counts.items():
            self.animations[state] = {
                'frame_count': count,
                'fps': 12,  # 12 FPS
                'loop': state in [AnimationState.IDLE, AnimationState.WALK]
            }

    def set_state(self, new_state: AnimationState, force: bool = False) -> bool:
        """设置动画状态"""
        if new_state == self.current_state and not force:
            return False

        # 检查是否可以中断
        if not self.can_interrupt(self.current_state, new_state):
            return False

        self.current_state = new_state
        self.frame = 0
        self.frame_time = 0.0
        return True

    def can_interrupt(self, from_state: AnimationState, to_state: AnimationState) -> bool:
        """检查是否可以中断当前动画"""
        # 攻击动画不能被普通移动中断
        attack_states = [
            AnimationState.ATTACK_LIGHT,
            AnimationState.ATTACK_HEAVY,
            AnimationState.ATTACK_SPECIAL
        ]

        if from_state in attack_states:
            # 攻击动画后期可以被打断
            progress = self.frame / max(1, self.get_frame_count(from_state) - 1)
            return progress >= 0.8

        # HIT状态动画播放完可以被中断
        if from_state == AnimationState.HIT:
            progress = self.frame / max(1, self.get_frame_count(from_state) - 1)
            return progress >= 0.9

        # KO状态不能被中断
        if from_state == AnimationState.KO:
            return False

        return True

    def get_frame_count(self, state: AnimationState = None) -> int:
        """获取指定状态的帧数"""
        if state is None:
            state = self.current_state

        if state in self.animations:
            return self.animations[state]['frame_count']
        return 1

    def get_current_frame(self) -> int:
        """获取当前帧"""
        return self.frame

    def is_animation_complete(self) -> bool:
        """检查当前动画是否播放完成"""
        return self.frame >= self.get_frame_count()

    def update(self, dt: float) -> bool:
        """更新动画，返回是否切换了动画帧"""
        frame_changed = False

        if self.current_state in self.animations:
            anim_data = self.animations[self.current_state]
            frame_duration = 1.0 / anim_data['fps']

            self.frame_time += dt
            if self.frame_time >= frame_duration:
                self.frame_time -= frame_duration
                self.frame += 1
                frame_changed = True

                # 检查循环
                if self.frame >= self.get_frame_count():
                    if anim_data['loop']:
                        self.frame = 0
                    else:
                        # 动画播放完成
                        self.frame = self.get_frame_count() - 1
                        if self.on_complete:
                            self.on_complete()

        return frame_changed

    def get_pose_name(self) -> str:
        """获取当前动画对应的精灵姿态名"""
        pose_mapping = {
            AnimationState.IDLE: 'idle',
            AnimationState.WALK: 'walk',
            AnimationState.JUMP: 'jump',
            AnimationState.FALL: 'jump',
            AnimationState.CROUCH: 'idle',
            AnimationState.ATTACK_LIGHT: 'attack_light',
            AnimationState.ATTACK_HEAVY: 'attack_heavy',
            AnimationState.ATTACK_SPECIAL: 'attack_special',
            AnimationState.HIT: 'hit',
            AnimationState.BLOCK: 'block',
            AnimationState.KO: 'ko',
            AnimationState.LAND: 'idle',
        }
        return pose_mapping.get(self.current_state, 'idle')

    def reset(self):
        """重置动画"""
        self.current_state = AnimationState.IDLE
        self.frame = 0
        self.frame_time = 0.0
