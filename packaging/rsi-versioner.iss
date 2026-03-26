#define MyAppName "RSI Versioner"
#define MyAppExeName "rsi-versioner.exe"

[Setup]
AppId={{B4B94EE1-73A8-4B76-9AA3-0A8D03A98ED2}
AppName={#MyAppName}
AppVersion={#GetEnv("RSI_VERSION")}
AppPublisher=RSI Versioner Contributors
DefaultDirName={localappdata}\Programs\RSI Versioner
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#GetEnv("RSI_OUTPUT_DIR")}
OutputBaseFilename=rsi-versioner-setup
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
PrivilegesRequired=lowest
WizardStyle=modern

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked

[Files]
Source: "{#GetEnv("RSI_PORTABLE_EXE")}"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Run]
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Flags: nowait postinstall skipifsilent
