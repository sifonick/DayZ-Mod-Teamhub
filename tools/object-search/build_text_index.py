"""Build the description search data (text_embeddings.bin + text_embeddings.json).

Run from the repo root after build_catalogue.py (and again whenever you re-run it,
for example after describe_images.py has added more descriptions):

    python tools/object-search/build_text_index.py

Uses the same packages as build_embeddings.py (torch, transformers). Takes a few
minutes on a normal processor. The page turns a search into the same kind of vector
in the visitor's browser (Xenova/all-MiniLM-L6-v2, about 23 MB) and compares them.
"""
import hashlib
import json
import os

import numpy as np
import torch
from transformers import AutoModel, AutoTokenizer

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = "sentence-transformers/all-MiniLM-L6-v2"
BROWSER_MODEL = "Xenova/all-MiniLM-L6-v2"


def readable(name):
    words = name.replace("land_", "").replace("staticobj_", "").replace("_", " ")
    return " ".join(w for w in words.split() if not w.isdigit())


def document(it):
    """One short paragraph describing the object, from everything we know about it."""
    parts = []
    if it.get("objectType"):
        parts.append(it["objectType"] + ".")
    if it.get("description"):
        parts.append(it["description"])
    mats = it.get("materials") or []
    if mats:
        parts.append("Made of " + ", ".join(mats[:4]) + ".")
    if it.get("rusty"):
        parts.append("Rusty.")
    if it.get("colours"):
        parts.append("Colours: " + ", ".join(it["colours"]) + ".")
    if it.get("condition") and it["condition"] != "not applicable":
        parts.append("Condition: " + it["condition"] + ".")
    if it.get("sizeClass"):
        w, h, d = it["size"]
        parts.append(f"{it['sizeClass'].capitalize()} size, {w:g} by {d:g} metres, {h:g} metres tall.")
    if it.get("mapType"):
        parts.append("Map type: " + it["mapType"] + ".")
    parts.append(f"{it['category']}: {readable(it['name'])}.")
    tags = [t for t in it.get("tags", []) if len(t) > 2][:20]
    if tags:
        parts.append("Tags: " + ", ".join(tags) + ".")
    return " ".join(parts)


def main():
    items = json.load(open(os.path.join(HERE, "catalogue.json"), encoding="utf-8"))["items"]
    docs = [document(it) for it in items]
    device = "cuda" if torch.cuda.is_available() else "cpu"
    tok = AutoTokenizer.from_pretrained(MODEL)
    model = AutoModel.from_pretrained(MODEL).to(device).eval()
    out = np.zeros((len(docs), model.config.hidden_size), dtype=np.float16)
    for s in range(0, len(docs), 128):
        batch = tok(docs[s:s + 128], padding=True, truncation=True, max_length=256, return_tensors="pt").to(device)
        with torch.no_grad():
            hidden = model(**batch).last_hidden_state
        mask = batch["attention_mask"].unsqueeze(-1).float()
        vec = (hidden * mask).sum(1) / mask.sum(1).clamp(min=1e-9)
        vec = torch.nn.functional.normalize(vec, dim=-1)
        out[s:s + 128] = vec.cpu().numpy().astype(np.float16)
        print(f"\r{min(s + 128, len(docs))}/{len(docs)} objects", end="", flush=True)
    print()
    out.tofile(os.path.join(HERE, "text_embeddings.bin"))
    meta = {
        "model": MODEL, "browserModel": BROWSER_MODEL, "dim": out.shape[1], "count": len(items), "dtype": "float16",
        "catalogueHash": hashlib.sha1("\n".join(i["img"] for i in items).encode()).hexdigest()[:16],
    }
    json.dump(meta, open(os.path.join(HERE, "text_embeddings.json"), "w"), indent=2)
    print(f"Saved text_embeddings.bin ({out.nbytes / 1e6:.1f} MB)")
    print("Example:", docs[min(500, len(docs) - 1)])


if __name__ == "__main__":
    main()
