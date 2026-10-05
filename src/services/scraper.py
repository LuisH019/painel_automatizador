from src.core.logger import log
from src.core.config import Config

class ScraperService:
    @staticmethod
    def fetch_units() -> list[str]:
        """
        Acessa a URL do painel em background e extrai as unidades disponíveis na tag <li> 
        dentro do elemento <ul> com id="O3F_id-picker-listEl".
        
        Returns:
            list[str]: Lista de unidades capturadas ou vazia se houver erro.
        """
        url = Config.get_app_config().get("url")
        if not url:
            log.error("URL do painel não configurada.")
            return []
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())
            
        unidades = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser_kwargs = {
                    "headless": True,
                    "args": [
                        "--disable-infobars",
                        "--no-sandbox"
                    ]
                }
                
                browser_executable_path = Config.get_browser_executable_path()
                if browser_executable_path:
                    browser_kwargs["executable_path"] = browser_executable_path
                    
                browser = p.chromium.launch(**browser_kwargs)
                context = browser.new_context()
                page = context.new_page()
                
                log.info(f"Acessando URL {url} para capturar unidades (webscrapping)...")
                page.goto(url, wait_until="load", timeout=30000)
                
                trigger_selector = "div#O3F_id-trigger-t1"
                page.wait_for_selector(trigger_selector, timeout=15000)
                page.click(trigger_selector)
                
                list_selector = "ul#O3F_id-picker-listEl li"
                page.wait_for_selector(list_selector, timeout=10000)
                
                li_elements = page.locator(list_selector).all()
                for li in li_elements:
                    text = li.inner_text().strip()
                    if text:
                        unidades.append(text)
                        
                browser.close()
                log.info(f"Foram capturadas {len(unidades)} unidades.")
        except Exception as e:
            log.error(f"Erro ao capturar unidades via web scraping: {e}")
            
        return unidades
