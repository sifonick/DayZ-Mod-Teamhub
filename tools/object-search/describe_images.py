"""Have a local AI model describe every object image (free, runs on your PC).

Setup once:
    1. Install Ollama from https://ollama.com and start it.
    2. ollama pull qwen2.5vl:7b        (6 GB; needs a graphics card with ~8 GB, or runs slowly on CPU)
       smaller/faster: ollama pull qwen2.5vl:3b   then add  --model qwen2.5vl:3b

Run from the repo root (after build_catalogue.py and, ideally, facts/extract_model_facts.py):
    python tools/object-search/describe_images.py

It saves after every image to tools/object-search/descriptions.jsonl, so you can stop it
(Ctrl+C) and start it again at any time and it carries on where it left off.
Try it on a few first:  python tools/object-search/describe_images.py --limit 20
"""
import argparse
import base64
import io
import json
import os
import sys
import time
import urllib.error
import re
import urllib.request

from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from build_catalogue import CZECH  # noqa: E402

NAME_PREFIXES = {"asf": "asphalt road piece", "grav": "gravel road piece", "mud": "dirt road piece",
                 "kr": "road crossing piece", "sidewalk": "pavement", "decal": "flat ground decal",
                 "proxy": "part of a bigger building", "terrain": "ground shape"}
OUT = os.path.join(HERE, "descriptions.jsonl")

PROMPT_VERSION = 4  # descriptions made with an older prompt are redone
MATERIALS = ["metal", "corrugated metal", "wood", "concrete", "brick", "mud brick", "stone", "plaster",
             "glass", "plastic", "rubber", "fabric", "leather", "asphalt", "earth", "foliage", "ice", "snow", "fur or feathers", "skin", "other"]
CONDITION = ["intact", "worn", "rusty", "damaged", "ruined", "wrecked", "not applicable"]

SCHEMA = {
    "type": "object",
    "properties": {
        "description": {"type": "string"},
        "objectType": {"type": "string"},
        "materials": {"type": "array", "items": {"type": "string", "enum": MATERIALS}},
        "colours": {"type": "array", "items": {"type": "string"}},
        "condition": {"type": "string", "enum": CONDITION},
        "tags": {"type": "array", "items": {"type": "string"}},
    },
    "required": ["description", "objectType", "materials", "colours", "condition", "tags"],
}

PROMPT = """This picture shows one 3D object, such as a building, prop, plant, rock or vehicle.
Known facts (trust these over the picture): {facts}

Look at the main object only, not the ground or sky behind it. Reply in JSON with:
- description: one plain English sentence saying what the object is and what it looks like, in your own words. Don't repeat the file name.
- objectType: the everyday name for what it is, one to three words.
- materials: what the object is really made of. Animals are "fur or feathers" or "skin"; people and clothing are "fabric"; trees and plants are "wood" and "foliage". Leave it empty if unsure.
- colours: up to 3 main colours, simple words.
- condition: "intact" unless you can clearly see rust, damage or ruin; "not applicable" for animals, people and plants.
- tags: 5 to 8 specific words someone might search for: other names for it, what it's used for, where you'd find it (e.g. kitchen, farm, roadside, military base), its style or era. No vague words like "simple", "utility", "structure" or "object".
Describe the object as if it were real. Never mention video games, DayZ, 3D models, renders or map making in any field."""


def load_jsonl(path):
    done = {}
    if os.path.exists(path):
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    r = json.loads(line)
                    if r.get("v") == PROMPT_VERSION:
                        done[r["img"]] = r  # last line per image wins
                except (json.JSONDecodeError, KeyError):
                    pass
    return done


def image_b64(path, max_side=672):
    img = Image.open(path)
    if img.mode != "RGB":
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img).convert("RGB")
    img.thumbnail((max_side, max_side))
    buf = io.BytesIO()
    img.save(buf, "JPEG", quality=88)
    return base64.b64encode(buf.getvalue()).decode()


def facts_text(it, facts):
    parts = [f'file name "{it["name"]}"', f'category {it["category"]}']
    words = re.split(r"[^a-z]+", (it["name"] + " " + it["img"].rsplit("/", 2)[-2]).lower())
    meanings = {f"{w} = {CZECH[w]}" for w in words if w in CZECH}
    for w in words:  # road-piece prefixes, e.g. asf3takistan, gravsakhal
        for pre, meaning in NAME_PREFIXES.items():
            if w.startswith(pre) and w not in CZECH:
                meanings.add(f"{pre} = {meaning}")
    meanings = sorted(meanings)
    if meanings:
        parts.append("Words in the name mean: " + ", ".join(meanings))
    if it.get("class"):
        parts.append(f'class {it["class"]}')
    f = facts.get((it.get("model") or "").lower())
    if f:
        if f.get("size"):
            w, h, d = f["size"]
            parts.append(f"size {w} x {h} x {d} m (width x height x depth)")
        if f.get("materials"):
            parts.append("made of " + ", ".join(f["materials"]))
        if f.get("mapType"):
            parts.append(f'map legend type "{f["mapType"]}"')
    return "; ".join(parts)


def ask(host, model, prompt, img_b64, num_ctx=2048, timeout=300):
    body = {
        "model": model,
        "messages": [{"role": "user", "content": prompt, "images": [img_b64]}],
        "format": SCHEMA,
        "stream": False,
        # A small working memory: one image + prompt + reply fits in 2048 tokens, and a smaller
        # budget keeps the whole model on the graphics card instead of spilling into normal RAM.
        "options": {"temperature": 0, "num_ctx": num_ctx},
        "keep_alive": "30m",
    }
    if model.startswith("qwen3"):
        body["think"] = False
    req = urllib.request.Request(host.rstrip("/") + "/api/chat", data=json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(json.loads(r.read())["message"]["content"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="qwen2.5vl:7b")
    ap.add_argument("--host", default="http://localhost:11434")
    ap.add_argument("--limit", type=int, default=0, help="stop after this many new images (0 = all)")
    ap.add_argument("--skip", default="Water,Characters,Weapons,Gear,Effects & data",
                    help="comma-separated categories to skip; their names already say what they are (use --skip \"\" for none)")
    ap.add_argument("--ctx", type=int, default=2048, help="AI working memory in tokens (default 2048)")
    ap.add_argument("--max-side", type=int, default=448, help="image size sent to the AI; smaller is faster (default 448)")
    ap.add_argument("--only", default="", help="only these categories, e.g. --only Structures")
    ap.add_argument("--shuffle", action="store_true", help="random order (good for a test run)")
    args = ap.parse_args()

    items = json.load(open(os.path.join(HERE, "catalogue.json"), encoding="utf-8"))["items"]
    facts_path = os.path.join(HERE, "model_facts.json")
    facts = json.load(open(facts_path, encoding="utf-8")) if os.path.exists(facts_path) else {}
    skip = {s.strip() for s in args.skip.split(",") if s.strip()}
    done = load_jsonl(OUT)
    only = {s.strip() for s in args.only.split(",") if s.strip()}
    def source(it):
        return it.get("studioImg") or it["img"]

    def finished(it):
        r = done.get(it["img"])
        return r is not None and r.get("src", it["img"]) == source(it)

    todo = [it for it in items if not finished(it) and it["category"] not in skip
            and (not only or it["category"] in only)]
    if args.shuffle:
        import random
        random.Random(1).shuffle(todo)
    if args.limit:
        todo = todo[: args.limit]
    print(f"{len(done)} already described, {len(todo)} to go with {args.model}.")
    try:
        urllib.request.urlopen(args.host.rstrip("/") + "/api/tags", timeout=5)
    except (urllib.error.URLError, OSError):
        sys.exit(f"Can't reach Ollama at {args.host}. Start the Ollama app, then run this again.")

    start, failed = time.time(), 0
    with open(OUT, "a", encoding="utf-8") as out:
        for n, it in enumerate(todo, 1):
            try:
                prompt = PROMPT.format(facts=facts_text(it, facts))
                if it.get("studioImg"):
                    prompt = prompt.replace("Known facts", "It stands alone on a plain grey floor. Known facts", 1)
                res = ask(args.host, args.model, prompt, image_b64(source(it), args.max_side), args.ctx)
            except urllib.error.HTTPError as e:
                if e.code == 404:
                    sys.exit(f'Model "{args.model}" isn\'t installed. Run:  ollama pull {args.model}')
                failed += 1
                print(f"\n  skipped {it['img']}: {e}")
                continue
            except Exception as e:  # bad image, timeout, odd reply: skip it, a re-run retries
                failed += 1
                print(f"\n  skipped {it['img']}: {e}")
                continue
            res["img"] = it["img"]
            res["src"] = source(it)
            res["v"] = PROMPT_VERSION
            out.write(json.dumps(res, ensure_ascii=False) + "\n")
            out.flush()
            rate = (time.time() - start) / n
            left = (len(todo) - n) * rate
            print(f"\r{n}/{len(todo)}  {rate:.1f}s each, about {left / 3600:.1f} h left   ", end="", flush=True)
    print(f"\nDone. {failed} skipped (run again to retry them).")


if __name__ == "__main__":
    main()
