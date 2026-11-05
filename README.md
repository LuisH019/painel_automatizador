# Painel de Chamamento - Inicializador Autônomo (IDS)

Aplicação desenvolvida em Python para automação, autenticação, exibição em monitor virtual dedicado e **transmissão automática via Google Cast (Chromecast / Google TV)** do painel web de chamamento.

---

## 🚀 Recursos Principais

- **Transmissão Automática para TVs (Google Cast via CDP & mDNS)**:
  - **Descoberta Instantânea (mDNS)**: Escaneia todas as interfaces de rede locais via pacotes UDP mDNS (`_googlecast._tcp.local` na porta `5353`) para listar as TVs disponíveis em ~100ms na tela de login, sem precisar abrir o navegador.
  - **Espelhamento 100% Automatizado (`Cast.startDesktopMirroring`)**: Utiliza o domínio `Cast` do Chrome DevTools Protocol combinado com `--auto-select-desktop-capture-source` e relay mDNS em segundo plano para espelhar automaticamente o monitor virtual na TV escolhida assim que o login é iniciado.
- **Busca Ultra-Rápida de Unidades (HTTP Keep-Alive + Fallback Playwright)**: Extrai dinamicamente a lista de unidades diretamente do endpoint Ajax do sistema (`idspaiele.dll/HandleEvent`) em ~150ms, mantendo o Playwright em modo headless como fallback automático de contingência.
- **Persistência e Criptografia no Escopo da Máquina (`ProgramData` + DPAPI)**:
  - As credenciais, a unidade de atuação e a TV de transmissão são salvas globalmente para o computador em `C:\ProgramData\PMRBS Inicializador do Painel IDS\credentials\credentials.json`.
  - A senha é protegida pela DPAPI do Windows com a flag `CRYPTPROTECT_LOCAL_MACHINE`, permitindo que **qualquer usuário do Windows** naquela máquina (ou scripts de inicialização via GPO) utilize a configuração padrão salva.
- **Interface Gráfica Adaptável (WebView2)**: As telas de Login e de Administração se ajustam automaticamente à área útil do monitor (`SPI_GETWORKAREA`), contam com layout responsivo para resoluções menores (ex: `1366x768`) e barra de rolagem integrada.
- **Monitor Virtual Inteligente (VDD)**: Instalação automatizada de monitor auxiliar virtual fixado em 1920x1080 (via `MttVDD` / DevCon), com verificação via PowerShell no instalador para evitar a criação de monitores duplicados.
- **Logs Temporais e Rotativos**: Geração de arquivos de log na pasta `logs/` nomeados com data e hora, mantendo automaticamente os 10 registros mais recentes.
- **Compilação Nativa com Nuitka**: Empacotado em código nativo via **Nuitka** e distribuído com **Inno Setup**, oferecendo inicialização rápida e integração nativa com o Edge WebView2.

---

## 📁 Estrutura do Projeto

```text
painel_automatizador/
├── bin/                       # Binários e drivers auxiliares (DevCon, Driver VDD, vdd_settings.xml)
├── credentials/               # Armazenamento local de credenciais em ambiente dev (credentials.json)
├── installer/                 # Scripts de compilação (build.py, build.ps1) e Inno Setup (.iss)
├── logs/                      # Histórico de logs rotativos da aplicação
├── releases/                  # Instaladores executáveis gerados por versão (.exe)
├── src/                       # Código-fonte da aplicação
│   ├── core/                  # Módulos centrais (Config, Logger, CredentialsRepository DPAPI)
│   ├── drivers/               # Gerenciador de hardware/display virtual (VirtualDisplayManager)
│   ├── services/              # Serviços de automação/Cast (AutomationService) e busca (ScraperService)
│   ├── ui/                    # Interfaces gráficas Edge WebView2 (HTML, CSS responsivo, JS)
│   └── main.py                # Ponto de entrada e roteamento de argumentos da aplicação
├── .env                       # Configuração opcional de ambiente (PAINEL_URL)
└── requirements.txt           # Dependências Python do projeto
```

---

## 🖥️ Modos de Execução

O sistema possui três rotas de execução acionadas por parâmetros de linha de comando:

### 1. Modo Padrão (Interface Gráfica de Login)
```bash
python -m src.main
```
Abre a interface gráfica (WebView2) carregando em paralelo e instantaneamente as **Unidades de Atuação** e as **TVs / Dispositivos Cast** disponíveis na rede. O operador pode marcar *"Manter estas credenciais como padrão"* para gravar o operador, senha, unidade e TV para todos os usuários do computador.

### 2. Modo Autônomo / Inicialização via GPO (`--auto`)
```bash
python -m src.main --auto
```
Ideal para inicialização automática no logon do Windows (via Registro `Run` ou GPO do Windows Server). Se houver credenciais salvas na máquina (`C:\ProgramData\PMRBS Inicializador do Painel IDS\credentials\credentials.json`), o sistema pula a tela de login, garante o monitor virtual ativo, faz login no painel e inicia a transmissão para a TV automaticamente. Caso não existam credenciais salvas, abre a tela de login normalmente.

### 3. Modo Administrativo / Configurações da TI (`--config`)
```bash
python -m src.main --config
```
Também acessível dando um **duplo clique na logo** na tela de login. Solicita elevação de Administrador (UAC) e permite alterar a URL global do painel no Registro do Windows (`HKLM\SOFTWARE\PMRBS\InicializadorPainelIDS`) e ativar/desativar manualmente o driver do monitor virtual.

---

## 🛠️ Como Compilar e Gerar o Instalador

1. Certifique-se de ter o Python, o **Nuitka** (com compilador C) e o **Inno Setup 6** (`iscc.exe`) instalados.
2. Para compilar o executável e gerar o instalador completo em um único passo via PowerShell:

```powershell
./installer/build.ps1
```

Ou execute as etapas separadamente a partir da raiz do projeto:

```powershell
python installer/build.py
iscc.exe installer/setup.iss
```

O instalador final (`Instalador_InicializadorPainelIDS_v1.7.exe`) será gerado na pasta `releases/v1.7/`.

---

## 📋 Requisitos do Sistema

- **OS**: Windows 10 / 11 (x64)
- **Navegador**: Google Chrome (recomendado para suporte completo ao Media Router / Google Cast) ou Microsoft Edge
- **Python**: 3.10 ou superior (para desenvolvimento/build)
- **Bibliotecas Principais**: `playwright`, `pywebview`, `screeninfo`, `pywin32` (`win32crypt`), `clr_loader`, `pythonnet`
