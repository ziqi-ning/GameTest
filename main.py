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
from ui.menu import Menu
from ui.character_select import CharacterSelect
from ui.map_select import MapSelect, MAPS
from ui.fight_ui import FightUI, VictoryScreen
from ui.timer import Timer, Announcement
from stages.dorm_stage import DormStage
from stages.castle_stage import CastleStage
from effects.ultimate_effect import UltimateEffectManager
from assets.screen_effects import ScreenEffects
from assets.vfx_player import VFXPlayer

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

        # 模式
        self.is_vs_ai = True

        # 上一帧按键状态（用于检测边缘触发）
        self.prev_keys = None

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
                    if result == "开始游戏":
                        self.is_vs_ai = True
                        self.state = GameState.CHARACTER_SELECT
                    elif result == "双人模式":
                        self.is_vs_ai = False
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
        elif self.state == GameState.FIGHTING:
            self.update_fight(dt)
        elif self.state == GameState.ROUND_END:
            self.victory_screen.update(dt)

        # 更新终极特效
        self.ultimate_effect.update(dt)

        # 更新屏幕特效系统
        self.screen_effects.update(dt)
        self.vfx_player.update(dt)

    def update_fight(self, dt: float):
        """更新战斗"""
        # 如果终极特效正在播放，暂停游戏更新
        if self.ultimate_effect.is_playing():
            self.ultimate_effect.update(dt)
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
            self.player1.handle_input(left, right, up, down, light, heavy, special, special_2, block, summon, toggle)

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
                self.player2.handle_input(p2_left, p2_right, p2_up, p2_down, False, False, p2_special, p2_special_2, p2_block, p2_summon, p2_toggle)
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

        # 检测胜负
        self.check_match_end()

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

    def start_match(self, p1_char: int, p2_char: int):
        """开始对战"""
        self.state = GameState.FIGHTING
        self.p1_wins = 0
        self.p2_wins = 0
        self.fight_ui.set_round_wins(0, 0)
        self.p1_char_index = p1_char
        self.p2_char_index = p2_char

        # 根据选择的地图创建场景
        map_info = MAPS[self.selected_map_index]
        self.selected_map = map_info
        self.stage = map_info['stage_class'](SCREEN_WIDTH, SCREEN_HEIGHT)

        # 获取角色数据并更新 UI 颜色
        p1_data = get_character(p1_char)
        p2_data = get_character(p2_char)

        # 更新技能名称
        p1_skills = [s.name_cn for s in p1_data.special] if p1_data.special else ["必杀1", "必杀2"]
        p2_skills = [s.name_cn for s in p2_data.special] if p2_data.special else ["必杀1", "必杀2"]
        self.fight_ui.set_skill_names(p1_skills, p2_skills)

        self.fight_ui.p1_health.character_color = p1_data.stats.color
        self.fight_ui.p1_health.secondary_color = p1_data.stats.secondary_color
        self.fight_ui.p1_health.health_high = p1_data.stats.color
        self.fight_ui.p1_health.health_med = p1_data.stats.secondary_color
        self.fight_ui.p1_health.max_health = p1_data.stats.max_health

        self.fight_ui.p2_health.character_color = p2_data.stats.color
        self.fight_ui.p2_health.secondary_color = p2_data.stats.secondary_color
        self.fight_ui.p2_health.health_high = p2_data.stats.color
        self.fight_ui.p2_health.health_med = p2_data.stats.secondary_color
        self.fight_ui.p2_health.max_health = p2_data.stats.max_health

        self.start_round()

    def start_round(self):
        """开始一回合"""
        self.round_state = RoundState.READY
        self.round_timer.reset(99)
        self.prev_keys = None

        p1_data = get_character(self.p1_char_index)
        p2_data = get_character(self.p2_char_index)

        self.player1 = Player(1, p1_data, 300, self.stage.ground_y, self.p1_char_index, self.stage)
        if self.is_vs_ai:
            self.player2 = AIFighter(2, p2_data, 980, self.stage.ground_y, self.p2_char_index, self.stage)
        else:
            self.player2 = Player(2, p2_data, 980, self.stage.ground_y, self.p2_char_index, self.stage)

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

            p1_name = CHARACTER_LIST[self.p1_char_index]['name'] if hasattr(self, 'p1_char_index') else "P1"
            p2_name = CHARACTER_LIST[self.p2_char_index]['name'] if hasattr(self, 'p2_char_index') else "P2"
            self.fight_ui.draw(main_surface, p1_name, p2_name)

            # 绘制金币HUD
            if self.player1 and hasattr(self.player1, 'minion_manager'):
                self.player1.minion_manager.draw_hud(
                    main_surface, 375, 52, True, self.fight_ui.name_font)
            if self.player2 and hasattr(self.player2, 'minion_manager'):
                self.player2.minion_manager.draw_hud(
                    main_surface, SCREEN_WIDTH - 375, 52, False, self.fight_ui.name_font)
            self.announcement.draw(main_surface)

            # 绘制终极必杀技特效
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
