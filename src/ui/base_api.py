from abc import ABC
import webview

class BaseWebviewAPI(ABC):
    """Classe base que fornece métodos utilitários genéricos para instâncias do PyWebView."""
    
    def close_window(self):
        """
        Fecha a janela do PyWebView.
        """
        if webview.windows:
            webview.windows[0].destroy()

    def show_alert(self, message: str):
        """
        Exibe um alerta na janela do PyWebView.

        Args:
            message (str): A mensagem a ser exibida no alerta.
        """
        if webview.windows:
            safe_message = message.replace("'", "\\'")
            # webview.windows[0].evaluate_js(f"alert('{safe_message}');")