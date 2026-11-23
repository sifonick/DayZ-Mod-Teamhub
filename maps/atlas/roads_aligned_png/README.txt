DayZ white road overlays
========================

Each transparent PNG matches the native pixel dimensions of its corresponding
High_Resolution satellite PNG exactly. Put the two images on the same square,
north-up canvas at 1:1 size and apply the same pan/zoom transform to both.

Image-to-world mapping used by these overlays:
  pixelX = X / worldSizeMetres * imageWidth
  pixelY = (worldSizeMetres - Z) / worldSizeMetres * imageHeight

For the tiled web map, use the roads tile layer in tile_manifest.json. Do not
place one of these full-size PNGs over the tile layer; both already share the
same map extent.
