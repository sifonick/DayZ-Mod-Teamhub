// Patch Atlas: list every config class that has a model, so we know which
// objects already have a vanilla class name.
//
// HOW TO USE (once):
// 1. Open your local server's mission init.c, e.g.
//    mpmissions/dayzOffline.chernarusplus/init.c
// 2. Paste this whole file at the very top of init.c.
// 3. Inside void main() { ... } add this line as the first line:
//        PA_DumpModelClasses();
// 4. Start the server (or the offline mission) once with the maps' DLCs loaded,
//    then stop it.
// 5. The list is in the server's profile folder: pa_model_classes.txt
//    (the folder set by -profiles=, often "profiles" next to DayZServer_x64.exe).
// 6. Remove the line and this code from init.c again.

void PA_DumpModelClasses()
{
	FileHandle fh = OpenFile("$profile:pa_model_classes.txt", FileMode.WRITE);
	if (fh == 0)
	{
		Print("[PatchAtlas] Could not create pa_model_classes.txt");
		return;
	}

	array<string> roots = {"CfgVehicles", "CfgNonAIVehicles"};
	int written = 0;
	foreach (string root : roots)
	{
		int count = GetGame().ConfigGetChildrenCount(root);
		for (int i = 0; i < count; i++)
		{
			string cls;
			GetGame().ConfigGetChildName(root, i, cls);
			string model;
			GetGame().ConfigGetText(root + " " + cls + " model", model);
			if (model != "")
			{
				int scope = GetGame().ConfigGetInt(root + " " + cls + " scope");
				FPrintln(fh, root + "\t" + cls + "\t" + model + "\t" + scope.ToString());
				written++;
			}
		}
	}
	CloseFile(fh);
	Print("[PatchAtlas] Wrote " + written.ToString() + " classes to pa_model_classes.txt");
}
