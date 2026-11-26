"""Make the list of objects for Patch Atlas Studio to photograph.

Run from the repo root:
    python tools/object-search/studio/make_capture_list.py            # everything not yet captured
    python tools/object-search/studio/make_capture_list.py --limit 25 # a short test
    python tools/object-search/studio/make_capture_list.py --only Rocks,Plants

Writes:
  %LOCALAPPDATA%\\DayZ\\pa_studio_list.txt     the list the studio mission reads (id|class or p3d)
  tools/object-search/studio/capture_plan.json which picture belongs to which catalogue images
"""
import argparse
import json
import os
import random
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEARCH = os.path.dirname(HERE)
OUT_DIR = "assets/model-images-studio"
DEFAULT_CATS = "Structures,Plants,Rocks,Vehicles"


def profile_dir():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "DayZ")


def out_name(spawn, category):
    base = spawn.replace("\\", "/").rsplit("/", 1)[-1]
    base = re.sub(r"\.p3d$", "", base, flags=re.I)
    base = re.sub(r"[^A-Za-z0-9_.-]+", "_", base).lower()
    return f"{OUT_DIR}/{category.lower().replace(' & ', '_')}/{base}.jpg"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=DEFAULT_CATS, help=f"categories (default {DEFAULT_CATS}; add Water if wanted)")
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--shuffle", action="store_true", help="random order (good for a test)")
    ap.add_argument("--redo", action="store_true", help="include objects that already have a studio picture")
    ap.add_argument("--profile", default=profile_dir(), help="DayZ profile folder (default %%LOCALAPPDATA%%\\DayZ)")
    args = ap.parse_args()

    items = json.load(open(os.path.join(SEARCH, "catalogue.json"), encoding="utf-8"))["items"]
    cats = {c.strip() for c in args.only.split(",") if c.strip()}
    plan = {}
    skipped_proxy = 0
    for it in items:
        if it["category"] not in cats:
            continue
        where = " ".join(str(it.get(k) or "") for k in ("class", "model", "img", "name")).lower()
        if "proxy" in where:
            skipped_proxy += 1  # proxies are pieces of other models, not objects of their own
            continue
        if it.get("class") and not (it["class"].startswith("PA_") and it.get("model")):
            spawn = it["class"]
        elif it.get("model"):
            # PA_ classes only name a model: place the model itself, which is safer (no game logic)
            spawn = it["model"].replace("/", "\\")
            spawn = "DZ" + spawn[2:] if spawn.lower().startswith("dz\\") else spawn
        else:
            continue
        key = spawn.lower()
        if key not in plan:
            category = "Vehicles" if "wreck" in where else it["category"]
            plan[key] = {"spawn": spawn, "file": out_name(it.get("class") or spawn, category), "imgs": []}
        plan[key]["imgs"].append(it["img"])

    entries = list(plan.values())
    if not args.redo:
        # skip objects already photographed, and ones that showed nothing last time
        empty = set()
        log = os.path.join(HERE, "studio_captures.jsonl")
        if os.path.exists(log):
            for line in open(log, encoding="utf-8"):
                try:
                    r = json.loads(line)
                except json.JSONDecodeError:
                    continue
                key = r.get("spawn", "").lower()
                if r.get("empty"):
                    empty.add(key)
                else:
                    empty.discard(key)
        entries = [e for e in entries if not os.path.exists(e["file"]) and e["spawn"].lower() not in empty]
    # objects that crashed the game before (the studio notes them in pa_studio_crashed.txt)
    crashed_path = os.path.join(args.profile, "pa_studio_crashed.txt")
    if os.path.exists(crashed_path):
        crashed = {l.strip().lower() for l in open(crashed_path, encoding="utf-8", errors="replace") if l.strip()}
        before = len(entries)
        entries = [e for e in entries if e["spawn"].lower() not in crashed]
        if before != len(entries):
            print(f"Skipped {before - len(entries)} objects that crashed the game before.")
    if args.shuffle:
        random.Random(7).shuffle(entries)
    if args.limit:
        entries = entries[: args.limit]
    for n, e in enumerate(entries):
        e["id"] = str(n)

    if not os.path.isdir(args.profile):
        sys.exit(f"DayZ profile folder not found: {args.profile}\nStart DayZ once, or pass --profile.")
    with open(os.path.join(args.profile, "pa_studio_list.txt"), "w", encoding="utf-8", newline="\r\n") as fh:
        for e in entries:
            fh.write(f"{e['id']}|{e['spawn']}\n")
    with open(os.path.join(HERE, "capture_plan.json"), "w", encoding="utf-8") as fh:
        json.dump({e["id"]: e for e in entries}, fh, indent=1)
    if skipped_proxy:
        print(f"Skipped {skipped_proxy} proxy parts.")
    print(f"{len(entries)} objects to photograph -> {os.path.join(args.profile, 'pa_studio_list.txt')}")


if __name__ == "__main__":
    main()
