# Painel de Chamamento - Inicializador Autônomo (IDS)

Aplicação desenvolvida em Python para automação, autenticação e exibição contínua do painel web de chamamento em monitores virtuais dedicados.

---

## 🚀 Recursos Principais

- **Automação Web de Alta Performance**: Utiliza o Playwright para gerenciar o login e navegação em background no navegador Chromium, direcionando a tela para as coordenadas exatas do monitor virtual.
- **Busca Dinâmica de Unidades (Scraping)**: O sistema não necessita de configuração manual de unidades. Ele utiliza o Playwright em modo invisível (headless) para acessar a URL do painel e extrair dinamicamente a lista de unidades em tempo real durante a tela de login.
- **Monitor Virtual Inteligente (VDD)**: Instalação automatizada de monitor auxiliar virtual fixado em 1920x1080 (via `MttVDD` / DevCon). O instalador possui travas de segurança via PowerShell para não criar monitores duplicados na máquina.
- **Segurança de Credenciais (DPAPI)**: Criptografia nativa das senhas utilizando a DPAPI do Windows, armazenando os dados em uma pasta própria e protegida (`credentials/credentials.json`).
- **Logs Temporais e Rotativos**: Geração de arquivos de log na pasta `logs/` nomeados com a data e hora, com limite automático de retenção.
- **Compilação Nuitka**: Empacotado nativamente utilizando o **Nuitka** (substituindo o antigo PyInstaller), entregando máxima performance, execução direta de binários, suporte ao Edge Chromium no WebView2 e menor chance de falsos-positivos em antivírus.

---

## 📁 Estrutura do Projeto

```text
painel_automatizador/
├── bin/                       # Binários e drivers auxiliares (DevCon, Driver VDD, vdd_settings.xml)
├── credentials/               # Armazenamento local de credenciais salvas (credentials.json)
├── installer/                 # Scripts de compilação (build.py) e Inno Setup (.iss)
├── logs/                      # Histórico de logs rotativos da aplicação
├── releases/                  # Instalador executável gerado (.exe)
├── src/                       # Código-fonte da aplicação
│   ├── core/                  # Módulos centrais (Config, Logger, Criptografia)
│   ├── drivers/               # Gerenciador de hardware/display virtual
│   ├── services/              # Serviços web (Automação Playwright e ScraperService)
│   ├── ui/                    # Interfaces gráficas Edge WebView2 (HTML, CSS, JS)
│   └── main.py                # Ponto de entrada da aplicação
├── .env                       # Configuração opcional de fallback (PAINEL_URL)
└── requirements.txt           # Dependências Python do projeto
```

---

## 🖥️ Modos de Execução

O sistema possui diferentes rotas de execução acionadas por parâmetros de linha de comando:

### 1. Modo Padrão (Interface Gráfica de Login)
```bash
python -m src.main
```
Abre a interface gráfica (WebView2) para o operador inserir usuário e senha. As unidades são carregadas dinamicamente via scraping e a interface trava o botão de acesso até que o carregamento online termine.

### 2. Modo Autônomo / Auto-Inicialização (`--auto`)
```bash
python -m src.main --auto
```
Indicado para tarefas agendadas ou inicialização via Registro do Windows. Se houver credenciais salvas como padrão, o painel é iniciado silenciosamente no monitor virtual. Caso falte alguma informação, ele recua graciosamente para a interface gráfica.

### 3. Modo Administrativo / Configurações da TI (`--config`)
```bash
python -m src.main --config
```
Abre o painel de controle restrito ao administrador (solicita elevação UAC) para alterar a URL global do sistema alvo e ligar/desligar manualmente o monitor virtual.

---

## 🛠️ Como Compilar e Empacotar

A compilação do executável é orquestrada por um script centralizado que lida com o Nuitka e com as cópias de dependências (como os binários do Chromium).

1. Certifique-se de que um compilador C (como MinGW64 ou MSVC) esteja configurado no seu sistema para o Nuitka.
2. Execute o script de build a partir do diretório raiz:

```powershell
python installer/build.py
```

Após a conclusão da compilação na pasta `dist/`, basta abrir o arquivo `installer/setup.iss` no **Inno Setup 6** e executar a compilação do instalador. O instalador finalizado será ejetado na pasta `releases/`.

---

## 📋 Requisitos do Sistema

- **OS**: Windows 10 / 11 (x64 nativo)
- **Python**: 3.10 ou superior
- **Bibliotecas**: `playwright`, `pywebview`, `screeninfo`, `clr_loader`, `pythonnet`
