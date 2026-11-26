# Patch Atlas Studio: setup

Patch Atlas Studio is a blank DayZ world: a flat, plain grey floor 5 km square, with no buildings, trees, grass or weather, and fixed daylight. Its offline mission can photograph a list of objects one by one, each framed the same way, so the Object Finder gets clean, matching pictures.

## What's in this folder

| Folder | What it is |
| --- | --- |
| `@PatchAtlas_Studio/` | The mod: mission, launcher, mod info. The packed terrain goes in `addons/`. |
| `source/pa_studio/` | The terrain source that you pack with Addon Builder: world config, terrain file and floor material. |
| `workshop_preview.jpg` | The Steam Workshop picture. |

The capture tools are in `tools/object-search/studio/` in your repo.

## 1. Pack the terrain (Addon Builder, once)

1. Copy `@PatchAtlas_Studio` into your DayZ folder: `C:\Program Files (x86)\Steam\steamapps\common\DayZ\`. Your `@PatchAtlas_Objects` should already be there.
2. Open **DayZ Tools → Addon Builder** and fill it in:
   - **Addon source directory:** `...\PatchAtlas_Studio\source\pa_studio`
   - **Destination directory:** `...\DayZ\@PatchAtlas_Studio\addons`
   - **Addon prefix:** `pa_studio`
   - **Binarize:** ticked. This converts the terrain file into the game's format.
3. Click **PACK**. You should get `@PatchAtlas_Studio\addons\pa_studio.pbo`.

If packing fails with an error about the work drive or `P:`, open the **DayZ Tools** launcher, mount the work drive (P:) under Settings, and pack again. If it still fails, click **LOGS** and send the error.

## 2. Look at it

Double-click `@PatchAtlas_Studio\Start_PA_Studio.bat`. DayZ starts offline, in a window, standing on the grey floor. Take a screenshot so we can check the floor colour and lighting.

## 3. Photograph a test batch

From the repo folder:

```
python tools/object-search/studio/make_capture_list.py --limit 25 --shuffle
```

Then:

1. Start the studio: double-click `Start_PA_Studio.bat`.
2. Straight away, run:
   ```
   python tools/object-search/studio/capture.py
   ```
3. Leave the PC alone until it says **Finished**. Anything that covers the DayZ window ends up in the pictures.

The pictures appear in `assets/model-images-studio/`. Problems are logged in `%LOCALAPPDATA%\DayZ\pa_studio_log.txt`.

You can adjust the look at the top of `missions\PAStudio.pa_studio\init.c`:

| Setting | What it changes |
| --- | --- |
| `PAS_HOUR` | Time of day. |
| `PAS_OVERCAST` | Shadow softness. |
| `PAS_YAW`, `PAS_PITCH` | Camera angle. |
| `PAS_MARGIN` | How tightly objects are framed. |

## 4. The full run

```
python tools/object-search/studio/make_capture_list.py
```

Then start the studio and `capture.py` as in step 3. By default this covers Structures, Plants, Rocks and Vehicles: about 7,000 objects, at roughly 2–3 seconds each. To stop part-way, close the game. Running `make_capture_list.py` again lists only the objects that don't have a picture yet.

Then, from the repo folder:

```
python tools/object-search/build_catalogue.py
python tools/object-search/describe_images.py
python tools/object-search/build_catalogue.py
python tools/object-search/build_embeddings.py
python tools/object-search/build_text_index.py
```

`describe_images.py` redoes only the objects that have a new studio picture. Commit `assets/model-images-studio/` and `tools/object-search/`, then push.

## 5. Publish to the Steam Workshop

1. Open **DayZ Tools → Publisher**.
2. Fill it in:
   - **Folder:** `...\DayZ\@PatchAtlas_Studio`
   - **Title:** Patch Atlas Studio
   - **Preview image:** `workshop_preview.jpg`
   - **Tags:** Terrain
   - **Description:** use the text below.
3. Leave **Visibility** on **Private** for the first upload, subscribe to it yourself, and check it loads. Then switch it to **Public**.

If you also publish `@PatchAtlas_Objects`, add it under **Required items**. Without it, the studio still works for objects that have vanilla classes.

Workshop description:

> A blank world for clean screenshots: one flat, plain grey floor 5 km square, with no buildings, trees, grass or weather, and fixed daylight. Good for object and build screenshots, thumbnails and testing.
>
> Start it offline with Start_PA_Studio.bat in the mod folder, or pick "Patch Atlas Studio" in tools that list maps.
>
> The mission can also photograph a list of objects automatically. See README.txt in the mod folder.
>
> This mod is not affiliated or authorized by Bohemia Interactive a.s. Bohemia Interactive, ARMA, DAYZ and all associated logos and designs are trademarks or registered trademarks of Bohemia Interactive a.s.
