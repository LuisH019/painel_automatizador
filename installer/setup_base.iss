[Setup]
AppName={#NomeApp}
AppPublisher={#NomePublisher}
AppVersion={#Versao}
DefaultDirName={autopf}\{#NomePublisher} {#NomeApp}
DefaultGroupName={#NomeApp}
UninstallDisplayIcon={app}\{#NomeExe}.exe
OutputDir=..\releases\v{#Versao}
OutputBaseFilename=Instalador_{#NomeInstalador}_v{#Versao}
Compression=lzma
SolidCompression=yes
PrivilegesRequired=admin
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible

[Languages]
Name: "portuguesebr"; MessagesFile: "compiler:Languages\BrazilianPortuguese.isl"

[Files]
Source: "..\dist\main.dist\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs
Source: "..\src\ui\static\images\icone.ico"; DestDir: "{app}"
Source: "..\bin\vdd\*"; DestDir: "{app}\bin\vdd"; Flags: ignoreversion recursesubdirs
Source: "..\bin\vdd\vdd_settings.xml"; DestDir: "C:\IddSampleDriver"; Flags: ignoreversion

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na área de trabalho"; Flags: unchecked

[Icons]
Name: "{group}\{#NomeApp}"; Filename: "{app}\{#NomeExe}.exe"; IconFilename: "{app}\icone.ico"
Name: "{userdesktop}\{#NomeApp}"; Filename: "{app}\{#NomeExe}.exe"; IconFilename: "{app}\icone.ico"; Tasks: desktopicon

[Registry]
Root: HKLM64; Subkey: "Software\{#NomePublisher}\{#NomeInstalador}"; ValueType: string; ValueName: "UrlPainel"; ValueData: "{code:GetUrlPainel}"; Flags: uninsdeletekey


[Run]
Filename: "certutil.exe"; Parameters: "-addstore ""TrustedPublisher"" ""{app}\bin\vdd\mttvdd.cat"""; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Aprovando certificado de hardware..."; Flags: runhidden

Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\bin\vdd\MttVDD.inf"" /install"; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Registrando arquivos do driver..."; Flags: runhidden

Filename: "powershell.exe"; Parameters: "-ExecutionPolicy Bypass -Command ""$status = & '{app}\bin\vdd\devcon.exe' status Root\MttVDD; if ($status -match 'No matching devices found') {{ & '{app}\bin\vdd\devcon.exe' install '{app}\bin\vdd\MttVDD.inf' Root\MttVDD }"""; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Configurando monitor auxiliar..."; Flags: runhidden

[Code]
var
  ConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  ConfigPage := CreateInputQueryPage(wpSelectDir,
    'Configuração do Sistema', 'Defina os parâmetros globais do painel.',
    'Por favor, insira a URL de destino.');

  ConfigPage.Add('URL do Painel:', False);

  ConfigPage.Values[0] := 'https://riobrancodosul-saude.ids.inf.br/riobrancodosul/painel/idspaiele.dll';
end;

function GetUrlPainel(Param: String): String;
begin
  Result := ConfigPage.Values[0];
end;
