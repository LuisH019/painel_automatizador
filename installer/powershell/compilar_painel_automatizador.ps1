# Arquivo: installer/powershell/compilar_cliente.ps1
# Compila o executável do cliente e cria o instalador.

Set-Location -Path "$PSScriptRoot/../../"

pyinstaller ./installer/pyinstaller/painel_automatizador.spec
iscc.exe ./installer/inno_setup/painel_automatizador.iss

Write-Host "Instalador do painel criado!"