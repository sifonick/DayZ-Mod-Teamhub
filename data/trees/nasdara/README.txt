Nasdara trees

Add an optional Trees overlay from maps/atlas/tiles/nasdara/trees/{z}/{x}/{y}.png. Use the satellite layer's XYZ grid, 256-pixel tiles and zooms 0–6. Stack trees above the satellite layer and below roads, buildings and labels.

For individual trees, load data/trees/nasdara/index.json. The listed chunks are relative to the index. Each row holds [X, Z, modelId]. X increases east, Z increases north. At zoom 6 the pixel position is [X, 16384-Z]. Fetch visible chunks on demand. These are standing tree model placements from the Nasdara vegetation export. The green symbols use a common size. They do not represent measured canopy outlines.

Southern highway

The M12 carriageways use the placed asphalt models and bridge decks. Nearby endpoints are joined along matching travel directions. Other roads use simplified curves. Refresh cached road tiles or pin the new release revision.
