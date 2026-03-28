# 矢量风格角色精灵程序化生成

import pygame
import math
from typing import Dict, Tuple, Optional
from config import Colors

class SpriteGenerator:
    """程序化生成矢量风格角色精灵"""

    def __init__(self):
        self.cache: Dict[str, pygame.Surface] = {}
        self.character_size = (120, 160)

    def generate(self, char_type: int, pose: str, facing_right: bool = True,
                 primary_color: Tuple[int, int, int] = (220, 50, 50),
                 secondary_color: Tuple[int, int, int] = (150, 30, 30)) -> pygame.Surface:
        """生成角色精灵"""
        cache_key = f"{char_type}_{pose}_{facing_right}"
        if cache_key in self.cache:
            return self.cache[cache_key]

        surface = pygame.Surface(self.character_size, pygame.SRCALPHA)
        getattr(self, f"draw_{pose}")(surface, facing_right, primary_color, secondary_color)

        self.cache[cache_key] = surface
        return surface

    def draw_idle(self, surface: pygame.Surface, facing_right: bool,
                  primary: Tuple, secondary: Tuple):
        """绘制待机姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体
        self.draw_body(surface, cx, 80, primary, secondary)

        # 头部
        self.draw_head(surface, cx, 35, primary, secondary)

        # 手臂（稍微张开）
        self.draw_arm(surface, cx - 20 * dir, 70, dir, primary, secondary, angle=20)
        self.draw_arm(surface, cx + 20 * dir, 70, -dir, primary, secondary, angle=-20)

    def draw_walk(self, surface: pygame.Surface, facing_right: bool,
                  primary: Tuple, secondary: Tuple):
        """绘制行走姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体（轻微倾斜）
        self.draw_body(surface, cx, 80, primary, secondary)

        # 头部
        self.draw_head(surface, cx, 35, primary, secondary)

        # 手臂（摆动）
        self.draw_arm(surface, cx - 15 * dir, 75, dir, primary, secondary, angle=30)
        self.draw_arm(surface, cx + 15 * dir, 65, -dir, primary, secondary, angle=-30)

        # 腿部（行走姿态）
        self.draw_leg(surface, cx - 10, 140, dir, primary, secondary, angle=10)
        self.draw_leg(surface, cx + 10, 140, -dir, primary, secondary, angle=-10)

    def draw_jump(self, surface: pygame.Surface, facing_right: bool,
                  primary: Tuple, secondary: Tuple):
        """绘制跳跃姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体
        self.draw_body(surface, cx, 85, primary, secondary)

        # 头部
        self.draw_head(surface, cx, 42, primary, secondary)

        # 手臂（向上）
        self.draw_arm(surface, cx - 25 * dir, 55, dir, primary, secondary, angle=60)
        self.draw_arm(surface, cx + 25 * dir, 55, -dir, primary, secondary, angle=60)

        # 腿部（收起）
        self.draw_leg(surface, cx - 15, 130, dir, primary, secondary, angle=45)
        self.draw_leg(surface, cx + 15, 130, -dir, primary, secondary, angle=-45)

    def draw_attack_light(self, surface: pygame.Surface, facing_right: bool,
                          primary: Tuple, secondary: Tuple):
        """绘制轻攻击姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体（向前倾）
        self.draw_body(surface, cx + 10 * dir, 82, primary, secondary)

        # 头部
        self.draw_head(surface, cx + 12 * dir, 38, primary, secondary)

        # 后手
        self.draw_arm(surface, cx - 20 * dir, 75, dir, primary, secondary, angle=-10)

        # 攻击的手（伸出）
        self.draw_arm(surface, cx + 35 * dir, 55, dir, primary, secondary, angle=0, extended=True)
        self.draw_fist(surface, cx + 50 * dir, 55, primary)

    def draw_attack_heavy(self, surface: pygame.Surface, facing_right: bool,
                          primary: Tuple, secondary: Tuple):
        """绘制重攻击姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体（大幅前倾）
        self.draw_body(surface, cx + 15 * dir, 85, primary, secondary)

        # 头部
        self.draw_head(surface, cx + 18 * dir, 40, primary, secondary)

        # 双手后拉
        self.draw_arm(surface, cx - 30 * dir, 60, dir, primary, secondary, angle=150)
        self.draw_arm(surface, cx - 25 * dir, 80, -dir, primary, secondary, angle=120)

    def draw_attack_special(self, surface: pygame.Surface, facing_right: bool,
                            primary: Tuple, secondary: Tuple):
        """绘制必杀技姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体（后仰蓄力）
        self.draw_body(surface, cx - 5 * dir, 85, primary, secondary)

        # 头部
        self.draw_head(surface, cx - 3 * dir, 38, primary, secondary)

        # 手臂（向上举）
        self.draw_arm(surface, cx - 15 * dir, 40, dir, primary, secondary, angle=80)
        self.draw_arm(surface, cx + 15 * dir, 40, -dir, primary, secondary, angle=100)

        # 能量效果
        self.draw_energy_effect(surface, cx + 30 * dir, 50, primary)

    def draw_hit(self, surface: pygame.Surface, facing_right: bool,
                 primary: Tuple, secondary: Tuple):
        """绘制受击姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体（后仰）
        self.draw_body(surface, cx - 15 * dir, 85, primary, secondary)

        # 头部（低下）
        self.draw_head(surface, cx - 12 * dir, 42, primary, secondary)

        # 手臂（向后）
        self.draw_arm(surface, cx - 25 * dir, 75, dir, primary, secondary, angle=-45)
        self.draw_arm(surface, cx - 20 * dir, 85, -dir, primary, secondary, angle=-60)

    def draw_block(self, surface: pygame.Surface, facing_right: bool,
                   primary: Tuple, secondary: Tuple):
        """绘制防御姿势"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体（半蹲）
        self.draw_body(surface, cx, 90, primary, secondary)

        # 头部（护住）
        self.draw_head(surface, cx, 48, primary, secondary)

        # 手臂（交叉防守）
        self.draw_arm(surface, cx - 5 * dir, 55, dir, primary, secondary, angle=30)
        self.draw_arm(surface, cx + 5 * dir, 55, -dir, primary, secondary, angle=-30)

    def draw_ko(self, surface: pygame.Surface, facing_right: bool,
                primary: Tuple, secondary: Tuple):
        """绘制KO姿势（倒地）"""
        cx = 60 if facing_right else 60
        dir = 1 if facing_right else -1

        # 身体（倒下）
        pygame.draw.ellipse(surface, primary, (30, 100, 80, 40))
        pygame.draw.ellipse(surface, secondary, (35, 105, 70, 30))

        # 头部
        self.draw_head(surface, 35, 100, primary, secondary)

    def draw_body(self, surface: pygame.Surface, cx: int, cy: int,
                  primary: Tuple, secondary: Tuple):
        """绘制身体"""
        # 身体主体（椭圆形）
        body_rect = (cx - 25, cy - 35, 50, 70)
        pygame.draw.ellipse(surface, primary, body_rect)
        pygame.draw.ellipse(surface, secondary, (cx - 20, cy - 30, 40, 60))

        # 胸部高光
        pygame.draw.ellipse(surface, tuple(min(255, c + 30) for c in primary),
                          (cx - 12, cy - 25, 24, 30))

    def draw_head(self, surface: pygame.Surface, cx: int, cy: int,
                  primary: Tuple, secondary: Tuple):
        """绘制头部"""
        # 头部（圆形）
        head_radius = 22
        pygame.draw.circle(surface, primary, (cx, cy), head_radius)
        pygame.draw.circle(surface, (240, 220, 200), (cx, cy), head_radius - 3)

        # 头发
        pygame.draw.arc(surface, secondary, (cx - 22, cy - 25, 44, 35),
                       math.radians(180), math.radians(360), 8)

        # 眼睛
        eye_y = cy + 2
        eye_size = 4
        pygame.draw.circle(surface, (30, 30, 30), (cx - 8, eye_y), eye_size)
        pygame.draw.circle(surface, (30, 30, 30), (cx + 8, eye_y), eye_size)

    def draw_arm(self, surface: pygame.Surface, cx: int, cy: int, direction: int,
                 primary: Tuple, secondary: Tuple, angle: float = 0, extended: bool = False):
        """绘制手臂"""
        length = 45 if extended else 35
        rad = math.radians(angle + (30 if direction > 0 else -30))
        end_x = cx + math.cos(rad) * length * direction
        end_y = cy + math.sin(rad) * length

        # 手臂
        pygame.draw.line(surface, primary, (cx, cy), (end_x, end_y), 12)
        pygame.draw.line(surface, (240, 220, 200), (cx, cy), (end_x, end_y), 8)

    def draw_fist(self, surface: pygame.Surface, cx: int, cy: int, primary: Tuple):
        """绘制拳头"""
        pygame.draw.circle(surface, primary, (cx, cy), 12)
        pygame.draw.circle(surface, (240, 220, 200), (cx, cy), 8)

    def draw_leg(self, surface: pygame.Surface, cx: int, cy: int, direction: int,
                  primary: Tuple, secondary: Tuple, angle: float = 0):
        """绘制腿部"""
        length = 35
        rad = math.radians(angle)
        end_x = cx + math.sin(rad) * length * direction
        end_y = cy + math.cos(rad) * length

        # 腿
        pygame.draw.line(surface, primary, (cx, cy), (end_x, end_y), 14)
        pygame.draw.line(surface, secondary, (cx, cy), (end_x, end_y), 10)

        # 脚
        foot_x = end_x + 8 * direction
        foot_y = end_y + 5
        pygame.draw.ellipse(surface, (50, 50, 50), (foot_x - 8, foot_y - 4, 16, 8))

    def draw_energy_effect(self, surface: pygame.Surface, cx: int, cy: int, primary: Tuple):
        """绘制能量效果（必杀技）"""
        # 能量球
        pygame.draw.circle(surface, (255, 255, 100), (cx, cy), 20)
        pygame.draw.circle(surface, (255, 200, 50), (cx, cy), 14)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 6)

        # 光芒
        for i in range(8):
            angle = math.radians(i * 45)
            ray_end_x = cx + math.cos(angle) * 30
            ray_end_y = cy + math.sin(angle) * 30
            pygame.draw.line(surface, (255, 255, 100), (cx, cy), (ray_end_x, ray_end_y), 3)


# 全局精灵生成器实例
sprite_generator = SpriteGenerator()


def get_sprite(char_type: int, pose: str, facing_right: bool = True,
               primary_color: Tuple[int, int, int] = (220, 50, 50),
               secondary_color: Tuple[int, int, int] = (150, 30, 30)) -> pygame.Surface:
    """获取角色精灵的便捷函数"""
    return sprite_generator.generate(char_type, pose, facing_right, primary_color, secondary_color)
