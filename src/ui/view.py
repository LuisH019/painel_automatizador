import sys
import os
import ctypes
from pathlib import Path
import webview
from src.core.config import Config
from src.core.credentials_repo import CredentialsRepository, SecureCredentials
from src.ui.base_api import BaseWebviewAPI
from src.utils.template_engine import TemplateEngine
from src.services.scraper import ScraperService
from src.core.logger import log

class LoginInterfaceAPI(BaseWebviewAPI):
    def __init__(self):
        super().__init__()
        self.credentials = None

    def ask_admin_config(self):
        """
        Abre a janela de configuração para o administrador.
        """
        try:
            current_dir = os.getcwd() 
            if getattr(sys, 'frozen', False) or '__compiled__' in globals():
                executable, params = sys.argv[0], "--config"
                current_dir = os.path.dirname(os.path.abspath(executable))
            else:   
                executable, params = sys.executable, "-m src.main --config"
                current_dir = str(Path(__file__).resolve().parents[2])

            ret = ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, current_dir, 1)
            if ret <= 32:
                from src.core.logger import log
                log.error(f"Erro ao solicitar elevação (UAC). Código: {ret}")
        except Exception as e:
            from src.core.logger import log
            log.error(f"Falha no ask_admin_config: {e}")

    def load_initial_data(self) -> dict: 
        """
        Carrega as credenciais salvas, se existirem, para pré-preenchimento do formulário de login.
        
        Returns:
            dict: Dicionário contendo as credenciais salvas, ou None se não houver.
        """
        return CredentialsRepository.load()
        
    def fetch_units(self) -> list[str]:
        """
        Invocado pelo JS para carregar dinamicamente as unidades.
        """
        try:
            log.info("Recebida requisição JS para fetch_units...")
            unidades = ScraperService.fetch_units()
            log.info(f"fetch_units retornando {len(unidades)} unidades ao JS.")
            return unidades
        except Exception as e:
            log.error(f"Erro ao processar fetch_units: {e}")
            return []

    def fetch_cast_devices(self, force_scan: bool = False) -> list[str]:
        """
        Invocado pelo JS para listar as TVs / dispositivos Google Cast disponíveis na rede.
        """
        try:
            log.info(f"Recebida requisição JS para fetch_cast_devices (force_scan={force_scan})...")
            devices = ScraperService.fetch_cast_devices(force_scan=force_scan)
            log.info(f"fetch_cast_devices retornando {len(devices)} dispositivo(s) ao JS.")
            return devices
        except Exception as e:
            log.error(f"Erro ao processar fetch_cast_devices: {e}")
            return []
    
    def process_login(self):
        """
        Invocado pelo JS quando o botão é clicado. 
        O Python vai até a interface e 'puxa' os valores da memória, 
        evitando o tráfego da senha em texto claro pelos logs de IPC do webview.
        """
        try:
            user = webview.windows[0].evaluate_js("document.getElementById('username').value;")
            password = webview.windows[0].evaluate_js("document.getElementById('password').value;")
            unidade = webview.windows[0].evaluate_js("document.getElementById('unidade').value;")
            dispositivo_cast = webview.windows[0].evaluate_js("document.getElementById('dispositivoCast').value;")
            save_pattern = webview.windows[0].evaluate_js("document.getElementById('salvarPadrao').checked;")
            
            self._authenticate(user, password, unidade, dispositivo_cast or "", save_pattern)
        except Exception as e:
            from src.core.logger import log
            log.error(f"Erro ao capturar dados do DOM: {e}")
            self.show_alert("Falha de segurança ao ler o formulário.")


    def _authenticate(self, user: str, password: str, unidade: str, dispositivo_cast: str, save_pattern: bool):
        """
        Recebe as credenciais do usuário, valida e salva se necessário.

        Args:
            user (str): Nome de usuário.
            password (str): Senha do usuário.
            unidade (str): Unidade do usuário.
            dispositivo_cast (str): Nome da TV / dispositivo Cast para espelhamento.
            save_pattern (bool): Indica se as credenciais devem ser salvas.

        Returns:
            bool: True se a autenticação for bem-sucedida, False caso contrário.
        """
        if save_pattern:
            CredentialsRepository.save(user, password, unidade, dispositivo_cast)
            
        if user and password and unidade:
            credentials = SecureCredentials()
            credentials["usuario"] = user
            credentials["senha"] = password
            credentials["unidade"] = unidade
            credentials["dispositivo_cast"] = dispositivo_cast
            
            self.credentials = credentials
            self.close_window()

class DesktopWindowManager:
    @staticmethod
    def capture_credentials() -> dict:
        """
        Abre a janela de login para o usuário e captura as credenciais fornecidas.

        Returns:
            dict: Dicionário contendo as credenciais do usuário, ou None se o usuário cancelar.
        """
        api = LoginInterfaceAPI()
        
        html_content = TemplateEngine.render(
            "login.html", 
            "base.css",
            "login.js",
            {}
        )
        
        win_w, win_h = Config.get_adaptive_window_size(600, 640)
        webview.create_window(
            title=Config.TITULO_APP,
            html=html_content,
            js_api=api,
            width=win_w,
            height=win_h,
            resizable=True,
            min_size=(380, 420)
        )
        webview.start()
        return api.credentials
