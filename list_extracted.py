import os
from PIL import Image

for base_name in ['LPC_pixelantasy_extracted', 'LPC_sidescroller_extracted']:
    base = r'e:\Workspace\游戏\DormFight\assets\sprites\fresh_characters' + os.sep + base_name
    if not os.path.exists(base):
        print('MISSING: ' + base_name)
        continue
    print('=== ' + base_name + ' ===')
    for root, dirs, files in os.walk(base):
        for f in sorted(files):
            fpath = os.path.join(root, f)
            rel = os.path.relpath(fpath, base)
            if f.endswith('.png'):
                try:
                    img = Image.open(fpath)
                    print('  PNG: %s %dx%d' % (rel, img.width, img.height))
                except:
                    print('  PNG: %s ERROR' % rel)
            else:
                size = os.path.getsize(fpath)
                print('  %s %dKB' % (rel, size//1024))
    print()
