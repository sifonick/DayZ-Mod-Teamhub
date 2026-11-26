# Object Finder

A search page for every object image in `assets/model-images`. You can search by description ("metal object", "rusty car wreck", "stone terrace") and filter by map, material, size and condition. It runs entirely in the visitor's browser, with no server.

## What it knows about each object

| Source | What it gives | Script |
| --- | --- | --- |
| Image folders | name, category, asset set, keyword tags | `build_catalogue.py` |
| Map data and the in-game class scan | class name, maps it's placed on | `class-pack/make_class_pack.py` |
| **Game files** (the PBOs) | **size in metres, what it's made of, map legend type** | `facts/extract_model_facts.py` |
| **Local AI model** (Ollama) | **a one-line description, object type, colours, condition, more tags** | `describe_images.py` |
| CLIP image model | picture vectors, for search by look and Find similar | `build_embeddings.py` |
| MiniLM text model | description vectors, for search by meaning | `build_text_index.py` |

"Made of" comes from each model's physics materials, which is how the game decides what bullets go through. It's the most reliable fact on the page.

## Running it all (from the repo root)

```bash
# 1. Game-file facts (already included, re-run after a DayZ update)
python tools/object-search/facts/extract_model_facts.py "C:/Program Files (x86)/Steam/steamapps/common/DayZServer"

# 2. AI descriptions (needs Ollama, see below). Resumable: stop with Ctrl+C, run again to carry on.
python tools/object-search/describe_images.py --limit 20     # try a few first
python tools/object-search/describe_images.py                 # then the rest (several hours)

# 3. Rebuild the object list with everything merged in
python tools/object-search/build_catalogue.py

# 4. Search data
python tools/object-search/build_text_index.py               # a few minutes, re-run after every step 3
python tools/object-search/build_embeddings.py               # only when images are added, removed or renamed
```

Then commit everything in `tools/object-search/` and push.

### Ollama setup (for step 2)

1. Install Ollama from https://ollama.com and start it.
2. In a terminal, run `ollama pull qwen2.5vl:7b`. It's 6 GB and runs well on a graphics card with 8 GB.
3. On a smaller graphics card, use the 3B version: run `ollama pull qwen2.5vl:3b`, then add `--model qwen2.5vl:3b` when you run step 2.

Water, Characters, Weapons, Gear and Effects are skipped by default, because their names already say what they are. Add `--skip ""` to describe everything. If it is slow, check `ollama ps` shows "100% GPU", or use `--max-side 336` or the 3b model.

## Files

| File | What it is |
| --- | --- |
| `index.html` | The search page. |
| `catalogue.json` | One entry per object, with everything above merged in. |
| `model_facts.json` | Size, materials and map type for each model, read from the game files. |
| `descriptions.jsonl` | The AI descriptions, one line per image. Kept so re-runs skip finished images. |
| `classes.json` | Class names (see `class-pack/README.md`). |
| `embeddings.*`, `text_embeddings.*` | Search data. |

## Putting it on Patch Atlas

When `index.html` is hosted outside the repo, it reads all its data and images from `raw.githubusercontent.com/sifonick/DayZ-Mod-Teamhub/main/`. To point it at other locations, set these before the script runs:

```html
<script>window.OBJECT_FINDER_DATA = 'https://…/object-search/'; window.OBJECT_FINDER_IMAGES = 'https://…/';</script>
```

Add `?debug` to the page address to see setup notes, such as missing or out-of-date search data.

## How results are ranked

Up to three rankings are combined:

- **Meaning:** your words compared with each object's description and facts. This ranking counts most.
- **Look:** your words compared with each picture.
- **Exact words:** matches in names, tags and materials. An object's main material counts most.

An object near the top of several lists comes first. The filters apply before ranking. **Find similar** combines look and meaning.
