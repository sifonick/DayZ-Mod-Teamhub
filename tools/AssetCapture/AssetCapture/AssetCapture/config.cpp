class CfgPatches
{
	class AssetCapture
	{
		units[] = {};
		weapons[] = {};
		requiredVersion = 0.1;
		requiredAddons[] = { "DZ_Data", "DZ_Scripts" };
	};
};

class CfgMods
{
	class AssetCapture
	{
		dir = "AssetCapture";
		name = "Asset Capture (dev tool)";
		author = "Patch Atlas";
		type = "mod";
		dependencies[] = { "Mission" };

		class defs
		{
			class missionScriptModule
			{
				value = "";
				files[] = { "AssetCapture/scripts/5_Mission" };
			};
		};
	};
};
