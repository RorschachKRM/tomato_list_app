; Inno Setup 安装脚本
; 下载 Inno Setup: https://jrsoftware.org/isinfo.php
; 安装后右键此文件 -> Compile 即可生成安装包

[Setup]
AppName=Tomato List
AppVersion=1.0
AppPublisher=Tomato List
DefaultDirName={autopf}\Tomato List
DefaultGroupName=Tomato List
UninstallDisplayIcon={app}\Tomato List.exe
OutputDir=.\installer
OutputBaseFilename=Tomato-List-Setup-1.0
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequiredOverridesAllowed=dialog

[Files]
Source: "dist\Tomato List.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\Tomato List"; Filename: "{app}\Tomato List.exe"
Name: "{group}\卸载 Tomato List"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Tomato List"; Filename: "{app}\Tomato List.exe"; Flags: createonlyiffileexists

[Run]
Filename: "{app}\Tomato List.exe"; Description: "启动 Tomato List"; Flags: nowait postinstall skipifsilent
