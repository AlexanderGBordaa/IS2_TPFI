import threading, socket, json
from typing import Dict

class ObserverRegistry:
    """Registro simple de subscriptores: UUID -> socket"""
    def __init__(self):
        self._subs: Dict[str, socket.socket] = {}
        self._lock = threading.Lock()

    def add(self, uuid: str, sock: socket.socket):
        with self._lock:
            # Si ya existe, cerramos la conexión anterior
            old = self._subs.get(uuid)
            if old and old is not sock:
                try:
                    old.shutdown(1)
                except Exception:
                    pass
                try:
                    old.close()
                except Exception:
                    pass
            self._subs[uuid] = sock

    def remove(self, uuid: str):
        with self._lock:
            self._subs.pop(uuid, None)

    def broadcast(self, payload: dict, send_fn):
        # copia para iterar sin bloquear
        with self._lock:
            items = list(self._subs.items())
        dead = []
        for uuid, sock in items:
            try:
                send_fn(sock, payload)
            except Exception:
                dead.append(uuid)
        for uuid in dead:
            self.remove(uuid)
