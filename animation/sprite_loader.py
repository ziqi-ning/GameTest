# 真实像素精灵加载器

import pygame
import os
from typing import Dict, List, Optional, Tuple

# 精灵尺寸配置
SPRITE_WIDTH = 96
SPRITE_HEIGHT = 63

# 动作名称映射: 游戏动作 -> 精灵文件名
ANIMATION_MAPPING = {
    'idle': 'idle.png',
    'walk': 'walk.png',
    'jump': 'jump.png',
    'attack_light': 'jab.png',
    'attack_heavy': 'kick.png',
    'hit': 'hurt.png',
    'block': 'hurt.png',  # 用hurt代替，需要新建
    'ko': 'hurt.png',  # 用hurt代替，需要新建
    'dive_kick': 'dive_kick.png',
    'jump_kick': 'jump_kick.png',
}

# 每个精灵表的总帧数
SPRITE_SHEET_FRAME_COUNTS = {
    'idle.png': 4,
    'walk.png': 10,
    'jump.png': 4,
    'punch.png': 3,
    'jab.png': 3,
    'kick.png': 5,
    'hurt.png': 2,
    'dive_kick.png': 5,
    'jump_kick.png': 3,
}

# 每个动作使用的帧数 (根据游戏需要)
ANIMATION_FRAME_COUNTS = {
    'idle': 4,
    'walk': 6,
    'jump': 4,
    'attack_light': 3,
    'attack_heavy': 5,
    'hit': 2,
    'block': 2,
    'ko': 2,
    'dive_kick': 5,
    'jump_kick': 3,
}


class SpriteLoader:
    """精灵加载器 - 加载并管理像素精灵"""

    def __init__(self):
        self.cache: Dict[str, List[pygame.Surface]] = {}
        self.base_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'assets', 'sprites', 'characters'
        )

    def load_character_sprites(self, char_index: int) -> Dict[str, List[pygame.Surface]]:
        """加载角色的所有精灵动画"""
        cache_key = f'char_{char_index}'
        if cache_key in self.cache:
            return self.cache[cache_key]

        char_path = os.path.join(self.base_path, f'p{char_index + 1}')
        animations = {}

        for anim_name, filename in ANIMATION_MAPPING.items():
            sprites = self._load_spritesheet(os.path.join(char_path, filename))
            if sprites:
                animations[anim_name] = sprites

        self.cache[cache_key] = animations
        return animations

    def _load_spritesheet(self, filepath: str) -> List[pygame.Surface]:
        """从精灵表加载所有帧"""
        if not os.path.exists(filepath):
            print(f"Sprite not found: {filepath}")
            return []

        try:
            full_image = pygame.image.load(filepath).convert_alpha()
            frame_count = SPRITE_SHEET_FRAME_COUNTS.get(
                os.path.basename(filepath), 4
            )
            frames = []

            for i in range(frame_count):
                frame = pygame.Surface((SPRITE_WIDTH, SPRITE_HEIGHT), pygame.SRCALPHA)
                frame.blit(full_image, (0, 0), (i * SPRITE_WIDTH, 0, SPRITE_WIDTH, SPRITE_HEIGHT))
                frames.append(frame)

            return frames
        except Exception as e:
            print(f"Error loading sprite {filepath}: {e}")
            return []

    def get_sprite_frame(self, char_index: int, pose: str, frame: int,
                         facing_right: bool = True) -> Optional[pygame.Surface]:
        """获取单个精灵帧"""
        animations = self.load_character_sprites(char_index)

        if pose not in animations:
            # 尝试使用默认姿态
            if 'idle' in animations:
                pose = 'idle'
            else:
                return None

        frames = animations[pose]
        if not frames:
            return None

        # 循环帧
        frame_index = frame % len(frames)
        sprite = frames[frame_index].copy()

        # 如果需要翻转
        if not facing_right:
            sprite = pygame.transform.flip(sprite, True, False)

        return sprite


# 全局实例
sprite_loader = SpriteLoader()


def get_sprite(char_index: int, pose: str, facing_right: bool = True,
               frame: int = 0) -> pygame.Surface:
    """获取角色精灵的便捷函数"""
    return sprite_loader.get_sprite_frame(char_index, pose, frame, facing_right)


def get_animations(char_index: int) -> Dict[str, List[pygame.Surface]]:
    """获取角色的所有动画帧"""
    return sprite_loader.load_character_sprites(char_index)
