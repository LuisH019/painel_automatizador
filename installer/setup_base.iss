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

[Tasks]
Name: "desktopicon"; Description: "Criar ícone na área de trabalho"; Flags: unchecked

[Icons]
Name: "{group}\{#NomeApp}"; Filename: "{app}\{#NomeExe}.exe"; IconFilename: "{app}\icone.ico"
Name: "{userdesktop}\{#NomeApp}"; Filename: "{app}\{#NomeExe}.exe"; IconFilename: "{app}\icone.ico"; Tasks: desktopicon

[Registry]
Root: HKLM64; Subkey: "Software\{#NomePublisher}\{#NomeInstalador}"; ValueType: string; ValueName: "UrlPainel"; ValueData: "{code:GetUrlPainel}"; Flags: uninsdeletekey
Root: HKLM64; Subkey: "Software\{#NomePublisher}\{#NomeInstalador}"; ValueType: string; ValueName: "Unidades"; ValueData: "{code:GetUnidades}"; Flags: uninsdeletekey


[Run]
Filename: "certutil.exe"; Parameters: "-addstore ""TrustedPublisher"" ""{app}\bin\vdd\mttvdd.cat"""; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Aprovando certificado de hardware..."; Flags: runhidden

Filename: "pnputil.exe"; Parameters: "/add-driver ""{app}\bin\vdd\MttVDD.inf"" /install"; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Registrando arquivos do driver..."; Flags: runhidden

Filename: "{app}\bin\vdd\devcon.exe"; Parameters: "install ""{app}\bin\vdd\MttVDD.inf"" ""Root\MttVDD"""; WorkingDir: "{app}\bin\vdd"; StatusMsg: "Criando monitor auxiliar..."; Flags: runhidden

[Code]
var
  ConfigPage: TInputQueryWizardPage;

procedure InitializeWizard;
begin
  ConfigPage := CreateInputQueryPage(wpSelectDir,
    'Configuração do Sistema', 'Defina os parâmetros globais do painel.',
    'Por favor, insira a URL de destino e as unidades disponíveis (separadas por vírgula).');

  ConfigPage.Add('URL do Painel:', False);
  ConfigPage.Add('Unidades:', False);

  ConfigPage.Values[0] := 'https://riobrancodosul-saude.ids.inf.br/riobrancodosul/painel/idspaiele.dll';
  ConfigPage.Values[1] := '1 - Hospital Municipal, 2 - UBS Nossa Senhora de Fátima, 3 - UBS Jardim Paraíso, 4 - CENTRO DE ATENCAO PSICOSSOCIAL CAPS I';
end;

function GetUrlPainel(Param: String): String;
begin
  Result := ConfigPage.Values[0];
end;

function GetUnidades(Param: String): String;
begin
  Result := ConfigPage.Values[1];
end;
