DayZ building-only data

These files contain standalone building models and building ruins extracted from the
local in-game world exports. The filter removes walls, gates, fences, embankments,
wrecks, containers, road and stream pieces, utility towers, oil pumps, and small props.
It keeps houses, sheds, shops, workshops, garages, industrial and military buildings,
public buildings, and building ruins.

Files
  chernarusplus_buildings.json  Chernarus       9,144 buildings
  enoch_buildings.json          Livonia          4,498 buildings
  nasdara_buildings.json        Nasdara         10,402 buildings
  sakhal_buildings.json         Sakhal           5,649 buildings
  index.json                    map/file summary

Coordinate fields
  x              DayZ world X in metres (east)
  z              DayZ world Z in metres (north)
  elevation      metres above sea level
  yaw/pitch/roll object orientation in degrees
  modelBounds    six local model bounds: minX, minY, minZ, maxX, maxY, maxZ

For a north-up image with a square world extent, convert with:
  pixelX = x / worldSizeMetres * imageWidth
  pixelY = (worldSizeMetres - z) / worldSizeMetres * imageHeight

Records are sorted north to south, then west to east. A few Chernarus and Sakhal
edge objects sit just outside the nominal world square; their original coordinates
are kept so the map renderer can clip them naturally.
