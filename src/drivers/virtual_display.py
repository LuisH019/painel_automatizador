import ctypes
import subprocess
import time
from screeninfo import get_monitors
from src.core.logger import log

class VirtualDisplayManager: 
    DEVICE_NAME = "Virtual Display"

    @staticmethod
    def get_monitor_count() -> int:
        """
        Retorna o número de monitores conectados ao sistema.

        Returns:
            int: Número de monitores conectados.
        """
        return ctypes.windll.user32.GetSystemMetrics(80)

    @staticmethod
    def _run_powershell(command: str) -> bool:
        """
        Executa comandos PowerShell em background sem piscar a tela preta.

        Args:
            command (str): Comando PowerShell a ser executado.
        
        Returns:
            bool: True se o comando for executado com sucesso, False caso contrário.
        """
        try:
            subprocess.run(["powershell", "-Command", command], 
                           check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                           creationflags=0x08000000)
            return True
        except subprocess.CalledProcessError as e:
            log.error(f"Falha no comando PowerShell: {e.stderr.decode('utf-8', errors='ignore')}")
            return False

    @classmethod
    def enable_driver(cls) -> bool:
        """
        Ativa o driver no Gerenciador de Dispositivos (Requer UAC Admin).

        Returns:
            bool: True se o driver for ativado com sucesso, False caso contrário.
        """
        log.info("Tentando ativar o Monitor Virtual via PnpDevice...")
        command = f'Get-PnpDevice -FriendlyName "*{cls.DEVICE_NAME}*" -Status Error,Unknown,OK | Enable-PnpDevice -Confirm:$false'
        return cls._run_powershell(command)

    @classmethod
    def disable_driver(cls) -> bool:
        """
        Desativa o driver no Gerenciador de Dispositivos (Requer UAC Admin).

        Returns:
            bool: True se o driver for desativado com sucesso, False caso contrário.
        """
        log.info("Tentando desativar o Monitor Virtual via PnpDevice...")
        command = f'Get-PnpDevice -FriendlyName "*{cls.DEVICE_NAME}*" -Status OK | Disable-PnpDevice -Confirm:$false'
        return cls._run_powershell(command)

    @classmethod
    def status_driver(cls) -> str:
        """
        Verifica se o driver está ativo ou desativado.

        Returns:
            str: "ATIVO", "DESATIVADO" ou "NÃO INSTALADO".
        """
        command = f'(Get-PnpDevice -FriendlyName "*{cls.DEVICE_NAME}*").Status'
        try:
            result = subprocess.run(["powershell", "-Command", command], 
                                    capture_output=True, text=True, creationflags=0x08000000)
            status = result.stdout.strip()
            if status == "OK":
                return "ATIVO"
            elif status in ["Error", "Unknown"]:
                return "DESATIVADO"
            else:
                return "NÃO INSTALADO"
        except Exception:
            return "ERRO"

    @classmethod
    def ensure_virtual_display(cls):
        """
        Garante que o monitor virtual esteja ativo. Se não estiver, tenta ativá-lo.
        """
        monitors = cls.get_monitor_count()
        log.info(f"Contagem inicial de monitores detectados: {monitors}")
        
        if monitors < 2:
            log.warning("Monitor virtual não detectado. Forçando extensão de telas (displayswitch.exe)...")
            try:
                subprocess.run(["cmd", "/c", "displayswitch.exe", "/extend"], check=True)
                time.sleep(3)
            except Exception as e:
                log.error(f"Falha crítica ao tentar estender o monitor virtual: {e}")
        else:
            log.info("Monitor auxiliar/virtual já se encontra ativo na topologia do Windows.")

    @staticmethod
    def get_last_monitor_coordinates() -> tuple:
        """
        Retorna as coordenadas do último monitor conectado.
        
        Returns:
            tuple: As coordenadas (x, y) do último monitor.
        """
        monitors = get_monitors()
        last_monitor = max(monitors, key=lambda m: m.x)
        log.info(f"Alvo do Chromium definido: Monitor '{last_monitor.name}' posicionado em X={last_monitor.x}, Y={last_monitor.y}")
        return last_monitor.x, last_monitor.y