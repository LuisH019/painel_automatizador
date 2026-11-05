import threading
from src.core.config import Config
from src.drivers.virtual_display import VirtualDisplayManager
from src.services.scraper import ScraperService
from src.core.logger import log

class AutomationService:
    @staticmethod
    def run_panel(credentials: dict):
        """
        Efetua a automação do painel web usando as credenciais fornecidas, abrindo o navegador Chromium
        em um monitor virtual e iniciando imediatamente o espelhamento de tela via Google Cast (CDP).

        Args:
            credentials (dict): Dicionário contendo "usuario", "senha", "unidade" e opcionalmente "dispositivo_cast".
        """
        if not credentials:
            log.error("Cancelado: Nenhuma credencial capturada.")
            return

        monitor_count = VirtualDisplayManager.get_monitor_count()
        pos_x, pos_y = VirtualDisplayManager.get_last_monitor_coordinates()
        capture_source = f"Tela {monitor_count}" if monitor_count > 1 else "Tela inteira"
        target_cast = (credentials.get("dispositivo_cast") or "").strip()

        log.info(
            f"Inicializando Chromium nas coordenadas X={pos_x}, Y={pos_y} "
            f"(Fonte de captura automática: '{capture_source}', TV alvo: '{target_cast or 'Nenhuma'}')"
        )

        from playwright.sync_api import sync_playwright
        with sync_playwright() as p:
            browser_kwargs = {
                "headless": False,
                "ignore_default_args": Config.get_cast_ignore_default_args(),
                "args": [
                    f"--window-position={pos_x},{pos_y}",
                    "--window-size=1920,1080",
                    "--disable-infobars",
                    "--no-sandbox",
                    f"--auto-select-desktop-capture-source={capture_source}",
                    *Config.get_cast_browser_args()
                ]
            }

            browser_executable_path = Config.get_browser_executable_path()
            if browser_executable_path:
                browser_kwargs["executable_path"] = browser_executable_path

            browser = p.chromium.launch(**browser_kwargs)
            context = browser.new_context(viewport={"width": 1920, "height": 1080})
            page = context.new_page()

            cdp_client = context.new_cdp_session(page)

            # Coloca em tela cheia imediatamente antes mesmo do carregamento da página
            try:
                window_id = cdp_client.send("Browser.getWindowForTarget").get("windowId")
                log.info("Forçando modo tela cheia definitivo (Fullscreen via CDP)...")
                cdp_client.send("Browser.setWindowBounds", {"windowId": window_id, "bounds": {"windowState": "fullscreen"}})
            except Exception as fs_err:
                log.warning(f"Não foi possível aplicar fullscreen inicial: {fs_err}")

            discovered_sinks: list[str] = []
            cast_state = {"started": False}

            if target_cast:
                try:
                    def _on_sinks_updated(event):
                        for sink in event.get("sinks", []):
                            name = sink.get("name", "").strip()
                            if name and name not in discovered_sinks:
                                discovered_sinks.append(name)
                                log.info(f"Dispositivo Cast detectado na rede: '{name}'")

                            # Assim que a TV alvo é detectada, dispara o espelhamento imediatamente em paralelo!
                            if name and name.lower() == target_cast.lower() and not cast_state["started"]:
                                cast_state["started"] = True
                                try:
                                    log.info(f"Disparando Cast.startDesktopMirroring imediato para '{name}'...")
                                    cdp_client.send("Cast.startDesktopMirroring", {"sinkName": name})
                                    log.info(f"Transmissão de tela (Desktop Mirroring) iniciada com sucesso para '{name}'!")
                                except Exception as cast_err:
                                    cast_state["started"] = False
                                    log.error(f"Falha ao iniciar Cast.startDesktopMirroring imediato para '{name}': {cast_err}")

                    def _on_issue_updated(event):
                        issue = event.get("issueMessage")
                        if issue:
                            log.warning(f"Aviso do domínio Cast (CDP): {issue}")

                    cdp_client.on("Cast.sinksUpdated", _on_sinks_updated)
                    cdp_client.on("Cast.issueUpdated", _on_issue_updated)
                    cdp_client.send("Cast.enable")
                    log.info("Domínio CDP Cast habilitado. Acelerando descoberta mDNS em segundo plano...")

                    # Acelera a descoberta mDNS em todas as placas de rede física paralelamente ao login
                    threading.Thread(
                        target=ScraperService.relay_mdns_for_chrome,
                        kwargs={"duration_sec": 3.0},
                        daemon=True
                    ).start()
                except Exception as cast_init_err:
                    log.error(f"Falha ao habilitar o domínio Cast no CDP: {cast_init_err}")

            log.info("Navegando até a URL do sistema alvo...")
            page.goto(Config.get_app_config().get("url"), wait_until="domcontentloaded")
            page.bring_to_front()

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

            if target_cast and not cast_state["started"]:
                AutomationService._ensure_desktop_cast(page, cdp_client, target_cast, discovered_sinks, cast_state)
            
            try:
                page.wait_for_event("close", timeout=0)
                log.info("O operador fechou o navegador. Encerrando o processo de automação...")
            except Exception as e:
                log.error(f"Finalizado por interrupção ou erro inesperado: {e}")
            finally:
                try:
                    if browser.is_connected():
                        browser.close()
                except Exception:
                    pass

    @staticmethod
    def _ensure_desktop_cast(page, cdp_client, target_cast: str, discovered_sinks: list[str], cast_state: dict):
        """
        Caso a transmissão ainda não tenha disparado durante o login, aguarda com polling rápido (100ms)
        até o callback iniciar ou dispara manualmente.
        """
        log.info(f"Aguardando resposta mDNS final da TV '{target_cast}'...")

        # Aguarda até 4 segundos em intervalos curtos de 100ms (sem sleep fixo inicial)
        for _ in range(40):
            if cast_state.get("started"):
                return
            for sink_name in discovered_sinks:
                if sink_name.lower() == target_cast.lower():
                    try:
                        cast_state["started"] = True
                        log.info(f"Disparando Cast.startDesktopMirroring para '{sink_name}'...")
                        cdp_client.send("Cast.startDesktopMirroring", {"sinkName": sink_name})
                        log.info(f"Transmissão de tela (Desktop Mirroring) iniciada com sucesso para '{sink_name}'!")
                        return
                    except Exception as e:
                        log.error(f"Falha ao iniciar Cast.startDesktopMirroring para '{sink_name}': {e}")
                        return
            page.wait_for_timeout(100)

        if not cast_state.get("started"):
            log.warning(
                f"Dispositivo '{target_cast}' ainda não listou em Cast.sinksUpdated "
                f"(Dispositivos vistos: {discovered_sinks}). Tentando transmitir mesmo assim..."
            )
            try:
                cdp_client.send("Cast.startDesktopMirroring", {"sinkName": target_cast})
            except Exception as e:
                log.error(f"Falha ao iniciar Cast.startDesktopMirroring para '{target_cast}': {e}")
