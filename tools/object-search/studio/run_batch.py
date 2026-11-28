"""Photograph the next batch of objects and put them straight into the Object Finder.

    python tools/object-search/studio/run_batch.py 100           # the next 100 objects
    python tools/object-search/studio/run_batch.py 1000 --push   # 1000, then upload to GitHub

Run from the repo root (or use Batch_100.bat / Batch_1000.bat in this folder). It:
  1. lists the next objects that have no studio picture yet (make_capture_list.py),
  2. starts Patch Atlas Studio and takes the pictures (capture.py), restarting the studio if
     the game crashes (the object it crashed on is skipped from then on),
  3. cuts every new picture out of its background (cutout.py) and copies the pictures of
     Patch Atlas's own PA_ objects into assets/model-images-pa (collect_pa.py),
  4. rebuilds the Object Finder's catalogue so the new pictures show up,
  5. with --push, commits the cut-outs and the catalogue and pushes them to GitHub, so the
     website shows them too.
Leave the PC alone while it runs: anything covering the DayZ window ends up in the pictures.
"""
import argparse
import json
import os
import subprocess
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.dirname(HERE)
DEFAULT_STUDIO = r"C:\Program Files (x86)\Steam\steamapps\common\DayZ\@PatchAtlas_Studio"
PY = sys.executable


def step(title):
    print(f"\n=== {title} ===", flush=True)


def py(script, *args, check=True):
    r = subprocess.run([PY, os.path.join(HERE, script), *args])
    if check and r.returncode != 0:
        sys.exit(f"{script} stopped with an error (code {r.returncode}).")
    return r.returncode


def close_game():
    subprocess.run(["taskkill", "/IM", "DayZ_x64.exe", "/F"], capture_output=True)
    time.sleep(3)


def start_studio(studio):
    bat = os.path.join(studio, "Start_PA_Studio.bat")
    if not os.path.exists(bat):
        sys.exit(f"Can't find {bat}. Pass --studio with the @PatchAtlas_Studio folder.")
    # Opened the same way as a double-click. "cmd /c <path>" breaks on paths with brackets,
    # such as "Program Files (x86)", and then the game never starts.
    os.startfile(bat)
    for _ in range(60):                       # wait up to a minute for DayZ to appear
        time.sleep(1)
        r = subprocess.run(["tasklist", "/FI", "IMAGENAME eq DayZ_x64.exe"], capture_output=True, text=True)
        if "DayZ_x64.exe" in r.stdout:
            print("DayZ started.")
            return
    print("DayZ did not start within a minute. Is Steam running? Try Start_PA_Studio.bat by hand to see why.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("count", type=int, nargs="?", default=0, help="how many objects to photograph (each gets two pictures)")
    ap.add_argument("--no-photos", action="store_true", help="don't start the game: only remake the pictures, catalogue and map files")
    ap.add_argument("--studio", default=DEFAULT_STUDIO, help="the @PatchAtlas_Studio folder")
    ap.add_argument("--only", default=None, help="categories, e.g. Structures,Vehicles")
    ap.add_argument("--restarts", type=int, default=5, help="how often to restart the studio after a crash")
    ap.add_argument("--push", action="store_true", help="commit and push the new cut-outs and catalogue to GitHub")
    args = ap.parse_args()
    if not os.path.isdir("assets") or not os.path.isdir(os.path.join("tools", "object-search")):
        sys.exit("Run this from the repo root (the folder with assets/ and tools/).")

    list_args = ["--limit", str(args.count)] + (["--only", args.only] if args.only else [])
    attempt = 0
    nothing_left = False
    while not args.no_photos:
        step("Listing the next objects" if attempt == 0 else f"Restarting after a crash ({attempt}/{args.restarts})")
        py("make_capture_list.py", *list_args)
        plan = os.path.join(HERE, "capture_plan.json")
        if not json.load(open(plan, encoding="utf-8")):
            print("Nothing left to photograph.")
            nothing_left = True
            break
        close_game()
        step("Starting Patch Atlas Studio")
        start_studio(args.studio)
        step("Taking pictures")
        code = py("capture.py", "--wait-window", "180", check=False)
        close_game()
        if code == 0:
            break
        attempt += 1
        if attempt > args.restarts:
            print("Too many crashes in a row; stopping here. The pictures taken so far are kept.")
            break
        # the next list leaves out what was photographed and what crashed the game
        list_args = ["--limit", str(args.count)] + (["--only", args.only] if args.only else [])

    step("Cutting the pictures out of the background")
    py("cutout.py")
    step("Copying the PA_ object pictures to assets/model-images-pa")
    py("collect_pa.py")
    step("Updating the Object Finder catalogue")
    r = subprocess.run([PY, os.path.join(SEARCH, "build_catalogue.py")])
    if r.returncode:
        sys.exit("build_catalogue.py stopped with an error.")

    if args.push:
        step("Uploading to GitHub")
        paths = ["assets/model-images-cutout", "assets/model-images-photo", "assets/model-images-pa",
                 "tools/object-search"]  # the whole finder: page, catalogue, map file, studio captures
        subprocess.run(["git", "add", "-A", "--", *[p for p in paths if os.path.exists(p)]])
        if subprocess.run(["git", "diff", "--cached", "--quiet"]).returncode:
            subprocess.run(["git", "commit", "-m", f"Object Finder: studio pictures, batch of {args.count}"])
        else:
            print("No new changes to commit.")
        # push even when nothing new was committed, so earlier commits that never got uploaded go too
        subprocess.run(["git", "pull", "--rebase", "--autostash"])
        subprocess.run(["git", "push"])
    print("\nDone. Refresh the Object Finder to see the new pictures.")
    if nothing_left:
        sys.exit(10)  # tells Batch_Continuous.bat that everything has been photographed


if __name__ == "__main__":
    main()
