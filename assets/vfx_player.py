# VFX Sprite Animation Player - VFX精灵动画播放器
# 播放来自精灵表的帧动画（命中火花、斩击、爆炸等）
import pygame
import math
import random
from assets.sprite_sheet_loader import SpriteSheet, SpriteSheetCache


class VFXAnimation:
    """单次VFX动画实例"""

    def __init__(self, frames: list[pygame.Surface], durations: list[float],
                 x: float, y: float, scale: float = 1.0, angle: float = 0.0,
                 flip_x: bool = False, flip_y: bool = False, loop: bool = False,
                 on_complete=None):
        self.frames = frames
        self.durations = durations
        self.x = x
        self.y = y
        self.scale = scale
        self.angle = angle
        self.flip_x = flip_x
        self.flip_y = flip_y
        self.loop = loop
        self.on_complete = on_complete

        self.current_frame = 0
        self.elapsed = 0.0
        self.active = True

    def update(self, dt: float):
        if not self.active:
            return

        self.elapsed += dt
        while self.elapsed >= self.durations[self.current_frame]:
            self.elapsed -= self.durations[self.current_frame]
            self.current_frame += 1

            if self.current_frame >= len(self.frames):
                if self.loop:
                    self.current_frame = 0
                else:
                    self.active = False
                    if self.on_complete:
                        self.on_complete()
                    return

    def draw(self, surface: pygame.Surface):
        if not self.active or self.current_frame >= len(self.frames):
            return

        frame = self.frames[self.current_frame]
        w = int(frame.get_width() * self.scale)
        h = int(frame.get_height() * self.scale)
        if w <= 0 or h <= 0:
            return

        frame_scaled = pygame.transform.scale(frame, (w, h))
        if self.flip_x or self.flip_y:
            frame_scaled = pygame.transform.flip(frame_scaled, self.flip_x, self.flip_y)
        if abs(self.angle) > 0.1:
            frame_scaled = pygame.transform.rotate(frame_scaled, self.angle)

        rect = frame_scaled.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(frame_scaled, rect)


class VFXPlayer:
    """VFX动画管理器 — 管理场景中所有VFX动画"""

    def __init__(self):
        self.animations: list[VFXAnimation] = []
        # 预加载的精灵表缓存
        self._sheets: dict[str, SpriteSheet] = {}

    def _load_sheet(self, image_path: str, json_path: str = None) -> SpriteSheet:
        key = image_path + (json_path or '')
        if key not in self._sheets:
            self._sheets[key] = SpriteSheetCache.get(image_path, json_path)
        return self._sheets[key]

    # ── 命中火花 (Hit Sparks) ──────────────────────────────────────────────

    def spawn_hit_spark(self, x: float, y: float, scale: float = 1.5,
                        angle: float = 0.0, flip_x: bool = False,
                        sheet_key: str = None):
        """生成命中火花动画
        sheet_key: 可选，预加载的精灵表键名。默认用 Kenney spark 精灵
        """
        sheet = self._get_spark_sheet(sheet_key)
        frames, durations = self._extract_all_frames(sheet)
        if not frames:
            return

        # 随机选一个火花变体
        variant = random.randint(0, max(0, len(frames) - 1))
        variant_frames = [frames[variant]] if variant < len(frames) else frames[:1]
        variant_durations = [durations[variant]] if variant < len(durations) else durations[:1]

        anim = VFXAnimation(
            frames=variant_frames,
            durations=variant_durations,
            x=x, y=y,
            scale=scale,
            angle=angle + random.uniform(-15, 15),
            flip_x=flip_x,
        )
        self.animations.append(anim)

    def spawn_hit_explosion(self, x: float, y: float, scale: float = 2.0,
                            color_override: tuple = None, sheet_key: str = None):
        """命中爆炸 — 多帧连锁动画"""
        sheet = self._get_explosion_sheet(sheet_key)
        frames, durations = self._extract_all_frames(sheet)
        if not frames:
            self.spawn_hit_spark(x, y, scale)
            return

        anim = VFXAnimation(
            frames=frames[:8],  # 只用前8帧
            durations=durations[:8],
            x=x, y=y,
            scale=scale,
            loop=False,
        )
        self.animations.append(anim)

    # ── 斩击特效 (Slash) ──────────────────────────────────────────────────

    def spawn_slash(self, x: float, y: float, direction: str = 'right',
                    scale: float = 1.5, color_override: tuple = None):
        """生成斩击动画
        direction: 'right', 'left', 'up', 'down'
        """
        sheet = self._get_slash_sheet()
        frames, durations = self._extract_all_frames(sheet)
        if not frames:
            return

        # 按方向映射
        angle_map = {'right': 0, 'left': 180, 'up': -90, 'down': 90}
        angle = angle_map.get(direction, 0)
        flip = direction == 'left'

        anim = VFXAnimation(
            frames=frames,
            durations=durations,
            x=x, y=y,
            scale=scale,
            angle=angle,
            flip_x=flip,
            loop=False,
        )
        self.animations.append(anim)

    # ── 魔法/火焰粒子 (Magic/Flame) ───────────────────────────────────────

    def spawn_magic_burst(self, x: float, y: float, color: tuple[int, int, int] = (100, 200, 255),
                          count: int = 3, scale: float = 1.5):
        """魔法爆发 — 生成多个魔法粒子精灵"""
        sheet = self._get_magic_sheet()
        frames, durations = self._extract_all_frames(sheet)
        if not frames:
            return

        for i in range(count):
            angle = random.uniform(0, 360)
            offset_x = math.cos(math.radians(angle)) * random.uniform(10, 30)
            offset_y = math.sin(math.radians(angle)) * random.uniform(10, 30)
            variant = i % len(frames) if frames else 0
            dur = durations[variant] if durations else 0.1

            anim = VFXAnimation(
                frames=[frames[variant]],
                durations=[dur],
                x=x + offset_x,
                y=y + offset_y,
                scale=scale * random.uniform(0.8, 1.2),
                angle=random.uniform(-30, 30),
            )
            self.animations.append(anim)

    # ── 冲击波 (Shockwave) ─────────────────────────────────────────────────

    def spawn_shockwave(self, x: float, y: float, scale: float = 1.5,
                        color: tuple[int, int, int] = (255, 200, 50)):
        """环形冲击波扩散"""
        sheet = self._get_ring_sheet()
        frames, durations = self._extract_all_frames(sheet)
        if not frames:
            # 用 generic 粒子代替
            sheet = self._get_generic_sheet()
            frames, durations = self._extract_all_frames(sheet)
            if not frames:
                return

        anim = VFXAnimation(
            frames=frames[:6],
            durations=durations[:6],
            x=x, y=y,
            scale=scale,
            loop=False,
        )
        self.animations.append(anim)

    # ── 烟尘/爆炸 (Smoke/Explosion) ────────────────────────────────────────

    def spawn_explosion(self, x: float, y: float, scale: float = 2.0):
        """大爆炸效果"""
        sheet = self._get_explosion_sheet()
        frames, durations = self._extract_all_frames(sheet)
        if not frames:
            return

        anim = VFXAnimation(
            frames=frames,
            durations=durations,
            x=x, y=y,
            scale=scale,
            loop=False,
        )
        self.animations.append(anim)

    # ── 地面炸裂 (Ground Impact) ───────────────────────────────────────────

    def spawn_ground_impact(self, x: float, y: float, scale: float = 1.5):
        """地面冲击 — 尘土+碎石"""
        # 冲击环
        self.spawn_shockwave(x, y, scale=scale * 0.8, color=(200, 150, 50))
        # 火花
        for _ in range(3):
            self.spawn_hit_spark(
                x + random.uniform(-20, 20),
                y + random.uniform(-10, 10),
                scale=scale * 0.6
            )

    # ── 内部：获取对应精灵表 ───────────────────────────────────────────────

    def _get_spark_sheet(self, key=None) -> SpriteSheet:
        if key:
            return self._sheets.get(key)
        # Kenney spark 粒子（Transparent 目录）
        path = 'assets/vfx/particles/extracted/PNG (Transparent)/spark_'
        variants = [
            path + '01.png',
            path + '02.png',
            path + '03.png',
            path + '04.png',
            path + '05.png',
            path + '06.png',
            path + '07.png',
        ]
        # 返回第一个，实际从多个文件随机选择
        return self._load_sheet(variants[0])

    def _get_explosion_sheet(self, key=None) -> SpriteSheet:
        if key:
            return self._sheets.get(key)
        # Kenney fire/flame 粒子
        path = 'assets/vfx/particles/extracted/PNG (Transparent)/'
        return self._load_sheet(path + 'flame_01.png')

    def _get_slash_sheet(self) -> SpriteSheet:
        path = 'assets/vfx/particles/extracted/PNG (Transparent)/'
        return self._load_sheet(path + 'slash_01.png')

    def _get_magic_sheet(self) -> SpriteSheet:
        path = 'assets/vfx/particles/extracted/PNG (Transparent)/'
        return self._load_sheet(path + 'magic_01.png')

    def _get_ring_sheet(self) -> SpriteSheet:
        path = 'assets/vfx/particles/extracted/PNG (Transparent)/'
        return self._load_sheet(path + 'trace_01.png')

    def _get_generic_sheet(self) -> SpriteSheet:
        path = 'assets/vfx/particles/extracted/PNG (Transparent)/'
        return self._load_sheet(path + 'circle_01.png')

    def _extract_all_frames(self, sheet: SpriteSheet) -> tuple:
        if not sheet:
            return [], []
        frames = []
        durations = []
        for i in range(sheet.frame_count()):
            frames.append(sheet.get_frame(i))
            durations.append(sheet.get_frame_duration(i))
        return frames, durations

    # ── 批量生成粒子群 ────────────────────────────────────────────────────

    def spawn_hit_cluster(self, x: float, y: float, intensity: str = 'medium'):
        """命中群 — 根据强度生成一组特效
        intensity: 'light', 'medium', 'heavy', 'ultimate'
        """
        configs = {
            'light':   {'sparks': 1, 'scale': 1.0, 'scale2': 0.8, 'explosion': False},
            'medium':  {'sparks': 3, 'scale': 1.2, 'scale2': 1.0, 'explosion': True},
            'heavy':   {'sparks': 5, 'scale': 1.5, 'scale2': 1.2, 'explosion': True},
            'ultimate': {'sparks': 8, 'scale': 2.0, 'scale2': 1.5, 'explosion': True},
        }
        cfg = configs.get(intensity, configs['medium'])

        for i in range(cfg['sparks']):
            self.spawn_hit_spark(
                x + random.uniform(-15, 15),
                y + random.uniform(-15, 15),
                scale=cfg['scale'] * random.uniform(0.8, 1.2),
                angle=random.uniform(-45, 45),
            )

        if cfg['explosion']:
            self.spawn_hit_explosion(x, y, scale=cfg['scale2'])

    def spawn_ultimate_blast(self, x: float, y: float, direction: int = 1):
        """终极技能爆发 — 震撼全屏的特效组"""
        # 中心爆炸
        self.spawn_explosion(x, y, scale=3.0)
        self.spawn_explosion(x, y - 20, scale=2.0)
        # 冲击波
        self.spawn_shockwave(x, y, scale=2.5)
        # 多个方向斩击
        for angle_deg in range(0, 360, 45):
            rad = math.radians(angle_deg)
            tx = x + math.cos(rad) * 50
            ty = y - 30 + math.sin(rad) * 30
            self.spawn_slash(tx, ty, direction='right', scale=2.0)
        # 大量火花
        for _ in range(12):
            self.spawn_hit_spark(
                x + random.uniform(-40, 40),
                y + random.uniform(-40, 10),
                scale=random.uniform(1.0, 2.0),
                angle=random.uniform(-60, 60),
            )

    # ── 更新 & 绘制 ────────────────────────────────────────────────────────

    def update(self, dt: float):
        for anim in self.animations:
            anim.update(dt)
        self.animations = [a for a in self.animations if a.active]

    def draw(self, surface: pygame.Surface):
        for anim in self.animations:
            anim.draw(surface)

    def clear(self):
        self.animations.clear()
        self._sheets.clear()
