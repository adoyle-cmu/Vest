#define AppVersion "1.0.0"

[Setup]

AppName=Vest

AppVersion={#AppVersion}

DefaultDirName={autopf}\Vest

DefaultGroupName=Vest

PrivilegesRequired=lowest

UninstallDisplayIcon={app}\main.exe

Compression=lzma2

SolidCompression=yes

OutputDir=user_output

OutputBaseFilename=Vest_Setup



[Languages]

Name: "english"; MessagesFile: "compiler:Default.isl"



[Files]

; This takes everything Nuitka put in the .dist folder

Source: "main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs



[Icons]



Name: "{group}\Vest"; Filename: "{app}\main.exe"



Name: "{autodesktop}\Vest"; Filename: "{app}\main.exe"