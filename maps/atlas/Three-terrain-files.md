# Chernarus, Livonia and Sakhal map files

Read each terrain's entry in tile-manifest.json. Layer tileTemplate paths are relative to the manifest. The assets paths are relative to the repository root. Chernarus uses the DayZ terrain ID chernarusplus, and Livonia uses enoch.

Satellite, road, tree and building layers use 256-pixel XYZ tiles from zoom 0 through 6. Paper uses the existing contour-map tiles through zoom 5 and supports display at zoom 6 by overzooming. A full-size 8192-pixel paper JPEG is linked per terrain. All five layers cover the full world. X increases east and Z increases north. At zoom z, the image coordinate is [X, worldSizeMetres - Z] multiplied by (256 * 2^z / worldSizeMetres).

The smooth roads JSON contains world-coordinate paths. Render each path separately with rounded joins. Building records contain four footprintXZ world corners, category colours and imagePath when a matching model photo was found. Project the footprint once. For a 3D box, extrude that polygon. Use a text-only hover card for a missing photo.

Tree JSON rows contain [X east, Z north, modelId]. Use the model dictionary for species and the terrain elevation at X/Z for a 3D trunk's ground position. The satellite, tree and building layers share the same world coordinates. For web rendering, load visible tree chunks from the index instead of parsing the whole forest on every visit. Green symbols indicate tree placements with a common display radius.
