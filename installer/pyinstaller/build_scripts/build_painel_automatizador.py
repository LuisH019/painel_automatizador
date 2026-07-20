from installer.pyinstaller.build_scripts.build_base import criarAplicacao, dadosPadrao, pathexPadrao, iconePadrao

def criarPainelAutomatizador(*, name: str, script: str, uac_admin: bool = False, onedir: bool = True):
    """
    Constrói a aplicação cliente ou de configuração
    usando as configurações padrão.
    """
    return criarAplicacao(
        name=name,
        script=script,
        console=False,
        icon=iconePadrao,
        datas=dadosPadrao,
        pathex=pathexPadrao,
        optimize=0,
        workpath='build',
        distpath='dist',
        debug=False,
        strip=False,
        upx=True,
        bootloader_ignore_signals=False,
        disable_windowed_traceback=False,
        argv_emulation=False,
        target_arch=None,
        codesign_identity=None,
        entitlements_file=None,
        uac_admin=uac_admin,
        onedir=onedir
    )