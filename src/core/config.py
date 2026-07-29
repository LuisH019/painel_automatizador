import os
import sys
import shutil
import json
import winreg
from dotenv import load_dotenv
from src.core.logger import log

# Carrega as variáveis do .env se o arquivo existir na raiz
load_dotenv()

class Config:
    TITULO_APP = "Painel de Chamamento - Inicializador Autônomo"
    REGISTRY_PATH = r"SOFTWARE\PMRBS\InicializadorPainelIDS"

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
        3. Fallback (Arquivo local config.json)

        Returns:
            dict: Dicionário contendo 'url' e 'unidades'.
        """
        # 1. Variáveis de Ambiente (.env) - Prioridade Máxima
        env_url = os.getenv("PAINEL_URL")
        env_unidades = os.getenv("PAINEL_UNIDADES")
        
        if env_url and env_unidades:
            return {
                "url": env_url,
                "unidades": [u.strip() for u in env_unidades.split(",")]
            }

        # 2. Registro do Windows
        try:
            # Tenta abrir a chave no HKEY_LOCAL_MACHINE
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, Config.REGISTRY_PATH) as key:
                reg_url, _ = winreg.QueryValueEx(key, "UrlPainel")
                reg_unidades_str, _ = winreg.QueryValueEx(key, "Unidades")
                return {
                    "url": reg_url,
                    "unidades": [u.strip() for u in reg_unidades_str.split(",") if u.strip()]
                }
        except WindowsError:
            pass

        # 3. Fallback (Arquivo local config.json)
        fallback_path = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            "PMRBS Inicializador do Painel IDS", "config.json"
        )
        if os.path.exists(fallback_path):
            try:
                with open(fallback_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return {
                        "url": data.get("url", ""),
                        "unidades": data.get("unidades", [])
                    }
            except Exception:
                pass
        
        # Default de segurança caso nada esteja configurado
        return {"url": "", "unidades": []}
    
    @staticmethod
    def save_app_config(url: str, unidades_str: str) -> bool:
        """
        Salva as configurações de volta no Registro do Windows.
        Requer que o script esteja rodando com privilégios de Administrador.

        Args:
            url (str): URL do painel.
            unidades_str (str): Unidades separadas por vírgula.
        Returns:
            bool: True se salvou com sucesso, False caso contrário.
        """
        try:
            with winreg.CreateKeyEx(winreg.HKEY_LOCAL_MACHINE, Config.REGISTRY_PATH, 0, winreg.KEY_ALL_ACCESS) as key:
                winreg.SetValueEx(key, "UrlPainel", 0, winreg.REG_SZ, url)
                winreg.SetValueEx(key, "Unidades", 0, winreg.REG_SZ, unidades_str)
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
        Obtém o caminho absoluto para um arquivo estático.

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
        Obtém o caminho absoluto para o arquivo de armazenamento de credenciais.

        Returns:
            str: Caminho absoluto para o arquivo de credenciais.
        """
        if Config.is_compiled():
            base_dir = os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                "PMRBS Inicializador do Painel IDS"
            )
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
        
        credentials_dir = os.path.join(base_dir, "credentials")
        os.makedirs(credentials_dir, exist_ok=True)
        return os.path.join(credentials_dir, "credentials.json")

    @staticmethod
    def get_legacy_storage_path() -> str:
        """
        Retorna o caminho do arquivo de credenciais antigo, caso exista.

        Returns:
            str: Caminho absoluto para o arquivo de credenciais antigo.
        """
        if Config.is_compiled():
            return os.path.join(
                os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
                "PMRBS Inicializador do Painel IDS",
                "credentials.json"
            )
        else:
            base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
            return os.path.join(base_dir, "credentials.json")

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