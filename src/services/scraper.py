import http.client
import re
import socket
import time
import urllib.parse
from src.core.logger import log
from src.core.config import Config

class ScraperService:
    _cached_cast_devices: list[str] | None = None

    @staticmethod
    def _ensure_event_loop():
        import asyncio
        try:
            asyncio.get_running_loop()
        except RuntimeError:
            asyncio.set_event_loop(asyncio.new_event_loop())

    @staticmethod
    def _get_local_ipv4_addresses() -> list[str]:
        """
        Retorna todos os endereços IPv4 ativos das interfaces de rede da máquina.
        """
        ips = []
        try:
            ips = [ip for ip in socket.gethostbyname_ex(socket.gethostname())[2] if not ip.startswith("127.")]
        except Exception:
            pass
        if not ips:
            ips = ["0.0.0.0"]
        return ips

    @staticmethod
    def relay_mdns_for_chrome(duration_sec: float = 2.5):
        """
        Envia consultas mDNS (_googlecast._tcp.local) em todas as interfaces físicas e retransmite
        as respostas unicast para o grupo multicast 224.0.0.251:5353, acelerando a detecção pelo Chrome
        em máquinas com múltiplos adaptadores de rede (ex: Hyper-V / WSL).
        """
        mcast_grp = "224.0.0.251"
        mcast_port = 5353
        query_qu = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0b_googlecast\x04_tcp\x05local\x00\x00\x0c\x80\x01"
        query_qm = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0b_googlecast\x04_tcp\x05local\x00\x00\x0c\x00\x01"

        ips = ScraperService._get_local_ipv4_addresses()
        end_time = time.time() + duration_sec

        while time.time() < end_time:
            for ip in ips:
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                    s.bind((ip, 0))
                    if ip != "0.0.0.0":
                        s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))
                    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_LOOP, 1)
                    s.settimeout(0.12)
                    s.sendto(query_qu, (mcast_grp, mcast_port))
                    s.sendto(query_qm, (mcast_grp, mcast_port))
                    while True:
                        try:
                            data, _ = s.recvfrom(4096)
                            s.sendto(data, (mcast_grp, mcast_port))
                        except socket.timeout:
                            break
                    s.close()
                except Exception:
                    pass
            time.sleep(0.15)

    @staticmethod
    def fetch_cast_devices(force_scan: bool = False, timeout: float = 0.6) -> list[str]:
        """
        Descobre instantaneamente TVs / dispositivos Google Cast na rede local via pacotes UDP mDNS
        (_googlecast._tcp.local) em todas as interfaces de rede, sem precisar inicializar o navegador.

        Args:
            force_scan (bool): Se True, ignora o cache em memória e faz nova consulta mDNS.
            timeout (float): Tempo máximo de escuta em segundos (padrão: 0.6s).

        Returns:
            list[str]: Lista de nomes amigáveis (fn) das TVs encontradas.
        """
        if not force_scan and ScraperService._cached_cast_devices is not None:
            return ScraperService._cached_cast_devices

        t0 = time.time()
        mcast_grp = "224.0.0.251"
        mcast_port = 5353
        query_qu = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0b_googlecast\x04_tcp\x05local\x00\x00\x0c\x80\x01"
        query_qm = b"\x00\x00\x00\x00\x00\x01\x00\x00\x00\x00\x00\x00\x0b_googlecast\x04_tcp\x05local\x00\x00\x0c\x00\x01"

        ips = ScraperService._get_local_ipv4_addresses()
        socks: list[socket.socket] = []

        for ip in ips:
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM, socket.IPPROTO_UDP)
                s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
                s.bind((ip, 0))
                if ip != "0.0.0.0":
                    s.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_IF, socket.inet_aton(ip))
                s.setblocking(False)
                s.sendto(query_qu, (mcast_grp, mcast_port))
                s.sendto(query_qm, (mcast_grp, mcast_port))
                socks.append(s)
            except Exception:
                pass

        def _extract_friendly_names(packet: bytes, target_list: list[str]):
            pos = 0
            while True:
                idx = packet.find(b"fn=", pos)
                if idx <= 0:
                    break
                length = packet[idx - 1]
                if 3 < length < 128 and idx + length <= len(packet):
                    fn = packet[idx + 3 : idx + length].decode("utf-8", errors="ignore").strip()
                    if fn and fn not in target_list:
                        target_list.append(fn)
                pos = idx + 3

        devices: list[str] = []
        end_time = time.time() + timeout

        while time.time() < end_time:
            for s in socks:
                while True:
                    try:
                        data, _ = s.recvfrom(4096)
                        _extract_friendly_names(data, devices)
                    except (BlockingIOError, socket.error):
                        break
            if devices:
                time.sleep(0.08)
                for s in socks:
                    while True:
                        try:
                            data, _ = s.recvfrom(4096)
                            _extract_friendly_names(data, devices)
                        except (BlockingIOError, socket.error):
                            break
                break
            time.sleep(0.015)

        for s in socks:
            try:
                s.close()
            except Exception:
                pass

        ScraperService._cached_cast_devices = list(devices)
        log.info(f"Varredura rápida mDNS concluída em {time.time() - t0:.2f}s: {devices}")
        return devices

    @staticmethod
    def _fetch_units_fast_http(url: str) -> list[str]:
        """
        Extrai a lista de unidades diretamente da API Ajax do UniGUI (idspaiele.dll/HandleEvent)
        reutilizando uma única conexão HTTPS Keep-Alive, sem precisar abrir o navegador (~0.3s).
        """
        t0 = time.time()
        clean_url = url.rstrip("/")
        parsed = urllib.parse.urlsplit(clean_url)
        conn_cls = http.client.HTTPSConnection if parsed.scheme == "https" else http.client.HTTPConnection
        conn = conn_cls(parsed.netloc, timeout=8)

        try:
            base_path = parsed.path or "/"
            conn.request("GET", base_path, headers={"Connection": "keep-alive"})
            resp1 = conn.getresponse()
            html = resp1.read().decode("utf-8", errors="ignore")

            m_sid = re.search(r'_S_ID:\s*"([^"]+)"|FRM_([A-Za-z0-9_]+)', html)
            sid = (m_sid.group(1) or m_sid.group(2)) if m_sid else ""
            if not sid:
                return []

            m_obj = re.search(r"HandleEvent\?IsEvent=1&Obj=([A-Za-z0-9_]+)&Evt=data", html)
            obj_id = m_obj.group(1) if m_obj else "O43"

            query_path = f"{base_path}/HandleEvent?IsEvent=1&Obj={obj_id}&Evt=data&_S_ID={sid}&query=&page=1&start=0&limit=50"
            conn.request(
                "GET",
                query_path,
                headers={
                    "UniSessionId": sid,
                    "_S_ID": sid,
                    "X-Requested-With": "XMLHttpRequest",
                    "Connection": "close",
                },
            )
            resp2 = conn.getresponse()
            raw_data = resp2.read().decode("utf-8", errors="ignore")

            unidades = [m.group(1).strip() for m in re.finditer(r'"val"\s*:\s*"([^"]+)"', raw_data) if m.group(1).strip()]
            if unidades:
                log.info(f"Foram capturadas {len(unidades)} unidades via HTTP direto em {time.time() - t0:.2f}s.")
            return unidades
        finally:
            try:
                conn.close()
            except Exception:
                pass

    @staticmethod
    def fetch_units() -> list[str]:
        """
        Obtém as unidades disponíveis no painel. Tenta primeiro via requisição HTTP Keep-Alive direta
        ao endpoint do UniGUI (~0.3s) e utiliza o Playwright em modo headless apenas como fallback.
        
        Returns:
            list[str]: Lista de unidades capturadas ou vazia se houver erro.
        """
        url = Config.get_app_config().get("url")
        if not url:
            log.error("URL do painel não configurada.")
            return []

        # 1. Rota ultra-rápida via HTTP Keep-Alive direto na store ExtJS/UniGUI (sem abrir navegador)
        try:
            unidades = ScraperService._fetch_units_fast_http(url)
            if unidades:
                return unidades
        except Exception as fast_err:
            log.warning(f"Busca rápida HTTP falhou ({fast_err}), recorrendo ao fallback via Playwright...")

        # 2. Fallback via Playwright Headless caso a estrutura da página mude
        ScraperService._ensure_event_loop()
            
        unidades = []
        try:
            from playwright.sync_api import sync_playwright
            with sync_playwright() as p:
                browser_kwargs = {
                    "headless": True,
                    "args": [
                        "--disable-infobars",
                        "--no-sandbox",
                        "--disable-gpu",
                        "--disable-extensions"
                    ]
                }
                
                browser_executable_path = Config.get_browser_executable_path()
                if browser_executable_path:
                    browser_kwargs["executable_path"] = browser_executable_path
                    
                browser = p.chromium.launch(**browser_kwargs)
                context = browser.new_context()
                page = context.new_page()
                
                log.info(f"Acessando URL {url} para capturar unidades (fallback Playwright)...")
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                
                trigger_selector = "div#O3F_id-trigger-t1"
                page.wait_for_selector(trigger_selector, timeout=15000)
                page.click(trigger_selector)
                
                list_selector = "ul#O3F_id-picker-listEl li"
                page.wait_for_selector(list_selector, timeout=10000)
                
                li_elements = page.locator(list_selector).all()
                for li in li_elements:
                    text = li.inner_text().strip()
                    if text:
                        unidades.append(text)
                        
                browser.close()
                log.info(f"Foram capturadas {len(unidades)} unidades via fallback.")
        except Exception as e:
            log.error(f"Erro ao capturar unidades via web scraping: {e}")
            
        return unidades
