#define AppVersion "0.3.0"
[Setup]
AppId={{7C970D72-62F7-4506-BCF2-C4A4B56E614A}
AppName=RFP Document Registry
AppVersion={#AppVersion}
AppPublisher=RFP Document Registry project
DefaultDirName={localappdata}\Programs\RFP Document Registry
DefaultGroupName=RFP Document Registry
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
MinVersion=10.0
OutputDir=..\dist
OutputBaseFilename=RFPRegistry-Setup-{#AppVersion}-x64
SetupIconFile=registry.ico
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
UninstallDisplayIcon={app}\RFPRegistry.exe
CloseApplications=yes

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; Flags: checkedonce

[Files]
Source: "..\dist\RFPRegistry.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\START_HERE.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\THIRD_PARTY_NOTICES.txt"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\RFP Document Registry"; Filename: "{app}\RFPRegistry.exe"
Name: "{autodesktop}\RFP Document Registry"; Filename: "{app}\RFPRegistry.exe"; Tasks: desktopicon

[Run]
Filename: "{app}\RFPRegistry.exe"; Description: "Open RFP Document Registry"; Flags: nowait postinstall skipifsilent
