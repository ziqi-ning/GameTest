# -*- coding: utf-8 -*-
# 真实像素精灵加载器
#
# 角色精灵来源（统一整理自开源素材）:
#   p1 = Streets of Fight Brawler Girl  - 红色 - 力量型拳击手
#   p2 = Streets of Fight Enemy Punk   - 蓝色 - 速度型敌人
#   p3 = PixelAntasy Barbarian 72x72 → 96x63 填充 - 暗紫色 - 技巧型
#   p4 = PixelAntasy Wizard 64x64  → 96x63 填充 - 绿色   - 控制型
#
# 精灵制作策略: 填满高度，水平居中，保持原始宽高比
#
# 许可证:
#   Streets of Fight: Free for any use (Luis Zuno @ansimuz)
#   PixelAntasy (LPC): CC0 Public Domain

import pygame
import os
from typing import Dict, List, Optional

# ─── 精灵尺寸配置 ────────────────────────────────────────────────────────────
SPRITE_WIDTH = 96
SPRITE_HEIGHT = 63

# ─── 动画名 → 精灵文件名映射 ──────────────────────────────────────────────────
ANIMATION_MAPPING = {
    'idle':           'idle.png',
    'walk':           'walk.png',
    'jump':           'jump.png',
    'attack_light':   'jab.png',
    'attack_heavy':   'kick.png',
    'attack_special': 'kick.png',
    'hit':            'hurt.png',
    'block':         'hurt.png',
    'ko':             'hurt.png',
    'dive_kick':      'dive_kick.png',
    'jump_kick':      'jump_kick.png',
    'special':        'kick.png',
}

# ─── 各精灵表帧数（所有角色统一）───────────────────────────────────────────────
SPRITE_SHEET_FRAME_COUNTS = {
    'idle.png':       4,
    'walk.png':      10,
    'jump.png':       4,
    'punch.png':      3,
    'jab.png':        3,
    'kick.png':       5,
    'hurt.png':       2,
    'dive_kick.png':  5,
    'jump_kick.png':  3,
}

# ─── 各角色精灵帧数例外（p2 某些动画帧数不同）─────────────────────────────────
CHAR_FRAME_OVERRIDES = {
    # p2: Enemy Punk 的 walk 只有4帧, hurt 有4帧
    'p2': {
        'walk.png':  4,
        'hurt.png':  4,
    },
}

# ─── 游戏动画帧数 ────────────────────────────────────────────────────────────
ANIMATION_FRAME_COUNTS = {
    'idle':           4,
    'walk':           6,    # 取10帧中的前6帧循环
    'jump':           4,
    'attack_light':   3,
    'attack_heavy':   5,
    'hit':            2,
    'block':          2,
    'ko':             2,
    'dive_kick':      5,
    'jump_kick':      3,
}

# ─── 角色配色（备用：调色失败时用于调试绘制）─────────────────────────────────
CHAR_COLORS = {
    0: {'primary': (220, 50, 50),   'secondary': (255, 100, 100), 'name': 'P1'},
    1: {'primary': (50, 100, 220),  'secondary': (100, 150, 255), 'name': 'P2'},
    2: {'primary': (80, 50, 180),   'secondary': (150, 100, 220), 'name': 'P3'},
    3: {'primary': (50, 160, 80),   'secondary': (100, 200, 120), 'name': 'P4'},
}


class SpriteLoader:
    """精灵加载器 - 加载并管理像素精灵"""

    def __init__(self):
        self.cache: Dict[str, Dict[str, List[pygame.Surface]]] = {}
        self.base_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            'assets', 'sprites', 'characters'
        )

    def load_character_sprites(self, char_index: int) -> Dict[str, List[pygame.Surface]]:
        """加载角色的所有精灵动画"""
        cache_key = f'char_{char_index}'
        if cache_key in self.cache:
            return self.cache[cache_key]

        char_subdir = f'p{char_index + 1}'
        char_path = os.path.join(self.base_path, char_subdir)

        if not os.path.isdir(char_path):
            print(f"[SpriteLoader] Character dir not found: {char_path}")
            self.cache[cache_key] = {}
            return {}

        animations = {}
        overrides = CHAR_FRAME_OVERRIDES.get(char_subdir, {})

        for anim_name, filename in ANIMATION_MAPPING.items():
            frame_count = overrides.get(filename,
                                       SPRITE_SHEET_FRAME_COUNTS.get(filename, 4))
            sprites = self._load_spritesheet(os.path.join(char_path, filename),
                                             frame_count)
            if sprites:
                animations[anim_name] = sprites

        self.cache[cache_key] = animations
        return animations

    def _load_spritesheet(self, filepath: str, frame_count: int) -> List[pygame.Surface]:
        """从精灵表加载所有帧"""
        if not os.path.exists(filepath):
            # 不打印warn，fallback会处理
            return []

        try:
            full_image = pygame.image.load(filepath).convert_alpha()
            frames = []

            for i in range(frame_count):
                frame = pygame.Surface((SPRITE_WIDTH, SPRITE_HEIGHT), pygame.SRCALPHA)
                frame.blit(full_image, (0, 0),
                          (i * SPRITE_WIDTH, 0, SPRITE_WIDTH, SPRITE_HEIGHT))
                frames.append(frame)

            return frames
        except Exception as e:
            print(f"[SpriteLoader] Error loading {filepath}: {e}")
            return []

    def get_sprite_frame(self, char_index: int, pose: str, frame: int,
                         facing_right: bool = True) -> Optional[pygame.Surface]:
        """获取单个精灵帧"""
        animations = self.load_character_sprites(char_index)

        if pose not in animations:
            if 'idle' in animations:
                pose = 'idle'
            else:
                return None

        frames = animations[pose]
        if not frames:
            return None

        frame_index = frame % len(frames)
        sprite = frames[frame_index].copy()

        if not facing_right:
            sprite = pygame.transform.flip(sprite, True, False)

        return sprite

    def preload_all(self):
        """预加载所有角色精灵（游戏启动时调用一次）"""
        for i in range(4):
            self.load_character_sprites(i)


# ─── 全局实例 ────────────────────────────────────────────────────────────────
sprite_loader = SpriteLoader()


def get_sprite(char_index: int, pose: str, facing_right: bool = True,
               frame: int = 0) -> Optional[pygame.Surface]:
    """获取角色精灵的便捷函数"""
    return sprite_loader.get_sprite_frame(char_index, pose, frame, facing_right)


def get_animations(char_index: int) -> Dict[str, List[pygame.Surface]]:
    """获取角色的所有动画帧"""
    return sprite_loader.load_character_sprites(char_index)
