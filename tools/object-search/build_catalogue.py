"""Build catalogue.json for the Patch Atlas object search.

Run from the root of the DayZ-Mod-Teamhub repo:
    python tools/object-search/build_catalogue.py

No extra packages needed. Re-run it whenever you add or rename images,
then re-run build_embeddings.py so the AI data matches the new catalogue.
"""
import json
import os
import re
import sys

ROOT = os.getcwd()
IMG = "assets/model-images"
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "catalogue.json")

# Folders that are not game objects (site promos, project screenshots) or that
# duplicate other folders (images/ mirrors the rest of the tree).
SKIP_TOP = {"images", "projects", "promos", "worlds"}
EXTS = (".jpg", ".jpeg", ".png", ".webp")

MAP_IDS = {"chernarusplus": "Chernarus", "enoch": "Livonia", "sakhal": "Sakhal", "nasdara": "Nasdara"}
TREE_FILES = {"chernarusplus": "chernarus", "enoch": "livonia", "sakhal": "sakhal", "nasdara": "nasdara"}
# Asset-set suffix on the top folder -> the map it was made for.
SET_HINT = {"bliss": "Livonia", "sakhal": "Sakhal", "takistan": "Nasdara"}

TOP_CATEGORY = {
    "structures": "Structures", "water": "Water", "plants": "Plants", "tree": "Plants",
    "rocks": "Rocks", "vehicles": "Vehicles", "vehicles_cropped": "Vehicles",
    "weapons": "Weapons", "gear": "Gear", "characters": "Characters", "animals": "Animals",
    "data": "Effects & data", "builds": "Compositions", "presets": "Compositions",
}

# Extra words for the keyword search, keyed by a token found in the path/name.
SYNONYMS = {
    # materials and looks
    "metal": "metal steel iron", "tin": "metal tin corrugated", "stainless": "metal steel",
    "container": "metal shipping container", "containers": "metal shipping container",
    "garage": "garage metal shed", "garages": "garage metal shed", "hangar": "hangar metal",
    "hanger": "hangar metal", "tank": "tank metal", "fueltank": "fuel tank metal",
    "pipe": "pipe metal", "pipes": "pipe metal", "rail": "rail railway metal train",
    "barrel": "barrel drum metal", "locker": "locker metal", "fridge": "fridge metal appliance",
    "wreck": "wreck wrecked metal rusty", "wrecks": "wreck wrecked metal rusty",
    "crane": "crane metal industrial", "gantry": "gantry metal", "scaffolding": "scaffolding metal",
    "wood": "wood wooden timber", "wooden": "wood wooden timber", "plank": "wood plank",
    "brick": "brick masonry", "concrete": "concrete cement", "stone": "stone rock",
    "glass": "glass window", "sand": "sand desert", "mud": "mud dirt earth",
    "ruin": "ruin ruined destroyed broken", "ruins": "ruin ruined destroyed", "rubble": "rubble debris destroyed",
    "aban": "abandoned", "collapsed": "collapsed destroyed ruin",
    # naming shorthands
    "mil": "military army", "ind": "industrial factory", "misc": "miscellaneous",
    "zmbm": "zombie infected male", "zmbf": "zombie infected female",
    "staticobj": "static object",
    "wall": "wall barrier", "walls": "wall barrier", "fen": "fence", "fence": "fence barrier",
    "gate": "gate entrance", "house": "house home residential building",
    "housebig": "big house building", "housesmall": "small house building",
    "tenement": "apartment block flats", "tenements": "apartment block flats",
    "houseblock": "apartment block flats", "shed": "shed hut outbuilding", "sheds": "shed hut",
    "tent": "tent camp", "camping": "tent camp", "bunker": "bunker underground military",
    "tower": "tower", "watertower": "water tower", "church": "church chapel religious",
    "cemetery": "cemetery graveyard grave", "tombstone": "grave gravestone",
    "hospital": "hospital medical", "medical": "medical medicine health",
    "police": "police station", "school": "school", "fuelstation": "petrol gas station fuel",
    "pier": "pier dock harbour", "harbour": "harbour port dock", "bridge": "bridge",
    "sign": "sign signpost", "signs": "sign signpost", "bilboard": "billboard advert sign",
    "decal": "decal ground marking", "road": "road", "roads": "road", "furniture": "furniture interior",
    "chair": "chair seat furniture", "table": "table furniture", "bench": "bench seat",
    "lamp": "lamp light", "power": "power electricity", "pole": "pole post",
    "airfield": "airfield airport runway", "runway": "runway airfield",
    # gear
    "mag": "magazine ammo", "ammo": "ammunition bullets", "optic": "scope sight optic",
    "optics": "scope sight optic", "headgear": "hat helmet head", "pants": "trousers legs clothing",
    "shoes": "boots footwear", "gloves": "gloves hands", "vests": "vest armour", "backpacks": "backpack bag",
    "jacket": "jacket coat clothing", "food": "food eat", "drinks": "drink bottle",
    # vehicles (also matched without trailing digits, e.g. sed02 -> sed)
    "sed": "car sedan vehicle", "hb": "car hatchback vehicle", "lr": "land rover 4x4 car vehicle",
    "trailer": "trailer vehicle", "bmp": "armoured vehicle military tank", "bmp1": "armoured vehicle military tank",
    "hatchback": "car vehicle", "sedan": "car vehicle", "civiliansedan": "car vehicle", "offroadhatchback": "car vehicle",
    "offroad": "car vehicle 4x4", "van": "van vehicle", "truck": "truck lorry vehicle", "bus": "bus vehicle",
    "transitbus": "bus vehicle", "tractor": "tractor vehicle farm", "skoda": "car vehicle", "volha": "car vehicle",
    "lada": "car vehicle", "sarka": "car vehicle", "ural": "truck lorry military vehicle", "v3s": "truck lorry vehicle",
    "c130j": "plane aircraft", "mi8": "helicopter aircraft", "uh1y": "helicopter aircraft", "boat": "boat",
    # vegetation
    "t": "tree", "b": "bush shrub", "c": "clutter grass", "d": "dead fallen",
    "piceaabies": "spruce conifer pine tree", "pinussylvestris": "scots pine tree conifer",
    "pinusbrutia": "pine tree conifer", "betulapendula": "birch tree", "betulapendulae": "birch tree",
    "betulahumilis": "birch shrub bush", "betulanana": "dwarf birch shrub",
    "quercusrobur": "oak tree", "fagussylvatica": "beech tree", "larixdecidua": "larch tree conifer",
    "fraxinusexcelsior": "ash tree", "salixalba": "willow tree", "alnusglutinosa": "alder tree",
    "carpinusbetulus": "hornbeam tree", "sorbusaucuparia": "rowan tree", "acerplatanoides": "maple tree",
    "malussylvestris": "apple tree fruit", "prunusdomestica": "plum tree fruit",
    "prunusspinosa": "blackthorn bush", "crataeguslaevigata": "hawthorn bush",
    "sambucusnigra": "elder bush", "corylusavellana": "hazel bush", "juniperuscommunis": "juniper bush",
    "populus": "poplar tree", "tiliacordata": "linden lime tree", "ficusbenjamina": "fig tree",
    "oleaeuropaea": "olive tree", "phoenixrupicola": "palm tree", "caraganaarborescens": "pea shrub bush",
    "phragmites": "reeds grass", "urtica": "nettles weeds", "naked": "bare leafless dead",
    "winter": "winter snow snowy", "frozen": "frozen ice icy snow", "latefall": "autumn late fall",
    "summer": "summer green", "autumn": "autumn fall", "snow": "snow snowy winter", "ice": "ice frozen",
}

# Czech words in Bohemia's file names -> English (used for tags and given to the AI describer)
CZECH = {
    "stul": "table", "kamna": "stove", "dkamna": "stove", "skrin": "wardrobe cupboard", "brownskrin": "brown wardrobe cupboard",
    "almara": "wardrobe cupboard", "plot": "fence", "postel": "bed", "palanda": "bunk bed", "panelak": "apartment block",
    "lekarnicka": "first aid cabinet", "pokladna": "cash register till", "pult": "shop counter", "pultskasou": "shop counter with till",
    "uhli": "coal", "bila": "white", "cerna": "black", "kov": "metal", "beton": "concrete", "klen": "maple",
    "vojenska": "military", "vojensky": "military", "korb": "basket hoop", "fluor": "fluorescent light", "tv": "television",
}
SYNONYMS.update(CZECH)

NOISE = {"pa", "jpg", "jpeg", "png", "webp", "p3d", "dz", "proxy", "dzplants"}


def stem_of(filename, rel_dir):
    s = filename.lower()
    for ext in EXTS:
        if s.endswith(ext):
            s = s[: -len(ext)]
    s = re.sub(r" \(\d+\)$", "", s)
    flat = "dz" + rel_dir.replace("/", "")
    if s.startswith(flat):  # e.g. dzplants_sakhalwinterb_x.p3d
        s = s[len(flat):]
    if s.endswith(".p3d"):
        s = s[:-4]
    return s


def load_map_data():
    """model path (lower, no dz/) -> {maps:set, class:str, category:str}"""
    known = {}
    for mid, name in MAP_IDS.items():
        path = os.path.join("data/buildings", f"{mid}_buildings.json")
        if os.path.exists(path):
            for r in json.load(open(path, encoding="utf-8"))["buildings"]:
                k = r["model"].lower().removeprefix("dz/")
                e = known.setdefault(k, {"maps": set(), "class": r.get("class"), "subcat": r.get("category")})
                e["maps"].add(name)
        path = os.path.join("data/trees", f"{TREE_FILES[mid]}_trees.json")
        if os.path.exists(path):
            for m in json.load(open(path, encoding="utf-8"))["models"].values():
                k = m.lower().removeprefix("dz/")
                known.setdefault(k, {"maps": set(), "class": None, "subcat": "vegetation"})["maps"].add(name)
    # Also index by bare stem for lookups where the folder layout differs.
    by_stem = {}
    for k, v in known.items():
        by_stem.setdefault(os.path.basename(k)[:-4], []).append((k, v))
    return known, by_stem


MATERIAL_WORDS = {"metal", "steel", "iron", "corrugated", "wood", "wooden", "timber", "rusty"}


def tags_for(model_dir, stem, cls, category):
    """Words for the keyword search. Synonyms that describe what something is made
    of are only added from the object's own name, and never for carried items,
    so 'containers' (a gear folder) or a gun 'barrel' don't count as metal."""
    def split(text):
        return [t for t in re.split(r"[^a-z0-9]+", text.lower()) if t and t not in NOISE and not t.isdigit()]
    carried = category in ("Weapons", "Gear", "Characters", "Animals")
    words = []
    for from_name, tokens in ((False, split(model_dir)), (True, split(f"{stem} {cls or ''}"))):
        for t in tokens:
            words.append(t)
            for w in SYNONYMS.get(t, SYNONYMS.get(re.sub(r"\d+$", "", t), "")).split():
                if w in MATERIAL_WORDS and (carried or not from_name):
                    continue
                words.append(w)
    seen, out = set(), []
    for w in words:
        if w not in seen:
            seen.add(w)
            out.append(w)
    return out


# Words the AI sometimes adds that describe the screenshot, not the object.
JUNK_TAGS = {"game", "dayz", "3d", "model", "3d model", "game asset", "asset", "virtual", "object", "map", "element",
             "video game", "render", "3d render", "screenshot", "game object", "map element", "digital", "cgi"}
AI_NOT_MATERIALS = {"other", "fur or feathers", "skin"}


GAME_PHRASE = re.compile(r",?\s*(used|intended|designed|made)?\s*(for|in)\s+(map[- ]making|map makers?|(the\s+)?(video\s+)?game\s+dayz|dayz)[^.]*", re.I)


def clean_sentence(text):
    """Remove 'used for map making in the video game DayZ' and similar from AI descriptions."""
    t = GAME_PHRASE.sub("", text or "").strip()
    t = re.sub(r"\s+([.,])", r"\1", t)
    return t if t.endswith(".") or not t else t + "."


def find_facts(it, facts, by_base):
    """Facts for an item: by model path, else by unique file name (images named after classes)."""
    m = (it.get("model") or "").lower()
    if m in facts:
        return facts[m]
    for cand in (os.path.basename(m), os.path.basename(m).removeprefix("land_"),
                 (it["name"].removeprefix("land_").removeprefix("staticobj_") + ".p3d")):
        hits = by_base.get(cand)
        if hits and len(hits) == 1:
            return facts[hits[0]]
    return None


def enrich(items, folder):
    """Add game-file facts (facts/extract_model_facts.py) and AI descriptions (describe_images.py)."""
    fpath = os.path.join(folder, "model_facts.json")
    facts = json.load(open(fpath, encoding="utf-8")) if os.path.exists(fpath) else {}
    by_base = {}
    for k in facts:
        by_base.setdefault(os.path.basename(k), []).append(k)
    desc = {}
    dpath = os.path.join(folder, "descriptions.jsonl")
    if os.path.exists(dpath):
        for line in open(dpath, encoding="utf-8"):
            try:
                r = json.loads(line)
                if r.get("v"):  # lines without a version came from the first test prompt: ignored
                    desc[r["img"]] = r  # later lines win
            except (json.JSONDecodeError, KeyError):
                pass
    nf = nd = 0
    for it in items:
        f = find_facts(it, facts, by_base) if facts else None
        d = desc.get(it["img"])
        mats = []
        if f:
            nf += 1
            it["size"] = f["size"]
            it["sizeClass"] = f["sizeClass"]
            it["mapType"] = f["mapType"]
            mats += f["materials"] + [h for h in f["materialHints"] if h not in ("rusty", "snow")]
            if "rusty" in f["materialHints"]:
                it["rusty"] = True
        if d:
            nd += 1
            it["description"] = clean_sentence(d.get("description", ""))
            it["objectType"] = d.get("objectType", "").strip().lower()
            it["colours"] = [c.lower() for c in d.get("colours", [])][:3]
            it["condition"] = {"new": "intact"}.get(d.get("condition"), d.get("condition"))
            if not f:  # game-file materials are exact; only use the AI's when there are none
                mats += [m for m in d.get("materials", []) if m not in AI_NOT_MATERIALS]
            extra = [t.lower().strip() for t in d.get("tags", []) if t.lower().strip() not in JUNK_TAGS]
            extra += it["objectType"].split()
            for t in extra:
                if t and t not in it["tags"]:
                    it["tags"].append(t)
        if mats:
            seen = []
            for m in mats:
                if m not in seen:
                    seen.append(m)
            it["materials"] = seen
            # facts first: the first physical material is the most reliable
            it["tags"] += [w for m in seen for w in m.split() if w not in it["tags"]]
        for k in ("colours",):
            if it.get(k):
                it["tags"] += [c for c in it[k] if c not in it["tags"]]
        if it.get("condition") and it["condition"] != "not applicable" and it["condition"] not in it["tags"]:
            it["tags"].append(it["condition"])
    if facts or desc:
        print(f"Game-file facts for {nf} objects, AI descriptions for {nd}.")


def attach_studio(items, folder):
    """Point each object at its Patch Atlas Studio pictures, if they have been taken.

    studioImgs lists the sides in the order to show them; studioImg is the one shown first.
    Side 1 (the front-left view) is the default. List an object in studio/use_side2.txt (its
    class, model file name or picture name, one per line) to show side 2 first instead, e.g.
    for objects with no back texture that look the wrong way round from side 1.
    Cut-outs (assets/model-images-cutout/..., made by studio/cutout.py) are used when they exist.
    """
    path = os.path.join(folder, "studio", "studio_captures.jsonl")
    if not os.path.exists(path):
        return
    side2_path = os.path.join(folder, "studio", "use_side2.txt")
    side2 = set()
    if os.path.exists(side2_path):
        for line in open(side2_path, encoding="utf-8"):
            line = line.split("#")[0].strip().lower()
            if line:
                side2.add(re.sub(r"\.(p3d|jpg|webp|png)$", "", line.replace("\\", "/").rsplit("/", 1)[-1]))

    def best(file):
        cut = "assets/model-images-cutout/" + os.path.splitext(os.path.relpath(file, "assets/model-images-studio"))[0].replace("\\", "/") + ".webp"
        return cut if os.path.exists(cut) else file

    views = {}   # catalogue img -> {view: file}
    spawn_of = {}
    for line in open(path, encoding="utf-8"):
        try:
            r = json.loads(line)
        except json.JSONDecodeError:
            continue
        if r.get("file") and os.path.exists(r["file"]):
            for img in r["imgs"]:
                views.setdefault(img, {})[r.get("view", 0)] = best(r["file"])
                spawn_of[img] = r.get("spawn", "")
    n = 0
    for it in items:
        v = views.get(it["img"])
        if not v:
            continue
        order = sorted(v)                                     # side 1 first, then side 2
        keys = {(it.get("class") or "").lower(), it["name"].lower(),
                spawn_of.get(it["img"], "").replace("\\", "/").rsplit("/", 1)[-1].lower().removesuffix(".p3d"),
                os.path.splitext(os.path.basename(v[order[0]]))[0].lower().removesuffix("_2")}
        if keys & side2 and 1 in v:
            order = [1] + [k for k in order if k != 1]
        it["studioImgs"] = [v[k] for k in order]
        it["studioImg"] = it["studioImgs"][0]
        n += 1
    print(f"Studio pictures for {n} objects.")


def main():
    if not os.path.isdir(IMG):
        sys.exit(f"Run this from the repo root: can't find {IMG}/")
    known, by_stem = load_map_data()
    entries = {}
    priority = {".jpg": 0, ".jpeg": 1, ".png": 2, ".webp": 3}
    for dp, dirs, files in os.walk(IMG):
        rel = os.path.relpath(dp, IMG).replace("\\", "/")
        top = rel.split("/")[0]
        if top in SKIP_TOP:
            dirs[:] = []
            continue
        dirs[:] = [d for d in dirs if not d.startswith(".")]
        for f in files:
            if f.startswith(".") or not f.lower().endswith(EXTS):
                continue
            stem = stem_of(f, rel)
            # one-folder-per-model layout: .../x/x.jpg
            model_dir = rel.lower()
            if os.path.basename(model_dir) == stem:
                model_dir = os.path.dirname(model_dir)
            if top in ("builds", "presets"):
                model_dir = top
            key = f"{model_dir}/{stem}"
            path = f"{IMG}/{rel}/{f}" if rel != "." else f"{IMG}/{f}"
            rank = (" (" in f, priority.get(os.path.splitext(f)[1].lower(), 9))
            if key in entries and entries[key]["_rank"] <= rank:
                continue
            entries[key] = {"_rank": rank, "_top": top, "dir": model_dir, "stem": stem, "img": path}

    # Class names from class-pack/make_class_pack.py (vanilla scan + PA_ classes).
    extra_path = os.path.join(os.path.dirname(OUT), "classes.json")
    extra = json.load(open(extra_path, encoding="utf-8")) if os.path.exists(extra_path) else {}

    items = []
    for key, e in sorted(entries.items()):
        model_rel = f"{e['dir']}/{e['stem']}.p3d"
        info = known.get(model_rel)
        if info is None:
            for alt in (e["stem"], e["stem"].removeprefix("land_")):
                cands = by_stem.get(alt)
                if cands and len(cands) == 1:
                    info = cands[0][1]
                    break
        top = e["_top"]
        suffix = top.split("_")[-1] if "_" in top else ""
        base_top = top.split("_")[0] if suffix in SET_HINT or top == "vehicles_cropped" else top
        category = TOP_CATEGORY.get(base_top, TOP_CATEGORY.get(top, "Other"))
        name = e["stem"]
        if "wreck" in name.lower() or "wreck" in e["dir"].lower():
            category = "Vehicles"  # wrecks are vehicles, wherever the game files keep them
        cls = info["class"] if info else None
        model = f"dz/{model_rel}"
        if name.startswith("land_") and not info:
            # Image is named after the class, not the model file.
            cls, model = "Land_" + name[5:], None
        if top in ("builds", "presets"):
            model = None
        source = "map data" if cls else None
        guess = model
        x = extra.get(e["img"])
        if cls and x and x["class"].lower() == cls.lower():
            cls = x["class"]  # exact spelling from the in-game scan
            model = model or x.get("model")
        if not cls and model and x and x["source"] != "map data":
            cls, source = x["class"], x["source"]
            model = x.get("model", model)  # real model path from the in-game scan
        items.append({
            "id": len(items),
            "name": name,
            "class": cls,
            # "map data", "vanilla" (found by the in-game scan) or "patch-atlas" (needs the PatchAtlas_Objects mod)
            "classSource": source,
            "model": model,
            "guessModel": guess if guess != model else None,
            "img": e["img"],
            "category": category,
            # asset set the object belongs to (from its folder)
            "set": SET_HINT.get(suffix, "Base"),
            # maps the object is placed on, from data/buildings and data/trees
            "maps": sorted(info["maps"]) if info else [],
            "tags": tags_for(e["dir"], name, cls, category),
        })

    enrich(items, os.path.dirname(OUT))
    attach_studio(items, os.path.dirname(OUT))
    out = {
        "version": 2,
        "imageBase": "https://raw.githubusercontent.com/sifonick/DayZ-Mod-Teamhub/main/",
        "count": len(items),
        "items": items,
    }
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(out, fh, separators=(",", ":"))
    print(f"Wrote {len(items)} objects to {OUT}")
    write_map_images(items, os.path.dirname(OUT))


def write_map_images(items, folder):
    """Write map_images.json: old picture path -> studio picture, for the Patch Atlas map.

    The map's buildings data names each building's picture by its old path
    (assets/model-images/...). The map looks that path up here and shows the studio
    picture (the side shown first in the Object Finder) when there is one.
    """
    images = {it["img"]: it["studioImgs"][0] for it in items if it.get("studioImgs")}
    path = os.path.join(folder, "map_images.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump({"version": 1, "images": images}, fh, separators=(",", ":"), sort_keys=True)
    print(f"Map pictures: {len(images)} objects use studio pictures ({path}).")


if __name__ == "__main__":
    main()
