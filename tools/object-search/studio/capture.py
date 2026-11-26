"""Take the studio pictures while Patch Atlas Studio shows each object.

1. python tools/object-search/studio/make_capture_list.py
2. Start the studio (Start_PA_Studio.bat in the mod folder). Use Windowed or Borderless
   display mode, not exclusive Fullscreen, so the screen can be captured.
3. python tools/object-search/studio/capture.py
   Leave the PC alone while it runs: anything covering the DayZ window ends up in the pictures.

Each time the game says an object is on screen, this waits until the picture stops changing
(models and shadows finished loading), saves a square crop to assets/model-images-studio/,
records it in tools/object-search/studio/studio_captures.jsonl, and tells the game to move on.
Needs only Pillow (already installed for the other scripts). Windows only.
"""
import argparse
import ctypes
import json
import os
import sys
import time
from ctypes import wintypes

from PIL import Image, ImageChops, ImageGrab, ImageStat

HERE = os.path.dirname(os.path.abspath(__file__))
LOG = os.path.join(HERE, "studio_captures.jsonl")

user32 = ctypes.windll.user32
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(2)  # real pixel sizes on scaled displays
except Exception:
    user32.SetProcessDPIAware()


def profile_dir():
    return os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), "DayZ")


def find_dayz_window():
    found = []
    proto = ctypes.WINFUNCTYPE(ctypes.c_bool, wintypes.HWND, wintypes.LPARAM)

    def cb(hwnd, _):
        if user32.IsWindowVisible(hwnd):
            n = user32.GetWindowTextLengthW(hwnd)
            buf = ctypes.create_unicode_buffer(n + 1)
            user32.GetWindowTextW(hwnd, buf, n + 1)
            if buf.value.strip().lower() == "dayz" or buf.value.lower().startswith("dayz ("):
                found.append(hwnd)
        return True

    user32.EnumWindows(proto(cb), 0)
    return found[0] if found else None


def client_box(hwnd):
    rect = wintypes.RECT()
    user32.GetClientRect(hwnd, ctypes.byref(rect))
    pt = wintypes.POINT(0, 0)
    user32.ClientToScreen(hwnd, ctypes.byref(pt))
    return (pt.x, pt.y, pt.x + rect.right, pt.y + rect.bottom)


def grab(box):
    return ImageGrab.grab(bbox=box, all_screens=True).convert("RGB")


def difference(a, b):
    small = (96, 54)
    d = ImageChops.difference(a.resize(small).convert("L"), b.resize(small).convert("L"))
    return ImageStat.Stat(d).mean[0]


def wait_stable(box, min_wait, max_wait):
    """Grab frames until two in a row match (loading finished), then return the last one."""
    time.sleep(min_wait)
    prev = grab(box)
    start = time.time()
    calm = 0
    while time.time() - start < max_wait:
        time.sleep(0.3)
        cur = grab(box)
        calm = calm + 1 if difference(prev, cur) < 0.8 else 0
        prev = cur
        if calm >= 2:
            break
    return prev


def hide_sky_bottom(img):
    """Looking down steeply, the camera sees the bottom of the sky, which the game draws as
    a solid black dome rising from the bottom edge. Paint every pure-black pixel connected
    to the bottom edge with the background colour, so it isn't taken for the object."""
    try:
        import numpy as np
        from scipy import ndimage
    except ImportError:
        return img
    a = np.asarray(img).copy()
    h, w, _ = a.shape
    black = a.max(axis=2) < 10
    if black[-1].sum() < w * 0.2:
        return img                       # no dome along the bottom
    labels, n = ndimage.label(black)
    touching = set(np.unique(labels[-1])) - {0}
    dome = np.isin(labels, list(touching))
    top = a[: max(1, h // 10)].reshape(-1, 3)
    fill = np.median(top, axis=0)
    # the dome's soft edge: darker-than-background pixels within a few pixels of it
    near = ndimage.binary_dilation(dome, iterations=max(10, h // 45))
    dark = a.astype(np.int16).max(axis=2) < fill.max() - 12
    dome |= near & dark
    a[dome] = fill.astype(np.uint8)
    return Image.fromarray(a)


def trim_to_object(img, size, pad=1.15):
    """Square crop around the object: compare each row to the floor/sky at its left and right
    edges, find where the object is, and crop around it.

    Works on a 4x smaller, blurred copy so the floor's own texture (ice, snow) isn't taken
    for the object. Returns None when nothing is visible."""
    try:
        import numpy as np
    except ImportError:
        return square_crop(img, size)
    from PIL import ImageFilter
    w, h = img.size
    k = 4
    small = img.resize((w // k, h // k), Image.BOX).filter(ImageFilter.GaussianBlur(1.5))
    a = np.asarray(small, dtype=np.float32)
    sh, sw, _ = a.shape
    edge = max(3, sw // 20)
    bg = np.median(np.concatenate([a[:, :edge], a[:, -edge:]], axis=1), axis=1)   # one colour per row
    diff = np.sqrt(((a - bg[:, None, :]) ** 2).sum(axis=2))
    mask = diff > 28
    mask[: int(sh * 0.03)] = False          # ignore the very top and bottom (any leftover HUD)
    mask[int(sh * 0.91):] = False
    need_r = max(2, int(sw * 0.004))
    need_c = max(2, int(sh * 0.004))
    rows = np.where(mask.sum(axis=1) >= need_r)[0]
    cols = np.where(mask.sum(axis=0) >= need_c)[0]
    if len(rows) < 2 or len(cols) < 2:
        return None  # nothing visible
    top, bottom, left, right = rows[0] * k, (rows[-1] + 1) * k, cols[0] * k, (cols[-1] + 1) * k
    if (bottom - top) * (right - left) < 0.001 * h * w:
        return None  # only a speck: the object didn't render
    side = int(max(bottom - top, right - left) * pad) + 1
    side = max(side, 64)
    cx, cy = (left + right) // 2, (top + bottom) // 2
    box = (cx - side // 2, cy - side // 2, cx - side // 2 + side, cy - side // 2 + side)
    # paste onto a background-coloured square so crops near the edge stay square
    fill = tuple(int(v) for v in np.median(bg, axis=0))
    out = Image.new("RGB", (side, side), fill)
    src = img.crop((max(box[0], 0), max(box[1], 0), min(box[2], w), min(box[3], h)))
    out.paste(src, (max(-box[0], 0), max(-box[1], 0)))
    return out.resize((size, size), Image.LANCZOS)


def square_crop(img, size):
    w, h = img.size
    s = min(w, h)
    left, top = (w - s) // 2, (h - s) // 2
    return img.crop((left, top, left + s, top + s)).resize((size, size), Image.LANCZOS)


def read_ready(path):
    """The game's latest message, with the file's time so each message is handled once."""
    try:
        stamp = os.stat(path).st_mtime_ns
        with open(path, encoding="utf-8", errors="replace") as fh:
            line = fh.readline().strip()
    except OSError:
        return None
    if line == "finished":
        return {"finished": True, "key": (0, stamp)}
    parts = line.split("|")
    if len(parts) < 4 or not parts[0].isdigit():
        return None
    view = int(parts[5]) if len(parts) > 5 and parts[5].isdigit() else 0
    return {"seq": int(parts[0]), "id": parts[1], "spawn": parts[2], "status": parts[3], "view": view,
            "key": (int(parts[0]), stamp)}


def view_file(path, view):
    """First picture keeps the plain name; the others get _2, _3 ... (other sides of the object)."""
    if view == 0:
        return path
    root, ext = os.path.splitext(path)
    return f"{root}_{view + 1}{ext}"


def say_done(profile, seq):
    tmp = os.path.join(profile, "pa_studio_done.tmp")
    with open(tmp, "w") as fh:
        fh.write(str(seq))
    os.replace(tmp, os.path.join(profile, "pa_studio_done.txt"))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--profile", default=profile_dir())
    ap.add_argument("--size", type=int, default=1024, help="saved picture size in pixels (square)")
    ap.add_argument("--views", type=int, default=2, help="pictures per object (must match PAS_VIEWS in the mission's init.c)")
    ap.add_argument("--min-wait", type=float, default=0.4)
    ap.add_argument("--max-wait", type=float, default=6.0)
    ap.add_argument("--no-trim", action="store_true", help="plain centre crop instead of cropping to the object")
    ap.add_argument("--wait-window", type=float, default=0, help="give up if the game window hasn't appeared after this many seconds (0 = wait forever)")
    args = ap.parse_args()

    plan = json.load(open(os.path.join(HERE, "capture_plan.json"), encoding="utf-8"))
    ready_path = os.path.join(args.profile, "pa_studio_ready.txt")
    print("Waiting for Patch Atlas Studio... (start it now if you haven't)")
    hwnd = None
    waited = 0
    while not hwnd:
        hwnd = find_dayz_window()
        time.sleep(1)
        waited += 1
        if args.wait_window and waited > args.wait_window:
            print("The studio didn't start.")
            sys.exit(3)
    user32.SetForegroundWindow(hwnd)

    # ignore a message left over from an earlier run
    try:
        stale_before = os.stat(ready_path).st_mtime_ns
    except OSError:
        stale_before = 0
    last_key, n_ok, n_fail, start = None, 0, 0, time.time()
    with open(LOG, "a", encoding="utf-8") as log:
        while True:
            msg = read_ready(ready_path)
            if not msg or msg["key"] == last_key or msg["key"][1] <= stale_before:
                time.sleep(0.1)
                if not user32.IsWindow(hwnd):
                    print(f"\nThe game closed (or crashed) after {n_ok} pictures.")
                    sys.exit(3)
                continue
            if msg.get("finished"):
                break
            last_key = msg["key"]
            entry = plan.get(msg["id"])
            if msg["status"] != "ok" or not entry:
                n_fail += 1
                print(f"\n  couldn't spawn {msg['spawn']}")
                say_done(args.profile, msg["seq"])
                continue
            box = client_box(hwnd)
            if box[2] - box[0] < 100:
                sys.exit("The DayZ window is minimised or too small. Restore it and run this again.")
            frame = wait_stable(box, args.min_wait, args.max_wait)
            frame = hide_sky_bottom(frame)
            img = square_crop(frame, args.size) if args.no_trim else trim_to_object(frame, args.size)
            if img is None:
                n_fail += 1
                print(f"\n  nothing visible for {entry['spawn']} (keeping its old picture)")
                log.write(json.dumps({"spawn": entry["spawn"], "empty": True, "view": msg["view"], "imgs": entry["imgs"]}) + "\n")
                log.flush()
                say_done(args.profile, msg["seq"])
                continue
            out_file = view_file(entry["file"], msg["view"])
            os.makedirs(os.path.dirname(out_file), exist_ok=True)
            img.save(out_file, "JPEG", quality=92)
            log.write(json.dumps({"spawn": entry["spawn"], "file": out_file, "view": msg["view"], "imgs": entry["imgs"]}) + "\n")
            log.flush()
            say_done(args.profile, msg["seq"])
            n_ok += 1
            done = n_ok + n_fail
            rate = (time.time() - start) / done
            total = len(plan) * args.views
            left = (total - done) * rate
            print(f"\r{done}/{total} pictures  {rate:.1f}s each, about {left / 3600:.1f} h left   ", end="", flush=True)
    print(f"\nFinished: {n_ok} pictures, {n_fail} pictures failed (object couldn't be spawned or didn't show up).")


if __name__ == "__main__":
    main()
