import sys

def main():
    # 1. Rota de Administração da TI
    from src.core.logger import log

    if "--config" in sys.argv:
        log.info("=== INICIANDO MODO DE CONFIGURAÇÃO ADMINISTRATIVA ===")
        from src.ui.config_view import AdminWindowManager
        AdminWindowManager.open()
        sys.exit(0)

    log.info("=== INICIALIZANDO ORQUESTRADOR DO PAINEL ===")

    # 2. Rota de Auto-Inicialização (GPO/Startup)
    if "--auto" in sys.argv:
        log.info("Flag --auto detectada. Tentando inicialização silenciosa...")
        from src.core.credentials_repo import CredentialsRepository, SecureCredentials
        loaded_data = CredentialsRepository.load()
        
        if loaded_data.get("usuario") and loaded_data.get("senha") and loaded_data.get("unidade"):
            log.info("Credenciais completas encontradas. Pulando interface gráfica.")
            
            secure_credentials = SecureCredentials(loaded_data)
            
            from src.drivers.virtual_display import VirtualDisplayManager
            VirtualDisplayManager.ensure_virtual_display()

            from src.services.automation import AutomationService
            AutomationService.run_panel(secure_credentials)
            sys.exit(0)
        else:
            log.warning("Modo --auto invocado, mas as credenciais estão ausentes ou incompletas. Recuando para a interface gráfica.")

    # 3. Rota Padrão (Interface Gráfica)
    from src.ui.view import DesktopWindowManager
    credentials = DesktopWindowManager.capture_credentials()
    
    if not credentials:
        log.warning("Execução abortada pelo operador na tela de login.")
        sys.exit(0)
        
    from src.drivers.virtual_display import VirtualDisplayManager
    VirtualDisplayManager.ensure_virtual_display()

    from src.services.automation import AutomationService
    AutomationService.run_panel(credentials)

if __name__ == "__main__":
    main()