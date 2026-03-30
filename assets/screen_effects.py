# 史诗级屏幕特效系统
# 屏幕闪白 (Flash)、镜头震动 (Screen Shake)、慢动作 (Slow Motion)
import pygame
import math
import random


class ScreenEffects:
    """全局屏幕特效 — 闪白、震动、慢动作"""

    def __init__(self):
        # 屏幕震动
        self.shake_intensity: float = 0.0
        self.shake_duration: float = 0.0
        self.shake_timer: float = 0.0
        self.shake_offset_x: float = 0.0
        self.shake_offset_y: float = 0.0

        # 屏幕闪白
        self.flash_color: tuple[int, int, int] = (255, 255, 255)
        self.flash_alpha: float = 0.0
        self.flash_duration: float = 0.0
        self.flash_timer: float = 0.0

        # 屏幕变暗（强化版命中）
        self.darkness_alpha: float = 0.0
        self.darkness_timer: float = 0.0
        self.darkness_duration: float = 0.0

        # 慢动作
        self.slowmo_factor: float = 1.0  # 1.0 = 正常速度
        self.slowmo_target: float = 1.0
        self.slowmo_duration: float = 0.0
        self.slowmo_timer: float = 0.0

        # 色调覆盖（用于必杀技等）
        self.tint_color: tuple[int, int, int] | None = None
        self.tint_alpha: float = 0.0

        # 全屏模糊（性能开销大，酌情使用）
        self.blur_enabled: bool = False

        self._surface: pygame.Surface | None = None

    def set_surface(self, surface: pygame.Surface):
        self._surface = surface

    # ── 屏幕震动 ──────────────────────────────────────────────────────────

    def shake(self, intensity: float = 8.0, duration: float = 0.3):
        """触发屏幕震动（自动叠加取最大值）"""
        if intensity > self.shake_intensity:
            self.shake_intensity = intensity
        self.shake_duration = duration
        self.shake_timer = duration

    def shake_heavy(self):
        """重型震动 — 必杀技命中时"""
        self.shake(intensity=15.0, duration=0.5)

    def shake_light(self):
        """轻型震动 — 普通命中时"""
        self.shake(intensity=5.0, duration=0.2)

    def shake_medium(self):
        """中型震动"""
        self.shake(intensity=10.0, duration=0.35)

    def _update_shake(self, dt: float):
        if self.shake_timer <= 0:
            self.shake_offset_x = 0.0
            self.shake_offset_y = 0.0
            return

        self.shake_timer -= dt
        progress = self.shake_timer / max(0.001, self.shake_duration)
        current_intensity = self.shake_intensity * progress

        # 随机偏移
        self.shake_offset_x = (random.uniform(-1, 1) * current_intensity
                                if current_intensity > 0.1 else 0.0)
        self.shake_offset_y = (random.uniform(-1, 1) * current_intensity
                                if current_intensity > 0.1 else 0.0)

    # ── 屏幕闪白 ──────────────────────────────────────────────────────────

    def flash(self, color: tuple[int, int, int] = (255, 255, 255),
              duration: float = 0.15, alpha: float = 200):
        """屏幕闪白/闪彩
        color: 闪光颜色，默认白色
        duration: 持续时间（秒）
        alpha: 峰值透明度（0-255）
        """
        self.flash_color = color
        self.flash_alpha = alpha
        self.flash_duration = duration
        self.flash_timer = duration

    def flash_hit(self):
        """命中闪白"""
        self.flash(color=(255, 255, 255), duration=0.12, alpha=180)

    def flash_fire(self):
        """火焰闪"""
        self.flash(color=(255, 120, 0), duration=0.2, alpha=200)

    def flash_ultimate(self):
        """终极必杀闪（蓝白强光）"""
        self.flash(color=(200, 230, 255), duration=0.35, alpha=250)
        self.darkness(color=(0, 0, 50), duration=0.4, alpha=100)

    def flash_critical(self):
        """暴击闪（红色）"""
        self.flash(color=(255, 50, 50), duration=0.25, alpha=220)

    def _update_flash(self, dt: float):
        if self.flash_timer <= 0:
            self.flash_alpha = 0.0
            return

        self.flash_timer -= dt
        progress = self.flash_timer / max(0.001, self.flash_duration)
        # 余弦衰减，更自然
        self.flash_alpha = int(
            self.flash_alpha * math.cos(math.pi * 0.5 * (1.0 - progress))
        )

    # ── 全屏变暗 ─────────────────────────────────────────────────────────

    def darkness(self, color: tuple[int, int, int] = (0, 0, 0),
                 duration: float = 0.3, alpha: float = 80):
        """全屏变暗遮罩（用于必杀技等）"""
        self.darkness_color = color
        self.darkness_alpha = alpha
        self.darkness_duration = duration
        self.darkness_timer = duration

    def _update_darkness(self, dt: float):
        if self.darkness_timer <= 0:
            self.darkness_alpha = 0.0
            return

        self.darkness_timer -= dt
        progress = self.darkness_timer / max(0.001, self.darkness_duration)
        self.darkness_alpha = int(self.darkness_alpha * math.cos(
            math.pi * 0.5 * (1.0 - progress)))

    # ── 慢动作 ───────────────────────────────────────────────────────────

    def slowmo(self, factor: float = 0.3, duration: float = 0.5):
        """触发慢动作效果
        factor: 速度倍率，0.3 = 正常速度的30%（更慢）
        duration: 持续时间（秒）
        """
        self.slowmo_factor = factor
        self.slowmo_target = 1.0  # 恢复到正常速度
        self.slowmo_duration = duration
        self.slowmo_timer = duration

    def slowmo_hit(self):
        """命中慢动作（0.4倍速，持续0.4秒）"""
        self.slowmo(factor=0.35, duration=0.4)

    def slowmo_ultimate(self):
        """终极必杀慢动作（0.2倍速，持续0.8秒）"""
        self.slowmo(factor=0.2, duration=0.8)

    def _update_slowmo(self, dt: float):
        if self.slowmo_timer <= 0:
            self.slowmo_factor = 1.0
            return

        self.slowmo_timer -= dt
        # 余弦插值恢复到正常速度
        progress = self.slowmo_timer / max(0.001, self.slowmo_duration)
        self.slowmo_factor = (
            self.slowmo_factor +
            (1.0 - self.slowmo_factor) * (1.0 - math.cos(math.pi * 0.5 * progress)) * 0.5
        )

    # ── 色调覆盖 ─────────────────────────────────────────────────────────

    def tint(self, color: tuple[int, int, int], alpha: float = 80):
        """全屏色调覆盖"""
        self.tint_color = color
        self.tint_alpha = alpha

    def clear_tint(self):
        self.tint_color = None
        self.tint_alpha = 0.0

    # ── 综合更新 & 绘制 ───────────────────────────────────────────────────

    def update(self, dt: float):
        self._update_shake(dt)
        self._update_flash(dt)
        self._update_darkness(dt)
        self._update_slowmo(dt)

    def get_shake_offset(self) -> tuple[float, float]:
        """获取当前震动偏移量"""
        return self.shake_offset_x, self.shake_offset_y

    def get_effective_dt(self, raw_dt: float) -> float:
        """获取经过慢动作调整后的实际 dt"""
        return raw_dt * self.slowmo_factor

    def draw_overlay(self, surface: pygame.Surface):
        """在主表面上绘制所有覆盖效果（在角色之后、主UI之前）"""
        w, h = surface.get_size()

        # 1. 全屏变暗
        if self.darkness_alpha > 0 and self.darkness_timer > 0:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((*self.darkness_color, max(0, int(self.darkness_alpha))))
            surface.blit(overlay, (0, 0))

        # 2. 色调覆盖
        if self.tint_color and self.tint_alpha > 0:
            overlay = pygame.Surface((w, h), pygame.SRCALPHA)
            overlay.fill((*self.tint_color, max(0, int(self.tint_alpha))))
            surface.blit(overlay, (0, 0))

    def draw_flash(self, surface: pygame.Surface):
        """绘制闪光效果（在所有内容之上）"""
        if self.flash_alpha <= 0 or self.flash_timer <= 0:
            return

        w, h = surface.get_size()
        overlay = pygame.Surface((w, h), pygame.SRCALPHA)
        overlay.fill((*self.flash_color, max(0, int(self.flash_alpha))))
        surface.blit(overlay, (0, 0))

    # ── 一键触发：Epic 命中特效组合 ──────────────────────────────────────

    def epic_hit(self, intensity: str = 'medium', color: str = 'white'):
        """Epic命中特效 — 闪白+震动+慢动作一键触发
        intensity: 'light', 'medium', 'heavy', 'ultimate'
        color: 'white', 'fire', 'critical'
        """
        if color == 'fire':
            self.flash_fire()
        elif color == 'critical':
            self.flash_critical()
        else:
            self.flash_hit()

        {
            'light': self.shake_light,
            'medium': self.shake_medium,
            'heavy': self.shake_heavy,
            'ultimate': self.shake_heavy,
        }.get(intensity, self.shake_medium)()

        if intensity in ('heavy', 'ultimate'):
            self.slowmo_hit()
        if intensity == 'ultimate':
            self.flash_ultimate()
            self.slowmo_ultimate()

    # ── 武器特效专用闪光 ────────────────────────────────────────────────────

    def weapon_nuke_warning(self):
        """核弹预警闪光"""
        self.darkness(color=(80, 0, 0), duration=0.4, alpha=60)
        self.flash(color=(255, 50, 0), duration=0.2, alpha=120)

    def weapon_staff_flash(self, color: tuple[int, int, int]):
        """法杖全屏特效闪光"""
        self.flash(color=color, duration=0.25, alpha=100)
        self.darkness(color=color, duration=0.3, alpha=40)

    # ── 武器专属屏幕效果 ────────────────────────────────────────────────────

    def weapon_nuke_impact(self):
        """核弹命中 - 强烈屏幕震动 + 全屏橙红闪光"""
        self.shake(intensity=20.0, duration=0.6)
        self.flash(color=(255, 150, 50), duration=0.3, alpha=230)
        self.darkness(color=(100, 30, 0), duration=0.5, alpha=120)
        self.slowmo(factor=0.3, duration=0.5)

    def weapon_gatling_hit(self):
        """加特林命中 - 轻微震动 + 快速黄色闪光"""
        self.shake(intensity=4.0, duration=0.15)
        self.flash(color=(255, 200, 80), duration=0.1, alpha=100)

    def weapon_staff_fire(self):
        """红色法杖(火焰) - 橙红渐变 + 强烈震动"""
        self.shake(intensity=12.0, duration=0.4)
        self.flash(color=(255, 80, 0), duration=0.3, alpha=200)
        self.darkness(color=(80, 20, 0), duration=0.35, alpha=80)
        self.tint(color=(255, 100, 0), alpha=50)

    def weapon_staff_wave(self):
        """蓝色法杖(海啸) - 蓝色渐变 + 波浪式震动"""
        self.shake(intensity=10.0, duration=0.5)
        self.flash(color=(50, 150, 255), duration=0.35, alpha=180)
        self.darkness(color=(0, 30, 100), duration=0.4, alpha=90)
        self.tint(color=(0, 100, 200), alpha=60)

    def weapon_staff_poison(self):
        """绿色法杖(毒雾) - 绿色渐变 + 闪烁效果"""
        self.shake(intensity=8.0, duration=0.4)
        self.flash(color=(50, 200, 50), duration=0.25, alpha=150)
        self.darkness(color=(20, 80, 20), duration=0.35, alpha=70)
        self.tint(color=(0, 150, 0), alpha=40)

    def clear_weapon_tint(self):
        """清除武器色调效果"""
        self.clear_tint()
