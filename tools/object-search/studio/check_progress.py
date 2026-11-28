"""Check how many objects already have a studio picture, and how many are left.

Run from the repo root:
    python tools/object-search/studio/check_progress.py                    # the default categories
    python tools/object-search/studio/check_progress.py --only Structures  # just buildings/props
    python tools/object-search/studio/check_progress.py --only Structures --list-remaining 20

Read-only: it reports counts, it doesn't photograph or change anything. It uses the exact same
catalogue.json, studio_captures.jsonl (which pictures came back blank) and pa_studio_crashed.txt
(which objects crashed the game) that make_capture_list.py uses, so "Left" here is exactly what
the next Batch_*.bat run would still try to photograph.
"""
import argparse
import json
import os
import re

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


def build_entries(cat):
    """One entry per unique spawnable object in this category (same de-duplication
    make_capture_list.py uses: skip proxies, prefer the class, fall back to the model)."""
    items = json.load(open(os.path.join(SEARCH, "catalogue.json"), encoding="utf-8"))["items"]
    plan = {}
    for it in items:
        if it["category"] != cat:
            continue
        where = " ".join(str(it.get(k) or "") for k in ("class", "model", "img", "name")).lower()
        if "proxy" in where:
            continue
        if it.get("class") and not (it["class"].startswith("PA_") and it.get("model")):
            spawn = it["class"]
        elif it.get("model"):
            spawn = it["model"].replace("/", "\\")
            spawn = "DZ" + spawn[2:] if spawn.lower().startswith("dz\\") else spawn
        else:
            continue
        key = spawn.lower()
        if key not in plan:
            out_cat = "Vehicles" if "wreck" in where else it["category"]
            plan[key] = {"spawn": spawn, "file": out_name(it.get("class") or spawn, out_cat)}
    return list(plan.values())


def load_empty_log():
    """Objects whose last capture came back blank (no model in frame) - skipped like already done."""
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
    return empty


def load_crashed(profile):
    path = os.path.join(profile, "pa_studio_crashed.txt")
    if not os.path.exists(path):
        return set()
    return {l.strip().lower() for l in open(path, encoding="utf-8", errors="replace") if l.strip()}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", default=DEFAULT_CATS, help=f"categories (default {DEFAULT_CATS})")
    ap.add_argument("--profile", default=profile_dir(), help="DayZ profile folder (default %%LOCALAPPDATA%%\\DayZ)")
    ap.add_argument("--list-remaining", type=int, default=0, metavar="N", help="also print up to N objects still left")
    args = ap.parse_args()

    cats = [c.strip() for c in args.only.split(",") if c.strip()]
    empty = load_empty_log()
    crashed = load_crashed(args.profile)

    totals = {"total": 0, "done": 0, "blank": 0, "crashed": 0, "left": 0}
    remaining = []
    print(f"{'Category':<14}{'Total':>8}{'Done':>8}{'Blank':>8}{'Crashed':>9}{'Left':>8}")
    for cat in cats:
        entries = build_entries(cat)
        total = len(entries)
        done = sum(1 for e in entries if os.path.exists(e["file"]))
        blank = sum(1 for e in entries if not os.path.exists(e["file"]) and e["spawn"].lower() in empty)
        crash = sum(1 for e in entries
                    if not os.path.exists(e["file"]) and e["spawn"].lower() not in empty
                    and e["spawn"].lower() in crashed)
        left = total - done - blank - crash
        print(f"{cat:<14}{total:>8}{done:>8}{blank:>8}{crash:>9}{left:>8}")
        totals["total"] += total
        totals["done"] += done
        totals["blank"] += blank
        totals["crashed"] += crash
        totals["left"] += left
        if args.list_remaining:
            for e in entries:
                k = e["spawn"].lower()
                if not os.path.exists(e["file"]) and k not in empty and k not in crashed:
                    remaining.append(e["spawn"])

    print(f"{'TOTAL':<14}{totals['total']:>8}{totals['done']:>8}{totals['blank']:>8}{totals['crashed']:>9}{totals['left']:>8}")
    print("\n(Blank = photographed before but the picture came back empty; Crashed = skipped because")
    print(" it crashed the game last time; Left = what the next batch run would still try.)")
    if args.list_remaining:
        print(f"\nFirst {min(args.list_remaining, len(remaining))} of {len(remaining)} still to photograph:")
        for s in remaining[: args.list_remaining]:
            print(" ", s)


if __name__ == "__main__":
    main()
