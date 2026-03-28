# 视觉特效系统
import pygame
import math
import random
from typing import List, Tuple, Optional


class EffectText:
    """技能文字特效"""

    def __init__(self, text: str, x: float, y: float,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 size: int = 36, duration: float = 1.5):
        self.text = text
        self.x = x
        self.y = y
        self.start_y = y
        self.color = color
        self.size = size
        self.duration = duration
        self.elapsed = 0.0
        self.active = True

        # 动画参数
        self.scale = 1.0
        self.alpha = 255
        self.rotation = random.uniform(-5, 5)

    def update(self, dt: float):
        if not self.active:
            return

        self.elapsed += dt
        progress = self.elapsed / self.duration

        if progress >= 1.0:
            self.active = False
            return

        # 向上飘动
        self.y = self.start_y - progress * 60

        # 缩放动画
        if progress < 0.2:
            self.scale = 1.0 + (1.0 - progress / 0.2) * 0.5
        else:
            self.scale = 1.0

        # 淡出
        if progress > 0.6:
            self.alpha = int(255 * (1.0 - (progress - 0.6) / 0.4))

    def draw(self, surface: pygame.Surface):
        if not self.active or self.alpha <= 0:
            return

        try:
            font = pygame.font.SysFont("microsoftyahei", int(self.size * self.scale), bold=True)
        except:
            font = pygame.font.Font(None, int(self.size * self.scale))

        text_surf = font.render(self.text, True, self.color)
        text_surf.set_alpha(self.alpha)

        # 描边效果
        for dx in [-2, 0, 2]:
            for dy in [-2, 0, 2]:
                if dx != 0 or dy != 0:
                    outline = font.render(self.text, True, (0, 0, 0))
                    outline.set_alpha(self.alpha // 2)
                    surface.blit(outline, (int(self.x - text_surf.get_width() // 2 + dx),
                                           int(self.y - text_surf.get_height() // 2 + dy)))

        surface.blit(text_surf, (int(self.x - text_surf.get_width() // 2),
                                  int(self.y - text_surf.get_height() // 2)))


class Particle:
    """粒子特效"""

    def __init__(self, x: float, y: float,
                 vx: float, vy: float,
                 color: Tuple[int, int, int],
                 size: float = 5.0,
                 lifetime: float = 0.5,
                 gravity: float = 0.0):
        self.x = x
        self.y = y
        self.vx = vx
        self.vy = vy
        self.color = color
        self.size = size
        self.lifetime = lifetime
        self.max_lifetime = lifetime
        self.gravity = gravity
        self.active = True

    def update(self, dt: float):
        if not self.active:
            return

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return

        self.x += self.vx * 60 * dt
        self.y += self.vy * 60 * dt
        self.vy += self.gravity * 60 * dt

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        alpha = int(255 * (self.lifetime / self.max_lifetime))
        size = int(self.size * (self.lifetime / self.max_lifetime))

        if size > 0:
            temp_surf = pygame.Surface((size * 2, size * 2), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, (*self.color, alpha), (size, size), size)
            surface.blit(temp_surf, (int(self.x - size), int(self.y - size)))


class EffectRing:
    """环形特效"""

    def __init__(self, x: float, y: float, radius: float,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 duration: float = 0.5, width: int = 3):
        self.x = x
        self.y = y
        self.radius = radius
        self.max_radius = radius
        self.color = color
        self.duration = duration
        self.lifetime = duration
        self.width = width
        self.active = True

    def update(self, dt: float):
        if not self.active:
            return

        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False
            return

        progress = 1.0 - (self.lifetime / self.duration)
        self.radius = self.max_radius * (0.5 + progress * 0.5)

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        alpha = int(255 * (self.lifetime / self.duration))
        if alpha > 0 and self.radius > 0:
            temp_surf = pygame.Surface((int(self.radius * 2 + 10), int(self.radius * 2 + 10)), pygame.SRCALPHA)
            pygame.draw.circle(temp_surf, (*self.color, alpha), (int(self.radius + 5), int(self.radius + 5)),
                             int(self.radius), self.width)
            surface.blit(temp_surf, (int(self.x - self.radius - 5), int(self.y - self.radius - 5)))


class SlashEffect:
    """斩击特效"""

    def __init__(self, x: float, y: float, angle: float,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 length: float = 100.0, width: float = 20.0):
        self.x = x
        self.y = y
        self.angle = angle
        self.color = color
        self.length = length
        self.width = width
        self.lifetime = 0.3
        self.max_lifetime = 0.3
        self.active = True

    def update(self, dt: float):
        if not self.active:
            return
        self.lifetime -= dt
        if self.lifetime <= 0:
            self.active = False

    def draw(self, surface: pygame.Surface):
        if not self.active:
            return

        alpha = int(255 * (self.lifetime / self.max_lifetime))
        if alpha > 0:
            # 创建旋转的斩击效果
            points = []
            for i in range(3):
                t = i / 2.0
                offset_x = math.cos(self.angle) * self.length * t
                offset_y = math.sin(self.angle) * self.length * t
                w = self.width * (1.0 - t)
                points.append((self.x + offset_x - math.sin(self.angle) * w,
                              self.y + offset_y + math.cos(self.angle) * w))

            temp_surf = pygame.Surface((int(self.length + 50), int(self.width * 2 + 50)), pygame.SRCALPHA)
            if len(points) >= 3:
                pygame.draw.polygon(temp_surf, (*self.color, alpha), [
                    (25, 25 + self.width),
                    (25 + self.length, 25 + self.width + 10),
                    (25 + self.length * 0.7, 25)
                ])
            surface.blit(temp_surf, (int(self.x - 25), int(self.y - 25 - self.width)))


class EffectManager:
    """特效管理器"""

    def __init__(self):
        self.effect_texts: List[EffectText] = []
        self.particles: List[Particle] = []
        self.effect_rings: List[EffectRing] = []
        self.slash_effects: List[SlashEffect] = []

    def add_text(self, text: str, x: float, y: float,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 size: int = 36, duration: float = 1.5):
        """添加文字特效"""
        self.effect_texts.append(EffectText(text, x, y, color, size, duration))

    def add_particle_burst(self, x: float, y: float, count: int = 10,
                          color: Tuple[int, int, int] = (255, 255, 255),
                          speed: float = 5.0, size: float = 5.0):
        """添加粒子爆发"""
        for _ in range(count):
            angle = random.uniform(0, math.pi * 2)
            vx = math.cos(angle) * speed * random.uniform(0.5, 1.5)
            vy = math.sin(angle) * speed * random.uniform(0.5, 1.5)
            self.particles.append(Particle(x, y, vx, vy, color, size, 0.5, 5.0))

    def add_ring(self, x: float, y: float, radius: float = 50,
                color: Tuple[int, int, int] = (255, 255, 255)):
        """添加环形特效"""
        self.effect_rings.append(EffectRing(x, y, radius, color))

    def add_slash(self, x: float, y: float, angle: float = 0,
                 color: Tuple[int, int, int] = (255, 255, 255),
                 length: float = 100.0):
        """添加斩击特效"""
        self.slash_effects.append(SlashEffect(x, y, angle, color, length))

    def update(self, dt: float):
        """更新所有特效"""
        for effect in self.effect_texts:
            effect.update(dt)
        for effect in self.particles:
            effect.update(dt)
        for effect in self.effect_rings:
            effect.update(dt)
        for effect in self.slash_effects:
            effect.update(dt)

        # 清理已结束的特效
        self.effect_texts = [e for e in self.effect_texts if e.active]
        self.particles = [p for p in self.particles if p.active]
        self.effect_rings = [r for r in self.effect_rings if r.active]
        self.slash_effects = [s for s in self.slash_effects if s.active]

    def draw(self, surface: pygame.Surface):
        """绘制所有特效"""
        for effect in self.effect_rings:
            effect.draw(surface)
        for effect in self.particles:
            effect.draw(surface)
        for effect in self.slash_effects:
            effect.draw(surface)
        for effect in self.effect_texts:
            effect.draw(surface)


# 角色特效工厂
class CharacterEffects:
    """角色特效工厂"""

    @staticmethod
    def gong_dage_effects(manager: EffectManager, x: float, y: float, move_name: str = ""):
        """龚大哥 - 爱国特效（红色火焰/红旗）"""
        # 粒子爆发 - 红色火焰
        manager.add_particle_burst(x, y, 20, (255, 100, 50), 8.0, 8.0)
        # 环形冲击波
        manager.add_ring(x, y, 60, (255, 50, 50))

        if "爱国" in move_name:
            manager.add_text(move_name, x, y - 80, (255, 50, 50), 42, 1.8)
        elif move_name:
            manager.add_text(move_name, x, y - 80, (255, 200, 100), 32, 1.5)

    @staticmethod
    def junshi_effects(manager: EffectManager, x: float, y: float, move_name: str = ""):
        """军师 - 实验室特效（紫色/蓝色能量）"""
        # 粒子爆发 - 紫色能量
        manager.add_particle_burst(x, y, 25, (150, 50, 255), 10.0, 6.0)
        # 环形特效
        manager.add_ring(x, y, 70, (100, 50, 255))
        # 斩击特效
        manager.add_slash(x, y, 0, (150, 100, 255), 120)

        if "实验室" in move_name:
            manager.add_text(move_name, x, y - 90, (150, 50, 255), 44, 2.0)
        elif move_name:
            manager.add_text(move_name, x, y - 80, (180, 120, 255), 32, 1.5)

    @staticmethod
    def shenmiren_effects(manager: EffectManager, x: float, y: float, move_name: str = ""):
        """神秘人 - 叛国特效（黑色/烟雾）"""
        # 粒子爆发 - 黑色烟雾
        manager.add_particle_burst(x, y, 15, (50, 50, 50), 6.0, 10.0)
        # 环形特效
        manager.add_ring(x, y, 50, (80, 80, 80))

        if "叛国" in move_name:
            manager.add_text(move_name, x, y - 80, (100, 100, 100), 42, 1.8)
        elif move_name:
            manager.add_text(move_name, x, y - 80, (150, 150, 150), 32, 1.5)

    @staticmethod
    def zitong_effects(manager: EffectManager, x: float, y: float, move_name: str = ""):
        """籽桐 - 雕特效（绿色/羽毛）"""
        # 粒子爆发 - 绿色
        manager.add_particle_burst(x, y, 18, (50, 200, 80), 7.0, 5.0)
        # 环形特效
        manager.add_ring(x, y, 55, (80, 200, 80))
        # 斩击特效
        manager.add_slash(x, y, math.pi / 6, (80, 255, 100), 80)

        if "雕" in move_name:
            manager.add_text(move_name, x, y - 80, (50, 200, 50), 42, 1.8)
        elif move_name:
            manager.add_text(move_name, x, y - 80, (100, 255, 120), 32, 1.5)

    @staticmethod
    def get_effect_function(char_name: str):
        """根据角色名获取特效函数"""
        effects_map = {
            "龚大哥": CharacterEffects.gong_dage_effects,
            "军师": CharacterEffects.junshi_effects,
            "神秘人": CharacterEffects.shenmiren_effects,
            "籽桐": CharacterEffects.zitong_effects,
        }
        return effects_map.get(char_name, CharacterEffects.gong_dage_effects)
