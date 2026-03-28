# 音频管理模块

import pygame
import os
from typing import Optional

class SoundManager:
    """音效管理器"""

    def __init__(self):
        pygame.mixer.init()
        self.sounds: dict = {}
        self.volume = 0.7
        self._load_placeholder_sounds()

    def _load_placeholder_sounds(self):
        """加载占位音效（实际项目中替换为真实音效）"""
        # 尝试加载音效文件，如果不存在则使用pygame内置
        sound_files = {
            'hit': 'assets/sounds/hit.wav',
            'block': 'assets/sounds/block.wav',
            'ko': 'assets/sounds/ko.wav',
            'fight': 'assets/sounds/fight.wav',
            'select': 'assets/sounds/select.wav',
        }

        for name, path in sound_files.items():
            try:
                if os.path.exists(path):
                    self.sounds[name] = pygame.mixer.Sound(path)
                    self.sounds[name].set_volume(self.volume)
                else:
                    # 创建简单的测试音效（实际不需要）
                    pass
            except:
                pass

    def play(self, sound_name: str):
        """播放音效"""
        if sound_name in self.sounds:
            self.sounds[sound_name].play()

    def play_hit(self):
        """播放命中音效"""
        self.play('hit')

    def play_block(self):
        """播放防御音效"""
        self.play('block')

    def play_ko(self):
        """播放KO音效"""
        self.play('ko')

    def play_fight(self):
        """播放开始音效"""
        self.play('fight')

    def play_select(self):
        """播放选择音效"""
        self.play('select')

    def set_volume(self, volume: float):
        """设置音量（0-1）"""
        self.volume = max(0.0, min(1.0, volume))
        for sound in self.sounds.values():
            sound.set_volume(self.volume)


class BGMManager:
    """背景音乐管理器"""

    def __init__(self):
        pygame.mixer.init(frequency=44100)
        self.current_bgm: Optional[pygame.mixer.Sound] = None
        self.volume = 0.5
        self.is_playing = False

    def play(self, bgm_name: str = 'battle'):
        """播放背景音乐"""
        bgm_files = {
            'menu': 'assets/music/menu.wav',
            'battle': 'assets/music/battle.wav',
            'victory': 'assets/music/victory.wav',
        }

        path = bgm_files.get(bgm_name)
        if path and os.path.exists(path):
            try:
                if self.current_bgm:
                    self.current_bgm.stop()
                self.current_bgm = pygame.mixer.Sound(path)
                self.current_bgm.set_volume(self.volume)
                self.current_bgm.play(loops=-1)
                self.is_playing = True
            except:
                pass

    def stop(self):
        """停止背景音乐"""
        if self.current_bgm:
            self.current_bgm.stop()
            self.is_playing = False

    def pause(self):
        """暂停背景音乐"""
        if self.current_bgm and self.is_playing:
            pygame.mixer.pause()

    def resume(self):
        """恢复背景音乐"""
        if self.current_bgm and self.is_playing:
            pygame.mixer.unpause()

    def set_volume(self, volume: float):
        """设置音量（0-1）"""
        self.volume = max(0.0, min(1.0, volume))
        if self.current_bgm:
            self.current_bgm.set_volume(self.volume)


# 全局实例
sound_manager = SoundManager()
bgm_manager = BGMManager()
