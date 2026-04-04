# AI Fighter - 智能AI控制系统
# 采用局势评估 + 对手建模 + 分层决策的架构
# 实现真正的"随机应变"和"有策略"行为

import random
import math
from typing import Optional, List, Dict, Tuple
from entities.fighter import Fighter
from config import GROUND_Y
from constants import FighterState, Direction
from game.state_machine import AnimationState


# ── 全局常量 ────────────────────────────────────────────────────────────────

EDGE_DANGER_ZONE = 200
SCREEN_LEFT = 60
SCREEN_RIGHT = 1220
SCREEN_CENTER = (SCREEN_LEFT + SCREEN_RIGHT) / 2
ARENA_WIDTH = SCREEN_RIGHT - SCREEN_LEFT


# ══════════════════════════════════════════════════════════════════════════════
# 第一层：局势评估系统（Situation Assessment）
# ══════════════════════════════════════════════════════════════════════════════

class SituationAssessment:
    """对当前战斗局势的全面评估"""

    def __init__(self, ai: 'AIFighter', opponent: Fighter, dt: float):
        self.ai = ai
        self.opponent = opponent
        self.dt = dt

        # 基础数据
        self.distance = abs(ai.x - opponent.x)
        self.health_gap = ai.health - opponent.health  # 正=AI占优
        self.health_ratio = ai.health / max(1, ai.max_health)
        self.opp_health_ratio = opponent.health / max(1, opponent.max_health)
        self.energy_ratio = ai.special_energy / max(1, ai.max_special)

        # 高度差（正=AI在上方）
        self.height_diff = ai.y - opponent.y

        # 时间压力
        self.ai_pressure_timer = getattr(ai, '_pressure_timer', 0.0)  # AI被压制多久了
        self.opp_pressure_timer = getattr(opponent, '_pressure_timer', 0.0)

        # 局势倾向
        self.ai_advantage = self._calc_advantage()

    def _calc_advantage(self) -> float:
        """计算AI的整体优势程度 [-1, 1]，正=AI优势"""
        ai_score = 0.0
        opp_score = 0.0

        # 血量优势（权重40%）
        health_weight = 0.4
        ai_score += self.health_ratio * health_weight
        opp_score += self.opp_health_ratio * health_weight

        # 能量优势（权重20%）
        energy_weight = 0.2
        ai_score += self.energy_ratio * energy_weight
        opp_score += (self.opponent.special_energy / max(1, self.opponent.max_special)) * energy_weight

        # 位置优势（权重20%）：靠近中央更安全
        pos_weight = 0.2
        ai_center_dist = abs(self.ai.x - SCREEN_CENTER) / (ARENA_WIDTH / 2)
        opp_center_dist = abs(self.opponent.x - SCREEN_CENTER) / (ARENA_WIDTH / 2)
        ai_score += (1 - ai_center_dist) * pos_weight
        opp_score += (1 - opp_center_dist) * pos_weight

        # 高度优势（权重10%）
        height_weight = 0.1
        if self.height_diff > 50:
            ai_score += height_weight
        elif self.height_diff < -50:
            opp_score += height_weight

        # 状态优势（权重10%）
        state_weight = 0.1
        if not self.ai.is_attacking and self.ai.hitstun_timer <= 0:
            ai_score += state_weight
        if not self.opponent.is_attacking and self.opponent.hitstun_timer <= 0:
            opp_score += state_weight

        total = ai_score + opp_score
        if total == 0:
            return 0.0
        return (ai_score - opp_score) / total  # 归一化到[-1, 1]

    def get_tactical_posture(self) -> str:
        """根据局势确定战术姿态"""
        adv = self.ai_advantage

        # 极端劣势 → 拼命
        if adv < -0.4 and self.health_ratio < 0.3:
            return "desperate"

        # 明显劣势 → 保守/反击
        if adv < -0.2:
            return "defensive"

        # 轻微劣势或均势 → 稳健
        if adv < 0.15:
            return "balanced"

        # 轻微优势 → 进取
        if adv < 0.4:
            return "aggressive"

        # 明显优势 → 压制
        return "dominant"

    def is_safe_to_approach(self) -> bool:
        """评估是否安全接近对手"""
        # 对手正在攻击且距离近 → 不安全
        if self.opponent.is_attacking and self.distance < 180:
            return False
        # 对手有高能量大招 → 不安全
        if self.opponent.special_energy >= self.opponent.max_special * 0.8:
            return False
        # AI自己血量低且对手在攻击 → 不安全
        if self.health_ratio < 0.3 and self.opponent.is_attacking:
            return False
        return True

    def should_retreat(self) -> bool:
        """是否应该战略性后撤"""
        # 血量很低
        if self.health_ratio < 0.2:
            return True
        # 被逼到边缘且对手逼近
        if (self.ai.x < SCREEN_LEFT + EDGE_DANGER_ZONE or
            self.ai.x > SCREEN_RIGHT - EDGE_DANGER_ZONE) and \
           self.opponent.x > self.ai.x:
            return self.ai.x < SCREEN_CENTER
        return False

    def get_engagement_urgency(self) -> float:
        """获取交战紧迫度 [0, 1]，越高越需要快速行动"""
        urgency = 0.0

        # 对手残血 → 高紧迫（收割）
        if self.opp_health_ratio < 0.25:
            urgency += 0.4
        elif self.opp_health_ratio < 0.5:
            urgency += 0.2

        # AI血量危险 → 高紧迫（需要决策）
        if self.health_ratio < 0.2:
            urgency += 0.3
        elif self.health_ratio < 0.4:
            urgency += 0.15

        # 对手正在攻击 → 中紧迫
        if self.opponent.is_attacking:
            urgency += 0.2

        # 对手有充能大招 → 高紧迫
        if self.opponent.special_energy >= self.opponent.max_special * 0.7:
            urgency += 0.15

        # 时间压力累积
        pressure = getattr(self.ai, '_pressure_timer', 0.0)
        if pressure > 2.0:
            urgency += min(0.3, (pressure - 2.0) * 0.1)

        return min(1.0, urgency)


# ══════════════════════════════════════════════════════════════════════════════
# 第二层：对手行为建模（Opponent Model）
# ══════════════════════════════════════════════════════════════════════════════

class OpponentModel:
    """对对手行为习惯的建模和学习"""

    def __init__(self):
        # 行为统计
        self.attack_frequency = 0.0       # 攻击频率（次/秒）
        self.attack_count = 0             # 总攻击次数
        self.attack_timestamps: List[float] = []  # 攻击时间戳
        self.heavy_attack_ratio = 0.0     # 重攻击比例
        self.heavy_attack_count = 0

        # 偏好分析
        self.prefers_ranged = False       # 是否偏好远程
        self.prefers_melee = False        # 是否偏好近战
        self.uses_jumps_aggressively = False  # 是否激进跳跃
        self.uses_blocking = False        # 是否经常防御

        # 习惯记录
        self.recent_attacks: List[Dict] = []  # 最近攻击记录
        self.last_attack_time = 0.0
        self.last_attack_type = ""        # "light", "heavy", "special"
        self.attack_pattern: List[str] = []  # 攻击模式序列
        self.pattern_window = 5           # 用于检测模式的窗口大小

        # 预测
        self.opponent_in_attack_startup = False  # 对手是否在攻击前摇
        self.predicted_next_attack = ""    # 预测的下次攻击类型

        # 危险评估
        self.opponent_threatening = False  # 对手当前是否有威胁

    def record_attack(self, attack_type: str, current_time: float):
        """记录一次攻击"""
        self.last_attack_time = current_time
        self.last_attack_type = attack_type
        self.attack_count += 1

        if attack_type == "heavy":
            self.heavy_attack_count += 1

        self.attack_timestamps.append(current_time)

        # 清理旧记录（保留最近5秒）
        cutoff = current_time - 5.0
        self.attack_timestamps = [t for t in self.attack_timestamps if t > cutoff]

        # 更新攻击频率（最近5秒内）
        if len(self.attack_timestamps) > 1:
            time_span = self.attack_timestamps[-1] - self.attack_timestamps[0]
            if time_span > 0:
                self.attack_frequency = len(self.attack_timestamps) / time_span

        # 更新重攻击比例
        if self.attack_count > 0:
            self.heavy_attack_ratio = self.heavy_attack_count / self.attack_count

        # 记录模式
        self.attack_pattern.append(attack_type)
        if len(self.attack_pattern) > self.pattern_window:
            self.attack_pattern.pop(0)

        # 分析偏好
        self._analyze_preferences()

    def _analyze_preferences(self):
        """分析对手偏好"""
        if self.attack_count < 3:
            return

        # 检测远程偏好（基于重攻击）
        self.prefers_ranged = self.heavy_attack_ratio > 0.4
        self.prefers_melee = self.heavy_attack_ratio < 0.3

        # 检测激进跳跃（攻击序列中是否有跳
        # 攻击模式分析：连续攻击=激进
        if len(self.attack_pattern) >= 3:
            consecutive = 1
            for i in range(1, len(self.attack_pattern)):
                if self.attack_pattern[i] == self.attack_pattern[i-1]:
                    consecutive += 1
            self.uses_jumps_aggressively = consecutive >= 3

    def update_threat(self, opponent: Fighter, distance: float, dt: float):
        """更新威胁评估"""
        # 对手正在攻击前摇
        if opponent.is_attacking:
            self.opponent_in_attack_startup = True
        else:
            self.opponent_in_attack_startup = False

        # 对手整体威胁
        self.opponent_threatening = (
            opponent.is_attacking and distance < 200
        ) or (
            opponent.special_energy >= opponent.max_special * 0.8
        )

    def predict_next_attack(self, distance: float, health_ratio: float) -> str:
        """预测对手的下次攻击"""
        if self.attack_count < 2:
            return "unknown"

        # 检测连续攻击模式
        if len(self.attack_pattern) >= 2:
            last_two = self.attack_pattern[-2:]
            if last_two[0] == last_two[1]:
                # 连续同类型攻击
                return last_two[0]

        # 根据距离预测
        if distance > 300:
            return "heavy" if self.prefers_ranged else "light"
        elif distance < 100:
            return "light"

        return self.last_attack_type or "light"

    def get_parry_opportunity(self, predicted_attack: str) -> float:
        """根据预测返回格挡机会 [0, 1]"""
        if predicted_attack == "heavy":
            return 0.7  # 重攻击值得格挡
        elif predicted_attack == "special":
            return 0.9  # 必杀技必须格挡
        return 0.3


# ══════════════════════════════════════════════════════════════════════════════
# 第三层：战术决策引擎（Tactical Decision Engine）
# ══════════════════════════════════════════════════════════════════════════════

class TacticalDecision:
    """战术决策 - 决定AI要做什么"""

    # 决策类型优先级（数字越小优先级越高）
    PRIORITY_EMERGENCY = 1      # 紧急：必须立即响应
    PRIORITY_SURVIVAL = 2        # 生存：保命优先
    PRIORITY_TACTICAL = 3       # 战术：策略性行动
    PRIORITY_OPPORTUNISTIC = 4  # 机会：见机行事
    PRIORITY_PRESERVATION = 5   # 保守：稳定局势

    def __init__(self, decision_type: str, priority: int,
                 confidence: float, reason: str, action_params: dict = None):
        self.decision_type = decision_type  # "attack", "defend", "retreat", "buff", etc.
        self.priority = priority
        self.confidence = confidence  # 决策置信度 [0, 1]
        self.reason = reason
        self.action_params = action_params or {}

    def __lt__(self, other):
        return self.priority < other.priority


class TacticalEngine:
    """战术决策引擎 - 生成并优先排序所有可能的行动"""

    PRIORITY_EMERGENCY = 1       # 紧急：必须立即响应
    PRIORITY_SURVIVAL = 2        # 生存：保命优先
    PRIORITY_TACTICAL = 3        # 战术：策略性行动
    PRIORITY_OPPORTUNISTIC = 4   # 机会：见机行事
    PRIORITY_PRESERVATION = 5    # 保守：稳定局势

    def __init__(self, ai: 'AIFighter', opponent: Fighter,
                 situation: SituationAssessment, model: OpponentModel,
                 current_time: float, dt: float):
        self.ai = ai
        self.opponent = opponent
        self.situation = situation
        self.model = model
        self.current_time = current_time
        self.dt = dt
        self.distance = situation.distance

        self.decisions: List[TacticalDecision] = []

    def generate_all_options(self) -> List[TacticalDecision]:
        """生成所有可能的战术选项"""
        self.decisions = []

        # 1. 紧急情况检查
        self._check_emergency()

        # 2. 生存检查
        self._check_survival()

        # 3. 战术机会检查
        self._check_tactical_opportunities()

        # 4. 资源利用检查
        self._check_resource_utilization()

        # 5. 位置调整检查
        self._check_positioning()

        # 按优先级排序
        self.decisions.sort()
        return self.decisions

    def _check_emergency(self):
        """紧急情况：必须立即响应"""
        opp = self.opponent

        # 对手正在攻击且靠近
        if opp.is_attacking and self.distance < 150:
            # 预测攻击类型
            predicted = self.model.predict_next_attack(self.distance, opp.health / opp.max_health)

            # 根据预测决定反应
            if predicted == "special":
                # 必杀技：必须防御或闪避
                parry_chance = self.model.get_parry_opportunity("special")
                if parry_chance > 0.7 and self.ai.on_ground:
                    self.decisions.append(TacticalDecision(
                        "defend",
                        self.PRIORITY_EMERGENCY,
                        parry_chance,
                        f"对手释放{predicted}！必须防御",
                        {"blocking": True, "duration": 0.5}
                    ))
                # 否则尝试跳跃躲避
                if self.ai.on_ground and self.ai.stats.jump_force > 0:
                    self.decisions.append(TacticalDecision(
                        "evade_jump",
                        self.PRIORITY_EMERGENCY,
                        0.8,
                        f"躲避{predicted}，跳！",
                        {"jump": True}
                    ))

            elif predicted == "heavy":
                # 重攻击：格挡或后退
                if self.ai.on_ground and self.ai.health > opp.health:
                    self.decisions.append(TacticalDecision(
                        "defend",
                        self.PRIORITY_EMERGENCY,
                        0.65,
                        "预判重攻击，防御！",
                        {"blocking": True, "duration": 0.3}
                    ))
                else:
                    self.decisions.append(TacticalDecision(
                        "evade_backward",
                        self.PRIORITY_EMERGENCY,
                        0.6,
                        "躲避重攻击，后撤",
                        {"back_distance": 80}
                    ))

            else:
                # 轻攻击：看情况防御或迎击
                if self.ai.health_ratio > 0.5:
                    # 血量健康可以选择对攻
                    self.decisions.append(TacticalDecision(
                        "counter_attack",
                        self.PRIORITY_EMERGENCY,
                        0.5,
                        "对攻！",
                        {"attack_type": "light"}
                    ))
                else:
                    self.decisions.append(TacticalDecision(
                        "defend",
                        self.PRIORITY_EMERGENCY,
                        0.6,
                        "保守防御",
                        {"blocking": True, "duration": 0.2}
                    ))

        # AI自己被击中后的硬直中
        if self.ai.hitstun_timer > 0:
            # 无事可做
            self.decisions.append(TacticalDecision(
                "recover",
                self.PRIORITY_EMERGENCY,
                1.0,
                "硬直中，等待恢复",
                {}
            ))

    def _check_survival(self):
        """生存检查：保命优先"""
        # AI血量危急
        if self.situation.health_ratio < 0.25:
            # 寻找治疗道具
            self.decisions.append(TacticalDecision(
                "seek_healing",
                self.PRIORITY_SURVIVAL,
                0.9,
                "血量危急，寻找治疗！",
                {"healing_only": True}
            ))

            # 如果有增益技能且能回血
            if self.ai._can_use_buff():
                move = self.ai.char_data.special[1]
                if hasattr(move, 'effect_type') and 'lifesteal' in move.effect_type:
                    self.decisions.append(TacticalDecision(
                        "use_buff",
                        self.PRIORITY_SURVIVAL,
                        0.85,
                        "激活吸血效果！",
                        {"move_index": 1}
                    ))

        # 被逼到边缘
        if self.ai.x < SCREEN_LEFT + EDGE_DANGER_ZONE or \
           self.ai.x > SCREEN_RIGHT - EDGE_DANGER_ZONE:
            escape_dir = 1 if self.ai.x < SCREEN_CENTER else -1
            self.decisions.append(TacticalDecision(
                "edge_escape",
                self.PRIORITY_SURVIVAL,
                0.85,
                "逃离边缘！",
                {"direction": escape_dir, "urgency": 0.9}
            ))

        # 对手有充能大招
        if self.opponent.special_energy >= self.opponent.max_special * 0.8:
            if self.situation.health_ratio < 0.5:
                self.decisions.append(TacticalDecision(
                    "avoid_finisher",
                    self.PRIORITY_SURVIVAL,
                    0.75,
                    "对手充能完毕，保持距离！",
                    {"min_distance": 200}
                ))

    def _check_tactical_opportunities(self):
        """战术机会检查"""
        opp = self.opponent
        posture = self.situation.get_tactical_posture()

        # 对手被控制（眩晕/冻结）→ 趁机攻击
        if opp.stun_timer > 0 or opp.freeze_timer > 0:
            self.decisions.append(TacticalDecision(
                "punish",
                self.PRIORITY_TACTICAL,
                0.95,
                "对手被控制！惩罚性攻击！",
                {"attack_type": "special" if self.situation.energy_ratio > 0.3 else "heavy"}
            ))

        # 对手残血 → 收割
        if self.situation.opp_health_ratio < 0.3:
            urgency = 1.0 - self.situation.opp_health_ratio
            self.decisions.append(TacticalDecision(
                "finisher",
                self.PRIORITY_TACTICAL,
                0.9 * urgency,
                "收割！",
                {"attack_type": "special" if self.situation.energy_ratio > 0.2 else "heavy"}
            ))

        # 对手在攻击后摇 → 惩罚
        if not opp.is_attacking and opp.attack_cooldown > 0.3:
            self.decisions.append(TacticalDecision(
                "punish_whiff",
                self.PRIORITY_TACTICAL,
                0.7,
                "对手攻击落空，惩罚！",
                {"attack_type": "light"}
            ))

        # AI血量优势明显且有能量 → 强势压制
        if posture in ("aggressive", "dominant") and self.situation.energy_ratio > 0.3:
            self.decisions.append(TacticalDecision(
                "pressure",
                self.PRIORITY_TACTICAL,
                0.75,
                "乘胜追击！",
                {"approach": True, "attack": True}
            ))

        # 对手远离且AI能量充足 → 远程消耗
        if self.distance > 250 and self.situation.energy_ratio > 0.5:
            if hasattr(self.ai.char_data, 'moves') and len(self.ai.char_data.moves) > 1:
                move = self.ai.char_data.moves[1]
                if getattr(move, 'is_ranged', False):
                    self.decisions.append(TacticalDecision(
                        "poke",
                        self.PRIORITY_OPPORTUNISTIC,
                        0.6,
                        "远程消耗",
                        {"attack_type": "heavy"}
                    ))

    def _check_resource_utilization(self):
        """资源利用检查"""
        # 能量充足 → 使用增益技能
        if self.situation.energy_ratio > 0.8 and self.ai._can_use_buff():
            self.decisions.append(TacticalDecision(
                "buff",
                self.PRIORITY_TACTICAL,
                0.7,
                "能量充足，激活增益！",
                {"move_index": 1}
            ))

        # 大招可用且时机合适
        if self.ai._should_use_ultimate(self.opponent, self.distance):
            self.decisions.append(TacticalDecision(
                "ultimate",
                self.PRIORITY_TACTICAL,
                0.85,
                "释放大招！",
                {"move_index": 0}
            ))

        # 有武器且有机会
        if self.ai.equipped_weapon and self.ai.weapon_uses > 0:
            if self.distance < 180 and not self.opponent.is_attacking:
                self.decisions.append(TacticalDecision(
                    "weapon_attack",
                    self.PRIORITY_OPPORTUNISTIC,
                    0.65,
                    "使用武器！",
                    {}
                ))

    def _check_positioning(self):
        """位置调整检查"""
        # 需要跳上平台追击
        if self.situation.height_diff > 80 and self.ai.on_ground:
            self.decisions.append(TacticalDecision(
                "platform_jump",
                self.PRIORITY_TACTICAL,
                0.7,
                "跳上平台追击！",
                {"jump": True}
            ))

        # 对手在平台上需要跳上去
        if self.situation.height_diff < -80 and self.ai.on_ground:
            if self.distance < 200:
                self.decisions.append(TacticalDecision(
                    "chase_platform",
                    self.PRIORITY_TACTICAL,
                    0.65,
                    "跳下追击！",
                    {"jump": True}
                ))

        # 距离太远需要接近
        if self.distance > 350:
            self.decisions.append(TacticalDecision(
                "approach",
                self.PRIORITY_TACTICAL,
                0.6,
                "需要接近对手",
                {"approach": True}
            ))

    def select_best_action(self) -> Optional[TacticalDecision]:
        """选择最佳行动"""
        if not self.decisions:
            return None

        # 找最高优先级且置信度足够的
        for decision in self.decisions:
            if decision.confidence >= 0.5:
                return decision

        # 如果没有高置信度决策，选择次优
        if self.decisions:
            return self.decisions[0]
        return None


# ══════════════════════════════════════════════════════════════════════════════
# 第四层：行动执行器（Action Executor）
# ══════════════════════════════════════════════════════════════════════════════

class ActionExecutor:
    """将战术决策转化为具体的游戏动作"""

    def __init__(self, ai: 'AIFighter', opponent: Fighter, dt: float):
        self.ai = ai
        self.opponent = opponent
        self.dt = dt
        self.distance = abs(ai.x - opponent.x)

    def execute(self, decision: TacticalDecision) -> bool:
        """执行战术决策，返回是否成功执行了攻击"""
        d_type = decision.decision_type

        # 防御类
        if d_type == "defend":
            self._execute_defend(decision)
            return False

        # 移动类
        elif d_type == "evade_backward":
            self._execute_evade_backward(decision)
            return False
        elif d_type == "evade_jump":
            self._execute_evade_jump()
            return False
        elif d_type == "edge_escape":
            self._execute_edge_escape(decision)
            return False
        elif d_type == "approach":
            self._execute_approach()
            return False

        # 攻击类
        elif d_type == "counter_attack":
            return self._execute_counter_attack(decision)
        elif d_type == "punish":
            return self._execute_punish(decision)
        elif d_type == "punish_whiff":
            return self._execute_punish_whiff(decision)
        elif d_type == "finisher":
            return self._execute_finisher(decision)
        elif d_type == "pressure":
            return self._execute_pressure(decision)
        elif d_type == "poke":
            return self._execute_poke(decision)
        elif d_type == "ultimate":
            return self._execute_ultimate(decision)

        # 增益类
        elif d_type == "buff":
            self._execute_buff(decision)
            return False
        elif d_type == "weapon_attack":
            return self._execute_weapon_attack()

        # 特殊类
        elif d_type == "seek_healing":
            self._execute_seek_healing(decision)
            return False
        elif d_type == "platform_jump":
            self._execute_platform_jump()
            return False
        elif d_type == "chase_platform":
            self._execute_platform_jump()
            return False
        elif d_type == "recover":
            # 硬直中什么都不做
            return False

        return False

    def _execute_defend(self, decision: TacticalDecision):
        """执行防御"""
        self.ai.apply_movement(False, False, False, False, True)
        self.ai.is_blocking = True

    def _execute_evade_backward(self, decision: TacticalDecision):
        """执行后撤闪避"""
        back_dist = decision.action_params.get("back_distance", 80)
        # 朝远离对手方向移动
        if self.opponent.x > self.ai.x:
            self.ai.apply_movement(True, False, False, False, False)  # 左移
        else:
            self.ai.apply_movement(False, True, False, False, False)  # 右移

    def _execute_evade_jump(self):
        """执行跳跃闪避"""
        if self.ai.on_ground:
            self.ai._do_jump()
            # 空中可以稍微移动
            if self.opponent.x > self.ai.x:
                self.ai.vel_x = -self.ai.stats.walk_speed * 0.5
            else:
                self.ai.vel_x = self.ai.stats.walk_speed * 0.5

    def _execute_edge_escape(self, decision: TacticalDecision):
        """逃离边缘"""
        direction = decision.action_params.get("direction", 1)
        urgency = decision.action_params.get("urgency", 0.8)

        # 朝中央移动
        if direction > 0:
            self.ai.apply_movement(False, True, False, False, False)
        else:
            self.ai.apply_movement(True, False, False, False, False)

        # 紧急时跳跃
        if urgency > 0.7 and self.ai.on_ground and random.random() < 0.5:
            self.ai._do_jump()

    def _execute_approach(self):
        """接近对手"""
        if self.opponent.x > self.ai.x:
            self.ai.apply_movement(False, True, False, False, False)
        else:
            self.ai.apply_movement(True, False, False, False, False)

        # 接近时考虑跳跃
        if self.ai.on_ground and random.random() < 0.1:
            self.ai._do_jump()

    def _execute_counter_attack(self, decision: TacticalDecision) -> bool:
        """对攻"""
        attack_type = decision.action_params.get("attack_type", "light")
        if self.ai.attack_cooldown <= 0:
            if attack_type == "light":
                self.ai.attack_light()
            else:
                self.ai.attack_heavy()
            return True
        return False

    def _execute_punish(self, decision: TacticalDecision) -> bool:
        """惩罚性攻击（对手被控制时）"""
        attack_type = decision.action_params.get("attack_type", "light")
        if self.ai.attack_cooldown <= 0 and self.ai.hitstun_timer <= 0:
            if attack_type == "special":
                self.ai.attack_special(self.dt, move_index=0)
            elif attack_type == "heavy":
                self.ai.attack_heavy()
            else:
                self.ai.attack_light()
            return True
        return False

    def _execute_punish_whiff(self, decision: TacticalDecision) -> bool:
        """惩罚对手攻击落空"""
        if self.distance < 150 and self.ai.attack_cooldown <= 0:
            self.ai.attack_light()
            return True
        elif self.distance >= 150 and self.ai._can_use_ranged():
            self.ai.attack_heavy()
            return True
        return False

    def _execute_finisher(self, decision: TacticalDecision) -> bool:
        """收割攻击"""
        attack_type = decision.action_params.get("attack_type", "heavy")

        if attack_type == "special" and self.ai._can_use_ultimate():
            self.ai.attack_special(self.dt, move_index=0)
            return True
        elif self.distance < 120:
            if self.ai.attack_cooldown <= 0:
                self.ai.attack_light()
                return True
        else:
            # 接近然后重攻击
            self._execute_approach()
            if self.distance < 150 and self.ai.attack_cooldown <= 0:
                self.ai.attack_heavy()
                return True
        return False

    def _execute_pressure(self, decision: TacticalDecision) -> bool:
        """压制性进攻"""
        # 接近并攻击
        self._execute_approach()

        if self.distance < 120 and self.ai.attack_cooldown <= 0:
            # 选择攻击类型
            if random.random() < 0.6:
                self.ai.attack_light()
            else:
                self.ai.attack_heavy()
            return True
        return False

    def _execute_poke(self, decision: TacticalDecision) -> bool:
        """远程消耗"""
        attack_type = decision.action_params.get("attack_type", "heavy")
        if self.ai._can_use_ranged() and self.ai.attack_cooldown <= 0:
            self.ai.attack_heavy()
            return True
        return False

    def _execute_ultimate(self, decision: TacticalDecision) -> bool:
        """释放大招"""
        if self.ai._should_use_ultimate(self.opponent, self.distance):
            self.ai.attack_special(self.dt, move_index=0)
            return True
        return False

    def _execute_buff(self, decision: TacticalDecision):
        """使用增益"""
        move_index = decision.action_params.get("move_index", 1)
        self.ai.attack_special(self.dt, move_index=move_index)
        self.ai.buff_cooldown = 3.0

    def _execute_weapon_attack(self) -> bool:
        """武器攻击"""
        if self.ai.equipped_weapon and self.ai.weapon_uses > 0:
            self.ai.attack_weapon()
            self.ai.weapon_cooldown = 2.0
            return True
        return False

    def _execute_seek_healing(self, decision: TacticalDecision):
        """寻找治疗"""
        # 如果AI正在追踪道具，优先移动到道具位置
        if hasattr(self.ai, '_healing_target') and self.ai._healing_target:
            item = self.ai._healing_target
            if item.active and item.landed:
                if item.x > self.ai.x:
                    self.ai.apply_movement(False, True, False, False, False)
                else:
                    self.ai.apply_movement(True, False, False, False, False)
                return

        # 否则寻找最近的回血道具
        if self.ai.item_manager:
            nearest = self.ai._get_nearest_item(self.ai.item_manager)
            if nearest:
                self.ai._healing_target = nearest
                is_health = nearest.item_type == "health_bag"
                urgency = self.ai.health < self.ai.max_health * 0.3

                if urgency or is_health:
                    if nearest.x > self.ai.x:
                        self.ai.apply_movement(False, True, False, False, False)
                    else:
                        self.ai.apply_movement(True, False, False, False, False)

                    if self.ai.on_ground and self.ai._should_jump_for_item(nearest):
                        self.ai._do_jump()

    def _execute_platform_jump(self):
        """跳上/下平台"""
        if self.ai.on_ground:
            self.ai._do_jump()


# ══════════════════════════════════════════════════════════════════════════════
# 主AI类：AIFighter
# ══════════════════════════════════════════════════════════════════════════════

class AIFighter(Fighter):
    """智能AI控制的角色 - 基于局势评估和对手建模"""

    def __init__(self, player_id: int, char_data, x: float, y: float,
                 char_index: int = 0, difficulty: str = "normal", stage=None,
                 item_manager=None):
        super().__init__(player_id, char_data, x, y, char_index, stage=stage)

        self.is_human = False
        self.difficulty = difficulty

        # ── 个性化参数（根据难度调整）─────────────────────────────
        self.aggression = self._get_aggression(difficulty)
        self.reaction_time = self._get_reaction_time(difficulty)
        self.defense_skill = self._get_defense_skill(difficulty)
        self.adaptability = self._get_adaptability(difficulty)

        # ── 状态追踪 ──────────────────────────────────────────────
        self.reaction_timer = 0.0
        self.ai_state = "thinking"
        self._pressure_timer = 0.0       # 被压制时间
        self._last_action = ""            # 上次行动
        self._action_streak = 0           # 连续同类行动计数
        _healing_target = None            # 当前追踪的治疗道具

        # ── 子系统初始化 ──────────────────────────────────────────
        self.opponent_model = OpponentModel()

        # ── 冷却管理 ──────────────────────────────────────────────
        self.buff_cooldown = 0.0
        self.weapon_cooldown = 0.0
        self.item_seek_cooldown = 0.0
        self.ranged_attack_streak = 0
        self.ranged_attack_streak_max = 2

        # ── 道具系统 ──────────────────────────────────────────────
        self.item_manager = item_manager

        # ── 行为多样性 ─────────────────────────────────────────────
        self.creative_seed = random.random()  # 个性化随机种子
        self.style_preference = self._determine_style_preference()

    def _get_aggression(self, difficulty: str) -> float:
        """获取进攻性参数"""
        base = {"easy": 0.4, "normal": 0.6, "hard": 0.8}
        return base.get(difficulty, 0.6) + (random.random() - 0.5) * 0.1

    def _get_reaction_time(self, difficulty: str) -> float:
        """获取反应时间"""
        base = {"easy": 0.3, "normal": 0.15, "hard": 0.08}
        return base.get(difficulty, 0.15)

    def _get_defense_skill(self, difficulty: str) -> float:
        """获取防御技巧"""
        return {"easy": 0.3, "normal": 0.5, "hard": 0.75}.get(difficulty, 0.5)

    def _get_adaptability(self, difficulty: str) -> float:
        """获取适应能力"""
        return {"easy": 0.3, "normal": 0.6, "hard": 0.9}.get(difficulty, 0.6)

    def _determine_style_preference(self) -> str:
        """确定AI的风格偏好"""
        styles = ["balanced", "aggressive", "defensive", "tactical"]
        weights = [0.3, 0.25, 0.2, 0.25]
        r = random.random()
        cumsum = 0
        for style, w in zip(styles, weights):
            cumsum += w
            if r < cumsum:
                return style
        return "balanced"

    # ── 道具系统 ─────────────────────────────────────────────────────────────

    def _get_nearest_item(self, item_manager) -> Optional['ItemDrop']:
        """找最近的可用道具"""
        if not item_manager or not item_manager.items:
            return None
        alive = [i for i in item_manager.items if i.active and i.landed]
        if not alive:
            return None
        nearest = min(alive, key=lambda i: abs(self.x - i.x))
        if abs(self.x - nearest.x) > 350:
            return None
        return nearest

    def _should_jump_for_item(self, item: 'ItemDrop') -> bool:
        """判断是否应该跳起来去捡道具"""
        if not item or not self.on_ground:
            return False
        if self.stage and self.stage.platforms:
            for px, py, pw, ph in self.stage.platforms:
                if px - 24 <= item.x <= px + pw + 24 and abs(item.y - py) < 20:
                    if py < self.y - 10:
                        return True
        return False

    # ── 必杀技判断 ─────────────────────────────────────────────────────────

    def _can_use_ultimate(self) -> bool:
        """判断终极技是否可用"""
        if self.is_attacking or self.hitstun_timer > 0:
            return False
        if self.ultimate_pending_trigger:
            return False
        if not self.char_data.special:
            return False
        move = self.char_data.special[0]
        return self.special_energy >= move.energy_cost

    def _can_use_buff(self) -> bool:
        """判断I键增益技能是否可用"""
        if self.buff_cooldown > 0:
            return False
        if self.is_attacking or self.hitstun_timer > 0:
            return False
        if not self.char_data.special or len(self.char_data.special) < 2:
            return False
        move = self.char_data.special[1]
        return self.special_energy >= move.energy_cost

    def _should_use_ultimate(self, opponent: Fighter, distance: float) -> bool:
        """战略级判断：该不该放大招"""
        if not self._can_use_ultimate():
            return False

        # 对手被控制 → 直接放大
        if opponent.stun_timer > 0 or opponent.freeze_timer > 0:
            return True

        # 对手血量很低 → 收割
        if opponent.health < opponent.max_health * 0.3:
            return True

        # AI自己快死了 → 搏命
        if self.health < self.max_health * 0.25:
            return True

        # 对手正在攻击且距离合适 → 打断
        if opponent.is_attacking and distance < 200:
            return True

        # 对手残血且在攻击范围内 → 贴身收割
        if opponent.health < opponent.max_health * 0.5 and distance < 100:
            return True

        return False

    # ── 远程攻击判断 ────────────────────────────────────────────────────────

    def _can_use_ranged(self) -> bool:
        """判断是否可以使用远程攻击"""
        if self.attack_cooldown > 0 or self.is_attacking or self.hitstun_timer > 0:
            return False
        if not self.char_data.moves or len(self.char_data.moves) < 2:
            return False
        move = self.char_data.moves[1]
        if not getattr(move, 'is_ranged', False):
            return False
        mana_cost = getattr(move, 'mana_cost', 0)
        if self.special_energy < mana_cost:
            return False
        if self.ranged_attack_streak >= self.ranged_attack_streak_max:
            return False
        if self.special_energy < self.max_special * 0.7:
            return False
        return True

    # ── 跳跃 ────────────────────────────────────────────────────────────────

    def _do_jump(self):
        """执行跳跃"""
        self.vel_y = -self.stats.jump_force
        self.on_ground = False
        self.y -= 5
        self.state = FighterState.JUMP
        self.animator.set_state(AnimationState.JUMP)

    def _try_random_jump(self):
        """尝试随机跳跃（增加行为多样性）"""
        if not self.on_ground or self.is_attacking or self.hitstun_timer > 0:
            return False

        # 根据风格决定跳跃倾向
        jump_chance = 0.008
        if self.style_preference == "aggressive":
            jump_chance = 0.015
        elif self.style_preference == "defensive":
            jump_chance = 0.005

        # 根据高度差增加跳跃概率
        height_diff = self.y - self.opponent_model.last_attack_time  # 复用变量名
        # 检测对手是否在高位
        if hasattr(self, '_opponent_ref') and self._opponent_ref:
            height_diff = self.y - self._opponent_ref.y
            if height_diff < -60:  # 对手在上方
                jump_chance += 0.02

        if random.random() < jump_chance:
            self._do_jump()
            return True
        return False

    # ── 小兵处理 ────────────────────────────────────────────────────────────

    def _find_nearest_enemy_minion(self, opponent: Fighter):
        """找最近的敌方小兵"""
        enemy_manager = getattr(opponent, 'minion_manager', None)
        if not enemy_manager:
            return None
        alive = [m for m in enemy_manager.minions if m.alive]
        if not alive:
            return None
        return min(alive, key=lambda m: abs(self.x - m.x))

    # ══════════════════════════════════════════════════════════════════════
    # 主更新循环
    # ══════════════════════════════════════════════════════════════════════

    def update_ai(self, dt: float, opponent: Fighter):
        """更新AI行为 - 智能决策引擎"""
        if opponent is None:
            return

        self._opponent_ref = opponent

        # 更新朝向
        self.update_direction(opponent.x)

        # ── 更新计时器 ────────────────────────────────────────────
        self.reaction_timer = max(0.0, self.reaction_timer - dt)
        self.buff_cooldown = max(0.0, self.buff_cooldown - dt)
        self.weapon_cooldown = max(0.0, self.weapon_cooldown - dt)
        self.item_seek_cooldown = max(0.0, self.item_seek_cooldown - dt)

        # 更新压力计时器
        if opponent.is_attacking and abs(self.x - opponent.x) < 200:
            self._pressure_timer += dt
        else:
            self._pressure_timer = max(0.0, self._pressure_timer - dt * 0.5)

        # 记录对手攻击
        if opponent.is_attacking and not hasattr(opponent, '_attack_recorded'):
            attack_type = "special" if getattr(opponent, 'is_special_attacking', False) else "heavy"
            if hasattr(opponent, 'current_attack') and opponent.current_attack:
                from characters.character_base import MoveData
                if isinstance(opponent.current_attack, MoveData):
                    name = opponent.current_attack.name.lower()
                    if 'light' in name or 'jab' in name:
                        attack_type = "light"
            self.opponent_model.record_attack(attack_type, dt)
            opponent._attack_recorded = True
        elif not opponent.is_attacking:
            opponent._attack_recorded = False

        # 更新对手威胁评估
        distance = abs(self.x - opponent.x)
        self.opponent_model.update_threat(opponent, distance, dt)

        # 反应延迟
        if self.reaction_timer > 0:
            # 即使在反应延迟中，也要处理紧急情况
            if self.opponent.is_attacking and distance < 120:
                # 紧急情况：立刻防御或闪避
                if self.defense_skill > 0.5 and self.on_ground:
                    self.apply_movement(False, False, False, False, True)
                    self.is_blocking = True
            return

        # 根据难度调整实际反应时间
        actual_reaction = self.reaction_time * (1.1 - self.aggression * 0.3)
        self.reaction_timer = actual_reaction

        # ── 构建局势评估 ───────────────────────────────────────────
        situation = SituationAssessment(self, opponent, dt)

        # ── 道具优先级检查 ─────────────────────────────────────────
        if self._check_item_priority(situation, opponent):
            return

        # ── 小兵威胁检查 ───────────────────────────────────────────
        if self._check_minion_threat(opponent):
            return

        # ── 生成战术决策 ──────────────────────────────────────────
        engine = TacticalEngine(self, opponent, situation,
                               self.opponent_model, dt, dt)
        engine.generate_all_options()
        best_decision = engine.select_best_action()

        if best_decision is None:
            # 无明确决策：执行默认行为
            self._execute_default_behavior(situation, opponent)
            return

        # ── 执行决策 ───────────────────────────────────────────────
        executor = ActionExecutor(self, opponent, dt)
        action_taken = executor.execute(best_decision)

        # 追踪行动
        self._last_action = best_decision.decision_type
        if best_decision.decision_type == self._last_action:
            self._action_streak += 1
        else:
            self._action_streak = 1

        # 如果没有执行攻击，尝试随机跳跃增加多样性
        if not action_taken:
            self._try_random_jump()

        # 跳跃后调整水平位置
        if not self.on_ground and self._last_action in ("approach", "pressure"):
            if opponent.x > self.x:
                self.vel_x = self.stats.walk_speed * 0.3
            else:
                self.vel_x = -self.stats.walk_speed * 0.3

    def _check_item_priority(self, situation: SituationAssessment,
                            opponent: Fighter) -> bool:
        """检查道具优先级，返回是否中断AI决策"""
        if self.item_seek_cooldown > 0 or not self.item_manager:
            return False

        nearest_item = self._get_nearest_item(self.item_manager)
        if not nearest_item:
            return False

        item_dist = abs(self.x - nearest_item.x)
        is_health = nearest_item.item_type == "health_bag"

        # 血量危急时的道具优先级
        if situation.health_ratio < 0.25:
            # 必须去找治疗
            self._chase_item(nearest_item, nearest_item.x > self.x)
            self.item_seek_cooldown = 0.3
            return True

        # 重要治疗道具
        if is_health and situation.health_ratio < 0.5:
            if not opponent.is_attacking or situation.distance > 200:
                self._chase_item(nearest_item, nearest_item.x > self.x)
                self.item_seek_cooldown = 0.5
                return True

        return False

    def _chase_item(self, item, move_right: bool):
        """追踪道具"""
        if move_right:
            self.apply_movement(False, True, False, False, False)
        else:
            self.apply_movement(True, False, False, False, False)

        if self.on_ground and self._should_jump_for_item(item):
            self._do_jump()

    def _check_minion_threat(self, opponent: Fighter) -> bool:
        """检查并处理小兵威胁"""
        nearest_minion = self._find_nearest_enemy_minion(opponent)
        if nearest_minion is None:
            return False

        minion_dist = abs(self.x - nearest_minion.x)

        # 小兵太近才处理
        if minion_dist < 100:
            self.update_direction(nearest_minion.x)
            if minion_dist > 60:
                if nearest_minion.x > self.x:
                    self.apply_movement(False, True, False, False, False)
                else:
                    self.apply_movement(True, False, False, False, False)
            elif self.attack_cooldown <= 0:
                self.attack_light()
            return True

        return False

    def _execute_default_behavior(self, situation: SituationAssessment,
                                  opponent: Fighter):
        """默认行为：没有明确决策时执行"""
        distance = situation.distance

        # 根据战术姿态选择默认行为
        posture = situation.get_tactical_posture()

        if posture == "desperate":
            # 拼命：激进攻击或寻找治疗
            if self.health_ratio < 0.3:
                self._seek_nearest_health()
            else:
                if distance > 100:
                    self.ai_approach(distance, opponent)
                elif self.attack_cooldown <= 0:
                    self.attack_light()

        elif posture == "defensive":
            # 防守：保持距离，等待机会
            if distance < 80:
                self._safe_retreat(distance, opponent)
            elif distance > 300 and self._can_use_ranged():
                self.attack_heavy()
            elif distance > 150:
                self.ai_approach(distance, opponent)

        elif posture == "balanced":
            # 均衡：稳健接近
            if distance > 200:
                self.ai_approach(distance, opponent)
                if self._can_use_ranged() and random.random() < 0.2:
                    self.attack_heavy()
            elif distance < 100:
                if self.attack_cooldown <= 0:
                    r = random.random()
                    if r < 0.6:
                        self.attack_light()
                    else:
                        self.attack_heavy()
            else:
                self.ai_approach(distance, opponent)

        elif posture == "aggressive":
            # 进取：积极进攻
            self.ai_approach(distance, opponent)
            if distance < 150 and self.attack_cooldown <= 0:
                if random.random() < 0.7:
                    self.attack_light()
                else:
                    self.attack_heavy()

        else:  # dominant
            # 压制：全力进攻
            if distance < 120:
                if self.attack_cooldown <= 0:
                    if random.random() < 0.5:
                        self.attack_light()
                    else:
                        self.attack_heavy()
            else:
                self.ai_approach(distance, opponent)
                if self._can_use_ranged() and distance > 200:
                    self.attack_heavy()

    # ── 辅助方法 ───────────────────────────────────────────────────────────

    def ai_approach(self, distance: float, opponent: Fighter):
        """接近目标"""
        target_x = opponent.x if hasattr(opponent, 'x') else opponent
        if target_x > self.x:
            self.apply_movement(False, True, False, False, False)
        else:
            self.apply_movement(True, False, False, False, False)

    def _safe_retreat(self, distance: float, opponent: Fighter):
        """安全后撤"""
        retreat_x = self.x - 50 if opponent.x > self.x else self.x + 50
        if retreat_x < SCREEN_LEFT + EDGE_DANGER_ZONE or \
           retreat_x > SCREEN_RIGHT - EDGE_DANGER_ZONE:
            # 后撤会进入危险区，改为向中央
            self._edge_escape()
        else:
            self.ai_retreat(distance, opponent)

    def ai_retreat(self, distance: float, opponent: Fighter):
        """后撤"""
        if opponent.x > self.x:
            self.apply_movement(False, True, False, False, False)
        else:
            self.apply_movement(True, False, False, False, False)

    def _edge_escape(self):
        """逃离边缘"""
        center = (SCREEN_LEFT + SCREEN_RIGHT) / 2
        if self.x < center:
            self.apply_movement(False, True, False, False, False)
        else:
            self.apply_movement(True, False, False, False, False)

    def _seek_nearest_health(self):
        """寻找最近的治疗"""
        if not self.item_manager:
            return

        health_items = [
            i for i in self.item_manager.items
            if i.active and i.landed and i.item_type == "health_bag"
        ]

        if not health_items:
            # 没有治疗，找任意道具
            health_items = [
                i for i in self.item_manager.items
                if i.active and i.landed
            ]

        if not health_items:
            return

        nearest = min(health_items, key=lambda i: abs(self.x - i.x))
        self._chase_item(nearest, nearest.x > self.x)

    # ══════════════════════════════════════════════════════════════════════
    # 公开更新接口
    # ══════════════════════════════════════════════════════════════════════

    def update(self, dt: float, opponent: Fighter = None):
        """更新AI角色"""
        if opponent:
            self.update_ai(dt, opponent)
        super().update(dt, opponent)

    def get_opponent(self):
        """获取对手引用"""
        return self._opponent_ref


# ── 类型注解 ────────────────────────────────────────────────────────────────
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from entities.item_drop import ItemDrop
