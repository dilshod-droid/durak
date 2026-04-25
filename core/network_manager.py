"""
core/network_manager.py — Tarmoq boshqaruvchisi
Local Wi-Fi orqali o'yinchilarni topish va bog'lanishni ta'minlaydi.

Tuzatishlar:
  - _tcp_reader: on_data_received Clock.schedule_once orqali UI threadga o'tkazildi (thread-safety)
  - _udp_broadcaster/_udp_receiver: aniq Exception loglanadi
  - connect_to_host: timeout qo'shildi
  - stop_all: thread-safe to'xtatish
  - on_connected callback ham Clock.schedule_once orqali
"""
import socket
import threading
import json
import time
import logging
from typing import Optional, Callable, Dict, Any

logger = logging.getLogger(__name__)

UDP_PORT  = 55555
TCP_PORT  = 55556
MAGIC_STR = "DURAK_ONLINE_FIND"
CONNECT_TIMEOUT = 5.0   # TCP ulanish kutish vaqti (soniya)


class NetworkManager:
    _instance = None

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self.mode: str = 'none'  # 'host' | 'join' | 'none'
        self.peer_ip: Optional[str] = None
        self.peer_name: str = "Raqib"

        # TCP connection
        self.socket: Optional[socket.socket] = None
        self.is_connected = False

        # Callbacks (UI dan o'rnatiladi)
        self.on_peer_found:    Optional[Callable[[str, str], None]] = None
        self.on_connected:     Optional[Callable[[], None]] = None
        self.on_disconnected:  Optional[Callable[[], None]] = None
        self.on_data_received: Optional[Callable[[Dict[str, Any]], None]] = None

        self._stop_threads = False
        self._threads = []
        self._lock = threading.Lock()   # socket kirish uchun lock

    # ─── DISCOVERY (UDP) ───────────────────────────────────────────────────────
    def start_hosting(self, player_name: str):
        """Host rejimini boshlash: UDP broadcast va TCP serverni yoqish"""
        self.mode = 'host'
        self._stop_threads = False

        t_udp = threading.Thread(
            target=self._udp_broadcaster, args=(player_name,), daemon=True, name="udp-broadcast"
        )
        t_tcp = threading.Thread(
            target=self._tcp_server_listener, daemon=True, name="tcp-server"
        )
        t_udp.start()
        t_tcp.start()
        self._threads = [t_udp, t_tcp]

    def start_searching(self):
        """Join rejimi: Tarmoqda hostlarni qidirish (UDP Receiver)"""
        self.mode = 'join'
        self._stop_threads = False
        t_udp = threading.Thread(
            target=self._udp_receiver, daemon=True, name="udp-receiver"
        )
        t_udp.start()
        self._threads = [t_udp]

    def stop_all(self):
        """Barcha threadlarni va ulanishlarni to'xtatish"""
        self._stop_threads = True
        self.is_connected = False
        with self._lock:
            if self.socket:
                try:
                    self.socket.shutdown(socket.SHUT_RDWR)
                    self.socket.close()
                except Exception:
                    pass
                self.socket = None

    # ─── MA'LUMOT YUBORISH ────────────────────────────────────────────────────
    def send_data(self, data: Dict[str, Any]):
        """TCP orqali JSON ma'lumot yuborish (thread-safe)"""
        with self._lock:
            if self.socket and self.is_connected:
                try:
                    msg = json.dumps(data) + "\n"
                    self.socket.sendall(msg.encode('utf-8'))
                except Exception as e:
                    logger.error(f"[NET] send_data xatosi: {e}")
                    self._handle_disconnect()

    def _handle_disconnect(self):
        """Ulanish uzilganda — UI threadga xabar berish"""
        was_connected = self.is_connected
        self.is_connected = False
        if was_connected and self.on_disconnected:
            try:
                from kivy.clock import Clock
                Clock.schedule_once(lambda dt: self.on_disconnected())
            except Exception as e:
                logger.error(f"[NET] disconnect callback xatosi: {e}")

    # ─── INTERNAL UDP ─────────────────────────────────────────────────────────
    def _udp_broadcaster(self, name: str):
        """Host: UDP broadcast orqali o'zini e'lon qiladi"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
            data = f"{MAGIC_STR}|{name}".encode('utf-8')

            while not self._stop_threads and not self.is_connected:
                try:
                    sock.sendto(data, ('<broadcast>', UDP_PORT))
                    time.sleep(2.0)
                except Exception as e:
                    logger.warning(f"[NET] UDP broadcast xatosi: {e}")
                    break
        except Exception as e:
            logger.error(f"[NET] UDP broadcaster yaratilmadi: {e}")
        finally:
            try:
                sock.close()
            except Exception:
                pass

    def _udp_receiver(self):
        """Joiner: UDP orqali hostlarni eshitadi"""
        sock = None
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            sock.bind(('', UDP_PORT))
            sock.settimeout(1.0)

            while not self._stop_threads and not self.is_connected:
                try:
                    data, addr = sock.recvfrom(1024)
                    msg = data.decode('utf-8')
                    if msg.startswith(MAGIC_STR):
                        parts = msg.split('|', 1)
                        if len(parts) == 2:
                            host_name = parts[1]
                            self.peer_ip   = addr[0]
                            self.peer_name = host_name
                            # UI threadga xabar berish
                            if self.on_peer_found:
                                try:
                                    from kivy.clock import Clock
                                    ip, nm = self.peer_ip, self.peer_name
                                    Clock.schedule_once(
                                        lambda dt, _ip=ip, _nm=nm: self.on_peer_found(_ip, _nm)
                                    )
                                except Exception:
                                    pass
                            # Hostga ulanish
                            self.connect_to_host(self.peer_ip)
                            break
                except socket.timeout:
                    continue
                except Exception as e:
                    logger.error(f"[NET] UDP receiver xatosi: {e}")
                    break
        except Exception as e:
            logger.error(f"[NET] UDP receiver socket xatosi: {e}")
        finally:
            if sock:
                try:
                    sock.close()
                except Exception:
                    pass

    # ─── INTERNAL TCP ─────────────────────────────────────────────────────────
    def _tcp_server_listener(self):
        """Host: Client ulanishini kutadi"""
        srv = None
        try:
            srv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            srv.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            srv.bind(('', TCP_PORT))
            srv.listen(1)
            srv.settimeout(1.0)

            while not self._stop_threads and not self.is_connected:
                try:
                    conn, addr = srv.accept()
                    with self._lock:
                        self.socket = conn
                    self.is_connected = True
                    self.peer_ip = addr[0]
                    logger.info(f"[NET] Client ulandi: {addr[0]}")
                    # UI threadga xabar berish
                    if self.on_connected:
                        try:
                            from kivy.clock import Clock
                            Clock.schedule_once(lambda dt: self.on_connected())
                        except Exception:
                            pass
                    self._start_reader_thread()
                except socket.timeout:
                    continue
                except Exception as e:
                    if not self._stop_threads:
                        logger.error(f"[NET] TCP server xatosi: {e}")
                    break
        except Exception as e:
            logger.error(f"[NET] TCP server socket xatosi: {e}")
        finally:
            if srv:
                try:
                    srv.close()
                except Exception:
                    pass

    def connect_to_host(self, ip: str):
        """Joiner: Hostga TCP orqali ulanadi"""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(CONNECT_TIMEOUT)
            sock.connect((ip, TCP_PORT))
            sock.settimeout(None)   # Ulanganidan keyin blocking mode
            with self._lock:
                self.socket = sock
            self.is_connected = True
            logger.info(f"[NET] Hostga ulandi: {ip}")
            # UI threadga xabar berish
            if self.on_connected:
                try:
                    from kivy.clock import Clock
                    Clock.schedule_once(lambda dt: self.on_connected())
                except Exception:
                    pass
            self._start_reader_thread()
        except Exception as e:
            logger.error(f"[NET] Hostga ulanib bo'lmadi ({ip}): {e}")

    def _start_reader_thread(self):
        t = threading.Thread(target=self._tcp_reader, daemon=True, name="tcp-reader")
        t.start()

    def _tcp_reader(self):
        """Kelayotgan JSON paketlarni o'qiydi va UI threadga jo'natadi"""
        try:
            with self._lock:
                sock = self.socket
            if not sock:
                return
            f = sock.makefile('r', encoding='utf-8')
            while not self._stop_threads and self.is_connected:
                try:
                    line = f.readline()
                    if not line:
                        break
                    data = json.loads(line.strip())
                    # ✅ UI thread-safe: Kivy Clock orqali chaqiramiz
                    if self.on_data_received:
                        try:
                            from kivy.clock import Clock
                            Clock.schedule_once(
                                lambda dt, d=data: self.on_data_received(d)
                            )
                        except Exception:
                            pass
                except json.JSONDecodeError as e:
                    logger.warning(f"[NET] JSON parse xatosi: {e}")
                    continue
                except Exception as e:
                    if not self._stop_threads:
                        logger.error(f"[NET] TCP reader xatosi: {e}")
                    break
        except Exception as e:
            logger.error(f"[NET] TCP reader start xatosi: {e}")
        finally:
            self._handle_disconnect()
