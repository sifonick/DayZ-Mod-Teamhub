"""Cut the studio pictures out of their background.

    python tools/object-search/studio/cutout.py          # every studio picture without a cut-out yet
    python tools/object-search/studio/cutout.py --redo   # all of them again

Reads assets/model-images-studio/<category>/<name>.jpg (and <name>_2.jpg) and writes
- assets/model-images-cutout/<category>/<name>.webp: the studio's plain background colour and
  the black bottom of the sky are made transparent, and the picture is cropped to the object.
  WebP keeps the transparency at a fraction of a PNG's size. Used by the Patch Atlas map.
- assets/model-images-photo/<category>/<name>.webp: the whole studio picture with its grey
  background, 768 px, small enough to upload. Used by the Object Finder.
Needs Pillow, numpy and scipy.
"""
import argparse
import os
import sys

import numpy as np
from PIL import Image
from scipy import ndimage

SRC = "assets/model-images-studio"
DST = "assets/model-images-cutout"
PHOTO = "assets/model-images-photo"
SIZE = 768


def cut_name(studio_path):
    """assets/model-images-studio/x/y.jpg -> assets/model-images-cutout/x/y.webp"""
    rel = os.path.relpath(studio_path, SRC)
    return os.path.join(DST, os.path.splitext(rel)[0] + ".webp").replace("\\", "/")


def photo_name(studio_path):
    """assets/model-images-studio/x/y.jpg -> assets/model-images-photo/x/y.webp"""
    rel = os.path.relpath(studio_path, SRC)
    return os.path.join(PHOTO, os.path.splitext(rel)[0] + ".webp").replace("\\", "/")


def stale(dst, src, redo):
    return redo or not os.path.exists(dst) or os.path.getmtime(dst) < os.path.getmtime(src)


def cutout(img, bg_tol=14, black_max=18, pad=0.06):
    a = np.asarray(img.convert("RGB")).astype(np.float32)
    h, w, _ = a.shape
    # background colour: the four corners (ignoring the black dome)
    k = max(4, min(h, w) // 25)
    corners = np.concatenate([a[:k, :k], a[:k, -k:], a[-k:, :k], a[-k:, -k:]]).reshape(-1, 3)
    corners = corners[corners.max(axis=1) > 60]
    bg = np.median(corners, axis=0) if len(corners) else np.array([224, 231, 240], np.float32)

    near_bg = np.sqrt(((a - bg) ** 2).sum(axis=2)) < bg_tol
    black = a.max(axis=2) < black_max
    # the dome: black plus its soft rim (darker shades of the background colour), one region
    # that holds black pixels and touches the bottom edge
    kk = (a @ bg) / (bg @ bg)
    shade = np.sqrt(((a - kk[..., None] * bg) ** 2).sum(axis=2)) < 16
    dark_key = black | (shade & (a.max(axis=2) < bg.max() - 6))
    labd, nd = ndimage.label(dark_key)
    dome = np.zeros_like(black)
    if nd:
        has_black = np.unique(labd[black])
        at_bottom = np.unique(labd[-1])
        ids = np.intersect1d(has_black[has_black > 0], at_bottom[at_bottom > 0])
        dome = np.isin(labd, ids)
        dome = ndimage.binary_dilation(dome, iterations=2) & (dark_key | near_bg | shade)
    key = near_bg | dome

    # remove keyed areas connected to the picture's edge (holes inside the object stay) ...
    lab, _ = ndimage.label(key)
    edge = np.unique(np.concatenate([lab[0], lab[-1], lab[:, 0], lab[:, -1]]))
    remove = np.isin(lab, edge[edge > 0])
    # ... and enclosed background-coloured gaps (between rails, inside a fence)
    gaps = near_bg & ~remove
    lab2, n2 = ndimage.label(gaps)
    if n2:
        sizes = ndimage.sum(gaps, lab2, range(1, n2 + 1))
        remove |= np.isin(lab2, 1 + np.nonzero(sizes > 40)[0])

    alpha = ndimage.gaussian_filter((~remove).astype(np.float32), 0.6)
    alpha[remove & (ndimage.distance_transform_edt(remove) > 2)] = 0
    ys, xs = np.nonzero(alpha > 0.5)
    if len(ys) < 30:
        return None
    t, b, l, r = ys.min(), ys.max(), xs.min(), xs.max()
    side = int(max(b - t, r - l) * (1 + pad * 2)) + 2
    cy, cx = (t + b) // 2, (l + r) // 2
    rgba = np.dstack([a, alpha * 255]).astype(np.uint8)
    out = Image.new("RGBA", (side, side), (0, 0, 0, 0))
    x0, y0 = cx - side // 2, cy - side // 2
    src = Image.fromarray(rgba, "RGBA").crop((max(x0, 0), max(y0, 0), min(x0 + side, w), min(y0 + side, h)))
    out.paste(src, (max(-x0, 0), max(-y0, 0)))
    return out


def run(redo=False, quiet=False):
    if not os.path.isdir(SRC):
        sys.exit(f"Run this from the repo root: can't find {SRC}/")
    todo = []
    for root, _, files in os.walk(SRC):
        if os.path.basename(root).startswith("_"):
            continue
        for f in files:
            if f.lower().endswith(".jpg"):
                src = os.path.join(root, f).replace("\\", "/")
                dst, pho = cut_name(src), photo_name(src)
                if stale(dst, src, redo) or stale(pho, src, redo):
                    todo.append((src, dst, pho))
    done = empty = photos = 0
    for i, (src, dst, pho) in enumerate(todo, 1):
        im = Image.open(src).convert("RGB")
        if stale(pho, src, redo):
            os.makedirs(os.path.dirname(pho), exist_ok=True)
            p = im.copy()
            p.thumbnail((SIZE, SIZE), Image.LANCZOS)
            p.save(pho, "WEBP", quality=82, method=4)
            photos += 1
        if stale(dst, src, redo):
            img = cutout(im)
            if img is None:
                empty += 1
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                img.resize((SIZE, SIZE), Image.LANCZOS).save(dst, "WEBP", quality=88, method=4)
                done += 1
        if not quiet and i % 50 == 0:
            print(f"  {i}/{len(todo)}")
    print(f"Cut-outs: {done} made, {empty} with nothing left after removing the background. "
          f"Finder pictures: {photos} made.")
    return done


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--redo", action="store_true", help="redo every cut-out, not only new pictures")
    run(ap.parse_args().redo)


if __name__ == "__main__":
    main()
