# Weapon Assets - 武器精灵资源管理
# 资源来源：
#   - Eradication Wars Weapon Sprite Pack (CC0) - https://opengameart.org/content/eradication-wars-weapon-sprite-pack
#   - 64x64 Dagger (CC0) - https://opengameart.org/content/dagger-64x64
#   - Bald Eagle (CC0) - https://opengameart.org/content/a-bald-eagle
#   - Custom inline sprites (procedural pixel art)

import os
import pygame

ASSET_BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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
        cls._load_era_weapons()
        cls._load_legacy_weapons()
        cls._load_inline_sprites()

    @classmethod
    def _load_era_weapons(cls):
        """从 Eradication Wars 武器包加载精选武器精灵

        文件直接放在 assets/weapons/era_weapons/ 下（无子目录）：
        knife.png, pistol_gun.png, small_pistol.png, smg_flag.png,
        weapon_p_01/38/44/45/55/60.png, weapon_s_01/08.png
        """
        era_dir = _path('assets/weapons/era_weapons')
        if not os.path.exists(era_dir):
            return

        # 文件名 -> sprite key 映射
        mappings = {
            'knife.png':         'knife',
            'pistol_gun.png':    'pistol_gun',
            'small_pistol.png':  'small_pistol',
            'smg_flag.png':      'smg_flag',
            'weapon_p_01.png':   'weapon_p_01',
            'weapon_p_38.png':   'weapon_p_38',
            'weapon_p_44.png':   'weapon_p_44',
            'weapon_p_45.png':   'weapon_p_45',
            'weapon_p_55.png':   'weapon_p_55',
            'weapon_p_60.png':   'weapon_p_60',
            'weapon_s_01.png':   'weapon_s_01',
            'weapon_s_08.png':   'weapon_s_08',
        }

        for fname, key in mappings.items():
            fpath = os.path.join(era_dir, fname)
            if os.path.exists(fpath):
                try:
                    cls._cache[key] = pygame.image.load(fpath).convert_alpha()
                except Exception:
                    pass

    @classmethod
    def _load_legacy_weapons(cls):
        """加载旧的武器精灵（向后兼容）"""
        # 激光枪：从 Arsenal spritesheet 切帧 (420x220, 5列×4行=20帧, 每帧84x55)
        arsenal_path = _path('assets/weapons/eradication_wars/Eradication Wars Weapon Sprite Pack/Eradication Wars Full Arsenal.png')
        dagger_path  = _path('assets/weapons/dagger_gold.png')
        eagle_path   = _path('assets/weapons/eagle_flap.png')

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
            cls._cache['laser_gun'] = frames[0]

        if os.path.exists(dagger_path):
            cls._cache['dagger'] = pygame.image.load(dagger_path).convert_alpha()

        # 老鹰：287x21 spritesheet，7帧，每帧 41x21
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
    def _load_inline_sprites(cls):
        """加载内联像素艺术武器精灵（纯Python生成，作为备用）"""
        # 如果某个sprite加载失败，提供内联的备用版本
        # 这里预分配key，但实际精灵由下层代码在需要时生成
        cls._cache['_inline_fist'] = cls._make_fist_sprite()
        cls._cache['_inline_flag'] = cls._make_flag_sprite()
        cls._cache['_inline_nunchaku'] = cls._make_nunchaku_sprite()
        cls._cache['_inline_shuriken'] = cls._make_shuriken_sprite()

    @classmethod
    def _make_fist_sprite(cls) -> pygame.Surface:
        """生成拳头像素艺术精灵"""
        surf = pygame.Surface((20, 16), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        # 拳头形状 (肤色)
        fist = [
            (3,6,12,8,(220,180,140)),   # 主体
            (5,4,10,4,(240,195,160)),   # 顶部高光
            (2,8,4,4,(200,155,120)),    # 阴影
        ]
        for x,y,w,h,c in fist:
            pygame.draw.rect(surf, c, (x,y,w,h))
        return surf

    @classmethod
    def _make_flag_sprite(cls) -> pygame.Surface:
        """生成红旗像素艺术精灵"""
        surf = pygame.Surface((36, 24), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        # 旗杆（金色）
        pygame.draw.line(surf, (210,170,50), (2,0), (2,24), 3)
        # 红旗
        pygame.draw.rect(surf, (220,30,30), (4,2,28,16))
        pygame.draw.rect(surf, (160,15,15), (4,2,28,16), 1)
        # 五角星（简化）
        star_cx, star_cy = 14, 10
        star_r = 5
        pts = []
        for i in range(5):
            oa = 90 + i * 72
            ia = 90 + i * 72 + 36
            pts.append((star_cx + int(6*math.cos(math.radians(oa))), star_cy - int(6*math.sin(math.radians(oa)))))
            pts.append((star_cx + int(2*math.cos(math.radians(ia))), star_cy - int(2*math.sin(math.radians(ia)))))
        if len(pts) >= 10:
            pygame.draw.polygon(surf, (255,220,0), pts)
        return surf

    @classmethod
    def _make_nunchaku_sprite(cls) -> pygame.Surface:
        """生成双截棍像素艺术精灵"""
        surf = pygame.Surface((28, 12), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        # 两截木棍
        pygame.draw.rect(surf, (180,140,80), (2,2,10,8), border_radius=2)
        pygame.draw.rect(surf, (180,140,80), (16,2,10,8), border_radius=2)
        # 连接链
        pygame.draw.line(surf, (160,160,170), (12,6), (16,6), 2)
        return surf

    @classmethod
    def _make_shuriken_sprite(cls) -> pygame.Surface:
        """生成手里剑像素艺术精灵"""
        surf = pygame.Surface((24, 24), pygame.SRCALPHA)
        surf.fill((0, 0, 0, 0))
        cx, cy = 12, 12
        r = 9
        pts = [(cx, cy-r), (cx+3,cy-3), (cx+r,cy), (cx+3,cy+3),
               (cx,cy+r), (cx-3,cy+3), (cx-r,cy), (cx-3,cy-3)]
        pygame.draw.polygon(surf, (180,180,190), pts)
        pygame.draw.circle(surf, (80,80,90), (cx,cy), 3)
        return surf

    @classmethod
    def clear(cls):
        """清空缓存（游戏重置时调用）"""
        cls._cache.clear()
        cls._loaded = False


# math import for _make_flag_sprite
import math
