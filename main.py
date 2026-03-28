# 主游戏文件

import pygame
import sys
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
from ui.fight_ui import FightUI, VictoryScreen
from ui.timer import Timer, Announcement
from stages.stage_1 import Stage1

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

        # 战斗
        self.fight_ui = FightUI(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.victory_screen = VictoryScreen(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 对战角色
        self.player1: Optional[Player] = None
        self.player2: Optional[Fighter] = None

        # 场景
        self.stage = Stage1(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 回合管理
        self.p1_wins = 0
        self.p2_wins = 0
        self.max_wins = 2
        self.round_timer = Timer(SCREEN_WIDTH // 2, 35, 99)
        self.round_state = RoundState.READY

        # 公告
        self.announcement = Announcement(SCREEN_WIDTH, SCREEN_HEIGHT)

        # 屏幕震动
        self.screen_shake = 0.0
        self.shake_offset_x = 0
        self.shake_offset_y = 0

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
                    self.start_match(selections[0], selections[1])

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
        elif self.state == GameState.FIGHTING:
            self.update_fight(dt)
        elif self.state == GameState.ROUND_END:
            self.victory_screen.update(dt)

        # 屏幕震动
        if self.screen_shake > 0:
            self.screen_shake -= dt * 30
            self.shake_offset_x = (pygame.time.get_ticks() % 7) - 3
            self.shake_offset_y = (pygame.time.get_ticks() % 5) - 2
        else:
            self.shake_offset_x = 0
            self.shake_offset_y = 0

    def update_fight(self, dt: float):
        """更新战斗"""
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
            block = bool(keys[pygame.K_u])
            light = key_pressed(pygame.K_j)
            heavy = key_pressed(pygame.K_k)
            special = key_pressed(pygame.K_l)

            self.player1.handle_input(left, right, up, down, light, heavy, special, block)
            self.player1.update(dt, self.player2)

        # 玩家2输入
        if self.player2 and self.round_state == RoundState.FIGHT:
            if self.is_vs_ai:
                self.player2.update_ai(dt, self.player1)
            else:
                p2_left = bool(keys[pygame.K_LEFT])
                p2_right = bool(keys[pygame.K_RIGHT])
                p2_up = bool(keys[pygame.K_UP])
                p2_down = bool(keys[pygame.K_DOWN])
                p2_block = bool(keys[pygame.K_KP0])
                self.player2.handle_input(p2_left, p2_right, p2_up, p2_down, False, False, False, p2_block)
            self.player2.update(dt, self.player1)

        # 检测胜负
        self.check_match_end()

        # 更新UI
        self.fight_ui.update(dt, self.player1, self.player2)

        # 屏幕震动
        if self.player1 and self.player1.screen_shake > 0:
            self.screen_shake = max(self.screen_shake, self.player1.screen_shake)
            self.player1.screen_shake = 0
        if self.player2 and self.player2.screen_shake > 0:
            self.screen_shake = max(self.screen_shake, self.player2.screen_shake)
            self.player2.screen_shake = 0

    def start_match(self, p1_char: int, p2_char: int):
        """开始对战"""
        self.state = GameState.FIGHTING
        self.p1_wins = 0
        self.p2_wins = 0
        self.fight_ui.set_round_wins(0, 0)
        self.p1_char_index = p1_char
        self.p2_char_index = p2_char
        self.start_round()

    def start_round(self):
        """开始一回合"""
        self.round_state = RoundState.READY
        self.round_timer.reset(99)
        self.prev_keys = None

        p1_data = get_character(self.p1_char_index)
        p2_data = get_character(self.p2_char_index)

        self.player1 = Player(1, p1_data, 300, self.stage.ground_y)
        if self.is_vs_ai:
            self.player2 = AIFighter(2, p2_data, 980, self.stage.ground_y)
        else:
            self.player2 = Player(2, p2_data, 980, self.stage.ground_y)

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

    def render(self):
        """渲染"""
        main_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))

        if self.state == GameState.MENU:
            self.menu.draw(main_surface)
        elif self.state == GameState.CHARACTER_SELECT:
            self.character_select.draw(main_surface)
        elif self.state in [GameState.FIGHTING, GameState.ROUND_END]:
            self.stage.draw(main_surface)
            if self.player1:
                self.player1.draw(main_surface)
            if self.player2:
                self.player2.draw(main_surface)

            p1_name = CHARACTER_LIST[self.p1_char_index]['name'] if hasattr(self, 'p1_char_index') else "P1"
            p2_name = CHARACTER_LIST[self.p2_char_index]['name'] if hasattr(self, 'p2_char_index') else "P2"
            self.fight_ui.draw(main_surface, p1_name, p2_name)
            self.announcement.draw(main_surface)

            if self.state == GameState.ROUND_END:
                self.victory_screen.draw(main_surface, p1_name, p2_name)

        if self.shake_offset_x != 0 or self.shake_offset_y != 0:
            self.screen.fill((0, 0, 0))
            self.screen.blit(main_surface, (self.shake_offset_x, self.shake_offset_y))
        else:
            self.screen.blit(main_surface, (0, 0))


if __name__ == "__main__":
    game = Game()
    game.run()
