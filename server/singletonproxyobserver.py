import argparse, socket, threading, json, uuid, time, sys
from common.logging_setup import setup
from common.net import send_json, recv_json
from storage.adapter import CorporateData, CorporateLog
from server.observer import ObserverRegistry


def handle_client(conn, addr, log, data_db, log_db, observers):
    req = None
    try:
        req = recv_json(conn)
        if not req:
            return

        action = (req.get("ACTION") or "").strip().lower()
        log.debug(f"RAW request: {req}")
        log.debug(f"ACTION interpretada: '{action}'")

        uuid_cli = req.get("UUID") or str(uuid.uuid4())
        session = str(uuid.uuid4())
        now = int(time.time() * 1000)

        log.debug(f"Request from {addr}: {req}")

        if action == "subscribe":
            observers.add(uuid_cli, conn)
            log_db.append(
                {"UUID": uuid_cli, "session": session, "action": "subscribe", "ts": now}
            )
            send_json(conn, {"OK": True, "ACTION": "subscribe"})
            # mantener viva la conexión
            while True:
                time.sleep(3600)
            return

        elif action == "get":
            id_ = req.get("ID")
            log_db.append(
                {"UUID": uuid_cli, "session": session, "action": "get", "id": id_, "ts": now}
            )
            item = data_db.get(id_) if id_ else None
            if item:
                send_json(conn, {"OK": True, "DATA": item})
            else:
                send_json(conn, {"OK": False, "Error": "NotFound"})
            return

        elif action == "list":
            log_db.append(
                {"UUID": uuid_cli, "session": session, "action": "list", "ts": now}
            )
            items = data_db.list_all()
            send_json(conn, {"OK": True, "DATA": items})
            return

        elif action == "set":
            payload = req.get("DATA") or {}
            if not isinstance(payload, dict) or not payload.get("id"):
                send_json(conn, {"OK": False, "Error": "Missing id in DATA"})
                return
            log_db.append(
                {"UUID": uuid_cli, "session": session, "action": "set", "id": payload.get("id"), "ts": now}
            )
            saved = data_db.upsert(payload)
            resp = {"OK": True, "DATA": saved}
            send_json(conn, resp)
            # notificar a subscriptores
            observers.broadcast({"ACTION": "change", "DATA": saved}, send_json)
            return

        else:
            send_json(conn, {"OK": False, "Error": f"Unknown ACTION '{req.get('ACTION')}'"})

    except Exception as e:
        log.error(f"Error handling client {addr}: {e}")
        try:
            send_json(conn, {"OK": False, "Error": f"{type(e).__name__}: {e}"})
        except Exception:
            pass
    finally:
        try:
            if req and (req.get("ACTION", "").strip().lower() == "subscribe"):
                return  # conexión viva
            conn.close()
        except Exception:
            pass


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-p", "--port", type=int, default=8080)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    log = setup(args.verbose)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    s.bind(("", args.port))
    s.listen(128)
    log.info(f"Server listening on *:{args.port}")

    data_db = CorporateData()
    log_db = CorporateLog()
    observers = ObserverRegistry()

    try:
        while True:
            conn, addr = s.accept()
            t = threading.Thread(
                target=handle_client,
                args=(conn, addr, log, data_db, log_db, observers),
                daemon=True,
            )
            t.start()
    except KeyboardInterrupt:
        log.info("Shutting down by Ctrl+C...")
    finally:
        try:
            s.close()
        except Exception:
            pass
        sys.exit(0)


if __name__ == "__main__":
    main()
