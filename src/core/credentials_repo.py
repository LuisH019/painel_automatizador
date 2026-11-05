import json
import os
import binascii
try:
    import win32crypt
except ImportError:
    win32crypt = None

from src.core.config import Config
from src.core.logger import log

# Flag da DPAPI do Windows que vincula a criptografia à máquina local (qualquer usuário do PC)
# em vez de restringir apenas ao usuário do Windows que salvou a credencial.
CRYPTPROTECT_LOCAL_MACHINE = 0x04

class SecureCredentials(dict):
    """
    Dicionário customizado que mascara a senha automaticamente 
    caso o objeto seja impresso (print) ou logado.
    """
    def __repr__(self) -> str:
        safe_dict = self.copy()
        if "senha" in safe_dict and safe_dict["senha"]:
            safe_dict["senha"] = "******** [OCULTO]"
        return dict.__repr__(safe_dict)

    def __str__(self) -> str:
        return self.__repr__()

class CredentialsRepository:
    
    @staticmethod
    def _encrypt(text: str) -> str:
        """
        Usa a DPAPI do Windows com escopo de máquina (CRYPTPROTECT_LOCAL_MACHINE) para criptografar
        a string vinculada ao computador, permitindo que qualquer usuário logado na máquina utilize
        as credenciais salvas.
        
        Args:
            text (str): Texto a ser criptografado.
        Returns:
            str: Texto criptografado em hexadecimal.
        """
        if not text or not win32crypt:
            return text
        
        bytes_data = text.encode('utf-8')
        encrypted = win32crypt.CryptProtectData(
            bytes_data, None, None, None, None, CRYPTPROTECT_LOCAL_MACHINE
        )
        return binascii.hexlify(encrypted).decode('utf-8')

    @staticmethod
    def _decrypt(hex_text: str) -> tuple[str, bool]:
        """
        Desfaz a criptografia DPAPI (tanto de escopo de máquina quanto legado por usuário).

        Args:
            hex_text (str): Texto criptografado em hexadecimal.
        Returns:
            tuple[str, bool]: (Texto descriptografado ou vazio se falhar, flag de sucesso).
        """
        if not hex_text:
            return "", True
        if not win32crypt:
            return hex_text, True
        
        try:
            encrypted = binascii.unhexlify(hex_text.encode('utf-8'))
            _, decrypted_data = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
            return decrypted_data.decode('utf-8'), True
        except Exception as e:
            log.warning(f"Não foi possível descriptografar a credencial salva anteriormente: {e}")
            return "", False

    @staticmethod
    def load() -> dict:
        """
        Lê as credenciais salvas na máquina e descriptografa a senha.
        Migra automaticamente arquivos antigos (por usuário ou escopo DPAPI antigo) para o
        escopo global do computador.

        Returns:
            dict: Dicionário com {"usuario": str, "senha": str, "unidade": str, "dispositivo_cast": str}
        """
        primary_path = Config.get_storage_path()
        paths = [primary_path]
        for legacy_path in Config.get_legacy_storage_paths():
            if legacy_path not in paths:
                paths.append(legacy_path)

        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)

                    raw_pass = data.get("senha", "")
                    decrypted_pass, decrypt_ok = CredentialsRepository._decrypt(raw_pass)
                    if not decrypt_ok:
                        continue

                    data["senha"] = decrypted_pass
                    if "dispositivo_cast" not in data:
                        data["dispositivo_cast"] = ""

                    # Migra automaticamente para o caminho global da máquina e/ou atualiza a chave DPAPI para escopo da máquina
                    if path != primary_path or data.get("scope") != "machine":
                        try:
                            CredentialsRepository.save(
                                data.get("usuario", ""), 
                                data.get("senha", ""), 
                                data.get("unidade", ""),
                                data.get("dispositivo_cast", "")
                            )
                            log.info("Credenciais migradas automaticamente para o escopo global do computador.")
                        except Exception:
                            pass

                    return data
                except Exception:
                    continue

        return {"usuario": "", "senha": "", "unidade": "", "dispositivo_cast": ""}

    @staticmethod
    def save(user: str, password: str, unidade: str, dispositivo_cast: str = ""):
        """
        Criptografa a senha no escopo da máquina (CRYPTPROTECT_LOCAL_MACHINE) e grava as credenciais
        para todos os usuários do computador.

        Args:
            user (str): Nome do usuário.
            password (str): Senha do usuário.
            unidade (str): Unidade do usuário.
            dispositivo_cast (str): Nome da TV / dispositivo Cast selecionado.
        """
        path = Config.get_storage_path()
        secure_password = CredentialsRepository._encrypt(password)
        
        data = {
            "usuario": user,
            "senha": secure_password,
            "unidade": unidade,
            "dispositivo_cast": dispositivo_cast,
            "scope": "machine"
        }
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
            try:
                os.chmod(path, 0o666)
            except Exception:
                pass
        except Exception as e:
            log.error(f"Não foi possível salvar as credenciais na máquina: {e}")
