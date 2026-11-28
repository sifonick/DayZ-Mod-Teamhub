// Asset Capture - client-side dev tool.
// Shows one item at a time on a flat magenta background and steps it through
// a list of angles. An external script (tools/asset_capture.py) takes the
// screenshots. The two talk through small files in $profile:AssetCapture/
//
//   queue.txt  (written by PC script)  "angle <pitch> <yaw> <roll>" lines, then one classname per line
//   start.txt  (written by PC script)  tells the mod to begin
//   ready.txt  (written by mod)        "<classname>|<angleIndex>" = frame is ready, take the shot
//              (deleted by PC script)  = shot taken, move on
//   stop.txt   (written by PC script)  abort
//   done.txt   (written by mod)        finished
//   skipped.txt(written by mod)        classnames that could not be spawned

class AssetCaptureRunner
{
	static const string DIR      = "$profile:AssetCapture";
	static const string F_QUEUE  = "$profile:AssetCapture/queue.txt";
	static const string F_START  = "$profile:AssetCapture/start.txt";
	static const string F_READY  = "$profile:AssetCapture/ready.txt";
	static const string F_STOP   = "$profile:AssetCapture/stop.txt";
	static const string F_DONE   = "$profile:AssetCapture/done.txt";
	static const string F_SKIP   = "$profile:AssetCapture/skipped.txt";
	static const string F_ALIVE  = "$profile:AssetCapture/alive.txt";

	// Seconds to wait before signalling "ready"
	static const float FIRST_ANGLE_DELAY = 2.0;  // new item: give textures time to stream in
	static const float NEXT_ANGLE_DELAY  = 0.35; // same item, new rotation

	protected Widget m_Root;
	protected ItemPreviewWidget m_Preview;
	protected ref array<string> m_Classes;
	protected ref array<vector> m_Angles;
	protected EntityAI m_Entity;
	protected int m_ClassIdx;
	protected int m_AngleIdx;
	protected bool m_Running;
	protected bool m_WaitingAck;
	protected float m_Timer;
	protected float m_Delay;

	void AssetCaptureRunner()
	{
		m_Classes = new array<string>;
		m_Angles = new array<vector>;
		if (!FileExist(DIR))
			MakeDirectory(DIR);
		Print("[AssetCapture] loaded, watching " + DIR);
	}

	void ~AssetCaptureRunner()
	{
		Cleanup();
	}

	bool IsRunning()
	{
		return m_Running;
	}

	// Lets the PC script confirm the mod is loaded and in-game
	void Heartbeat()
	{
		WriteLine(F_ALIVE, GetGame().GetTime().ToString());
	}

	bool TryStart()
	{
		if (!FileExist(F_START))
			return false;

		DeleteFile(F_START);
		DeleteFile(F_DONE);
		DeleteFile(F_READY);
		DeleteFile(F_STOP);
		DeleteFile(F_SKIP);

		LoadQueue();
		if (m_Classes.Count() == 0)
		{
			WriteLine(F_DONE, "empty queue");
			return false;
		}
		if (m_Angles.Count() == 0)
		{
			// Default: 8-step turntable + a high three-quarter view
			for (int a = 0; a < 8; a++)
				m_Angles.Insert(Vector(0, a * 45, 0));
			m_Angles.Insert(Vector(35, 35, 0));
		}

		m_Root = GetGame().GetWorkspace().CreateWidgets("AssetCapture/gui/capture.layout");
		if (!m_Root)
		{
			WriteLine(F_DONE, "layout failed to load");
			return false;
		}
		m_Root.SetSort(10000);
		m_Preview = ItemPreviewWidget.Cast(m_Root.FindAnyWidget("Preview"));

		Mission mission = GetGame().GetMission();
		if (mission && mission.GetHud())
			mission.GetHud().Show(false);

		m_Running = true;
		m_ClassIdx = -1;
		NextClass();
		Print("[AssetCapture] started: " + m_Classes.Count() + " items x " + m_Angles.Count() + " angles");
		return true;
	}

	void Update(float dt)
	{
		if (!m_Running)
			return;

		if (FileExist(F_STOP))
		{
			DeleteFile(F_STOP);
			Finish("stopped");
			return;
		}

		if (m_WaitingAck)
		{
			// PC script deletes ready.txt once the screenshot is saved
			if (!FileExist(F_READY))
			{
				m_WaitingAck = false;
				NextAngle();
			}
			return;
		}

		m_Timer += dt;
		if (m_Timer >= m_Delay)
		{
			WriteLine(F_READY, m_Classes[m_ClassIdx] + "|" + m_AngleIdx.ToString());
			m_WaitingAck = true;
		}
	}

	protected void NextAngle()
	{
		m_AngleIdx++;
		if (m_AngleIdx >= m_Angles.Count())
		{
			NextClass();
			return;
		}
		ApplyAngle();
		m_Delay = NEXT_ANGLE_DELAY;
	}

	protected void NextClass()
	{
		DeleteEntity();

		while (true)
		{
			m_ClassIdx++;
			if (m_ClassIdx >= m_Classes.Count())
			{
				Finish("ok");
				return;
			}

			string cls = m_Classes[m_ClassIdx];
			vector pos = "0 0 0";
			PlayerBase player = PlayerBase.Cast(GetGame().GetPlayer());
			if (player)
				pos = player.GetPosition() + "0 -30 0"; // out of sight, local only

			m_Entity = EntityAI.Cast(GetGame().CreateObjectEx(cls, pos, ECE_LOCAL));
			if (m_Entity)
				break;

			Print("[AssetCapture] could not spawn " + cls);
			AppendLine(F_SKIP, cls);
		}

		m_Preview.SetItem(m_Entity);
		m_Preview.SetView(m_Entity.GetViewIndex());
		m_AngleIdx = 0;
		ApplyAngle();
		m_Delay = FIRST_ANGLE_DELAY;
	}

	protected void ApplyAngle()
	{
		m_Preview.SetModelOrientation(m_Angles[m_AngleIdx]);
		m_Timer = 0;
	}

	protected void LoadQueue()
	{
		m_Classes.Clear();
		m_Angles.Clear();

		FileHandle f = OpenFile(F_QUEUE, FileMode.READ);
		if (f == 0)
			return;

		string line;
		while (FGets(f, line) > 0)
		{
			line = line.Trim();
			if (line == "" || line.IndexOf("#") == 0)
				continue;

			if (line.IndexOf("angle ") == 0)
			{
				TStringArray parts = new TStringArray;
				line.Split(" ", parts);
				if (parts.Count() >= 4)
					m_Angles.Insert(Vector(parts[1].ToFloat(), parts[2].ToFloat(), parts[3].ToFloat()));
				continue;
			}

			m_Classes.Insert(line);
		}
		CloseFile(f);
	}

	protected void Finish(string reason)
	{
		Print("[AssetCapture] finished: " + reason);
		Cleanup();
		WriteLine(F_DONE, reason);
	}

	protected void Cleanup()
	{
		m_Running = false;
		m_WaitingAck = false;
		DeleteEntity();

		if (m_Root)
		{
			m_Root.Unlink();
			m_Root = null;
			m_Preview = null;
		}

		Mission mission = GetGame().GetMission();
		if (mission && mission.GetHud())
			mission.GetHud().Show(true);
	}

	protected void DeleteEntity()
	{
		if (m_Preview)
			m_Preview.SetItem(null);
		if (m_Entity)
		{
			GetGame().ObjectDelete(m_Entity);
			m_Entity = null;
		}
	}

	protected void WriteLine(string path, string text)
	{
		FileHandle f = OpenFile(path, FileMode.WRITE);
		if (f != 0)
		{
			FPrintln(f, text);
			CloseFile(f);
		}
	}

	protected void AppendLine(string path, string text)
	{
		FileHandle f = OpenFile(path, FileMode.APPEND);
		if (f != 0)
		{
			FPrintln(f, text);
			CloseFile(f);
		}
	}
}

modded class MissionGameplay
{
	protected ref AssetCaptureRunner m_AssetCapture;
	protected float m_AssetCapturePoll;

	override void OnUpdate(float timeslice)
	{
		super.OnUpdate(timeslice);

		if (!m_AssetCapture)
			m_AssetCapture = new AssetCaptureRunner();

		if (m_AssetCapture.IsRunning())
		{
			m_AssetCapture.Update(timeslice);
			return;
		}

		// Check for start.txt once a second, and refresh the heartbeat file
		m_AssetCapturePoll += timeslice;
		if (m_AssetCapturePoll >= 1.0)
		{
			m_AssetCapturePoll = 0;
			m_AssetCapture.Heartbeat();
			m_AssetCapture.TryStart();
		}
	}
}
