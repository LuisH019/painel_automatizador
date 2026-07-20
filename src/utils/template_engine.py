from pathlib import Path
from src.core.config import Config

class TemplateEngine:
    @staticmethod
    def render(template_name: str, css_name: str, js_name: str, context: dict = None) -> str:
        """
        Lê um arquivo HTML e substitui tags genéricas pelas variáveis fornecidas.
        Automaticamente injeta os caminhos padronizados de CSS e JS correspondentes.

        Args:
            template_name (str): Nome do arquivo de template HTML.
            css_name (str): Nome do arquivo CSS.
            js_name (str): Nome do arquivo JS.
            context (dict, optional): Dicionário contendo as variáveis a serem substituídas no template.
        Returns:
            str: O conteúdo HTML final com as substituições aplicadas.
        """
        if context is None:
            context = {}

        template_path = Config.get_template_path(template_name)
        html_content = Path(template_path).read_text(encoding="utf-8")
        
        css_content = Path(Config.get_static_path(f"css/{css_name}")).read_text(encoding="utf-8")
        js_content = Path(Config.get_static_path(f"js/{js_name}")).read_text(encoding="utf-8")
        
        html_content = html_content.replace("{{CSS_CONTENT}}", css_content)
        html_content = html_content.replace("{{JS_CONTENT}}", js_content)

        for key, value in context.items():
            html_content = html_content.replace(f"{{{{{key}}}}}", str(value))

        return html_content