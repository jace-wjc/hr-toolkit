#ifndef MyAppVersion
  #error MyAppVersion must be provided by build_windows_installers.py
#endif
#ifndef SourceDir
  #error SourceDir must be provided by build_windows_installers.py
#endif
#ifndef OutputDir
  #error OutputDir must be provided by build_windows_installers.py
#endif
#ifndef SetupIconFile
  #error SetupIconFile must be provided by build_windows_installers.py
#endif
#ifndef InstallerSuffix
  #error InstallerSuffix must be provided by build_windows_installers.py
#endif
#ifndef MinWindowsVersion
  #error MinWindowsVersion must be provided by build_windows_installers.py
#endif

#define MyAppName "HRToolkit"
#define MyAppPublisher "xhzwjc"
#define MyAppExeName "HRToolkit.exe"

[Setup]
AppId={{8BBD86A8-CB7D-4D5D-A940-BD3F5942FBA6}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppVerName={#MyAppName} {#MyAppVersion}
AppPublisher={#MyAppPublisher}
DefaultDirName={localappdata}\Programs\HRToolkit
DefaultGroupName=HRToolkit
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion={#MinWindowsVersion}
#ifdef Win7Compatibility
OnlyBelowVersion=6.3
#endif
OutputDir={#OutputDir}
OutputBaseFilename=HRToolkit_{#MyAppVersion}_{#InstallerSuffix}-setup
SetupIconFile={#SetupIconFile}
UninstallDisplayIcon={app}\app\{#MyAppExeName}
Compression=lzma2/max
SolidCompression=yes
WizardStyle=modern
CloseApplications=yes
RestartApplications=no
UsePreviousAppDir=yes
ChangesAssociations=no
ChangesEnvironment=no
VersionInfoVersion={#MyAppVersion}.0
VersionInfoProductName={#MyAppName}
VersionInfoProductVersion={#MyAppVersion}
#ifdef SignToolName
SignTool={#SignToolName}
SignedUninstaller=yes
#endif

[Languages]
Name: "chinesesimplified"; MessagesFile: "compiler:Default.isl,ChineseSimplified.isl"

[Tasks]
Name: "desktopicon"; Description: "创建桌面快捷方式"; GroupDescription: "其他选项："; Flags: unchecked

[Files]
; 安装器和卸载器保留在 {app}，可自更新 payload 独立放在 {app}\app。
; HRToolkitUpdater 只替换 sys.executable.parent，因此不会删除 unins*.exe。
Source: "{#SourceDir}\*"; DestDir: "{app}\app"; Flags: ignoreversion recursesubdirs createallsubdirs; BeforeInstall: ReportInstallingFile; AfterInstall: ClearInstallingFile

[InstallDelete]
#ifdef CleanExistingPayload
; Win7 首次安装会替换原现代 payload，避免 Python 3.12 DLL 残留混用。
Type: filesandordirs; Name: "{app}\app"
#else
; 仅当现代包替换已安装的 Win7 payload 时清理；普通现代版安装不受影响。
Type: filesandordirs; Name: "{app}\app"; Check: ExistingPayloadIsWin7
#endif

[Icons]
Name: "{userprograms}\HRToolkit"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"
Name: "{userdesktop}\HRToolkit"; Filename: "{app}\app\{#MyAppExeName}"; WorkingDir: "{app}\app"; Tasks: desktopicon

[Run]
Filename: "{app}\app\{#MyAppExeName}"; Description: "启动 HRToolkit"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; 自更新可能改变 payload 文件集合，卸载时递归清理 app 子目录。
Type: filesandordirs; Name: "{app}\app"
Type: dirifempty; Name: "{app}"

[Code]
var
  UpdateProgressPath, UpdateFilename, LastProgressText: String;
  UpdatePercent: Integer;
  LastProgressTick: Cardinal;

function ProgressTick: Cardinal;
  external 'GetTickCount@kernel32.dll stdcall';

procedure WriteUpdateProgress(Force: Boolean);
var
  Lines: TArrayOfString;
  Snapshot: String;
  Tick: Cardinal;
begin
  if UpdateProgressPath = '' then Exit;
  Tick := ProgressTick;
  if not Force and (Tick >= LastProgressTick) and (Tick - LastProgressTick < 200) then Exit;
  Snapshot := IntToStr(UpdatePercent) + #10 + UpdateFilename;
  if not Force and (Snapshot = LastProgressText) then Exit;
  SetArrayLength(Lines, 3);
  Lines[0] := 'HRToolkitProgress1';
  Lines[1] := IntToStr(UpdatePercent);
  Lines[2] := UpdateFilename;
  LastProgressTick := Tick;
  // UI feedback must never abort file installation if the reader has exited.
  if SaveStringsToUTF8File(UpdateProgressPath, Lines, False) then
  begin
    LastProgressText := Snapshot;
  end;
end;

procedure InitializeWizard;
begin
  UpdateProgressPath := ExpandConstant('{param:HRPROGRESS|}');
  UpdatePercent := 0;
  WriteUpdateProgress(True);
end;

procedure ReportInstallingFile;
begin
  UpdateFilename := ExtractFileName(ExpandConstant(CurrentFilename));
  WriteUpdateProgress(False);
end;

procedure ClearInstallingFile;
begin
  UpdateFilename := '';
end;

procedure CurInstallProgressChanged(CurProgress, MaxProgress: Integer);
begin
  if MaxProgress > 0 then
  begin
    UpdatePercent := Round((CurProgress * 1.0 / MaxProgress) * 100);
    // Only the updater, after a successful installer exit, may show 100%.
    if UpdatePercent > 99 then UpdatePercent := 99;
    WriteUpdateProgress(False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if CurStep = ssPostInstall then
  begin
    UpdateFilename := '';
    WriteUpdateProgress(True);
  end;
end;

#ifndef CleanExistingPayload
function ExistingPayloadIsWin7: Boolean;
begin
  Result := FileExists(ExpandConstant('{app}\app\_internal\python38.dll'));
end;
#endif
