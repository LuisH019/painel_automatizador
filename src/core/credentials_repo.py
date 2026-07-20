import json
import os
import binascii
try:
    import win32crypt
except ImportError:
    win32crypt = None

from src.core.config import Config
from src.core.logger import log

class SecureCredentials(dict):
    """
    Dicionário customizado que mascara a senha automaticamente 
    caso o objeto seja impresso (print) ou logado.
    """
    def __repr__(self) -> str:
        """
        Retorna uma representação do dicionário com a senha mascarada.

        Returns:
            str: Representação do dicionário com a senha mascarada.
        """
        safe_dict = self.copy()
        if "senha" in safe_dict and safe_dict["senha"]:
            safe_dict["senha"] = "******** [OCULTO]"
        return super(SecureCredentials, safe_dict).__repr__()

    def __str__(self) -> str:
        """
        Retorna uma representação do dicionário com a senha mascarada.

        Returns:
            str: Representação do dicionário com a senha mascarada.
        """
        return self.__repr__()

class CredentialsRepository:
    
    @staticmethod
    def _encrypt(text: str) -> str:
        """
        Usa a DPAPI do Windows para criptografar a string com base no usuário logado.
        
        Args:
            text (str): Texto a ser criptografado.
        Returns:
            str: Texto criptografado em hexadecimal.
        """
        if not text or not win32crypt:
            return text
        
        bytes_data = text.encode('utf-8')
        encrypted = win32crypt.CryptProtectData(bytes_data, None, None, None, None, 0)
        return binascii.hexlify(encrypted).decode('utf-8')

    @staticmethod
    def _decrypt(hex_text: str) -> str:
        """
        Desfaz a criptografia DPAPI se o usuário logado for o dono da credencial.

        Args:
            hex_text (str): Texto criptografado em hexadecimal.
        Returns:
            str: Texto descriptografado, ou o texto original se não puder ser descriptografado.
        """
        if not hex_text or not win32crypt:
            return hex_text
        
        try:
            encrypted = binascii.unhexlify(hex_text.encode('utf-8'))
            _, decrypted_data = win32crypt.CryptUnprotectData(encrypted, None, None, None, 0)
            return decrypted_data.decode('utf-8')
        except Exception:
            return hex_text

    @staticmethod
    def load() -> dict:
        """
        Lê as credenciais salvas no arquivo local e descriptografa a senha.
        

        Returns:
            dict: Dicionário com as credenciais {"usuario": str, "senha": str}
        """
        primary_path = Config.get_storage_path()
        paths = [primary_path]
        legacy_path = Config.get_legacy_storage_path()
        if legacy_path not in paths:
            paths.append(legacy_path)

        for path in paths:
            if os.path.exists(path):
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        data = json.load(f)
                        if "senha" in data:
                            data["senha"] = CredentialsRepository._decrypt(data["senha"])

                        # Migra automaticamente o arquivo antigo para a nova pasta 'credentials/'
                        if path != primary_path and not os.path.exists(primary_path):
                            try:
                                CredentialsRepository.save(
                                    data.get("usuario", ""), 
                                    data.get("senha", ""), 
                                    data.get("unidade", "")
                                )
                            except Exception:
                                pass

                        return data
                except Exception:
                    continue

        return {"usuario": "", "senha": "", "unidade": ""}

    @staticmethod
    def save(user: str, password: str, unidade: str):
        """
        Criptografa a senha e grava as credenciais no arquivo local.

        Args:
            user (str): Nome do usuário.
            password (str): Senha do usuário.
            unidade (str): Unidade do usuário.
        """
        path = Config.get_storage_path()
        secure_password = CredentialsRepository._encrypt(password)
        
        # Inclui a unidade no dicionário persistido
        data = {"usuario": user, "senha": secure_password, "unidade": unidade}
        
        try:
            with open(path, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except Exception as e:
            from src.core.logger import log
            log.error(f"Não foi possível salvar as credenciais locais: {e}")