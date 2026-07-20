# Painel de Chamamento - Inicializador Autônomo (IDS)

Aplicação desenvolvida em Python para automação, autenticação e exibição contínua do painel web de chamamento em monitores virtuais dedicados.

---

## 🚀 Recursos Principais

- **Automação Web de Alta Performance**: Utiliza o Playwright para gerenciar o login e navegação em background no navegador Chromium, direcionando a tela para as coordenadas exatas do monitor virtual.
- **Suporte a Monitor Virtual (VDD)**: Detecção e ativação automatizada de monitor auxiliar virtual (`MttVDD` / DevCon), garantindo isolamento da exibição do painel.
- **Segurança de Credenciais (DPAPI)**: Criptografia nativa das senhas utilizando a DPAPI do Windows, armazenando os dados em uma pasta própria e protegida (`credentials/credentials.json`).
- **Logs Temporais e Rotativos**: Geração de arquivos de log individuais na pasta `logs/` nomeados com a data e hora do início da sessão (`app_YYYY-MM-DD_HH-MM-SS.log`), com limite automático de retenção mantendo apenas as 10 sessões mais recentes.
- **Inicialização Instantânea**: Empacotamento configurado em modo `onedir` via PyInstaller + Inno Setup, evitando o impacto de desempenho e varreduras do Windows Defender durante a inicialização.

---

## 📁 Estrutura do Projeto

```
painel_automatizador/
├── bin/                       # Binários e drivers auxiliares (DevCon, Driver VDD)
├── credentials/               # Armazenamento local de credenciais salvas (credentials.json)
├── installer/                 # Scripts de compilação e instalação
│   ├── inno_setup/            # Arquivos de receita do Inno Setup (.iss)
│   ├── powershell/            # Script PowerShell de automação do build (.ps1)
│   └── pyinstaller/           # Arquivos spec e scripts auxiliares do PyInstaller
├── logs/                      # Histórico de logs rotativos da aplicação
├── releases/                  # Instalador executável gerado (.exe)
├── src/                       # Código-fonte da aplicação
│   ├── core/                  # Módulos centrais (Config, Logger, Criptografia)
│   ├── drivers/               # Gerenciador de hardware/display virtual
│   ├── services/              # Serviços de automação web (Playwright)
│   ├── ui/                    # Interfaces gráficas PyWebView (HTML, CSS, JS)
│   └── main.py                # Ponto de entrada da aplicação
├── .env                       # Configurações locais e parâmetros globais
└── requirements.txt           # Dependências Python do projeto
```

---

## 🖥️ Modos de Execução

O sistema possui diferentes rotas de execução acionadas por flags na linha de comando:

### 1. Modo Padrão (Interface Gráfica de Login)
```bash
python -m src.main
```
Abre a interface gráfica gráfica para o operador inserir usuário, senha e selecionar a unidade de atuação.

### 2. Modo Autônomo / Auto-Inicialização (`--auto`)
```bash
python -m src.main --auto
```
Indicado para tarefas agendadas, inicialização pelo registro ou GPO. Se houver credenciais completas registradas em `credentials/credentials.json`, o painel é iniciado diretamente de forma silenciosa. Caso contrário, recua para a interface gráfica.

### 3. Modo Administrativo / Configurações da TI (`--config`)
```bash
python -m src.main --config
```
Abre a painel de controle administrativo para alterar a URL do sistema alvo, opções de unidades e alternar o status do driver de monitor virtual.

---

## 🛠️ Como Compilar o Instalador

Para gerar o arquivo executável de instalação (`Instalador_InicializadorPainelIDS_v1.3.exe`):

1. Certifique-se de que o **Inno Setup Compiler (`iscc.exe`)** e o **PyInstaller** estejam instalados no ambiente.
2. Execute o script de compilação em PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\installer\powershell\compilar_painel_automatizador.ps1
```

O instalador compilado será gerado na pasta `releases/v1.3/`.

---

## 📋 Requisitos do Sistema

- **OS**: Windows 10 / 11 (x64)
- **Python**: 3.10 ou superior (para execução em modo de desenvolvimento)
- **Dependências**:
  - `playwright` (Chromium)
  - `pywebview`
  - `screeninfo`
