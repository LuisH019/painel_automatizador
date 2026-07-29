import os
import shutil
import subprocess
import sys

# Caminho raiz do projeto (voltando de installer/nuitka para a raiz)
CAMINHO_BASE = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

def compilar_nuitka():
    # Muda o diretório atual para a raiz do projeto
    os.chdir(CAMINHO_BASE)
    
    script_alvo = os.path.join('src', 'main.py')
    pasta_saida = 'dist'
    
    print(f"Iniciando compilação com Nuitka na raiz: {CAMINHO_BASE}...\n")
    
    # Montando a lista de argumentos para o Nuitka
    comando = [
        sys.executable, "-m", "nuitka",
        "--standalone",                        
        "--windows-console-mode=disable",                   
        f"--output-dir={pasta_saida}",         
        "--output-filename=InicializadorPainelIDS.exe", 
        "--windows-icon-from-ico=src/ui/static/images/icone.ico", 
        
        # Arquivos estáticos
        "--include-data-dir=src/ui/static=static",
        "--include-data-dir=src/ui/templates=templates",
        
        # Otimizações para Tempo de Build
        "--remove-output",                     
        "--assume-yes-for-downloads",          
        # Removido --low-memory e --jobs=1 para permitir uso total do CPU/RAM
        "--lto=no",                            
        
        # Playwright Configs
        "--nofollow-import-to=playwright",
        "--include-module=greenlet",
        "--include-package=pyee",
        "--include-package=typing_extensions",
        "--plugin-enable=playwright",
        "--playwright-include-browser=all",
        
        # Correções de pacotes (Pythonnet/WebView2)
        "--plugin-enable=pywebview",
        "--include-module=clr",
        "--include-package=pythonnet",
        
        script_alvo                            
    ]
    
    print("Comando gerado:")
    print(" ".join(comando))
    print("\nIsso pode demorar alguns minutos. Aguarde...")
    
    try:
        subprocess.run(comando, check=True)
        print("\nCompilação concluída pelo Nuitka. Aplicando correção do Playwright...")
        
        # O Nuitka gera a pasta de distribuição baseada no nome do script principal (main.dist)
        pasta_dist_interna = os.path.join(CAMINHO_BASE, pasta_saida, 'main.dist')
        
        if os.path.exists(pasta_dist_interna):
            print("-> A compilação da pasta interna dist ocorreu com sucesso.")
            
            import playwright
            playwright_dir = os.path.dirname(playwright.__file__)
            print(f"Copiando o diretório do playwright de {playwright_dir} para a dist...")
            destino = os.path.join(pasta_dist_interna, 'playwright')
            if os.path.exists(destino):
                shutil.rmtree(destino)
            shutil.copytree(playwright_dir, destino, ignore=shutil.ignore_patterns('__pycache__', '*.pyc'))
            print("-> playwright copiado com sucesso!")
                
        print(f"\nProcesso finalizado! Verifique a pasta '{pasta_saida}'.")
        
    except subprocess.CalledProcessError as e:
        print(f"\nErro durante a compilação: {e}")
        
if __name__ == "__main__":
    compilar_nuitka()