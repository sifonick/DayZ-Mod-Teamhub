# Class pack: class names for every map object

Many map objects, like `terrace_b1_10m.p3d`, are only models with no config class. Without a class, the DayZ Editor can't export them to `init.c` or JSON, and the Object Spawner can't place them. This folder fixes that.

## What's here

| File | What it does |
| --- | --- |
| `PA_ModelClassScan.c` | Optional. Run it once in-game to list the vanilla classes that already exist for each model. |
| `make_class_pack.py` | Gives every object without a class a new one (`PA_<model name>`). It writes the mod and `../classes.json`. |
| `PatchAtlas_Objects/config.cpp` | The generated mod config: 7,099 classes, each a `HouseNoDestruct` pointing at the vanilla model. |

## Steps

1. **Optional: find the vanilla classes first.** Follow the steps at the top of `PA_ModelClassScan.c`. It writes `pa_model_classes.txt` to your server's profile folder. Then run this from the repo root:

   ```bash
   python tools/object-search/class-pack/make_class_pack.py path/to/pa_model_classes.txt
   python tools/object-search/build_catalogue.py
   ```

   Objects that already have a vanilla class keep it, and only the rest get `PA_` classes. Skip this step and every object without a class gets a `PA_` class.

2. **Pack the mod.** Open DayZ Tools, then Addon Builder:
   - **Source directory:** `tools/object-search/class-pack/PatchAtlas_Objects`
   - **Destination directory:** a new folder, `@PatchAtlas_Objects/addons`
   - Click **Pack**. You get `@PatchAtlas_Objects/addons/PatchAtlas_Objects.pbo`.

3. **Load it with the editor.** Add `@PatchAtlas_Objects` to the mods you launch the DayZ Editor with, for example `-mod=@DabsFramework;@DayZ-Editor;@PatchAtlas_Objects`. In the editor's object list, search for `PA_terrace` and the terrace pieces appear.

4. **Load it on the server.** Anything you export that uses a `PA_` class needs the mod on the server, in both `-mod=` and the mods clients download. Objects that use vanilla classes don't need it.

## Notes

- Class names stay the same each time you re-run the script, as long as the objects don't change. That means saved builds keep working.
- When two models share a file name, the second gets a suffix for its asset set, for example `PA_farm_manurepile_tk` for the Nasdara version.
- The Object Finder shows the class for every object, and marks the ones that need this mod.

## Publishing

The mod contains no Bohemia models or textures, only a config that points at models already in every player's game. Keep it free, and put this on its Workshop page:

> This mod is not affiliated or authorized by Bohemia Interactive a.s. Bohemia Interactive, ARMA, DAYZ and all associated logos and designs are trademarks or registered trademarks of Bohemia Interactive a.s.
