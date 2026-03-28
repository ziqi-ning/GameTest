# 连招系统

from typing import List, Tuple

class ComboSystem:
    """连击管理系统"""

    def __init__(self):
        self.combo_count = 0
        self.combo_timer = 0.0
        self.combo_window = 1.5  # 连击判定时间窗口（秒）
        self.max_combo = 30
        self.damage_dealt = 0

        # 连击历史
        self.hit_history: List[Tuple[float, int, str]] = []  # (时间, 伤害, 攻击类型)

    def register_hit(self, damage: int, attack_type: str = "light") -> int:
        """记录一次命中，返回当前连击数"""
        self.combo_count += 1
        self.combo_timer = self.combo_window
        self.damage_dealt += damage

        # 记录命中历史
        self.hit_history.append((self.combo_timer, damage, attack_type))

        # 保持历史在合理范围
        if len(self.hit_history) > 50:
            self.hit_history.pop(0)

        return self.combo_count

    def update(self, dt: float) -> None:
        """每帧更新连击计时器"""
        if self.combo_timer > 0:
            self.combo_timer -= dt
            if self.combo_timer <= 0:
                self.reset()

    def reset(self) -> None:
        """重置连击"""
        self.combo_count = 0
        self.damage_dealt = 0
        self.hit_history.clear()

    def is_combo_active(self) -> bool:
        """检查连击是否有效"""
        return self.combo_count > 0 and self.combo_timer > 0

    def get_combo_multiplier(self) -> float:
        """获取连击伤害倍率"""
        if self.combo_count <= 1:
            return 1.0
        # 连击越多，后续伤害衰减
        return max(0.5, 1.0 - (self.combo_count - 1) * 0.05)

    def get_combo_text(self) -> str:
        """获取连击显示文本"""
        if self.combo_count <= 1:
            return ""
        return f"{self.combo_count} HIT!"

    def get_max_hit_combo(self) -> int:
        """获取最大连击数"""
        return self.max_combo if self.combo_count > self.max_combo else self.combo_count


class HitboxManager:
    """攻击判定盒管理器"""

    def __init__(self):
        self.active_hitboxes: List = []
        self.hit_history: List = []  # 记录命中历史

    def create_hitbox(self, x: float, y: float, width: float, height: float,
                      damage: int, hitstun: int, knockback: float,
                      knockback_up: float = 0, attack_type: str = "light",
                      owner_id: int = 0) -> None:
        """创建攻击判定盒"""
        from utils.geometry import Hitbox
        hitbox = Hitbox(x, y, width, height, damage, hitstun, knockback, attack_type)
        hitbox.owner_id = owner_id
        hitbox.knockback_up = knockback_up
        self.active_hitboxes.append(hitbox)

    def check_collision(self, hurtbox_rect: Tuple[float, float, float, float],
                       target_id: int, can_block: bool = True) -> Tuple[bool, object]:
        """检查与受击判定盒的碰撞"""
        for hitbox in self.active_hitboxes:
            if not hitbox.active:
                continue
            if hitbox.can_hit(target_id):
                # 矩形碰撞检测
                if self._rects_intersect(hitbox, hurtbox_rect):
                    return True, hitbox
        return False, None

    def _rects_intersect(self, rect1, rect2: Tuple) -> bool:
        """矩形碰撞检测"""
        return (rect1.x < rect2[0] + rect2[2] and
                rect1.x + rect1.width > rect2[0] and
                rect1.y < rect2[1] + rect2[3] and
                rect1.y + rect1.height > rect2[1])

    def remove_hitbox(self, hitbox) -> None:
        """移除攻击判定盒"""
        if hitbox in self.active_hitboxes:
            self.active_hitboxes.remove(hitbox)

    def clear(self) -> None:
        """清除所有攻击判定盒"""
        self.active_hitboxes.clear()

    def update(self) -> None:
        """更新攻击判定盒（移除已过期的）"""
        self.active_hitboxes = [hb for hb in self.active_hitboxes if hb.active]

    def get_hitboxes_for_owner(self, owner_id: int) -> List:
        """获取属于指定所有者的攻击判定盒"""
        return [hb for hb in self.active_hitboxes if hb.owner_id == owner_id]
