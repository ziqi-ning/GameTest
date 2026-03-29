# 小兵管理器 - 挂载在Fighter上，管理金币和小兵

import pygame
from typing import List, Optional, TYPE_CHECKING
from entities.minion import Minion, create_minion

if TYPE_CHECKING:
    from entities.fighter import Fighter

# 金币配置
COIN_PER_SECOND = 1.0       # 每秒自动获得金币
COIN_PER_MINION_KILL = 5    # 击杀敌方小兵获得金币
MINION_COST = 20            # 召唤一个小兵的金币消耗


class MinionManager:
    """小兵管理器"""

    def __init__(self, owner_id: int, char_name: str):
        self.owner_id = owner_id
        self.char_name = char_name

        self.coins = 0.0            # 当前金币（浮点，显示取整）
        self.coin_timer = 0.0       # 自动金币计时

        self.minions: List[Minion] = []
        self.mode = "charge"        # 全局指令："charge" | "follow"

        self.stage = None           # 场景引用（传给小兵）

    @property
    def coin_int(self) -> int:
        return int(self.coins)

    def update(self, dt: float, owner_x: float, owner_y: float,
               enemy: 'Fighter', enemy_manager: Optional['MinionManager']):
        """每帧更新"""
        # 自动金币
        self.coin_timer += dt
        if self.coin_timer >= 1.0:
            self.coin_timer -= 1.0
            self.coins += COIN_PER_SECOND

        # 获取敌方小兵列表
        enemy_minions = enemy_manager.minions if enemy_manager else []

        # 更新所有小兵
        for minion in self.minions[:]:
            minion.stage = self.stage
            minion.mode = self.mode
            minion.update(dt, owner_x, owner_y, enemy, enemy_minions)

            # 检查小兵投射物是否命中敌方
            self._check_projectile_hits(minion, enemy, enemy_minions)

        # 清理死亡小兵
        self.minions = [m for m in self.minions if m.alive]

    def _check_projectile_hits(self, minion: Minion, enemy: 'Fighter',
                                enemy_minions: List[Minion]):
        """检查小兵投射物命中"""
        for proj in minion.projectiles[:]:
            if not proj.alive:
                continue
            pr = proj.get_rect()

            # 命中敌方主角
            if enemy and hasattr(enemy, 'health') and enemy.health > 0:
                er = enemy.get_hurtbox_rect()
                if _rects_overlap(pr, er):
                    enemy.take_minion_damage(proj.damage, self.owner_id)
                    proj.alive = False
                    continue

            # 命中敌方小兵
            for em in enemy_minions:
                if not em.alive:
                    continue
                mr = em.get_hurtbox()
                if _rects_overlap(pr, mr):
                    em.take_damage(proj.damage)
                    proj.alive = False
                    if not em.alive:
                        self.coins += COIN_PER_MINION_KILL
                    break

    def try_summon(self, owner_x: float, owner_y: float) -> bool:
        """尝试召唤一个小兵，返回是否成功"""
        if self.coins < MINION_COST:
            return False
        self.coins -= MINION_COST

        # 在主人旁边生成，稍微偏移避免重叠
        offset = len(self.minions) * 20 - 40
        spawn_x = owner_x + offset
        spawn_y = owner_y
        minion = create_minion(self.char_name, spawn_x, spawn_y, self.owner_id)
        minion.stage = self.stage
        self.minions.append(minion)
        return True

    def toggle_mode(self):
        """切换冲锋/跟随模式"""
        self.mode = "follow" if self.mode == "charge" else "charge"
        return self.mode

    def on_enemy_minion_killed(self):
        """击杀敌方小兵时调用"""
        self.coins += COIN_PER_MINION_KILL

    def draw(self, surface: pygame.Surface):
        """绘制所有小兵"""
        for minion in self.minions:
            minion.draw(surface)

    def draw_hud(self, surface: pygame.Surface, hud_x: int, hud_y: int,
                 is_player1: bool, font: pygame.font.Font):
        """绘制金币HUD（血条旁边）"""
        # 金币图标（金色圆形）
        icon_r = 9
        icon_x = hud_x + icon_r
        icon_y = hud_y + icon_r

        pygame.draw.circle(surface, (200, 160, 20), (icon_x, icon_y), icon_r)
        pygame.draw.circle(surface, (255, 220, 60), (icon_x, icon_y), icon_r, 2)
        # 金币上的"¥"或"$"符号
        coin_sym = font.render("G", True, (80, 50, 0))
        sym_rect = coin_sym.get_rect(center=(icon_x, icon_y))
        surface.blit(coin_sym, sym_rect)

        # 数量
        coin_text = font.render(f"{self.coin_int}", True, (255, 220, 60))
        if is_player1:
            surface.blit(coin_text, (icon_x + icon_r + 4, hud_y))
        else:
            surface.blit(coin_text, (hud_x - coin_text.get_width() - icon_r * 2 - 4, hud_y))

        # 小兵数量
        minion_count = len(self.minions)
        if minion_count > 0:
            mode_icon = "⚔" if self.mode == "charge" else "↩"
            count_text = font.render(f"x{minion_count} {mode_icon}", True, (200, 200, 255))
            if is_player1:
                surface.blit(count_text, (icon_x + icon_r + 4, hud_y + 14))
            else:
                surface.blit(count_text, (hud_x - count_text.get_width() - icon_r * 2 - 4, hud_y + 14))

        # 费用提示（金币不足时变红）
        cost_color = (255, 80, 80) if self.coin_int < MINION_COST else (150, 150, 150)
        cost_text = font.render(f"U:{MINION_COST}G", True, cost_color)
        if is_player1:
            surface.blit(cost_text, (icon_x + icon_r + 4, hud_y + 28))
        else:
            surface.blit(cost_text, (hud_x - cost_text.get_width() - icon_r * 2 - 4, hud_y + 28))


def _rects_overlap(r1, r2) -> bool:
    """检查两个矩形是否重叠"""
    return (r1[0] < r2[0] + r2[2] and r1[0] + r1[2] > r2[0] and
            r1[1] < r2[1] + r2[3] and r1[1] + r1[3] > r2[1])
