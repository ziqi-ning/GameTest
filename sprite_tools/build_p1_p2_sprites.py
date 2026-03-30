# -*- coding: utf-8 -*-
"""
从现有开源素材为 p1/p2 生成 96×63 spritesheet

p1 — 红色拳击手：Boxer CC0（Raga2D）
     来源：assets/sprites/fresh_characters/boxer_cc0_extracted/Boxer Game Sprite OGA/
     每帧原始尺寸：744×711，单帧 PNG

p2 — 科学家：lablady_frames（实验室女士，白大褂）
     来源：assets/sprites/fresh_characters/lablady_frames/
     格式：散帧 lablady_rROW_cCOL.png，LPC 标准布局
     行：0=上 1=左 2=下 3=右，取行3（右向）
"""

from PIL import Image
import os

OUT_W, OUT_H = 96, 63
CHAR_DIR = "assets/sprites/characters"

# ─── 工具函数 ─────────────────────────────────────────────────────────────────

def scale_to_fit(img: Image.Image, w: int, h: int) -> Image.Image:
    """强制缩放到目标尺寸（与compose_lpc_chars.py的make_sheet一致）"""
    return img.resize((w, h), Image.NEAREST)

def make_sheet(frames: list, out_path: str):
    """把帧列表横向拼成 spritesheet 并保存"""
    if not frames:
        print(f"  [SKIP] 无帧: {out_path}")
        return
    sheet = Image.new("RGBA", (OUT_W * len(frames), OUT_H), (0, 0, 0, 0))
    for i, f in enumerate(frames):
        sheet.paste(f, (i * OUT_W, 0))
    sheet.save(out_path)
    print(f"  [OK] {os.path.basename(out_path)}  ({len(frames)} 帧)")

def load_frames_from_dir(folder: str, prefix: str, count: int) -> list:
    """从目录加载 prefix_000.png ~ prefix_00N.png"""
    frames = []
    for i in range(count):
        p = os.path.join(folder, f"{prefix}_{i:03d}.png")
        if not os.path.exists(p):
            print(f"  [MISS] {p}")
            break
        frames.append(Image.open(p).convert("RGBA"))
    return frames

def load_lablady_row(frames_dir: str, row: int, cols: list) -> list:
    """从 lablady_frames 散帧加载指定行的指定列"""
    frames = []
    for c in cols:
        p = os.path.join(frames_dir, f"lablady_r{row}_c{c}.png")
        if not os.path.exists(p):
            print(f"  [MISS] {p}")
            continue
        frames.append(Image.open(p).convert("RGBA"))
    return frames

# ─── P1：红色拳击手（Boxer CC0）────────────────────────────────────────────────

def build_p1():
    base = "assets/sprites/fresh_characters/boxer_cc0_extracted/Boxer Game Sprite OGA"
    out_dir = os.path.join(CHAR_DIR, "p1")
    os.makedirs(out_dir, exist_ok=True)
    print("\n=== p1 红色拳击手（Boxer CC0）===")

    def load_boxer(subpath: str, prefix: str, count: int) -> list:
        folder = os.path.join(base, subpath)
        raw = load_frames_from_dir(folder, prefix, count)
        return [scale_to_fit(f, OUT_W, OUT_H) for f in raw]

    # idle (4帧，从10帧取前4)
    idle = load_boxer("1-Idle", "__Boxer2_Idle", 10)[:4]
    make_sheet(idle, os.path.join(out_dir, "idle.png"))

    # walk (6帧，从10帧取前6)
    walk = load_boxer("2-Walk/1-Forward", "__Boxer2_Forward", 10)[:6]
    make_sheet(walk, os.path.join(out_dir, "walk.png"))

    # jump (4帧，复用idle)
    make_sheet(idle, os.path.join(out_dir, "jump.png"))

    # jab (3帧，从8帧取前3)
    jab = load_boxer("3-Punch/1-JabRight", "__Boxer2_Punch1", 8)[:3]
    make_sheet(jab, os.path.join(out_dir, "jab.png"))

    # punch (3帧，同jab)
    make_sheet(jab, os.path.join(out_dir, "punch.png"))

    # kick (5帧，用uppercut前5帧)
    kick = load_boxer("3-Punch/3-Uppercut", "__Boxer2_Punch3", 8)[:5]
    if not kick:
        kick = load_boxer("3-Punch/2-JabLeft", "__Boxer2_Punch2", 8)[:5]
    make_sheet(kick, os.path.join(out_dir, "kick.png"))

    # dive_kick / jump_kick (5帧，复用kick)
    make_sheet(kick, os.path.join(out_dir, "dive_kick.png"))
    make_sheet(kick[:3], os.path.join(out_dir, "jump_kick.png"))

    # hurt (2帧)
    hurt = load_boxer("5-Hurt/1-Hurt", "__Boxer2_Hurt1", 8)[:2]
    make_sheet(hurt, os.path.join(out_dir, "hurt.png"))

    print("  p1 done!")

# ─── P2：科学家（LPC_professor，标准LPC 32×64）──────────────────────────────────
# LPC_professor_walk.png: 576×256，18列×4行，32×64每帧
# 行布局：0=上 1=左 2=下 3=右
# 列布局（每行18列）：
#   0~8   = walk (9帧)
#   9~14  = slash/attack (6帧)
#   15~17 = cast (3帧)
#
# LPC_professor_hurt.png: 384×64，12列×1行，32×64每帧

def build_p2():
    walk_src = "assets/sprites/fresh_characters/LPC_professor_walk.png"
    hurt_src = "assets/sprites/fresh_characters/LPC_professor_hurt.png"
    out_dir = os.path.join(CHAR_DIR, "p2")
    os.makedirs(out_dir, exist_ok=True)
    print("\n=== p2 科学家（LPC_professor，32x64）===")

    walk_img = Image.open(walk_src).convert("RGBA")
    hurt_img = Image.open(hurt_src).convert("RGBA")
    FW, FH = 32, 64
    ROW = 3  # 右向

    def get_walk_frames(cols: list) -> list:
        frames = []
        for c in cols:
            frame = walk_img.crop((c * FW, ROW * FH, (c + 1) * FW, (ROW + 1) * FH))
            frames.append(scale_to_fit(frame, OUT_W, OUT_H))
        return frames

    def get_hurt_frames(cols: list) -> list:
        frames = []
        for c in cols:
            frame = hurt_img.crop((c * FW, 0, (c + 1) * FW, FH))
            frames.append(scale_to_fit(frame, OUT_W, OUT_H))
        return frames

    # idle (4帧，walk前4帧)
    idle = get_walk_frames([0, 1, 2, 3])
    make_sheet(idle, os.path.join(out_dir, "idle.png"))

    # walk (6帧)
    walk = get_walk_frames([0, 1, 2, 3, 4, 5])
    make_sheet(walk, os.path.join(out_dir, "walk.png"))

    # jump (4帧，复用idle)
    make_sheet(idle, os.path.join(out_dir, "jump.png"))

    # jab (3帧，slash前3帧)
    jab = get_walk_frames([9, 10, 11])
    make_sheet(jab, os.path.join(out_dir, "jab.png"))

    # punch (3帧，同jab)
    make_sheet(jab, os.path.join(out_dir, "punch.png"))

    # kick (5帧，slash全部)
    kick = get_walk_frames([9, 10, 11, 12, 13])
    make_sheet(kick, os.path.join(out_dir, "kick.png"))

    # dive_kick / jump_kick
    make_sheet(kick, os.path.join(out_dir, "dive_kick.png"))
    make_sheet(kick[:3], os.path.join(out_dir, "jump_kick.png"))

    # hurt (2帧，用professor_hurt.png前2帧)
    hurt = get_hurt_frames([0, 1])
    make_sheet(hurt, os.path.join(out_dir, "hurt.png"))

    print("  p2 done!")


if __name__ == "__main__":
    build_p1()
    build_p2()
    print("\nAll done! 重启游戏查看效果。")
