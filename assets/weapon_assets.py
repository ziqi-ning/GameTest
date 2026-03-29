# Weapon Assets - 武器精灵资源管理
# 资源来源：
#   - Eradication Wars Weapon Sprite Pack (CC0) - https://opengameart.org/content/eradication-wars-weapon-sprite-pack
#   - 64x64 Dagger (CC0) - https://opengameart.org/content/dagger-64x64
#   - Bald Eagle (CC0) - https://opengameart.org/content/a-bald-eagle

import os
import pygame

ASSET_BASE = os.path.dirname(os.path.abspath(__file__))


def _path(rel: str) -> str:
    return os.path.join(ASSET_BASE, rel)


class WeaponAssets:
    """所有武器精灵的缓存和访问接口（懒加载）"""

    _cache: dict = {}
    _loaded: bool = False

    @classmethod
    def get(cls, key: str) -> pygame.Surface:
        """获取武器精灵，无则返回空surface"""
        cls._ensure_loaded()
        return cls._cache.get(key, pygame.Surface((1, 1), pygame.SRCALPHA))

    @classmethod
    def get_frame(cls, key: str, frame_idx: int) -> pygame.Surface:
        """获取武器精灵的某一帧"""
        cls._ensure_loaded()
        frames = cls._cache.get(key + '_frames', [])
        if not frames:
            return pygame.Surface((1, 1), pygame.SRCALPHA)
        return frames[frame_idx % len(frames)]

    @classmethod
    def _ensure_loaded(cls):
        """懒加载：首次访问时加载（需要 pygame.display 已初始化）"""
        if cls._loaded:
            return
        cls._loaded = True
        cls._load_all()

    @classmethod
    def _load_all(cls):
        """加载所有武器精灵"""
        arsenal_path = _path('weapons/eradication_wars/Eradication Wars Weapon Sprite Pack/Eradication Wars Full Arsenal.png')
        dagger_path = _path('weapons/dagger_gold.png')
        eagle_path = _path('weapons/eagle_flap.png')

        # ── 激光枪：从 Arsenal spritesheet 切帧 ───────────────────────
        # 420x220，5列×4行 = 20帧，每帧 84x55
        if os.path.exists(arsenal_path):
            sheet = pygame.image.load(arsenal_path).convert_alpha()
            sheet_w, sheet_h = sheet.get_size()
            cols, rows = 5, 4
            fw, fh = sheet_w // cols, sheet_h // rows
            frames = []
            for r in range(rows):
                for c in range(cols):
                    surf = pygame.Surface((fw, fh), pygame.SRCALPHA)
                    surf.blit(sheet, (0, 0), (c * fw, r * fh, fw, fh))
                    frames.append(surf)
            cls._cache['laser_gun_frames'] = frames
            # 主激光枪帧（第0帧）
            cls._cache['laser_gun'] = frames[0]

        # ── 匕首：64x64 单帧 ─────────────────────────────────────────
        if os.path.exists(dagger_path):
            cls._cache['dagger'] = pygame.image.load(dagger_path).convert_alpha()

        # ── 老鹰：287x21 spritesheet，7帧，每帧 41x21 ─────────────────
        if os.path.exists(eagle_path):
            sheet = pygame.image.load(eagle_path).convert_alpha()
            sheet_w, sheet_h = sheet.get_size()
            cols_e = 7
            fw_e = sheet_w // cols_e
            frames = []
            for c in range(cols_e):
                surf = pygame.Surface((fw_e, sheet_h), pygame.SRCALPHA)
                surf.blit(sheet, (0, 0), (c * fw_e, 0, fw_e, sheet_h))
                frames.append(surf)
            cls._cache['eagle_frames'] = frames
            cls._cache['eagle'] = frames[0]

    @classmethod
    def clear(cls):
        """清空缓存（游戏重置时调用）"""
        cls._cache.clear()
        cls._loaded = False
