# -*- coding: utf-8 -*-
"""
生成游戏道具图像（32x32 像素风格）
输出到 assets/items/
"""
from PIL import Image, ImageDraw
import os

os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
OUT = "assets/items"
os.makedirs(OUT, exist_ok=True)

SZ = 32  # 图标尺寸

def new_img():
    return Image.new("RGBA", (SZ, SZ), (0, 0, 0, 0))

def save(img, name):
    img.save(os.path.join(OUT, name))
    print(f"  {name}")

# ── 金币袋子 ──────────────────────────────────────────────────────────────────
def make_coin_bag():
    img = new_img(); d = ImageDraw.Draw(img)
    # 袋子主体（棕色）
    d.ellipse([6, 10, 26, 28], fill=(160, 100, 40), outline=(100, 60, 20), width=2)
    # 袋口
    d.ellipse([10, 6, 22, 14], fill=(130, 80, 30), outline=(80, 50, 15), width=1)
    # 绑绳
    d.line([14, 6, 14, 3], fill=(80, 50, 15), width=2)
    d.line([18, 6, 18, 3], fill=(80, 50, 15), width=2)
    d.line([14, 3, 18, 3], fill=(80, 50, 15), width=2)
    # 金币符号
    d.text((12, 14), "G", fill=(255, 220, 50))
    save(img, "coin_bag.png")

# ── 法术袋子 ──────────────────────────────────────────────────────────────────
def make_mana_bag():
    img = new_img(); d = ImageDraw.Draw(img)
    # 袋子主体（蓝色）
    d.ellipse([6, 10, 26, 28], fill=(40, 80, 200), outline=(20, 50, 150), width=2)
    # 袋口
    d.ellipse([10, 6, 22, 14], fill=(30, 60, 170), outline=(15, 40, 120), width=1)
    # 绑绳
    d.line([14, 6, 14, 3], fill=(15, 40, 120), width=2)
    d.line([18, 6, 18, 3], fill=(15, 40, 120), width=2)
    d.line([14, 3, 18, 3], fill=(15, 40, 120), width=2)
    # 魔法符号（星形）
    d.text((12, 14), "★", fill=(150, 220, 255))
    save(img, "mana_bag.png")

# ── 血袋子 ────────────────────────────────────────────────────────────────────
def make_health_bag():
    img = new_img(); d = ImageDraw.Draw(img)
    # 袋子主体（红色）
    d.ellipse([6, 10, 26, 28], fill=(200, 40, 40), outline=(140, 20, 20), width=2)
    # 袋口
    d.ellipse([10, 6, 22, 14], fill=(170, 30, 30), outline=(110, 15, 15), width=1)
    # 绑绳
    d.line([14, 6, 14, 3], fill=(110, 15, 15), width=2)
    d.line([18, 6, 18, 3], fill=(110, 15, 15), width=2)
    d.line([14, 3, 18, 3], fill=(110, 15, 15), width=2)
    # 十字符号
    d.rectangle([14, 14, 18, 26], fill=(255, 100, 100))
    d.rectangle([10, 18, 22, 22], fill=(255, 100, 100))
    save(img, "health_bag.png")

# ── 核弹发射器 ────────────────────────────────────────────────────────────────
def make_nuke_launcher():
    img = new_img(); d = ImageDraw.Draw(img)
    # 发射管（深灰）
    d.rectangle([4, 14, 24, 22], fill=(80, 80, 80), outline=(50, 50, 50), width=1)
    d.rectangle([20, 12, 28, 24], fill=(100, 100, 100), outline=(60, 60, 60), width=1)
    # 握把
    d.rectangle([6, 22, 12, 28], fill=(60, 40, 20), outline=(40, 25, 10), width=1)
    # 核弹头（黄色警告）
    d.ellipse([22, 8, 30, 16], fill=(255, 220, 0), outline=(200, 150, 0), width=1)
    d.text((23, 9), "☢", fill=(200, 0, 0))
    # 警告条纹
    d.line([4, 14, 24, 14], fill=(255, 200, 0), width=1)
    save(img, "nuke_launcher.png")

# ── 加特林 ────────────────────────────────────────────────────────────────────
def make_gatling():
    img = new_img(); d = ImageDraw.Draw(img)
    # 多管（6根）
    for i, y in enumerate([8, 11, 14, 17, 20, 23]):
        color = (120, 120, 120) if i % 2 == 0 else (100, 100, 100)
        d.rectangle([14, y, 28, y+2], fill=color, outline=(70, 70, 70))
    # 旋转轴
    d.ellipse([10, 12, 18, 20], fill=(80, 80, 80), outline=(50, 50, 50), width=1)
    d.ellipse([12, 14, 16, 18], fill=(150, 150, 150))
    # 握把
    d.rectangle([4, 18, 12, 28], fill=(60, 40, 20), outline=(40, 25, 10), width=1)
    # 弹链
    for i in range(3):
        d.ellipse([2+i*3, 22, 4+i*3, 26], fill=(255, 200, 0), outline=(180, 140, 0))
    save(img, "gatling.png")

# ── 红色法杖（火焰）─────────────────────────────────────────────────────────
def make_staff_red():
    img = new_img(); d = ImageDraw.Draw(img)
    # 杖身
    d.line([8, 28, 20, 8], fill=(150, 80, 40), width=3)
    d.line([9, 28, 21, 8], fill=(180, 100, 50), width=1)
    # 宝珠（红色）
    d.ellipse([16, 4, 26, 14], fill=(220, 50, 20), outline=(255, 100, 50), width=2)
    d.ellipse([18, 6, 24, 12], fill=(255, 150, 80))
    # 火焰效果
    d.polygon([(21, 4), (19, 0), (23, 2), (21, -1), (25, 3)], fill=(255, 200, 0))
    save(img, "staff_red.png")

# ── 蓝色法杖（海啸）─────────────────────────────────────────────────────────
def make_staff_blue():
    img = new_img(); d = ImageDraw.Draw(img)
    # 杖身
    d.line([8, 28, 20, 8], fill=(40, 80, 160), width=3)
    d.line([9, 28, 21, 8], fill=(60, 120, 200), width=1)
    # 宝珠（蓝色）
    d.ellipse([16, 4, 26, 14], fill=(30, 100, 220), outline=(100, 180, 255), width=2)
    d.ellipse([18, 6, 24, 12], fill=(150, 210, 255))
    # 水波效果
    d.arc([14, 2, 28, 10], 200, 340, fill=(100, 200, 255), width=2)
    d.arc([16, 0, 26, 8], 200, 340, fill=(200, 240, 255), width=1)
    save(img, "staff_blue.png")

# ── 绿色法杖（炸弹）─────────────────────────────────────────────────────────
def make_staff_green():
    img = new_img(); d = ImageDraw.Draw(img)
    # 杖身
    d.line([8, 28, 20, 8], fill=(40, 120, 40), width=3)
    d.line([9, 28, 21, 8], fill=(60, 160, 60), width=1)
    # 宝珠（绿色）
    d.ellipse([16, 4, 26, 14], fill=(40, 180, 40), outline=(100, 255, 100), width=2)
    d.ellipse([18, 6, 24, 12], fill=(150, 255, 150))
    # 爆炸效果
    for angle_pts in [[(21,2),(23,0),(25,4)], [(25,6),(28,5),(26,9)], [(19,0),(17,2),(21,4)]]:
        d.polygon(angle_pts, fill=(200, 255, 0))
    save(img, "staff_green.png")

# ── 生成所有道具 ──────────────────────────────────────────────────────────────
print("生成道具图像...")
make_coin_bag()
make_mana_bag()
make_health_bag()
make_nuke_launcher()
make_gatling()
make_staff_red()
make_staff_blue()
make_staff_green()
print(f"\n全部保存到 {OUT}/")
print("道具列表：")
for f in sorted(os.listdir(OUT)):
    print(f"  {f}")
