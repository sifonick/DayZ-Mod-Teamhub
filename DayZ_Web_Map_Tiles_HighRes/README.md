DAYZ HIGH-RESOLUTION XYZ TILE SET
================================

Each of the four terrains has one satellite base, one paper base, one transparent
road overlay and one transparent building-box overlay.

MAPS: chernarus, livonia, nasdara, sakhal
TILE SIZE: 256 x 256 pixels
ZOOM LEVELS: z0-z5 (native detail through z5)
TILES PER LAYER: 1365
TOTAL: 21840 tiles

ALIGNED BASE IMAGE SIZES:
Chernarus 7616 x 7616; Livonia 7616 x 7616; Nasdara 8064 x 8064; Sakhal 7616 x 7616.
The standalone white road PNGs are rendered at these exact native base dimensions.
Use the matching PNG one-to-one with its satellite base. For the tiled map, use
the roads tile layer; every tiled layer is normalized to 8192 x 8192 first.

FULL-SIZE ALIGNED WHITE ROAD PNGS:
roads_aligned_png/Chernarus_Roads_White_Aligned_7616.png
roads_aligned_png/Livonia_Roads_White_Aligned_7616.png
roads_aligned_png/Nasdara_Roads_White_Aligned_8064.png
roads_aligned_png/Sakhal_Roads_White_Aligned_7616.png

FOLDER PATTERNS:
tiles/{map}/sat/{z}/{x}/{y}.jpg
tiles/{map}/paper/{z}/{x}/{y}.jpg
tiles/{map}/roads/{z}/{x}/{y}.png
tiles/{map}/buildings/{z}/{x}/{y}.png

The paper maps use terrain height data, contour lines, roads and English place
labels. Nasdara uses the aged high-resolution paper map made for this project.
The roads and buildings are transparent overlays. The paper base already has
printed roads and labels, so show the roads overlay primarily with the satellite
base to avoid drawing roads twice.

All source images were normalized across the full square DayZ world to a common
8192-pixel map extent before being tiled. Source maps have different native pixel
dimensions; this normalization preserves their shared world-coordinate bounds.
Transparent overlays retain their alpha channel. Tile rows use standard XYZ
ordering with y=0 at the top; there is no TMS y flip.

LEAFLET CRS.SIMPLE SETUP:

const bounds = [[0, 0], [256, 256]];
const map = L.map('map', {
  crs: L.CRS.Simple,
  minZoom: 0,
  maxZoom: 5,
  maxBounds: bounds
});
map.fitBounds(bounds);

L.tileLayer('/tiles/chernarus/sat/{z}/{x}/{y}.jpg', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds
}).addTo(map);

// Optional overlays use the same bounds:
L.tileLayer('/tiles/chernarus/roads/{z}/{x}/{y}.png', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds, pane: 'overlayPane'
}).addTo(map);
L.tileLayer('/tiles/chernarus/buildings/{z}/{x}/{y}.png', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds, pane: 'overlayPane'
}).addTo(map);

DAYZ WORLD COORDINATES:

For a DayZ point [X, Z] in metres, convert it to Leaflet CRS.Simple as:
[lat, lng] = [Z / worldSizeMetres * 256, X / worldSizeMetres * 256]

Use the selected map's worldSizeMetres from tile_manifest.json. X increases east
and Z increases north. The tile set is a local square map and must not use a
latitude/longitude or Web Mercator projection.

PAPER STYLES:

Chernarus, Livonia and Sakhal paper rasters were generated from the exported
terrain, road and place-name data. Nasdara uses the existing 8192-pixel aged
relief paper map. The categories building overlay includes standard buildings,
large structures, military structures, tents, containers, and the Nasdara dam.

See tile_manifest.json for map sizes, URL templates, formats and zoom ranges.


REPOSITORY PACKAGE NOTES
========================
This package contains the deployable 21,840-tile pyramids, the tile manifest, the setup guide and previews, plus four native-size white road PNGs in roads_aligned_png/. Use a raw road PNG only with its matching full-size satellite image at identical dimensions. For a tiled website, use the roads tile layer with the other map tiles; do not overlay the raw PNG over the tiled map.

The original source-maps folder and ZIP archive remain in the local output folder and are omitted from this repository package. The ZIP duplicates the tile files and exceeds GitHub's individual-file limit; three source paper PNGs exceed that limit. The original local files are unchanged.

