# Arquivo: installer/powershell/compilar_cliente.ps1
# Compila o executável do cliente e cria o instalador.

Set-Location -Path "$PSScriptRoot/../"

python ./installer/build.py
iscc.exe ./installer/setup.iss

Write-Host "Instalador do painel criado!"