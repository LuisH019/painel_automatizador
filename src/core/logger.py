import glob
import logging
import os
import sys
from datetime import datetime

def _cleanup_old_logs(logs_dir: str, max_files: int = 10):
    """
    Mantém apenas os 'max_files' arquivos de log mais recentes na pasta de logs, 
    deletando os excedentes para garantir o limite configurado.

    Args:
        logs_dir (str): Caminho para a pasta de logs.
        max_files (int): Número máximo de arquivos de log a serem mantidos.
    """
    if not os.path.exists(logs_dir):
        return

    log_files = glob.glob(os.path.join(logs_dir, "*.log"))
    log_files.sort(key=os.path.getmtime)

    while len(log_files) >= max_files:
        oldest_file = log_files.pop(0)
        try:
            os.remove(oldest_file)
        except Exception:
            pass

def _setup_logger() -> logging.Logger:
    """
    Configura o logger principal da aplicação.

    Returns:
        logging.Logger: Instância do logger configurado.
    """
    if getattr(sys, 'frozen', False):
        base_dir = os.path.join(
            os.environ.get("LOCALAPPDATA", os.path.expanduser("~")),
            "PMRBS Inicializador do Painel IDS"
        )
    else:
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "../.."))
    
    logs_dir = os.path.join(base_dir, "logs")
    os.makedirs(logs_dir, exist_ok=True)

    _cleanup_old_logs(logs_dir, max_files=10)

    timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
    log_file = os.path.join(logs_dir, f"app_{timestamp}.log")

    app_logger = logging.getLogger("PainelIDS")
    app_logger.setLevel(logging.INFO)

    if not app_logger.handlers:
        formatter = logging.Formatter(
            fmt="%(asctime)s | %(levelname)-8s | [%(module)s] %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )

        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        app_logger.addHandler(console_handler)

        file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
        file_handler.setFormatter(formatter)
        app_logger.addHandler(file_handler)
    
    logging.getLogger("pywebview").setLevel(logging.ERROR)
    logging.getLogger("comtypes").setLevel(logging.ERROR)

    return app_logger

log = _setup_logger()