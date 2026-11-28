"""
Asset Capture - PC side.

Drives the AssetCapture DayZ mod: sends it a list of classnames, screenshots
each angle when the mod says it's ready, keys out the magenta background,
crops, and saves transparent PNGs.

Requirements (Windows):  pip install pillow numpy   (optional: pip install mss)

Usage:
  python asset_capture.py --classes classes.txt
  python asset_capture.py --classes AKM M4A1 Apple --angles 12 --size 1024
  python asset_capture.py --classes classes.txt --angles "0 0 0" "0 90 0" "35 35 0"

Then load into DayZ (offline or your own server) with -mod=@AssetCapture,
spawn in, and leave the game window in front. The mod picks up the job
within a second.
"""
import argparse
import os
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image

KEY = np.array([255, 0, 255], dtype=np.float32)  # magenta, matches capture.layout


def default_profile():
    return Path(os.environ.get("LOCALAPPDATA", str(Path.home()))) / "DayZ"


def parse_args():
    p = argparse.ArgumentParser(description="Capture multi-angle images of DayZ items.")
    p.add_argument("--classes", nargs="+", required=True,
                   help="Classnames, or a path to a .txt file with one classname per line")
    p.add_argument("--profile", type=Path, default=default_profile(),
                   help="DayZ client profile folder (default: %%LOCALAPPDATA%%\\DayZ, or your -profiles= path)")
    p.add_argument("--out", type=Path, default=Path("captures"), help="Output folder")
    p.add_argument("--angles", nargs="+", default=["8"],
                   help="A number N for an N-step turntable (+ one high 3/4 view), "
                        "or explicit 'pitch yaw roll' triples in quotes")
    p.add_argument("--size", type=int, default=0,
                   help="Fit each image into a square canvas of this many px (0 = keep tight crop)")
    p.add_argument("--pad", type=int, default=16, help="Padding around the cropped item, px")
    p.add_argument("--monitor", type=int, default=1, help="Monitor to capture (mss numbering, 1 = primary)")
    p.add_argument("--keep-raw", action="store_true", help="Also save the untouched screenshot")
    p.add_argument("--timeout", type=float, default=120, help="Seconds to wait for the game to respond")
    return p.parse_args()


def load_classes(items):
    if len(items) == 1 and Path(items[0]).is_file():
        lines = Path(items[0]).read_text(encoding="utf-8").splitlines()
        return [l.strip() for l in lines if l.strip() and not l.strip().startswith("#")]
    return items


def build_angles(spec):
    if len(spec) == 1 and spec[0].isdigit():
        n = max(1, int(spec[0]))
        angles = [(0.0, i * 360.0 / n, 0.0) for i in range(n)]
        angles.append((35.0, 35.0, 0.0))
        return angles
    angles = []
    for s in spec:
        parts = s.split()
        if len(parts) != 3:
            sys.exit(f"Bad angle '{s}' - use 'pitch yaw roll'")
        angles.append(tuple(float(x) for x in parts))
    return angles


def make_grabber(monitor):
    try:
        import mss
        sct = mss.MSS() if hasattr(mss, "MSS") else mss.mss()
        mon = sct.monitors[monitor]

        def grab():
            shot = sct.grab(mon)
            return Image.frombytes("RGB", shot.size, shot.bgra, "raw", "BGRX")
        return grab
    except ImportError:
        from PIL import ImageGrab
        return lambda: ImageGrab.grab().convert("RGB")


def key_out(img, lo=40.0, hi=140.0):
    """Turn the magenta background transparent, with soft edges and de-spill."""
    rgb = np.asarray(img, dtype=np.float32)
    dist = np.linalg.norm(rgb - KEY, axis=2)
    alpha = np.clip((dist - lo) / (hi - lo), 0.0, 1.0)

    # Remove the background's contribution from edge pixels: C = a*F + (1-a)*K
    a = alpha[..., None]
    safe = np.where(a > 0.001, a, 1.0)
    fg = (rgb - (1.0 - a) * KEY) / safe
    fg = np.clip(fg, 0, 255)

    out = np.dstack([fg, alpha * 255.0]).astype(np.uint8)
    return Image.fromarray(out, "RGBA")


def crop_and_fit(img, pad, size):
    bbox = img.getchannel("A").point(lambda v: 255 if v > 8 else 0).getbbox()
    if not bbox:
        return None
    l, t, r, b = bbox
    img = img.crop((max(0, l - pad), max(0, t - pad), min(img.width, r + pad), min(img.height, b + pad)))
    if size:
        img.thumbnail((size, size), Image.LANCZOS)
        canvas = Image.new("RGBA", (size, size), (0, 0, 0, 0))
        canvas.paste(img, ((size - img.width) // 2, (size - img.height) // 2), img)
        img = canvas
    return img


def main():
    args = parse_args()
    classes = load_classes(args.classes)
    angles = build_angles(args.angles)
    if not classes:
        sys.exit("No classnames given.")

    work = args.profile / "AssetCapture"
    work.mkdir(parents=True, exist_ok=True)
    f_queue, f_start, f_ready, f_stop, f_done, f_skip, f_alive = (
        work / n for n in ("queue.txt", "start.txt", "ready.txt", "stop.txt",
                           "done.txt", "skipped.txt", "alive.txt"))
    for f in (f_ready, f_done, f_stop, f_start):
        f.unlink(missing_ok=True)

    # The mod refreshes alive.txt every second while you're in-game
    def game_alive():
        return f_alive.exists() and time.time() - f_alive.stat().st_mtime < 5

    if not game_alive():
        print("Waiting for the AssetCapture mod (spawn in-game with the mod loaded on your CLIENT)...")
        t0 = time.time()
        while not game_alive():
            if time.time() - t0 > args.timeout:
                if f_alive.exists():
                    sys.exit("The mod was loaded earlier but isn't running now. Are you spawned in "
                             "(not in the menu or loading screen)?")
                sys.exit(f"The mod has never checked in at {work}.\n"
                         "  - Is @AssetCapture in the client's -mod= list / DayZ Launcher mods?\n"
                         "  - Search for [AssetCapture] in the newest script_*.log in "
                         f"{args.profile}\n"
                         "  - If you launch DayZ with -profiles=, pass the same folder with --profile")
            time.sleep(0.5)
    print("Mod detected in-game.")

    with f_queue.open("w", encoding="utf-8", newline="\n") as q:
        for pitch, yaw, roll in angles:
            q.write(f"angle {pitch:g} {yaw:g} {roll:g}\n")
        for c in classes:
            q.write(c + "\n")
    f_start.write_text("go\n")

    total = len(classes) * len(angles)
    print(f"Queued {len(classes)} items x {len(angles)} angles = {total} shots")
    print(f"Watching {work}")
    print("Switch to DayZ and leave it in front (borderless/windowed works best). Ctrl+C to abort.")

    grab = make_grabber(args.monitor)
    args.out.mkdir(parents=True, exist_ok=True)
    done_shots = 0
    last_activity = time.time()

    try:
        while True:
            if f_done.exists():
                reason = f_done.read_text().strip()
                print(f"\nGame reports finished: {reason}")
                break

            if f_ready.exists():
                tag = f_ready.read_text(errors="ignore").strip()
                if "|" not in tag:          # file still being written
                    time.sleep(0.05)
                    continue
                cls, idx = tag.split("|", 1)
                time.sleep(0.05)            # let the frame settle on screen
                raw = grab()

                item_dir = args.out / cls
                item_dir.mkdir(parents=True, exist_ok=True)
                name = f"{cls}_{int(idx):02d}"
                if args.keep_raw:
                    raw.save(item_dir / f"{name}_raw.png")

                result = crop_and_fit(key_out(raw), args.pad, args.size)
                if result is None:
                    print(f"\n  ! {name}: nothing visible (is DayZ in front?)")
                else:
                    result.save(item_dir / f"{name}.png", optimize=True)

                done_shots += 1
                print(f"\r  {done_shots}/{total}  {name}          ", end="", flush=True)
                f_ready.unlink(missing_ok=True)  # tells the mod to move on
                last_activity = time.time()
                continue

            if time.time() - last_activity > args.timeout:
                print(f"\nNo response from the game for {args.timeout:.0f}s. "
                      "Is the mod loaded and are you in-game (not in the main menu)?")
                f_stop.write_text("stop\n")
                break
            time.sleep(0.05)
    except KeyboardInterrupt:
        print("\nAborting...")
        f_stop.write_text("stop\n")

    if f_skip.exists():
        skipped = [l for l in f_skip.read_text().splitlines() if l.strip()]
        if skipped:
            print(f"Could not spawn ({len(skipped)}): {', '.join(skipped)}")
    print(f"Images saved to {args.out.resolve()}")


if __name__ == "__main__":
    main()
