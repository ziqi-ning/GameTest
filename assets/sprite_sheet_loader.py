# Sprite Sheet Loader - 精灵表加载器
# 支持 Aseprite JSON 格式（由 Starling/Python-aseprite-json-util 生成）
# 同时支持手动 grid 格式（简单等大帧排列）
# 注意：所有图片加载使用懒加载，在首次访问帧时才加载，避免 pygame.display 未初始化错误
import json
import os
import pygame

ASSET_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class SpriteSheet:
    """精灵表加载器，支持 Aseprite JSON 格式和 Grid 格式（懒加载）"""

    def __init__(self, image_path: str, json_path: str = None):
        self.base_path = ASSET_BASE
        self.image_path = image_path
        self.json_path = json_path
        self.frames: list[dict] = []
        self.meta: dict = {}
        self.sheet: pygame.Surface | None = None
        self._loaded: bool = False

    def _ensure_loaded(self):
        """懒加载：首次访问时加载"""
        if self._loaded:
            return
        self._loaded = True

        if not os.path.isabs(self.image_path):
            self.image_path = os.path.join(self.base_path, self.image_path)
        if self.json_path and not os.path.isabs(self.json_path):
            self.json_path = os.path.join(self.base_path, self.json_path)

        self.sheet = pygame.image.load(self.image_path).convert_alpha()
        if self.json_path and os.path.exists(self.json_path):
            self._load_aseprite_json()
        else:
            self._load_grid_fallback()

    def _load_aseprite_json(self):
        """加载 Aseprite JSON 格式"""
        with open(self.json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.meta = data.get('meta', {})
        frame_data = data.get('frames', {})

        for name, info in frame_data.items():
            frame_rect = info['frame']
            self.frames.append({
                'name': name,
                'x': frame_rect['x'],
                'y': frame_rect['y'],
                'w': frame_rect['w'],
                'h': frame_rect['h'],
                'duration': info.get('duration', 100),
                'rotated': info.get('rotated', False),
                'trimmed': info.get('trimmed', False),
            })

    def _load_grid_fallback(self):
        """Grid 格式：从文件名推断帧尺寸，横向等分排列"""
        w, h = self.sheet.get_size()
        frame_w, frame_h = self._guess_frame_size(w, h)
        cols = w // frame_w
        rows = h // frame_h
        for row in range(rows):
            for col in range(cols):
                self.frames.append({
                    'name': f'grid_{row}_{col}',
                    'x': col * frame_w,
                    'y': row * frame_h,
                    'w': frame_w,
                    'h': frame_h,
                    'duration': 100,
                    'rotated': False,
                    'trimmed': False,
                })

    def _guess_frame_size(self, sheet_w: int, sheet_h: int) -> tuple:
        """猜测帧尺寸"""
        candidates = [
            (sheet_w, sheet_h),
            (sheet_w // 2, sheet_h), (sheet_w // 3, sheet_h),
            (sheet_w // 4, sheet_h), (sheet_w // 5, sheet_h),
            (sheet_w // 6, sheet_h), (sheet_w // 7, sheet_h),
            (sheet_w // 8, sheet_h), (sheet_w // 10, sheet_h),
        ]
        for fw, fh in candidates:
            if fw > 0 and fh > 0:
                return fw, fh
        return 64, 64

    def get_frame(self, index: int) -> pygame.Surface:
        """获取指定帧"""
        self._ensure_loaded()
        if not self.frames or index < 0 or index >= len(self.frames):
            return pygame.Surface((1, 1), pygame.SRCALPHA)

        f = self.frames[index]
        return self.sheet.subsurface((f['x'], f['y'], f['w'], f['h']))

    def get_frame_info(self, index: int) -> dict:
        self._ensure_loaded()
        return self.frames[index] if 0 <= index < len(self.frames) else {}

    def frame_count(self) -> int:
        self._ensure_loaded()
        return len(self.frames)

    def get_frame_duration(self, index: int) -> float:
        """获取帧持续时间（秒）"""
        self._ensure_loaded()
        if 0 <= index < len(self.frames):
            return self.frames[index]['duration'] / 1000.0
        return 0.1

    def get_animation_frames(self, tag_name: str) -> list:
        """按 frameTags 获取动画帧"""
        self._ensure_loaded()
        frame_tags = self.meta.get('frameTags', [])
        for tag in frame_tags:
            if tag['name'] == tag_name:
                start = tag['from']
                end = tag['to'] + 1
                return list(range(start, min(end, len(self.frames))))
        return list(range(len(self.frames)))


class SpriteSheetCache:
    """精灵表缓存，避免重复加载"""
    _cache: dict[str, SpriteSheet] = {}

    @classmethod
    def get(cls, image_path: str, json_path: str = None) -> SpriteSheet:
        key = image_path + (json_path or '')
        if key not in cls._cache:
            cls._cache[key] = SpriteSheet(image_path, json_path)
        return cls._cache[key]

    @classmethod
    def clear(cls):
        cls._cache.clear()
