DAYZ HIGH-RESOLUTION XYZ TILE SET
================================

Each terrain has seven tile layers: a satellite base, a paper base, a transparent
road overlay, a transparent building-box overlay, and three transparent place-name
tiers (major, minor, village).

MAPS: chernarus, livonia, nasdara, sakhal
TILE SIZE: 256 x 256 pixels
ZOOM LEVELS: z0-z5 (native detail through z5)
TILES PER LAYER: 1365
TOTAL: 38220 tiles
FORMATS: JPEG for satellite and paper; lossless WebP with alpha for overlays

ALIGNED BASE IMAGE SIZES:
Chernarus 7616 x 7616; Livonia 7616 x 7616; Nasdara 8064 x 8064; Sakhal 7616 x 7616.
The standalone white road PNGs are rendered at these exact native base dimensions.
Use a raw road PNG one-to-one with its matching satellite base. For a tiled map,
use the roads tile layer; every tile layer shares an 8192 x 8192 normalized extent.

FULL-SIZE ALIGNED WHITE ROAD PNGS:
roads_aligned_png/Chernarus_Roads_White_Aligned_7616.png
roads_aligned_png/Livonia_Roads_White_Aligned_7616.png
roads_aligned_png/Nasdara_Roads_White_Aligned_8064.png
roads_aligned_png/Sakhal_Roads_White_Aligned_7616.png

FOLDER PATTERNS:
tiles/{map}/sat/{z}/{x}/{y}.jpg
tiles/{map}/paper/{z}/{x}/{y}.jpg
tiles/{map}/roads/{z}/{x}/{y}.webp
tiles/{map}/buildings/{z}/{x}/{y}.webp
tiles/{map}/labels_major/{z}/{x}/{y}.webp
tiles/{map}/labels_minor/{z}/{x}/{y}.webp
tiles/{map}/labels_village/{z}/{x}/{y}.webp

Transparent overlay tiles use lossless WebP with an alpha channel. The separate
label tiers let a website choose which names to show at each zoom. As a starting
point, show major labels at z0-z1, minor labels at z2-z3, and village labels at
z4-z5; show only one tier at a time to avoid duplicate names. The paper base
already has roads and place names printed on it, so show the roads and labels
overlays primarily with the satellite base.

All source images are normalized across the full square DayZ world to a common
8192-pixel map extent before tiling. Source maps have different native pixel
dimensions; this normalization preserves their shared world-coordinate bounds.
Tile rows use standard XYZ ordering with y=0 at the top; there is no TMS y flip.

LEAFLET CRS.SIMPLE SETUP:

const bounds = [[0, 0], [256, 256]];
const map = L.map('map', {
  crs: L.CRS.Simple,
  minZoom: 0,
  maxZoom: 5,
  maxBounds: bounds
});
map.fitBounds(bounds);

L.tileLayer('/maps/atlas/tiles/chernarus/sat/{z}/{x}/{y}.jpg', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds
}).addTo(map);

// Transparent WebP overlays use the same bounds:
const roads = L.tileLayer('/maps/atlas/tiles/chernarus/roads/{z}/{x}/{y}.webp', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds
});
const buildings = L.tileLayer('/maps/atlas/tiles/chernarus/buildings/{z}/{x}/{y}.webp', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds
});
const labelsMajor = L.tileLayer('/maps/atlas/tiles/chernarus/labels_major/{z}/{x}/{y}.webp', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds
});
const labelsMinor = L.tileLayer('/maps/atlas/tiles/chernarus/labels_minor/{z}/{x}/{y}.webp', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds
});
const labelsVillage = L.tileLayer('/maps/atlas/tiles/chernarus/labels_village/{z}/{x}/{y}.webp', {
  tileSize: 256, minZoom: 0, maxNativeZoom: 5,
  maxZoom: 5, noWrap: true, bounds
});

roads.addTo(map);
buildings.addTo(map);

function updateLabelTier() {
  const zoom = map.getZoom();
  const selected = zoom < 2 ? labelsMajor : zoom < 4 ? labelsMinor : labelsVillage;
  for (const layer of [labelsMajor, labelsMinor, labelsVillage]) {
    if (layer === selected) map.addLayer(layer);
    else map.removeLayer(layer);
  }
}
map.on('zoomend', updateLabelTier);
updateLabelTier();

DAYZ WORLD COORDINATES:

For a DayZ point [X, Z] in metres, convert it to Leaflet CRS.Simple as:
[lat, lng] = [Z / worldSizeMetres * 256, X / worldSizeMetres * 256]

Use the selected map's worldSizeMetres from tile-manifest.json. X increases east
and Z increases north. The tile set is a local square map and must not use a
latitude/longitude or Web Mercator projection.

PAPER STYLES:

Chernarus, Livonia and Sakhal paper rasters were generated from the exported
terrain, road and place-name data. Nasdara uses the existing 8192-pixel aged
relief paper map. The categories building overlay includes standard buildings,
large structures, military structures, tents, containers, and the Nasdara dam.

See tile-manifest.json for map sizes, URL templates, formats and zoom ranges.


REPOSITORY PACKAGE NOTES
========================
This package contains 38,220 tiles, the tile manifest, the setup guide and
previews, plus four native-size white road PNGs in roads_aligned_png/. Use a raw
road PNG only with its matching full-size satellite image. For a tiled website,
use the corresponding tile layer. Update any hard-coded overlay URLs from .png
to .webp; tile-manifest.json now lists the current templates and formats.

The original full-size source maps, ZIP archive, and source label PNGs remain in
the local output folders and are omitted from this GitHub package. The ZIP
duplicates the tile files and exceeds GitHub's individual-file limit; three
source paper PNGs exceed that limit. The original local source files are unchanged.
