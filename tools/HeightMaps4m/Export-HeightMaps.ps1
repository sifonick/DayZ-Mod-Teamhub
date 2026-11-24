param([string]$ServerFolder, [string]$OutputFolder = (Join-Path $PSScriptRoot 'HeightMaps'), [int]$Port = 2452)
$ErrorActionPreference = 'Stop'
if (!$ServerFolder) {
    $ServerFolder = Join-Path ${env:ProgramFiles(x86)} 'Steam\steamapps\common\DayZServer'
    if (!(Test-Path (Join-Path $ServerFolder 'DayZServer_x64.exe'))) {
        $ServerFolder = (Read-Host 'Enter the folder containing DayZServer_x64.exe').Trim('"')
    }
}
$server = (Resolve-Path -LiteralPath $ServerFolder).Path
$exe = Join-Path $server 'DayZServer_x64.exe'
if (!(Test-Path -LiteralPath $exe)) { throw "DayZ Server missing from $server" }
$template = Get-Content (Join-Path $PSScriptRoot 'mission-template.c') -Raw
$dest = [IO.Directory]::CreateDirectory($OutputFolder).FullName
$lockPath = Join-Path $dest 'export.lock'
try { $lock = [IO.File]::Open($lockPath,'OpenOrCreate','ReadWrite','None') }
catch { throw "Another height exporter has this output folder open. Use its console window for progress: $dest" }
try {
$stale = Get-CimInstance Win32_Process -Filter "Name='DayZServer_x64.exe'" -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -and $_.CommandLine.IndexOf((Join-Path $dest 'profiles\'),[StringComparison]::OrdinalIgnoreCase) -ge 0 }
if ($stale) { throw "An earlier height-export server is still using $dest (PID $($stale.ProcessId -join ', ')). Close its exporter before retrying." }
foreach ($map in @(@('chernarusplus','Chernarus',3840), @('enoch','Livonia',3200), @('sakhal','Sakhal',3840))) {
    $world,$label,$width = $map
    $stem = "PatchAtlas_${label}_4m"
    $profile = [IO.Directory]::CreateDirectory((Join-Path $dest "profiles\$world")).FullName
    # DayZ sees a short, unquoted relative profile path, including when Documents contains spaces.
    $profileAlias = "Atlas4mProfile_" + [Guid]::NewGuid().ToString('N')
    $grid = Join-Path $profile "$stem.asc"
    $marker = Join-Path $profile "$stem.done.txt"
    $final = Join-Path $dest "$stem.asc"
    if (!(Test-Path $marker) -or !(Test-Path $grid)) {
        if (Test-Path $marker) { throw "Completion marker without grid in $profile. Move the marker aside and rerun." }
        $name = "AtlasHeight4m_$([Guid]::NewGuid().ToString('N')).$world"
        $mission = Join-Path $server "mpmissions\$name"
        $null = New-Item -ItemType Directory -Path $mission
        $init = Join-Path $mission 'init.c'
        $cfg = Join-Path $server "$name.cfg"
        $junction = $null; $proc = $null
        try {
            $junction = New-Item -ItemType Junction -Path (Join-Path $server $profileAlias) -Target $profile
            $template.Replace('__WORLD__',$world).Replace('__LABEL__',$label) | Set-Content -LiteralPath $init -Encoding ASCII
            $password = [Guid]::NewGuid().ToString('N')
            @(
                'hostname="Local terrain sampler";', "password=`"$password`";", 'maxPlayers=1;', 'verifySignatures=2;',
                'disableVoN=1;', 'vonCodecQuality=0;', 'disable3rdPerson=0;', 'disableCrosshair=0;', 'instanceId=971;', "steamQueryPort=$($Port+3);", "class Missions { class DayZ { template=`"$name`"; }; };"
            ) | Set-Content -LiteralPath $cfg -Encoding ASCII
            Write-Host "Sampling $label on a 4 m grid. Output and logs: $profile"
            $proc = Start-Process -FilePath $exe -WorkingDirectory $server -NoNewWindow -ArgumentList @("-config=$name.cfg","-profiles=$profileAlias","-port=$Port",'-dologs','-noPause','-noSplash') -PassThru
            Write-Host "Server started. Waiting for the terrain to load..."; $progressAt = Get-Date
            $length = -1
            while (!(Test-Path $marker)) {
                Start-Sleep -Seconds 5
                if ($proc.HasExited) { throw "$label server exited. See $profile for the server logs." }
                if (Test-Path $grid) {
                    $newLength = (Get-Item $grid).Length
                    if ($newLength -ne $length) { $length=$newLength; $progressAt=Get-Date; Write-Host "$label - $([math]::Round($length/1MB,1)) MiB written" }
                }
                if (!(Test-Path $grid)) {
                    $elapsed = [int]((Get-Date)-$progressAt).TotalSeconds
                    Write-Host "Waiting for $label - $elapsed seconds (server PID $($proc.Id))."
                    if ($elapsed -ge 120 -and !(Get-ChildItem $profile -Filter '*.RPT' | Where-Object LastWriteTime -ge $proc.StartTime)) {
                        throw "DayZ Server did not write a startup log within two minutes. Restart Windows, then run this launcher once before starting DayZ or DayZDiag. If it still stalls, launch DayZ Dedicated Server from Steam and check its startup window."
                    }
                }
                if (((Get-Date)-$progressAt).TotalMinutes -gt 10) { throw "No export progress for 10 minutes. Check $profile and that port $Port is available." }
            }
        } finally {
            if ($proc -and !$proc.HasExited) { $proc.Kill(); $proc.WaitForExit() }
            if ($junction -and $junction.Attributes -band [IO.FileAttributes]::ReparsePoint) { [IO.Directory]::Delete($junction.FullName) }; if (Test-Path $cfg) { Remove-Item -LiteralPath $cfg }; if (Test-Path $init) { Remove-Item -LiteralPath $init }
            if (!(Get-ChildItem -LiteralPath $mission -Force)) { [IO.Directory]::Delete($mission) }
            Write-Progress -Activity "Sampling $label" -Completed
        }
    }
    $header = @(Get-Content -LiteralPath $grid -TotalCount 6)
    if ($header[0] -notmatch "^ncols $width$" -or $header[1] -notmatch "^nrows $width$" -or $header[4] -notmatch '^cellsize 4(\.0+)?$' -or (Get-Content $marker -Raw).Trim() -ne "Finished rows: $width") { throw "Unexpected $label grid dimensions or completion marker in $profile" }
    Copy-Item -LiteralPath $grid -Destination "$final.partial" -Force
    Move-Item -LiteralPath "$final.partial" -Destination $final -Force
    Write-Host "Ready: $final"
}



} finally { $lock.Dispose() }

