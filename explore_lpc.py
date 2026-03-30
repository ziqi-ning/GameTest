import urllib.request, json, os

BASE_API = "https://api.github.com/repos/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator/contents/spritesheets"
BASE_RAW = "https://raw.githubusercontent.com/LiberatedPixelCup/Universal-LPC-Spritesheet-Character-Generator/master/spritesheets"
OUT = "lpc_layers"
os.makedirs(OUT, exist_ok=True)

def api_get(path):
    url = f"{BASE_API}/{path}"
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as r:
        return json.loads(r.read())

def download(path, out_name):
    url = f"{BASE_RAW}/{path}"
    out = os.path.join(OUT, out_name)
    try:
        urllib.request.urlretrieve(url, out)
        print(f"OK: {out_name}")
        return True
    except Exception as e:
        print(f"FAIL: {path} -> {e}")
        return False

# 探索 torso/clothes/collared/thick
print("=== torso/clothes/collared/thick ===")
items = api_get("torso/clothes/collared/thick")
for item in items:
    print(f"  {item['name']} ({item['type']})")
    if item['type'] == 'dir':
        sub = api_get(f"torso/clothes/collared/thick/{item['name']}")
        for s in sub[:5]:
            print(f"    {s['name']} ({s['type']})")
            if s['type'] == 'dir':
                sub2 = api_get(f"torso/clothes/collared/thick/{item['name']}/{s['name']}")
                for s2 in sub2[:5]:
                    print(f"      {s2['name']} ({s2['type']}) {s2.get('download_url','')[:80]}")
