import time
from src.core.config import Config
from src.drivers.virtual_display import VirtualDisplayManager
from src.core.logger import log

class AutomationService:
    @staticmethod
    def run_panel(credentials: dict):
        """
        Efetua a automação do painel web usando as credenciais fornecidas, abrindo o navegador Chromium em um monitor virtual.

        Args:
            credentials (dict): Dicionário contendo as credenciais do usuário, com as chaves "usuario", "senha" e "unidade".
        """
        if not credentials:
            log.error("Cancelado: Nenhuma credencial capturada.")
            return

        pos_x, pos_y = VirtualDisplayManager.get_last_monitor_coordinates()
        log.info(f"Inicializando Chromium nas coordenadas X={pos_x}, Y={pos_y}")

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_kwargs = {
                "headless": False,
                "args": [
                    f"--window-position={pos_x},{pos_y}",
                    f"--window-size=1920,1080",
                    "--disable-infobars",
                    "--no-sandbox"
                ]
            }

            browser_executable_path = Config.get_browser_executable_path()
            if browser_executable_path:
                browser_kwargs["executable_path"] = browser_executable_path

            browser = p.chromium.launch(**browser_kwargs)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            log.info("Navegando até a URL do sistema alvo...")
            page.goto(Config.get_app_config().get("url"), wait_until="load")
            page.bring_to_front()
            page.wait_for_timeout(1000)

            cdp_client = context.new_cdp_session(page)
            window_id = cdp_client.send("Browser.getWindowForTarget").get("windowId")

            log.info("Forçando modo tela cheia definitivo (Fullscreen via CDP)...")
            cdp_client.send("Browser.setWindowBounds", {"windowId": window_id, "bounds": {"windowState": "fullscreen"}})

            page.wait_for_selector('input[name="O51"]')
            page.fill('input[name="O51"]', credentials["usuario"])
            page.fill('input[name="O55"]', credentials["senha"])
            
            log.info(f"Selecionando a unidade de atuação: {credentials['unidade']}")
            page.locator("div#O3F_id-trigger-t1").click()
            
            opcao_seletor = f'li.x-boundlist-item:has-text("{credentials["unidade"]}")'
            page.wait_for_selector(opcao_seletor)
            page.click(opcao_seletor)

            log.info("Efetuando o login automático...")
            page.wait_for_selector("#O4D_id")
            page.click("#O4D_id")
            
            log.info("Sistema logado com sucesso e isolado no monitor virtual.")
            
            try:
                page.wait_for_event("close", timeout=0)
                log.info("O operador fechou o navegador. Encerrando o processo de automação...")
            except Exception as e:
                log.error(f"Finalizado por interrupção ou erro inesperado: {e}")
            finally:
                if browser.is_connected():
                    browser.close()