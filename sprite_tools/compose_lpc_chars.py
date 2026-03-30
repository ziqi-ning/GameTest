# -*- coding: utf-8 -*-
"""
LPC角色精灵合成脚本
新版LPC行布局（每组4行=上/左/下/右，右向=组内第3行，0-indexed）：
  行3  = jump  (7帧)
  行7  = run   (8帧)  → 用作walk
  行11 = walk  (9帧)  → 用作idle
  行15 = attack(6帧)  → 用作所有攻击动作
  hair层只有21行(0-20)，以上行号均在范围内
"""
from PIL import Image
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CHAR_DIR   = "assets/sprites/characters"
MINION_DIR = "assets/sprites/minions"
W, H = 96, 63

# 新版LPC右向行号
ROW_JUMP   = 3   # 7帧
ROW_WALK   = 11  # 9帧 (walk)
ROW_IDLE   = 7   # 8帧 (run，用作idle站立)
ROW_ATTACK = 15  # 6帧

def make_sheet(frames, path):
    if not frames:
        print("  No frames: " + path)
        return
    sheet = Image.new("RGBA", (W * len(frames), H), (0,0,0,0))
    for i, f in enumerate(frames):
        sheet.paste(f.resize((W, H), Image.NEAREST), (i * W, 0))
    sheet.save(path)
    print("  Saved: " + os.path.basename(path) + " (" + str(len(frames)) + " frames)")

def build_char(out_dir, layer_files):
    """通用角色合成：加载层 → 提取帧 → 输出所有动作"""
    os.makedirs(out_dir, exist_ok=True)
    layers = {}
    for k, p in layer_files.items():
        if os.path.exists(p):
            layers[k] = Image.open(p).convert('RGBA')
        else:
            print("  MISSING: " + p)

    def get(row, ncols):
        frames = []
        for col in range(ncols):
            f = Image.new('RGBA', (64, 64), (0,0,0,0))
            for layer in layers.values():
                if row < layer.height // 64 and col < layer.width // 64:
                    f = Image.alpha_composite(f, layer.crop((col*64, row*64, (col+1)*64, (row+1)*64)))
            frames.append(f)
        return frames

    jump   = get(ROW_JUMP,   7)
    walk   = get(ROW_WALK,   8)
    idle   = get(ROW_IDLE,   9)
    attack = get(ROW_ATTACK, 6)

    make_sheet(idle[:4],    os.path.join(out_dir, "idle.png"))
    make_sheet(walk[:6],    os.path.join(out_dir, "walk.png"))
    make_sheet(jump[:4],    os.path.join(out_dir, "jump.png"))
    make_sheet(attack[:3],  os.path.join(out_dir, "jab.png"))
    make_sheet(attack[:3],  os.path.join(out_dir, "punch.png"))
    make_sheet(attack[:5],  os.path.join(out_dir, "kick.png"))
    make_sheet(attack[:5],  os.path.join(out_dir, "dive_kick.png"))
    make_sheet(attack[:3],  os.path.join(out_dir, "jump_kick.png"))
    make_sheet(attack[:2],  os.path.join(out_dir, "hurt.png"))

# ── 四个主角 ──────────────────────────────────────────────────────────────────

print("\n=== p1 红色拳击手 ===")
build_char(CHAR_DIR + "/p1", {
    'body':  'lpc_layers/body_musc_full.png',
    'head':  'lpc_layers/head_male_light.png',
    'hair':  'lpc_layers/hair_plain_red.png',
    'torso': 'lpc_layers/torso_red.png',
    'legs':  'lpc_layers/legs_shorts_red.png',
})

print("\n=== p2 科学家 ===")
build_char(CHAR_DIR + "/p2", {
    'body':    'lpc_layers/body_male_full.png',
    'head':    'lpc_layers/head_male_light.png',
    'hair':    'lpc_layers/hair_plain_black.png',
    'torso':   'lpc_layers/torso_blue.png',
    'legs':    'lpc_layers/legs_pants_blue.png',
    'glasses': 'lpc_layers/glasses_round_black.png',
})

print("\n=== p3 忍者 ===")
build_char(CHAR_DIR + "/p3", {
    'body':    'lpc_layers/body_male_full.png',
    'head':    'lpc_layers/head_male_light.png',
    'hair':    'lpc_layers/hair_bangsshort_black.png',
    'torso':   'lpc_layers/torso_black.png',
    'legs':    'lpc_layers/legs_pants_black.png',
    'bandana': 'lpc_layers/hat_bandana.png',
})

print("\n=== p4 魔法师 ===")
build_char(CHAR_DIR + "/p4", {
    'body':  'lpc_layers/body_male_full.png',
    'head':  'lpc_layers/head_male_light.png',
    'hair':  'lpc_layers/hair_long_purple.png',
    'torso': 'lpc_layers/torso_purple.png',
    'legs':  'lpc_layers/legs_pants_black.png',
    'cape':  'lpc_layers/cape_lavender.png',
    'hat':   'lpc_layers/hat_wizard_purple.png',
})

# ── 小兵 ──────────────────────────────────────────────────────────────────────

def build_minion(prefix, layer_files):
    os.makedirs(MINION_DIR, exist_ok=True)
    layers = {}
    for k, p in layer_files.items():
        if os.path.exists(p):
            layers[k] = Image.open(p).convert('RGBA')
        else:
            print("  MISSING: " + p)

    def get(row, ncols):
        frames = []
        for col in range(ncols):
            f = Image.new('RGBA', (64, 64), (0,0,0,0))
            for layer in layers.values():
                if row < layer.height // 64 and col < layer.width // 64:
                    f = Image.alpha_composite(f, layer.crop((col*64, row*64, (col+1)*64, (row+1)*64)))
            frames.append(f)
        return frames

    idle   = get(ROW_IDLE,   9)
    walk   = get(ROW_WALK,   8)
    attack = get(ROW_ATTACK, 6)

    make_sheet(idle[:4],    os.path.join(MINION_DIR, prefix + "_idle.png"))
    make_sheet(walk[:6],    os.path.join(MINION_DIR, prefix + "_walk.png"))
    make_sheet(attack[:4],  os.path.join(MINION_DIR, prefix + "_attack.png"))
    make_sheet(attack[:2],  os.path.join(MINION_DIR, prefix + "_hurt.png"))

print("\n=== 小兵 boxer ===")
build_minion("boxer", {
    'body':  'lpc_layers/body_teen_full.png',
    'head':  'lpc_layers/head_male_light.png',
    'hair':  'lpc_layers/hair_buzzcut_black.png',
    'torso': 'lpc_layers/torso_red.png',
    'legs':  'lpc_layers/legs_shorts_red.png',
})

print("\n=== 小兵 scientist ===")
build_minion("scientist", {
    'body':    'lpc_layers/body_teen_full.png',
    'head':    'lpc_layers/head_male_light.png',
    'hair':    'lpc_layers/hair_plain_white.png',
    'torso':   'lpc_layers/torso_white.png',
    'legs':    'lpc_layers/legs_pants_black.png',
    'glasses': 'lpc_layers/glasses_round_black.png',
})

print("\n=== 小兵 samurai ===")
build_minion("samurai", {
    'body':    'lpc_layers/body_teen_full.png',
    'head':    'lpc_layers/head_male_light.png',
    'hair':    'lpc_layers/hair_bangsshort_black.png',
    'torso':   'lpc_layers/torso_black.png',
    'legs':    'lpc_layers/legs_pants_black.png',
    'bandana': 'lpc_layers/hat_bandana.png',
})

print("\n=== 小兵 eagle ===")
build_minion("eagle", {
    'body':  'lpc_layers/body_teen_full.png',
    'head':  'lpc_layers/head_male_light.png',
    'hair':  'lpc_layers/hair_brown.png',
    'torso': 'lpc_layers/torso_green.png',
    'legs':  'lpc_layers/legs_pants_black.png',
})

print("\nAll done!")
