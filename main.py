# 主游戏文件

import pygame
import sys
import random
from typing import Optional

# 初始化Pygame
pygame.init()

from config import SCREEN_WIDTH, SCREEN_HEIGHT, FPS, TITLE, Colors
from game.game_state import GameState, RoundState, MatchResult
from characters import get_character, CHARACTER_LIST
from entities.fighter import Fighter
from entities.player import Player
from entities.ai_fighter import AIFighter
from entities.item_drop import ItemDropManager
from ui.menu import Menu
from ui.character_select import CharacterSelect
from ui.map_select import MapSelect, MAPS
from ui.fight_ui import FightUI, VictoryScreen
from ui.timer import Timer, Announcement
from ui.loading_screen import LoadingScreen
from stages.dorm_stage import DormStage
from stages.castle_stage import CastleStage
from effects.ultimate_effect import UltimateEffectManager
from assets.screen_effects import ScreenEffects
from assets.vfx_player import VFXPlayer
from entities.fighter import get_ultimate_entity_manager, reset_ultimate_entity_manager

class Game:
    """游戏主类"""

    def __init__(self):
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()
        self.running = True

        # 游戏状态
        self.state = GameState.MENU

        # 菜单
        self.menu = Menu(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 角色选择
        self.character_select = CharacterSelect(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 地图选择
        self.map_select = MapSelect(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.selected_map_index = 0  # 默认选第一张地图
        self.selected_map = None

        # 加载界面
        self.loading_screen = LoadingScreen(SCREEN_WIDTH, SCREEN_HEIGHT)
        self._loading_stage = 0          # 加载阶段索引
        self._loading_frame = 0          # 当前阶段已渲染帧数（至少1帧才能显示进度）
        self._loading_progress = [       # 阶段 → (进度, 描述)
            (0.10, "加载地图资源..."),
            (0.30, "预渲染地图背景..."),
            (0.55, "加载角色精灵..."),
            (0.75, "加载道具贴图..."),
            (0.90, "初始化战斗系统..."),
            (1.00, "战斗开始!"),
        ]
        self._loading_p1_char = 0       # 待加载的P1角色索引
        self._loading_p2_char = 0       # 待加载的P2角色索引

        # 战斗（暂时使用默认颜色，会在 start_match 时更新）
        self.fight_ui = FightUI(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.victory_screen = VictoryScreen(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 对战角色
        self.player1: Optional[Player] = None
        self.player2: Optional[Fighter] = None

        # 场景（由 start_match 根据地图创建）
        self.stage = None
        self.selected_map = None

        # 回合管理
        self.p1_wins = 0
        self.p2_wins = 0
        self.max_wins = 2
        self.round_timer = Timer(SCREEN_WIDTH // 2, 35, 99)
        self.round_state = RoundState.READY

        # 公告
        self.announcement = Announcement(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 终极必杀技特效管理器
        self.ultimate_effect = UltimateEffectManager(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.last_special1_state = {}
        self.last_special2_state = {}

        # 史诗级屏幕特效系统
        self.screen_effects = ScreenEffects()
        self.vfx_player = VFXPlayer()

        # 终极必杀技实体管理器（P1国旗/P2激光/P3黑影/P4鸡蛋，使用全局单例）
        self.ultimate_entity_manager = get_ultimate_entity_manager(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 模式
        self.is_vs_ai = True
        self.debug_mode = False

        # 上一帧按键状态（用于检测边缘触发）
        self.prev_keys = None

        # 道具掉落管理器
        self.item_drop_manager: Optional[ItemDropManager] = None

    def run(self):
        """游戏主循环"""
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0

            self.handle_events()
            self.update(dt)
            self.render()
            pygame.display.flip()

        pygame.quit()
        sys.exit()

    def handle_events(self):
        """处理事件"""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.state == GameState.MENU:
                        self.running = False
                    elif self.state == GameState.CHARACTER_SELECT:
                        self.state = GameState.MENU
                    elif self.state == GameState.MAP_SELECT:
                        self.state = GameState.CHARACTER_SELECT
                        self.map_select.is_transitioning = False
                        self.map_select.confirm_timer = 0.0
                    elif self.state == GameState.FIGHTING:
                        self.state = GameState.MENU
                    elif self.state == GameState.LOADING:
                        pass  # 加载中不允许取消

            # 定时器事件
            elif event.type == pygame.USEREVENT + 1:
                self.round_state = RoundState.FIGHT
                self.announcement.show("FIGHT!", 1.0)
            elif event.type == pygame.USEREVENT + 2:
                self.start_round()
            elif event.type == pygame.USEREVENT + 3:
                self.start_round()

            # 菜单输入
            if self.state == GameState.MENU:
                result = self.menu.handle_input(event)
                if result:
                    if result == "普通模式":
                        self.is_vs_ai = True
                        self.debug_mode = False
                        self.state = GameState.CHARACTER_SELECT
                    elif result == "双人模式":
                        self.is_vs_ai = False
                        self.debug_mode = False
                        self.state = GameState.CHARACTER_SELECT
                    elif result == "调试模式":
                        self.is_vs_ai = True
                        self.debug_mode = True
                        self.state = GameState.CHARACTER_SELECT
                    elif result == "退出":
                        self.running = False

            # 角色选择输入
            elif self.state == GameState.CHARACTER_SELECT:
                selections = self.character_select.handle_input(event)
                if selections:
                    self.state = GameState.MAP_SELECT
                    self.map_select.selection = 0
                    self.map_select.is_transitioning = False
                    self.map_select.confirm_timer = 0.0

            # 地图选择输入
            elif self.state == GameState.MAP_SELECT:
                result = self.map_select.handle_input(event)
                if result == -1:
                    self.state = GameState.CHARACTER_SELECT
                elif result is not None and result >= 0:
                    self.selected_map_index = result
                    p1_char = self.character_select.p1_selection
                    p2_char = self.character_select.p2_selection
                    self.start_match(p1_char, p2_char)

            # 回合结束输入
            elif self.state == GameState.ROUND_END:
                if event.type == pygame.KEYDOWN:
                    if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                        if self.p1_wins >= self.max_wins or self.p2_wins >= self.max_wins:
                            self.state = GameState.CHARACTER_SELECT
                            self.reset_match()
                        else:
                            self.start_round()

    def update(self, dt: float):
        """更新游戏"""
        if self.state == GameState.MENU:
            self.menu.update(dt)
        elif self.state == GameState.CHARACTER_SELECT:
            self.character_select.update(dt)
        elif self.state == GameState.MAP_SELECT:
            self.map_select.update(dt)
        elif self.state == GameState.LOADING:
            self._update_loading(dt)
        elif self.state == GameState.FIGHTING:
            self.update_fight(dt)
        elif self.state == GameState.ROUND_END:
            self.victory_screen.update(dt)
            self.update_fight(dt)  # 保持战斗画面更新

        # 更新终极特效
        self.ultimate_effect.update(dt)

        # 更新屏幕特效系统
        self.screen_effects.update(dt)
        self.vfx_player.update(dt)

    def update_fight(self, dt: float):
        """更新战斗"""
        # 调试模式：无限血、无限蓝、金币9999
        if self.debug_mode and self.player1 and self.player2:
            self.player1.health = self.player1.max_health
            self.player2.health = self.player2.max_health
            self.player1.special_energy = self.player1.max_special
            self.player2.special_energy = self.player2.max_special
            self.player1.minion_manager.coins = 9999.0
            self.player2.minion_manager.coins = 9999.0
        # 如果终极特效正在播放，暂停游戏更新
        if self.ultimate_effect.is_playing():
            self.ultimate_effect.update(dt)
            self.fight_ui.update(dt, self.player1, self.player2)
            return

        # 回合状态
        if self.round_state == RoundState.READY:
            self.round_timer.pause()
        elif self.round_state == RoundState.FIGHT:
            self.round_timer.resume()
            self.round_timer.update(dt)
            if self.round_timer.is_finished:
                self.end_round_timeout()

        # 获取当前按键状态
        keys = pygame.key.get_pressed()
        prev_keys = self.prev_keys if self.prev_keys else keys
        self.prev_keys = keys

        # 边缘触发检测
        def key_pressed(key): return bool(keys[key]) and not bool(prev_keys[key])

        # 玩家1输入
        if self.player1 and self.round_state == RoundState.FIGHT:
            left = bool(keys[pygame.K_a])
            right = bool(keys[pygame.K_d])
            up = bool(keys[pygame.K_w])
            down = bool(keys[pygame.K_s])
            block = bool(keys[pygame.K_p])
            light = key_pressed(pygame.K_j)
            heavy = key_pressed(pygame.K_k)
            special = key_pressed(pygame.K_l)
            special_2 = key_pressed(pygame.K_i)
            summon = key_pressed(pygame.K_u)
            toggle = key_pressed(pygame.K_o)

            # 先update更新_opponent_ref，再处理输入
            self.player1.update(dt, self.player2)
            self.player1.handle_input(dt, left, right, up, down, light, heavy, special, special_2, block, summon, toggle)

            # 更新小兵管理器
            p2_manager = getattr(self.player2, 'minion_manager', None)
            self.player1.minion_manager.stage = self.stage
            self.player1.minion_manager.update(dt, self.player1.x, self.player1.y, self.player2, p2_manager)

            # 检测终极必杀技释放（发动时一次性触发）
            if self.player1.ultimate_pending_trigger:
                self.player1.ultimate_pending_trigger = False
                char_name = self.player1.char_data.stats.name_cn
                direction = 1 if self.player1.facing_right else -1
                self.ultimate_effect.trigger(char_name, "ultimate", direction)
                self.player1.special_energy = 0

        # 玩家2输入
        if self.player2 and self.round_state == RoundState.FIGHT:
            if self.is_vs_ai:
                # AI：先保存opponent引用，再调用update（包含AI逻辑和timer更新）
                self.player2.update(dt, self.player1)
                # AI也更新小兵管理器
                p1_manager = getattr(self.player1, 'minion_manager', None)
                self.player2.minion_manager.stage = self.stage
                self.player2.minion_manager.update(dt, self.player2.x, self.player2.y, self.player1, p1_manager)
                # AI自动召唤小兵（有足够金币时）
                if self.player2.minion_manager.coin_int >= 20:
                    if random.random() < 0.3:  # 30%概率召唤
                        self.player2.minion_manager.try_summon(self.player2.x, self.player2.y)
            else:
                p2_left = bool(keys[pygame.K_LEFT])
                p2_right = bool(keys[pygame.K_RIGHT])
                p2_up = bool(keys[pygame.K_UP])
                p2_down = bool(keys[pygame.K_DOWN])
                p2_block = bool(keys[pygame.K_KP0])
                p2_special = key_pressed(pygame.K_KP3)
                p2_special_2 = key_pressed(pygame.K_PERIOD)
                p2_summon = key_pressed(pygame.K_KP4)
                p2_toggle = key_pressed(pygame.K_KP5)
                # 先update更新_opponent_ref，再处理输入
                self.player2.update(dt, self.player1)
                self.player2.handle_input(dt, p2_left, p2_right, p2_up, p2_down, False, False, p2_special, p2_special_2, p2_block, p2_summon, p2_toggle)
                # 更新小兵管理器
                p1_manager = getattr(self.player1, 'minion_manager', None)
                self.player2.minion_manager.stage = self.stage
                self.player2.minion_manager.update(dt, self.player2.x, self.player2.y, self.player1, p1_manager)

            # 检测终极必杀技释放
            if self.player2.ultimate_pending_trigger:
                self.player2.ultimate_pending_trigger = False
                char_name = self.player2.char_data.stats.name_cn
                direction = 1 if self.player2.facing_right else -1
                self.ultimate_effect.trigger(char_name, "ultimate", direction)
                self.player2.special_energy = 0

        # 更新终极必杀技实体（P1国旗/P2激光/P3黑影/P4鸡蛋）
        if self.player1 and self.player2:
            self.ultimate_entity_manager.update(dt, self.player1, self.player2)
            # 处理终极实体伤害
            self._handle_ultimate_entity_damage()

        # 检测胜负
        self.check_match_end()

        # 更新道具掉落系统
        if self.round_state == RoundState.FIGHT and self.item_drop_manager is not None:
            self.item_drop_manager.start()  # idempotent
            players = [p for p in [self.player1, self.player2] if p]
            self.item_drop_manager.update(dt, self.stage, players)
            # Handle pending weapon attacks
            for p in players:
                if getattr(p, 'weapon_attack_pending', False):
                    p.weapon_attack_pending = False
                    equipped = getattr(p, 'equipped_weapon', None)
                    self.item_drop_manager.execute_weapon_attack(p, self.stage)
                    # 武器屏幕特效
                    if equipped == "nuke_launcher":
                        self.screen_effects.weapon_nuke_warning()
                    elif equipped == "gatling":
                        self.screen_effects.shake(intensity=3.0, duration=0.2)
                    elif equipped in ("staff_red", "staff_blue", "staff_green"):
                        staff_colors = {
                            "staff_red": (255, 80, 20),
                            "staff_blue": (50, 150, 255),
                            "staff_green": (80, 220, 60)
                        }
                        self.screen_effects.weapon_staff_flash(staff_colors.get(equipped, (200, 200, 200)))

        # 更新UI
        self.fight_ui.update(dt, self.player1, self.player2)

        # ── 屏幕震动 & VFX 命中特效 ───────────────────────────────────
        if self.player1 and self.player1.screen_shake > 0:
            # 将角色的震动信号转移到全局特效系统
            self.screen_effects.shake(intensity=self.player1.screen_shake * 2.0, duration=0.25)
            self.player1.screen_shake = 0
        if self.player2 and self.player2.screen_shake > 0:
            self.screen_effects.shake(intensity=self.player2.screen_shake * 2.0, duration=0.25)
            self.player2.screen_shake = 0

        # 检测命中并触发VFX（通过命中特效计时器）
        if self.player1 and self.player2:
            # P2 被 P1 命中时
            if hasattr(self.player2, 'last_hit_by') and self.player2.last_hit_by == 1:
                self._spawn_hit_vfx(self.player2.x, self.player2.y - 50)
                self.player2.last_hit_by = 0
            # P1 被 P2 命中时
            if hasattr(self.player1, 'last_hit_by') and self.player1.last_hit_by == 2:
                self._spawn_hit_vfx(self.player1.x, self.player1.y - 50)
                self.player1.last_hit_by = 0

    def _spawn_hit_vfx(self, x: float, y: float):
        """生成命中VFX特效"""
        self.vfx_player.spawn_hit_cluster(x, y, intensity='medium')
        self.screen_effects.epic_hit(intensity='medium', color='white')

    def _handle_ultimate_entity_damage(self):
        """处理终极必杀技实体对角色的伤害"""
        manager = self.ultimate_entity_manager

        # ── P1 国旗伤害检测 ─────────────────────────────────
        for flag in manager.p1_flags:
            if not flag.active:
                continue
            if flag.has_dealt_damage:
                continue  # 已经造成过伤害了
            # 国旗一次性对敌方造成伤害
            for target in [self.player1, self.player2]:
                if not target:
                    continue
                if target.player_id == flag.owner_id:
                    continue  # 不伤害自己
                # 一次性伤害
                flag.has_dealt_damage = True
                target.take_damage(flag.damage, 15, 5, 1 if flag.x > target.x else -1)
                target.effect_manager.add_text(
                    f"★ {flag.damage}", target.x, target.y - 120, (255, 220, 0), 48, 1.5
                )
                target.effect_manager.add_particle_burst(target.x, target.y - 80, 20,
                                                        (255, 200, 50), 8.0, 5.0)
                self.screen_effects.shake(intensity=8.0, duration=0.3)
                break  # 只打一个目标

        # ── P2 激光伤害检测 ─────────────────────────────────
        for laser in manager.p2_lasers:
            if not laser.active:
                continue
            if laser.timer < laser.charge_duration:
                continue  # 还在蓄力阶段
            if laser.has_dealt_damage:
                continue
            # 激光对前方的敌人造成伤害（检查x轴方向）
            for target in [self.player1, self.player2]:
                if not target:
                    continue
                if target.player_id == laser.owner_id:
                    continue  # 不伤害自己
            # 检查目标是否在激光的横向和纵向范围内
            target_x = target.x
            target_h = 160  # 角色高度
            if laser.direction > 0:  # 向右发射
                if laser.x < target_x <= laser.x + laser.laser_length and laser.is_in_laser_row(target.y, target_h):
                    laser.has_dealt_damage = True
                    target.take_damage(laser.damage, 30, 15, laser.direction)
                    target.effect_manager.add_text(
                        f"★ {laser.damage}", target.x, target.y - 120, (50, 150, 255), 56, 1.5
                    )
                    target.effect_manager.add_particle_burst(target.x, target.y - 80, 30,
                                                            (50, 100, 255), 12.0, 8.0)
                    self.screen_effects.shake(intensity=15.0, duration=0.4)
                else:  # 向左发射
                    if laser.x > target_x >= laser.x + laser.laser_length and laser.is_in_laser_row(target.y, target_h):
                        laser.has_dealt_damage = True
                        target.take_damage(laser.damage, 30, 15, laser.direction)
                        target.effect_manager.add_text(
                            f"★ {laser.damage}", target.x, target.y - 120, (50, 150, 255), 56, 1.5
                        )
                        target.effect_manager.add_particle_burst(target.x, target.y - 80, 30,
                                                                (50, 100, 255), 12.0, 8.0)
                        self.screen_effects.shake(intensity=15.0, duration=0.4)

        # ── P3 黑影伤害检测（敌人攻击黑影）──────────────────────
        for shadow in manager.p3_shadows:
            if not shadow.alive:
                continue
            # 敌人攻击黑影
            for attacker in [self.player1, self.player2]:
                if not attacker:
                    continue
                if attacker.player_id == shadow.owner_id:
                    continue  # 不攻击自己的黑影
                # 检查攻击判定框是否命中黑影
                hit_rect = attacker.get_hitbox_rect()
                if hit_rect:
                    shadow_rect = shadow.get_hurtbox()
                    if (hit_rect[0] < shadow_rect[0] + shadow_rect[2] and
                        hit_rect[0] + hit_rect[2] > shadow_rect[0] and
                        hit_rect[1] < shadow_rect[1] + shadow_rect[3] and
                        hit_rect[1] + hit_rect[3] > shadow_rect[1]):
                        damage = int(attacker.stats.attack_power * 0.5)
                        shadow.take_damage(damage)
                        attacker.effect_manager.add_particle_burst(
                            shadow.x, shadow.y - 80, 8, (180, 80, 255), 3.0, 2.0
                        )
                        if not shadow.alive:
                            attacker.effect_manager.add_text(
                                "黑影消灭!", shadow.x, shadow.y - 150, (180, 80, 255), 32, 1.0
                            )

        # ── P4 鸡蛋伤害检测 ─────────────────────────────────
        for egg in manager.p4_entities:
            if not egg.active:
                continue
            for target in [self.player1, self.player2]:
                if not target:
                    continue
                if target.player_id == egg.owner_id:
                    continue  # 不伤害自己
                if not egg.can_damage_target():
                    continue
                egg_rect = egg.get_egg_rect()
                my_rect = (target.x - 35, target.y - 150, 70, 150)
                if (egg_rect[0] < my_rect[0] + my_rect[2] and
                    egg_rect[0] + egg_rect[2] > my_rect[0] and
                    egg_rect[1] < my_rect[1] + my_rect[3] and
                    egg_rect[1] + egg_rect[3] > my_rect[1]):
                    target.take_damage(egg.damage, 5, 1,
                                      1 if egg.x > target.x else -1)
                    target.effect_manager.add_text(
                        f"啄! {egg.damage}", target.x, target.y - 120,
                        (200, 180, 80), 32, 0.5
                    )

    def _update_loading(self, dt: float):
        """分帧加载资源，避免一次性卡顿"""
        self.loading_screen.update(dt)

        # 每步至少渲染1帧再进入下一步（让进度条可见）
        if self._loading_frame < 1:
            self._loading_frame += 1
            prog, status = self._loading_progress[self._loading_stage]
            self.loading_screen.set_progress(prog, status)
            return

        stages = [
            (0.10, "加载地图资源...",        self._loading_step_bg),
            (0.30, "预渲染地图背景...",      self._loading_step_bg_cache),
            (0.55, "加载角色精灵...",       self._loading_step_sprites),
            (0.75, "加载道具贴图...",       self._loading_step_items),
            (0.90, "初始化战斗系统...",     self._loading_step_fight),
            (1.00, "战斗开始!",             self._loading_step_done),
        ]

        if self._loading_stage < len(stages):
            prog, status, action = stages[self._loading_stage]
            self.loading_screen.set_progress(prog, status)
            if action():
                self._loading_stage += 1
                self._loading_frame = 0
                if self._loading_stage >= len(stages):
                    self.state = GameState.FIGHTING
                    self.start_round()

    def _loading_step_bg(self, dt: float = 0.0) -> bool:
        """步骤0：加载地图"""
        map_info = MAPS[self.selected_map_index]
        self.selected_map = map_info
        self.stage = map_info['stage_class'](SCREEN_WIDTH, SCREEN_HEIGHT)
        self.loading_screen.set_map_name(map_info['name'])
        return True

    def _loading_step_bg_cache(self, dt: float = 0.0) -> bool:
        """步骤1：触发地图背景预渲染（在下一帧首次绘制时完成）"""
        self.stage._ensure_cache()
        return True

    def _loading_step_sprites(self, dt: float = 0.0) -> bool:
        """步骤2：加载角色精灵"""
        from animation.sprite_loader import sprite_loader
        sprite_loader.preload_all()
        return True

    def _loading_step_items(self, dt: float = 0.0) -> bool:
        """步骤3：加载道具贴图"""
        from entities.item_drop import ItemDrop
        ItemDrop.load_images()
        return True

    def _loading_step_fight(self, dt: float = 0.0) -> bool:
        """步骤4：初始化战斗数据"""
        p1_data = get_character(self._loading_p1_char)
        p2_data = get_character(self._loading_p2_char)

        p1_skills = [s.name_cn for s in p1_data.special] if p1_data.special else ["必杀1", "必杀2"]
        p2_skills = [s.name_cn for s in p2_data.special] if p2_data.special else ["必杀1", "必杀2"]
        self.fight_ui.set_skill_names(p1_skills, p2_skills)

        self.fight_ui.p1_health.character_color = p1_data.stats.color
        self.fight_ui.p1_health.secondary_color = p1_data.stats.secondary_color
        self.fight_ui.p1_health.health_high = p1_data.stats.color
        self.fight_ui.p1_health.health_med = p1_data.stats.secondary_color
        self.fight_ui.p1_health.max_health = p1_data.stats.max_health
        self.fight_ui.p1_skills.skill1_color = p1_data.stats.color
        self.fight_ui.p1_skills.skill2_color = p1_data.stats.secondary_color

        self.fight_ui.p2_health.character_color = p2_data.stats.color
        self.fight_ui.p2_health.secondary_color = p2_data.stats.secondary_color
        self.fight_ui.p2_health.health_high = p2_data.stats.color
        self.fight_ui.p2_health.health_med = p2_data.stats.secondary_color
        self.fight_ui.p2_health.max_health = p2_data.stats.max_health
        self.fight_ui.p2_skills.skill1_color = p2_data.stats.color
        self.fight_ui.p2_skills.skill2_color = p2_data.stats.secondary_color
        return True

    def _loading_step_done(self, dt: float = 0.0) -> bool:
        """步骤5：完成"""
        return True

    def start_match(self, p1_char: int, p2_char: int):
        """开始对战 - 启动分帧加载"""
        self.state = GameState.LOADING
        self._loading_stage = 0
        self._loading_p1_char = p1_char
        self._loading_p2_char = p2_char
        self.p1_wins = 0
        self.p2_wins = 0
        self.fight_ui.set_round_wins(0, 0)
        self.ultimate_entity_manager.clear()
        self.p1_char_index = p1_char
        self.p2_char_index = p2_char
        self.loading_screen.phase_in = 0.0
        self.loading_screen._display_progress = 0.0
        self.loading_screen.target_progress = 0.0

    def start_round(self):
        """开始一回合"""
        self.round_state = RoundState.READY
        self.round_timer.reset(99)
        self.prev_keys = None

        p1_data = get_character(self.p1_char_index)
        p2_data = get_character(self.p2_char_index)

        self.player1 = Player(1, p1_data, 300, self.stage.ground_y, self.p1_char_index, self.stage)
        if self.is_vs_ai:
            self.player2 = AIFighter(2, p2_data, 980, self.stage.ground_y, self.p2_char_index, self.stage,
                                     item_manager=self.item_drop_manager)
        else:
            self.player2 = Player(2, p2_data, 980, self.stage.ground_y, self.p2_char_index, self.stage)

        self.item_drop_manager = ItemDropManager()

        self.announcement.show("ROUND 1", 1.5)
        pygame.time.set_timer(pygame.USEREVENT + 1, 2000, loops=1)

    def check_match_end(self):
        """检查比赛结束"""
        if self.round_state != RoundState.FIGHT:
            return
        if self.player1.health <= 0:
            self.end_round(2)
        elif self.player2.health <= 0:
            self.end_round(1)

    def end_round(self, winner: int):
        """回合结束"""
        self.round_state = RoundState.KO
        self.round_timer.pause()

        if winner == 1:
            self.p1_wins += 1
            self.fight_ui.show_announcement("P1 WIN!")
        else:
            self.p2_wins += 1
            self.fight_ui.show_announcement("P2 WIN!")

        self.fight_ui.set_round_wins(self.p1_wins, self.p2_wins)

        if self.p1_wins >= self.max_wins:
            self.state = GameState.ROUND_END
            self.victory_screen.show(1)
        elif self.p2_wins >= self.max_wins:
            self.state = GameState.ROUND_END
            self.victory_screen.show(2)
        else:
            pygame.time.set_timer(pygame.USEREVENT + 2, 2000, loops=1)

    def end_round_timeout(self):
        """超时结束"""
        self.round_state = RoundState.TIMEOUT
        self.round_timer.pause()
        if self.player1.health > self.player2.health:
            self.end_round(1)
        elif self.player2.health > self.player1.health:
            self.end_round(2)
        else:
            self.announcement.show("TIME!", 1.0)
            pygame.time.set_timer(pygame.USEREVENT + 3, 1500, loops=1)

    def reset_match(self):
        """重置比赛"""
        self.p1_wins = 0
        self.p2_wins = 0
        self.fight_ui.set_round_wins(0, 0)
        # 重置角色选择状态
        self.character_select.p1_selection = 0
        self.character_select.p2_selection = 1
        self.character_select.phase = "p1_select"
        self.character_select.confirm_timer = 0.0

    def render(self):
        """渲染"""
        main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.state == GameState.MENU:
            self.menu.draw(main_surface)
        elif self.state == GameState.CHARACTER_SELECT:
            self.character_select.draw(main_surface)
        elif self.state == GameState.MAP_SELECT:
            self.map_select.draw(main_surface)
        elif self.state == GameState.LOADING:
            self.loading_screen.draw(main_surface)
        elif self.state in [GameState.FIGHTING, GameState.ROUND_END]:
            self.stage.draw(main_surface)
            if self.player1:
                self.player1.draw(main_surface)
            if self.player2:
                self.player2.draw(main_surface)

            # 绘制小兵
            if self.player1:
                self.player1.minion_manager.draw(main_surface)
            if self.player2:
                self.player2.minion_manager.draw(main_surface)

            # 绘制VFX精灵动画（命中火花、斩击等）
            self.vfx_player.draw(main_surface)

            # 绘制道具掉落
            if self.item_drop_manager is not None:
                self.item_drop_manager.draw(main_surface)

            p1_name = CHARACTER_LIST[self.p1_char_index]['name'] if hasattr(self, 'p1_char_index') else "P1"
            p2_name = CHARACTER_LIST[self.p2_char_index]['name'] if hasattr(self, 'p2_char_index') else "P2"
            self.fight_ui.draw(main_surface, p1_name, p2_name, self.player1, self.player2)

            # 绘制金币HUD
            if self.player1 and hasattr(self.player1, 'minion_manager'):
                self.player1.minion_manager.draw_hud(
                    main_surface, 375, 52, True, self.fight_ui.name_font)
            if self.player2 and hasattr(self.player2, 'minion_manager'):
                self.player2.minion_manager.draw_hud(
                    main_surface, SCREEN_WIDTH - 375, 52, False, self.fight_ui.name_font)
            self.announcement.draw(main_surface)

            # 绘制终极必杀技实体（国旗/激光/黑影/鸡蛋）
            self.ultimate_entity_manager.draw(main_surface)

            # 绘制终极必杀技特效（公告文字等）
            self.ultimate_effect.draw(main_surface)

            # 绘制屏幕特效（色调变暗等覆盖层）
            self.screen_effects.draw_overlay(main_surface)

            if self.state == GameState.ROUND_END:
                self.victory_screen.draw(main_surface, p1_name, p2_name)

        # 应用屏幕震动偏移（新的特效系统）
        sx, sy = self.screen_effects.get_shake_offset()
        if sx != 0 or sy != 0:
            self.screen.fill((0, 0, 0))
            self.screen.blit(main_surface, (sx, sy))
        else:
            self.screen.blit(main_surface, (0, 0))

        # 绘制闪光（始终在最上层）
        self.screen_effects.draw_flash(self.screen)


if __name__ == "__main__":
    game = Game()
    game.run()
