#define AppVersion "1.0.0"

[Setup]
AppName=ChainOfTitle
AppVersion={#AppVersion}
DefaultDirName={autopf}\ChainOfTitle
DefaultGroupName=ChainOfTitle
UninstallDisplayIcon={app}\main.exe
Compression=lzma2
SolidCompression=yes
OutputDir=user_output
OutputBaseFilename=ChainOfTitle_Setup

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"



[Files]
; This takes everything Nuitka put in the .dist folder
Source: "main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\ChainOfTitle"; Filename: "{app}\main.exe"
Name: "{commondesktop}\ChainOfTitle"; Filename: "{app}\main.exe"