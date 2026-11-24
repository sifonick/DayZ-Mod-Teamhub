"""Build maps/atlas/empty-tiles.json: which transparent overlay tiles are completely blank.

The map page uses this list to skip downloading blank tiles. Re-run it whenever overlay
tiles are added or regenerated, and commit the new empty-tiles.json with the tiles:

    python tools/make-empty-tiles.py

Format, per map and layer: {"minZoom", "maxZoom", "bits"}. "bits" is base64 of a bit array
covering every tile from minZoom to maxZoom in order: for zoom z the tiles start at
index (4**z - 4**minZoom) / 3 and run row by row, index = start + y * 2**z + x.
Bit i is (byte[i >> 3] >> (i & 7)) & 1; 1 means the tile is fully transparent.
"""
import base64
import json
import os
import sys
from concurrent.futures import ProcessPoolExecutor

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
ATLAS = os.path.join(HERE, '..', 'maps', 'atlas')
OVERLAYS = ('roads', 'buildings', 'trees', 'labels_major', 'labels_minor', 'labels_village')


def blank(path):
    try:
        im = Image.open(path)
        if im.mode not in ('RGBA', 'LA', 'PA') and 'transparency' not in im.info:
            return False
        a = im.convert('RGBA').getchannel('A')
        return a.getextrema()[1] == 0
    except Exception:
        return False


def layer_bits(args):
    tpl, zmin, zmax = args
    n = sum(4 ** z for z in range(zmin, zmax + 1))
    bits = bytearray((n + 7) // 8)
    count = 0
    i = 0
    for z in range(zmin, zmax + 1):
        side = 1 << z
        for y in range(side):
            for x in range(side):
                p = os.path.join(ATLAS, tpl.replace('{z}', str(z)).replace('{x}', str(x)).replace('{y}', str(y)))
                if os.path.exists(p) and blank(p):
                    bits[i >> 3] |= 1 << (i & 7)
                    count += 1
                i += 1
    return base64.b64encode(bytes(bits)).decode('ascii'), count, n


def main():
    with open(os.path.join(ATLAS, 'tile-manifest.json'), encoding='utf-8') as fh:
        manifest = json.load(fh)
    jobs = []
    for key, m in manifest['maps'].items():
        for layer in OVERLAYS:
            L = m['layers'].get(layer)
            if L:
                jobs.append((key, layer, L['tileTemplate'], int(L['minZoom']), int(L['maxNativeZoom'])))
    out = {'schema': 'DayZEmptyTiles/1',
           'note': 'Fully transparent overlay tiles; the map skips downloading these. Rebuild with tools/make-empty-tiles.py after changing tiles.',
           'maps': {}}
    with ProcessPoolExecutor() as ex:
        results = list(ex.map(layer_bits, [(t, a, b) for _, _, t, a, b in jobs]))
    for (key, layer, tpl, zmin, zmax), (b64, count, n) in zip(jobs, results):
        out['maps'].setdefault(key, {})[layer] = {'template': tpl, 'minZoom': zmin, 'maxZoom': zmax, 'blank': count, 'total': n, 'bits': b64}
        print(f'{key:10s} {layer:15s} {count:6d} of {n:6d} blank', file=sys.stderr)
    with open(os.path.join(ATLAS, 'empty-tiles.json'), 'w', encoding='utf-8') as fh:
        json.dump(out, fh, separators=(',', ':'))
        fh.write('\n')


if __name__ == '__main__':
    main()
