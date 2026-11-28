# Asset Capture for DayZ

Automatically captures several angles of any DayZ item (vanilla or modded) as
transparent PNGs, ready for an item database or a website.

## How it works

1. `tools/asset_capture.py` writes a job (classnames + angles) to
   `%LOCALAPPDATA%\DayZ\AssetCapture\`.
2. The **AssetCapture** client mod spots the job, puts a full-screen magenta
   background over the game and displays each item in DayZ's 3D item preview
   (the same renderer used for the inventory).
3. For each angle the mod writes `ready.txt`. The script then takes a screenshot,
   removes the magenta background, crops and saves the image, and deletes
   `ready.txt` so the mod moves on to the next angle.

The items are spawned **locally on your client only** (`ECE_LOCAL`), so nothing
appears on the server or for other players.

## Setup

1. **Build the mod.** In DayZ Tools > Addon Builder, pack the `AssetCapture`
   folder into `@AssetCapture\Addons\AssetCapture.pbo`.
2. **Load it.** Use offline mode (e.g. DayZ Community Offline Mode) or your own
   local or test server. Add `-mod=@AssetCapture` (plus any mods whose items
   you want to capture) to the client. On a real server, the server needs to
   load or allow the mod too.
3. **Install Python bits:** `pip install pillow numpy mss`

## Running

```
python tools\asset_capture.py --classes tools\classes_example.txt --size 1024
```

Spawn into the game and keep DayZ in front. **Borderless or windowed mode is
best**, because exclusive fullscreen can produce black screenshots. The mod
checks for new jobs once a second.

Output: `captures\<ClassName>\<ClassName>_00.png`, `_01.png` and so on.

### Options

| Option | Meaning |
|---|---|
| `--angles 12` | 12-step turntable plus one high three-quarter view (default 8) |
| `--angles "0 0 0" "0 90 0" "35 35 0"` | Exact `pitch yaw roll` angles |
| `--size 1024` | Fit each image into a 1024x1024 transparent square |
| `--pad 16` | Padding around the cropped item |
| `--profile D:\DayZProfile` | Use this if you launch DayZ with `-profiles=` |
| `--monitor 2` | Capture a different monitor |
| `--keep-raw` | Also keep the untouched screenshot |

To abort, press Ctrl+C in the script (this writes `stop.txt`, and the mod
cleans up). Classnames that couldn't be spawned are listed when the run ends.

## Tuning

* **Textures blurry on the first angle?** Increase `FIRST_ANGLE_DELAY` in
  `scripts/5_Mission/AssetCapture.c`.
* **Rotating on the wrong axis?** The mod passes the angles straight to
  `ItemPreviewWidget.SetModelOrientation()` as (pitch, yaw, roll). If your
  build uses a different order, swap the numbers in `--angles`.
* **Item too small or too big in frame?** Uncomment or adjust a
  `m_Preview.SetModelPosition(...)` call after `SetView()` in `NextClass()`.
  The script crops to the item either way.
* **Purple or pink items:** the magenta key could eat into them. Change the
  `color` in `gui/capture.layout` and `KEY` in the script to match (green
  `0 1 0 1` / `[0,255,0]` works for most non-military items).
