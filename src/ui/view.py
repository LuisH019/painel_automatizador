import sys
import os
import ctypes
from pathlib import Path
import webview
from src.core.config import Config
from src.core.credentials_repo import CredentialsRepository, SecureCredentials
from src.ui.base_api import BaseWebviewAPI
from src.utils.template_engine import TemplateEngine

class LoginInterfaceAPI(BaseWebviewAPI):
    def __init__(self):
        super().__init__()
        self.credentials = None

    def ask_admin_config(self):
        """
        Abre a janela de configuração para o administrador.
        """
        current_dir = os.getcwd() 
        if getattr(sys, 'frozen', False):
            executable, params = sys.executable, "--config"
            current_dir = os.path.dirname(executable)
        else:   
            executable, params = sys.executable, "-m src.main --config"
            current_dir = str(Path(__file__).resolve().parents[2])

        ctypes.windll.shell32.ShellExecuteW(None, "runas", executable, params, current_dir, 1)

    def load_initial_data(self) -> dict: 
        """
        Carrega as credenciais salvas, se existirem, para pré-preenchimento do formulário de login.
        
        Returns:
            dict: Dicionário contendo as credenciais salvas, ou None se não houver.
        """
        return CredentialsRepository.load()
    
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
            save_pattern = webview.windows[0].evaluate_js("document.getElementById('salvarPadrao').checked;")
            
            self._authenticate(user, password, unidade, save_pattern)
        except Exception as e:
            from src.core.logger import log
            log.error(f"Erro ao capturar dados do DOM: {e}")
            self.show_alert("Falha de segurança ao ler o formulário.")


    def _authenticate(self, user: str, password: str, unidade: str, save_pattern: bool):
        """
        Recebe as credenciais do usuário, valida e salva se necessário.

        Args:
            user (str): Nome de usuário.
            password (str): Senha do usuário.
            unidade (str): Unidade do usuário.
            save_pattern (bool): Indica se as credenciais devem ser salvas.

        Returns:
            bool: True se a autenticação for bem-sucedida, False caso contrário.
        """
        if save_pattern:
            CredentialsRepository.save(user, password, unidade)
            
        if user and password and unidade:
            credentials = SecureCredentials()
            credentials["usuario"] = user
            credentials["senha"] = password
            credentials["unidade"] = unidade
            
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
        
        app_config = Config.get_app_config()
        configured_unidades = app_config.get("unidades", [])
        
        html_options = "".join([f'<option value="{u.replace('"', '&quot;')}">{u}</option>\n' for u in configured_unidades])

        html_content = TemplateEngine.render(
            "login.html", 
            "base.css",
            "login.js",
            {"UNIDADES_OPTIONS": html_options}
        )
        
        webview.create_window(title=Config.TITULO_APP, html=html_content, js_api=api, width=600, height=600, resizable=False)
        webview.start(gui='edgechromium')
        return api.credentials