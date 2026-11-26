"""Build the AI search data (embeddings.bin + embeddings.json) for the object search.

Run from the root of the DayZ-Mod-Teamhub repo, after build_catalogue.py:

    pip install torch transformers pillow
    python tools/object-search/build_embeddings.py

It reads every image listed in catalogue.json from your local copy of the repo,
turns each one into a CLIP vector, and saves them in catalogue order.
A GPU makes it fast (a few minutes); on CPU expect roughly 20-60 minutes for
~11,000 images. Run it again whenever you re-run build_catalogue.py.

Optional: --model openai/clip-vit-base-patch16 (sharper, ~3x slower). The search
page reads the model name from embeddings.json, so it always stays in step.
"""
import argparse
import hashlib
import json
import os
import sys

import numpy as np
import torch
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

HERE = os.path.dirname(os.path.abspath(__file__))

# Python model -> the same weights converted for the browser (transformers.js)
BROWSER_MODELS = {
    "openai/clip-vit-base-patch32": "Xenova/clip-vit-base-patch32",
    "openai/clip-vit-base-patch16": "Xenova/clip-vit-base-patch16",
    "openai/clip-vit-large-patch14": "Xenova/clip-vit-large-patch14",
}


def load_image(path):
    img = Image.open(path)
    if img.mode in ("RGBA", "LA", "P"):
        img = img.convert("RGBA")
        bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(bg, img)
    return img.convert("RGB")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--model", default="openai/clip-vit-base-patch32", choices=sorted(BROWSER_MODELS))
    ap.add_argument("--batch", type=int, default=64)
    args = ap.parse_args()

    cat_path = os.path.join(HERE, "catalogue.json")
    if not os.path.exists(cat_path):
        sys.exit("catalogue.json not found: run build_catalogue.py first.")
    items = json.load(open(cat_path, encoding="utf-8"))["items"]
    catalogue_hash = hashlib.sha1("\n".join(i["img"] for i in items).encode()).hexdigest()[:16]

    device = "cuda" if torch.cuda.is_available() else ("mps" if torch.backends.mps.is_available() else "cpu")
    print(f"Loading {args.model} on {device} ...")
    model = CLIPModel.from_pretrained(args.model).to(device).eval()
    proc = CLIPProcessor.from_pretrained(args.model)
    dim = model.config.projection_dim

    out = np.zeros((len(items), dim), dtype=np.float16)
    failed = []
    for start in range(0, len(items), args.batch):
        batch = items[start:start + args.batch]
        imgs, rows = [], []
        for n, it in enumerate(batch):
            try:
                imgs.append(load_image(it.get("studioImg") or it["img"]))
                rows.append(start + n)
            except Exception as exc:  # missing/corrupt file: leave a zero vector
                failed.append((it["img"], str(exc)))
        if imgs:
            with torch.no_grad():
                inputs = proc(images=imgs, return_tensors="pt").to(device)
                feats = model.get_image_features(**inputs)
                if not torch.is_tensor(feats):  # newer transformers return an output object
                    emb = getattr(feats, "image_embeds", None)
                    feats = emb if emb is not None else feats.pooler_output
                feats = feats / feats.norm(dim=-1, keepdim=True)
            out[rows] = feats.cpu().numpy().astype(np.float16)
        done = min(start + args.batch, len(items))
        print(f"\r{done}/{len(items)} images", end="", flush=True)
    print()

    out.tofile(os.path.join(HERE, "embeddings.bin"))
    meta = {
        "model": args.model,
        "browserModel": BROWSER_MODELS[args.model],
        "dim": dim,
        "count": len(items),
        "dtype": "float16",
        "catalogueHash": catalogue_hash,
    }
    json.dump(meta, open(os.path.join(HERE, "embeddings.json"), "w"), indent=2)
    print(f"Saved embeddings.bin ({out.nbytes / 1e6:.1f} MB) and embeddings.json")
    if failed:
        print(f"{len(failed)} images could not be read (they will only match keyword searches):")
        for p, e in failed[:20]:
            print("  ", p, "-", e)


if __name__ == "__main__":
    main()
