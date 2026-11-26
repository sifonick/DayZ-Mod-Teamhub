"""Read facts about every model straight from DayZ's game files.

For each .p3d model in the given PBO folders it records:
  - size        bounding box in metres (width x height x depth), from the model header
  - materials   what it is made of, from its physics (penetration) materials and textures
  - mapType     what the map legend calls it (building, fence, wall, rock, tree...)
  - props       raw named properties (class, damage, placement)

Usage (from the repo root; any DayZ or DayZServer install works):
    python tools/object-search/facts/extract_model_facts.py "C:/Program Files (x86)/Steam/steamapps/common/DayZServer"

Writes tools/object-search/model_facts.json. Needs no extra packages.
"""
import glob
import json
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pbo  # noqa: E402

OUT = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "model_facts.json")
WANTED = re.compile(r"^(structures|plants|rocks|water|vehicles)", re.I)

# Physics material (dz\data\data\penetration\<name>.bisurf) -> plain material word
PENETRATION = [
    (r"^(metalplate|metalplatefence|iron|ironplate|castiron|castironplate|armor_\d+mm_plate|armour|thin_wire)", "metal"),
    (r"^(wood|wood_desk)", "wood"),
    (r"^concrete", "concrete"),
    (r"^bricks", "brick"),
    (r"^mud_brick", "mud brick"),
    (r"^(granite|stone|rock)", "stone"),
    (r"^dirt", "earth"),
    (r"^(glass|glassplate|glass_house|glass_armored|glass_impenetrable)", "glass"),
    (r"^(plastic|plastic_material|plexiplate)", "plastic"),
    (r"^(rubber|rubberplate)", "rubber"),
    (r"^(cloth|fabric_thin|fabricp|mattress|cushion)", "fabric"),
    (r"^leather", "leather"),
    (r"^(foliage|foliage_green|coniferfoliage)", "foliage"),
    (r"^hay", "hay"),
    (r"^pottery", "ceramic"),
    (r"^ice", "ice"),
]
# Extra material hints from texture/material file names (English and Czech words BI uses)
TEXTURE_HINTS = [
    (r"asphalt|asfalt", "asphalt"),
    (r"plaster|omitka", "plaster"),
    (r"roof_?tile|tasky|tiles?_roof|strecha_tasky", "roof tiles"),
    (r"corrugat|plech|sheet_?metal", "corrugated metal"),
    (r"rust|rez", "rusty"),
    (r"concrete|beton", "concrete"),
    (r"brick|cihl", "brick"),
    (r"wood|drevo|plank|prkn|timber", "wood"),
    (r"metal|steel|iron|ocel|zelez", "metal"),
    (r"glass|sklo|window", "glass"),
    (r"stone|kamen|rock|granite", "stone"),
    (r"sand|pisek", "sand"),
    (r"snow|snih", "snow"),
    (r"canvas|tarp|plachta|cloth|fabric", "fabric"),
]
PROP_RE = re.compile(rb"\x00(class|damage|dammage|map|placement)\x00([\x20-\x7e]{1,40})\x00", re.I)
PEN_RE = re.compile(rb"penetration\\([a-z0-9_]+)\.bisurf", re.I)
TEX_RE = re.compile(rb"[\x20-\x7e]{3,200}\.(?:paa|rvmat)", re.I)


def bounding_box(d):
    """Model bounding box from the ODOL header, or None if it doesn't look right."""
    try:
        if d[:4] != b"ODOL":
            return None
        nlods = struct.unpack_from("<I", d, 8)[0]
        if not 1 <= nlods <= 64:
            return None
        o = 12 + 4 * nlods  # after the LOD resolution table: ModelInfo
        vals = struct.unpack_from("<18f", d, o)
        mn, mx = vals[12:15], vals[15:18]
        size = [mx[i] - mn[i] for i in range(3)]
        if all(0 <= s < 5000 for s in size) and any(s > 0 for s in size):
            return [round(s, 2) for s in size]
    except struct.error:
        pass
    return None


def materials_of(d):
    counts = {}
    for raw in PEN_RE.findall(d):
        name = raw.decode().lower()
        if name == "weaponlift":
            continue
        for pat, mat in PENETRATION:
            if re.match(pat, name):
                counts[mat] = counts.get(mat, 0) + 1
                break
    hints = set()
    for raw in TEX_RE.findall(d):
        p = raw.decode("latin-1").lower()
        if "penetration\\" in p or p.startswith("#"):
            continue
        base = p.replace("\\", "/").rsplit("/", 2)
        tail = "/".join(base[-2:])  # folder + file name, e.g. "metal/plech_rez_co.paa"
        for pat, mat in TEXTURE_HINTS:
            if re.search(pat, tail):
                hints.add(mat)
    physical = [m for m, _ in sorted(counts.items(), key=lambda kv: -kv[1])]
    return physical, sorted(hints - set(physical))


def size_class(size):
    if not size:
        return None
    big = max(size)
    if big < 1:
        return "tiny"
    if big < 3:
        return "small"
    if big < 10:
        return "medium"
    if big < 30:
        return "large"
    return "huge"


def main():
    roots = sys.argv[1:] or ["."]
    pbos = []
    for r in roots:
        pbos += glob.glob(os.path.join(r, "**", "*.pbo"), recursive=True)
    pbos = [p for p in pbos if WANTED.match(os.path.basename(p))]
    if not pbos:
        sys.exit("No structures/plants/rocks/water/vehicles PBOs found under: " + ", ".join(roots))
    facts = {}
    for path in sorted(pbos):
        prefix, files = pbo.read_pbo(path)
        for name, d in files:
            if not name.lower().endswith(".p3d"):
                continue
            model = f"{prefix}/{name}".lower().lstrip("/")
            props = {}
            for k, v in PROP_RE.findall(d):
                k = k.decode().lower().replace("dammage", "damage")
                props.setdefault(k, v.decode().strip().lower())
            size = bounding_box(d)
            physical, hints = materials_of(d)
            facts[model] = {
                "size": size,
                "sizeClass": size_class(size),
                "materials": physical,
                "materialHints": hints,
                "mapType": props.get("map") if props.get("map") not in (None, "hide", "none") else None,
                "props": props,
            }
        print(f"{os.path.basename(path)}: {len(files)} files")
    with open(OUT, "w", encoding="utf-8") as fh:
        json.dump(facts, fh, separators=(",", ":"), sort_keys=True)
    with_size = sum(1 for f in facts.values() if f["size"])
    with_mat = sum(1 for f in facts.values() if f["materials"])
    print(f"\n{len(facts)} models: {with_size} with size, {with_mat} with physical materials -> {OUT}")


if __name__ == "__main__":
    main()
