#define MyAppName "Verse Switcher"
#define MyAppExeName "verse-switcher.exe"

[Setup]
AppId={{A34A5B88-EE44-4A5D-B11B-9D307399CF62}
AppName={#MyAppName}
AppVersion={#GetEnv("RSI_VERSION")}
AppPublisher=Verse Switcher Contributors
DefaultDirName={localappdata}\Programs\Verse Switcher
DefaultGroupName={#MyAppName}
DisableProgramGroupPage=yes
OutputDir={#GetEnv("RSI_OUTPUT_DIR")}
OutputBaseFilename=verse-switcher-setup
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
