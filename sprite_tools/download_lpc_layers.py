# -*- coding: utf-8 -*-
"""
从 GitHub 下载 LPC 完整角色层素材（含头部）
来源：sanderfrenken/Universal-LPC-Spritesheet-Character-Generator
"""
import urllib.request
import os

OUT_DIR = "lpc_layers"
os.makedirs(OUT_DIR, exist_ok=True)

BASE = "https://raw.githubusercontent.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator/master/spritesheets"

layers = {
    # 完整身体（含头部+肤色，这是真正完整的角色层）
    "body_male_full.png":     f"{BASE}/body/bodies/male.png",
    "body_musc_full.png":     f"{BASE}/body/bodies/muscular.png",
    # 头发（男性短发）
    "hair_white_short.png":   f"{BASE}/hair/male/short/white.png",
    "hair_black_short.png":   f"{BASE}/hair/male/short/black.png",
    "hair_brown_short.png":   f"{BASE}/hair/male/short/brown.png",
    "hair_blonde_short.png":  f"{BASE}/hair/male/short/blonde.png",
}

print("开始下载 LPC 层素材...")
success = []
failed = []

for filename, url in layers.items():
    out_path = os.path.join(OUT_DIR, filename)
    try:
        print(f"  下载 {filename}...", end=" ", flush=True)
        urllib.request.urlretrieve(url, out_path)
        size = os.path.getsize(out_path)
        if size < 500:
            os.remove(out_path)
            raise Exception(f"文件太小({size}字节)")
        print(f"OK ({size//1024}KB)")
        success.append(filename)
    except Exception as e:
        print(f"FAILED: {e}")
        failed.append((filename, url))

print(f"\n成功: {len(success)}/{len(layers)}")
if failed:
    print("失败:")
    for f, u in failed:
        print(f"  {f} <- {u}")
