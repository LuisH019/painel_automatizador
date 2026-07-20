import webview
from src.core.config import Config
from src.ui.base_api import BaseWebviewAPI
from src.utils.template_engine import TemplateEngine
from src.drivers.virtual_display import VirtualDisplayManager # <-- Nova importação

class ConfigAdminAPI(BaseWebviewAPI):
    def save_settings(self, url: str, unidades: str):
        """
        Recebe os dados da interface HTML e salva no registro do Windows.
        
        Args:
            url (str): A URL do sistema alvo.
            unidades (str): As unidades separadas por vírgula.
        """
        success = Config.save_app_config(url, unidades)
        if success:
            self.show_alert("Configurações salvas no Registro do Windows com sucesso! Reinicie o aplicativo.")
            self.close_window()
        else:
            self.show_alert("Erro de Permissão. Verifique se você está rodando como Administrador.")

    def toggle_virtual_monitor(self, action: str):
        """
        Recebe o comando da interface HTML para ligar/desligar o driver.
        
        Args:
            action (str): "LIGAR" para ativar o driver, "DESLIGAR" para desativar.
        """
        sucesso = False
        if action == "LIGAR":
            sucesso = VirtualDisplayManager.enable_driver()
        elif action == "DESLIGAR":
            sucesso = VirtualDisplayManager.disable_driver()
            
        if sucesso:
            self.show_alert(f"Comando executado! O monitor virtual foi {action.lower()} com sucesso. Reinicie a aplicação para visualizar.")
        else:
            self.show_alert("Erro. Verifique se o driver já foi instalado na máquina e se possui permissão de Administrador.")

class AdminWindowManager:
    @staticmethod
    def open():
        """
        Abre a janela de configuração avançada para o usuário.
        """
        api = ConfigAdminAPI()
        current_config = Config.get_app_config()
        status_driver = VirtualDisplayManager.status_driver() # <-- Busca o status
        
        html_content = TemplateEngine.render(
            "admin.html", 
            "base.css",
            "admin.js",
            {
                "CURRENT_URL": current_config.get("url", ""),
                "CURRENT_UNIDADES": ", ".join(current_config.get("unidades", [])),
                "STATUS_DRIVER": status_driver
            }
        )

        webview.create_window(title="Configuração Avançada - TI", html=html_content, js_api=api, width=900, height=900, resizable=False)
        webview.start()