void main()
{
    GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(PatchAtlasStartExport, 1000, false);
}
Mission CreateCustomMission(string path)
{
    return new MissionServer();
}

// Patch Atlas | DayZ mission terrain sampler
// Look in the server profile directory for the .asc grid and its .done.txt
// marker. Use the grid after the marker appears. To repeat at the same
// spacing, move both files aside while the test server is stopped.

const int PATCH_ATLAS_SPACING_M = 4;
string g_PatchAtlasGridPath;
int g_PatchAtlasWidth;
int g_PatchAtlasRow;
float g_PatchAtlasCell;
string g_PatchAtlasDone;

void PatchAtlasWriteRow()
{
    FileHandle grid = OpenFile(g_PatchAtlasGridPath, FileMode.APPEND);
    if (grid == 0)
    {
        Print("[Patch Atlas] Could not append to " + g_PatchAtlasGridPath);
        g_PatchAtlasGridPath = "";
        return;
    }

    float z = (g_PatchAtlasWidth - g_PatchAtlasRow - 0.5) * g_PatchAtlasCell;
    string chunk = "";
    for (int col = 0; col < g_PatchAtlasWidth; col++)
    {
        float x = (col + 0.5) * g_PatchAtlasCell;
        float height = GetGame().SurfaceY(x, z);
        chunk += height.ToString();
        if (col + 1 == g_PatchAtlasWidth)
        {
            FPrintln(grid, chunk);
        }
        else
        {
            chunk += " ";
            if ((col + 1) % 64 == 0)
            {
                FPrint(grid, chunk);
                chunk = "";
            }
        }
    }

    CloseFile(grid);
    g_PatchAtlasRow++;
    if (g_PatchAtlasRow < g_PatchAtlasWidth)
    {
        if (g_PatchAtlasRow % 100 == 0)
            Print("[Patch Atlas] Rows written " + g_PatchAtlasRow.ToString() + "/" + g_PatchAtlasWidth.ToString());
        GetGame().GetCallQueue(CALL_CATEGORY_SYSTEM).CallLater(PatchAtlasWriteRow, 50, false);
        return;
    }

    g_PatchAtlasGridPath = "";
    FileHandle doneFile = OpenFile(g_PatchAtlasDone, FileMode.WRITE);
    if (doneFile == 0)
    {
        Print("[Patch Atlas] Grid closed, but completion marker could not be written.");
        return;
    }
    FPrintln(doneFile, "Finished rows: " + g_PatchAtlasRow.ToString());
    CloseFile(doneFile);
    Print("[Patch Atlas] Elevation export complete.");
}

void PatchAtlasStartExport()
{
    if (!GetGame().IsServer() || g_PatchAtlasGridPath != "" || PATCH_ATLAS_SPACING_M <= 0)
        return;

    string worldName;
    GetGame().GetWorldName(worldName);
    worldName.ToLower();
    if (worldName != "__WORLD__")
    {
        Print("[Patch Atlas] Skipping elevation export for " + worldName);
        return;
    }

    string basePath = "$profile:PatchAtlas___LABEL___" + PATCH_ATLAS_SPACING_M.ToString() + "m";
    string gridPath = basePath + ".asc";
    g_PatchAtlasDone = basePath + ".done.txt";
    if (FileExist(g_PatchAtlasDone) && FileExist(gridPath))
        return;
    if (FileExist(g_PatchAtlasDone))
    {
        Print("[Patch Atlas] Found an old completion marker without its grid. Move the marker aside to restart.");
        return;
    }

    int worldSize = GetGame().GetWorld().GetWorldSize();
    if (worldSize <= 0)
    {
        Print("[Patch Atlas] World size unavailable.");
        return;
    }
    // Fit whole cells exactly inside the world, even for non-divisible widths.
    g_PatchAtlasWidth = Math.Ceil(worldSize * 1.0 / PATCH_ATLAS_SPACING_M);
    g_PatchAtlasCell = worldSize * 1.0 / g_PatchAtlasWidth;
    g_PatchAtlasRow = 0;
    FileHandle grid = OpenFile(gridPath, FileMode.WRITE);
    if (grid == 0)
    {
        Print("[Patch Atlas] Could not open " + gridPath);
        return;
    }

    FPrintln(grid, "ncols " + g_PatchAtlasWidth.ToString());
    FPrintln(grid, "nrows " + g_PatchAtlasWidth.ToString());
    FPrintln(grid, "xllcorner 0");
    FPrintln(grid, "yllcorner 0");
    FPrintln(grid, "cellsize " + g_PatchAtlasCell.ToString(false));
    FPrintln(grid, "NODATA_value -9999");
    CloseFile(grid);
    g_PatchAtlasGridPath = gridPath;
    Print("[Patch Atlas] Writing " + gridPath);
    PatchAtlasWriteRow();
}





