# LPC 角色素材清单

来源：[sanderfrenken/Universal-LPC-Spritesheet-Character-Generator](https://github.com/sanderfrenken/Universal-LPC-Spritesheet-Character-Generator)
许可证：CC-BY-SA 3.0 / GPL3

---

## 身体体型 `body/bodies/`

| 体型 | 说明 |
|------|------|
| male | 普通男性 |
| female | 普通女性 |
| muscular | 肌肉男性 |
| teen | 青少年 |
| child | 儿童 |
| pregnant | 孕妇 |
| skeleton | 骷髅 |
| zombie | 僵尸 |

---

## 发型 `hair/` （80+ 种）

| 类别 | 发型 |
|------|------|
| 短发 | balding, buzzcut, curtains, high_and_tight, pixie, plain, relm_short, shorthawk, bangsshort, curly_short, curly_short2, flat_top_fade, flat_top_straight, twists_fade, twists_straight |
| 中长发 | bangs, bangs_bun, bob, bob_side_part, bedhead, cowlick, cowlick_tall, halfmessy, idol, messy, messy1, messy2, messy3, mop, natural, page, page2, parted, parted2, parted3, parted_side_bangs, parted_side_bangs2, relm_ponytail, sara, single, spiked, spiked2, swoop, swoop_side, unkempt, wavy |
| 长发 | bangslong, bangslong2, braid, braid2, curtains_long, dreadlocks_long, dreadlocks_short, extensions, half_up, high_ponytail, lob, long, long_band, long_center_part, long_messy, long_messy2, long_straight, long_tied, longhawk, loose, pigtails, pigtails_bangs, ponytail, ponytail2, princess, shoulderl, shoulderr, xlong |
| 特殊 | afro, bunches, cornrows, jewfro, spiked_beehive, spiked_liberty, spiked_liberty2, spiked_porcupine |

**颜色**（每种发型都有）：ash, black, blonde, blue, carrot, chestnut, dark_brown, dark_gray, gray, light_brown, navy, orange, pink, platinum, raven, red, redhead, rose, sandy, strawberry, violet, white

---

## 帽子 `hat/`

| 类别 | 款式 |
|------|------|
| 头盔 helmet | armet, barbarian, barbuta, bascinet, close, flattop, greathelm, horned, kettle, legion, mail, maximus, morion, nasal, norman, pointed, spangenhelm, sugarloaf, xeon 等 |
| 布帽 cloth | bandana, bandana2, feather_cap, hijab, hood, hood_sack |
| 正式 formal | bowler（圆顶礼帽）, crown（王冠）, tiara（头冠）, tophat（大礼帽）|
| 海盗 pirate | bandana, bicorne, bonnie, cavalier, kerchief, tricorne |
| 魔法 magic | misc, wizard（巫师帽）|
| 头带 headband | hairtie, thick, tied |
| 节日 holiday | christmas, elf, santa |
| 配件 accessory | crest, horns_downward, horns_short, horns_upward, plumage, wings |

---

## 面部配件 `facial/`

| 类别 | 款式 |
|------|------|
| 眼镜 glasses | glasses, halfmoon, nerd（书呆子眼镜）, round, secretary, shades, sunglasses |
| 耳环 earrings | emerald, moon, pear, princess, simple, stud |
| 眼罩 patches | eyepatch, eyepatch2, small |
| 单片眼镜 monocle | left, right |
| 面具 masks | plain |

---

## 上衣 `torso/clothes/longsleeve/longsleeve/male/`

24种颜色：black, blue, bluegray, brown, charcoal, forest, gray, green, lavender, leather, maroon, navy, orange, pink, purple, red, rose, sky, slate, tan, teal, walnut, **white**, yellow

---

## 裤子 `legs/pants/male/`

25种颜色：black, blue, bluegray, brown, charcoal, forest, gray, green, lavender, leather, magenta, maroon, navy, orange, pink, purple, red, rose, sky, slate, tan, teal, walnut, white, yellow

---

## 武器 `weapon/`

| 类别 | 武器 |
|------|------|
| 剑类 sword | arming, dagger, glowsword, katana, longsword, rapier, saber, scimitar |
| 钝器 blunt | club, flail, mace, waraxe |
| 长柄 polearm | cane, dragonspear, halberd, longspear, scythe, spear, trident |
| 远程 ranged | boomerang, bow, crossbow, slingshot |
| 魔法 magic | crystal, diamond, gnarled, loop, simple（法杖）|

---

## 鞋子 `feet/`

armour, boots, boots2, boots_fold, boots_plating, boots_rim, ghillies, hoofs, sandals, shoes, shoes2, slippers, socks

---

## 其他配件

| 类别 | 内容 |
|------|------|
| 披风 cape | solid, tattered, trim |
| 肩甲 shoulders | epaulets, leather, legion, mantal, plate |
| 盾牌 shield | crusader, heater, kite, scutum 等 |
| 裙子 dress | bodice, kimono, sash, slit |
| 眼睛 eyes | cyclops, eyebrows, human |
| 胡须 beards | beard, mustache |
| 头部 head | ears, fins, horns, nose, wrinkles |

---

## 当前已下载到 `lpc_layers/` 的层

| 文件 | 说明 |
|------|------|
| body_male_full.png | 普通男性完整身体（含头部） |
| body_musc_full.png | 肌肉男性完整身体（含头部） |
| hair_black.png | 黑色短发（plain发型） |
| hair_white.png | 白色短发 |
| hair_brown.png | 棕色短发 |
| hair_blonde.png | 金色短发 |
| hair_balding.png | 秃顶 |
| torso_white.png | 白色长袖上衣 |
| torso_red.png | 红色长袖上衣 |
| torso_purple.png | 紫色长袖上衣 |
| torso_green.png | 绿色长袖上衣 |
| legs_pants_black.png | 黑色裤子 |
| legs_shorts_red.png | 红色短裤 |

---

## 如何给角色换装

修改 `compose_lpc_chars.py` 里对应角色的调用参数：

```python
compose_new_lpc(
    char_idx=3,
    body_file="body_male_full.png",   # 换体型
    hair_file="hair_black.png",        # 换发型
    torso_file="torso_purple.png",     # 换上衣颜色
    legs_file="legs_pants_black.png",  # 换裤子颜色
    label="忍者"
)
```

需要新素材时运行 `download_lpc_layers.py`，修改里面的下载列表即可。
