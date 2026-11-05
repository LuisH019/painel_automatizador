import os
import sys
import shutil
import json
import ctypes
from ctypes import wintypes
import winreg
from dotenv import load_dotenv
from src.core.logger import log

# Carrega as variáveis do .env se o arquivo existir na raiz
load_dotenv()

class Config:
    TITULO_APP = "Painel de Chamamento - Inicializador Autônomo"
    REGISTRY_PATH = r"SOFTWARE\PMRBS\InicializadorPainelIDS"
    APP_DATA_FOLDER_NAME = "PMRBS Inicializador do Painel IDS"

    @staticmethod
    def is_compiled() -> bool:
        """
        Verifica se a aplicação está empacotada/compilada (PyInstaller ou Nuitka).
        """
        return getattr(sys, 'frozen', False) or '__compiled__' in globals()

    @staticmethod
    def _ui_base_path() -> str:
        """
        Retorna o caminho base para os arquivos de UI (templates e estáticos).
        Se o aplicativo estiver empacotado, retorna o diretório apropriado.
        Caso contrário, retorna o diretório raiz do projeto.

        Returns:
            str: Caminho absoluto para a pasta base de UI.
        """
        if Config.is_compiled():
            if hasattr(sys, '_MEIPASS'):
                return sys._MEIPASS
            else:
                return os.path.dirname(sys.executable)
        return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    
    @staticmethod
    def get_app_config() -> dict:
        """
        Retorna as configurações seguindo a hierarquia de prioridades.
        1. Variáveis de Ambiente (.env)
        2. Registro do Windows (HKLM)
        3. Fallback (Arquivo local config.json em ProgramData ou LocalAppData)

        Returns:
            dict: Dicionário contendo 'url'.
        """
        # 1. Variáveis de Ambiente (.env) - Prioridade Máxima
        env_url = os.getenv("PAINEL_URL")
        
        if env_url:
            return {
                "url": env_url
            }

        # 2. Registro do Windows
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, Config.REGISTRY_PATH) as key:
                reg_url, _ = winreg.QueryValueEx(key, "UrlPainel")
                return {
                    "url": reg_url
                }
        except WindowsError:
            pass

        # 3. Fallback (Arquivo config.json global da máquina ou por usuário)
        fallback_paths = [
            os.path.join(os.environ.get("PROGRAMDATA", r"C:\ProgramData"), Config.APP_DATA_FOLDER_NAME, "config.json"),
            os.path.join(os.environ.get("LOCALAPPDATA", os.path.expanduser("~")), Config.APP_DATA_FOLDER_NAME, "config.json"),
        ]
        for fallback_path in fallback_paths:
            if os.path.exists(fallback_path):
                try:
                    with open(fallback_path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        return {
                            "url": data.get("url", "")
                        }
                except Exception:
                    pass
        
        # Default de segurança caso nada esteja configurado
        return {"url": ""}
    
    @staticmethod
    def save_app_config(url: str) -> bool:
        """
        Salva as configurações de volta no Registro do Windows.
        Requer que o script esteja rodando com privilégios de Administrador.

        Args:
            url (str): URL do painel.
        Returns:
            bool: True se salvou com sucesso, False caso contrário.
        """
        try:
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, Config.REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
                winreg.SetValueEx(key, "UrlPainel", 0, winreg.REG_SZ, url)
            return True
        except PermissionError:
            log.error("Permissão negada. O aplicativo não foi executado como Administrador.")
            return False
        except Exception as e:
            log.error(f"Falha ao gravar no registro: {e}")
            return False

    @staticmethod
    def get_template_path(filename: str) -> str:
        """
        Obtém o caminho absoluto para um arquivo de template.

        Args:
            filename (str): Nome do arquivo de template.

        Returns:
            str: Caminho absoluto para o arquivo de template.
        """
        base_path = Config._ui_base_path()
        if Config.is_compiled():
            return os.path.join(base_path, "templates", filename)
        return os.path.join(base_path, "ui", "templates", filename)

    @staticmethod
    def get_static_path(filename: str) -> str:
        """
        Obtém o caminho absoluto para o arquivo estático.

        Args:
            filename (str): Nome do arquivo estático.

        Returns:
            str: Caminho absoluto para o arquivo estático.
        """
        base_path = Config._ui_base_path()
        if Config.is_compiled():
            return os.path.join(base_path, "static", filename)
        return os.path.join(base_path, "ui", "static", filename)
    
    @staticmethod
    def get_storage_path() -> str:
        """
        Obtém o caminho absoluto para o arquivo de armazenamento de credenciais compartilhado na máquina
        (em C:\\ProgramData quando compilado, ou na pasta do projeto em modo dev), garantindo que as
        credenciais valham para o computador inteiro e não apenas para o usuário logado.

        Returns:
            str: Caminho absoluto para o arquivo de credenciais.
        """
        if Config.is_compiled():
            base_dir = os.path.join(
                os.environ.get("PROGRAMDATA", r"C:\ProgramData"),
                Config.APP_DATA_FOLDER_NAME
            )
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        credentials_dir = os.path.join(base_dir, "credentials")
        os.makedirs(credentials_dir, exist_ok=True)
        return os.path.join(credentials_dir, "credentials.json")

    @staticmethod
    def get_legacy_storage_path() -> str:
        """
        Retorna o caminho antigo principal de credenciais (mantido por compatibilidade).
        """
        return Config.get_legacy_storage_paths()[0]

    @staticmethod
    def get_legacy_storage_paths() -> list[str]:
        """
        Retorna todos os possíveis caminhos antigos de credenciais (por usuário em LOCALAPPDATA
        ou na raiz antiga) para migração automática para o armazenamento global da máquina.
        """
        local_app_data = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
        program_data = os.environ.get("PROGRAMDATA", r"C:\ProgramData")
        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))

        return [
            os.path.join(local_app_data, Config.APP_DATA_FOLDER_NAME, "credentials", "credentials.json"),
            os.path.join(local_app_data, Config.APP_DATA_FOLDER_NAME, "credentials.json"),
            os.path.join(program_data, Config.APP_DATA_FOLDER_NAME, "credentials.json"),
            os.path.join(project_root, "credentials.json"),
        ]

    @staticmethod
    def get_adaptive_window_size(ideal_width: int, ideal_height: int) -> tuple[int, int]:
        """
        Calcula o tamanho ideal da janela limitando-o à área útil do monitor principal
        (descontando a barra de tarefas e respeitando a escala de DPI do Windows).

        Args:
            ideal_width (int): Largura desejada em telas grandes.
            ideal_height (int): Altura desejada em telas grandes.

        Returns:
            tuple[int, int]: (largura, altura) ajustadas para caber perfeitamente na tela.
        """
        try:
            rect = wintypes.RECT()
            # SPI_GETWORKAREA = 0x0030
            if ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0):
                work_w = max(400, rect.right - rect.left)
                work_h = max(400, rect.bottom - rect.top)
                width = min(ideal_width, int(work_w * 0.92))
                height = min(ideal_height, int(work_h * 0.88))
                return width, height
        except Exception:
            pass
        return ideal_width, ideal_height

    @staticmethod
    def get_browser_executable_path() -> str | None:
        """
        Retorna o caminho do executável do navegador (Chrome ou Edge) instalado no sistema.

        Returns:
            str | None: Caminho absoluto para o executável do navegador, ou None se não encontrado.
        """
        candidate_paths = [
            os.path.join(os.environ.get("PROGRAMFILES", r"C:\Program Files"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("PROGRAMFILES(X86)", r"C:\Program Files (x86)"), "Google", "Chrome", "Application", "chrome.exe"),
            os.path.join(os.environ.get("LOCALAPPDATA", r"C:\Users\Default\AppData\Local"), "Microsoft", "Edge", "Application", "msedge.exe"),
        ]

        for path in candidate_paths:
            if path and os.path.exists(path):
                return path

        return shutil.which("chrome") or shutil.which("msedge")

    @staticmethod
    def get_cast_ignore_default_args() -> list[str]:
        """
        Retorna a lista de argumentos padrão do Playwright que devem ser ignorados
        para permitir que o Media Router e a descoberta de dispositivos Cast (mDNS/DIAL) funcionem.
        """
        return [
            "--disable-background-networking",
            "--disable-component-extensions-with-background-pages",
            "--disable-default-apps",
            "--disable-extensions",
            "--mute-audio",
            "--disable-features=AvoidUnnecessaryBeforeUnloadCheckSync,DestroyProfileOnBrowserClose,DialMediaRouteProvider,GlobalMediaControls,HttpsUpgrades,LensOverlay,MediaRouter,PaintHolding,ThirdPartyStoragePartitioning,BlockOriginHeaderModificationOnRedirect,Translate,AutoDeElevate,OptimizationHints,msForceBrowserSignIn,msEdgeUpdateLaunchServicesPreferredVersion",
        ]

    @staticmethod
    def get_cast_browser_args() -> list[str]:
        """
        Retorna as flags do Chrome necessárias para habilitar o domínio Cast via CDP.
        """
        return [
            "--enable-features=MediaRouter,DialMediaRouteProvider,CastMediaRouteProvider,CastAllowAllIPs",
            "--allow-running-insecure-content",
            "--lang=pt-BR",
        ]
