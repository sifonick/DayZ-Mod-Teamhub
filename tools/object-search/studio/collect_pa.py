"""Copy the pictures of Patch Atlas's own objects (PA_ classes) into one folder.

    python tools/object-search/studio/collect_pa.py

Run from the repo root. Every cut-out whose name starts with pa_ in
assets/model-images-cutout/<category>/ is copied to assets/model-images-pa/<category>/.
If a PA_ object has no cut-out yet, its studio JPG is copied instead.
Only new or changed pictures are copied; run_batch.py calls this after every batch.
"""
import os
import shutil
import sys

CUTOUT = "assets/model-images-cutout"
STUDIO = "assets/model-images-studio"
OUT = "assets/model-images-pa"


def pa_files(src, ext):
    if not os.path.isdir(src):
        return
    for root, _, files in os.walk(src):
        for f in files:
            if f.lower().startswith("pa_") and f.lower().endswith(ext):
                yield os.path.relpath(os.path.join(root, f), src)


def copy_if_newer(src, dst):
    if os.path.exists(dst) and os.path.getsize(dst) == os.path.getsize(src) \
            and os.path.getmtime(dst) >= os.path.getmtime(src):
        return False
    os.makedirs(os.path.dirname(dst), exist_ok=True)
    shutil.copy2(src, dst)
    return True


def run():
    if not os.path.isdir("assets"):
        sys.exit("Run this from the repo root (the folder with assets/).")
    copied = total = 0
    have = set()
    for rel in pa_files(CUTOUT, ".webp"):
        total += 1
        have.add(os.path.splitext(rel)[0])
        copied += copy_if_newer(os.path.join(CUTOUT, rel), os.path.join(OUT, rel))
    for rel in pa_files(STUDIO, ".jpg"):
        if os.path.splitext(rel)[0] in have:
            continue
        total += 1
        copied += copy_if_newer(os.path.join(STUDIO, rel), os.path.join(OUT, rel))
    print(f"PA_ pictures: {total} in {OUT}/ ({copied} new or updated).")


if __name__ == "__main__":
    run()
