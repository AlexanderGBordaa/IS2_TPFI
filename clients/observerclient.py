import argparse, json, socket, time, uuid, sys
from common.logging_setup import setup
from common.net import send_json, recv_json

def run_once(server, port, out_path, log):
    with socket.create_connection((server, port)) as sock:
        req = {"UUID": str(uuid.uuid4()), "ACTION": "subscribe"}
        send_json(sock, req)
        # primer acuse
        first = recv_json(sock)
        if first:
            s = json.dumps(first, ensure_ascii=False)
            log.info("Subscribed: %s", s)
        while True:
            msg = recv_json(sock)
            if msg is None:
                # socket cerrado
                return
            line = json.dumps(msg, ensure_ascii=False)
            if out_path:
                with open(out_path, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            print(line)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-s","--server", default="127.0.0.1")
    ap.add_argument("-p","--port", type=int, default=8080)
    ap.add_argument("-o","--output", help="output file (append)")
    ap.add_argument("-r","--retry", type=int, default=30, help="reintento (segundos)")
    ap.add_argument("-v","--verbose", action="store_true")
    args = ap.parse_args()
    log = setup(args.verbose)

    while True:
        try:
            run_once(args.server, args.port, args.output, log)
        except Exception as e:
            log.warning("Conexión caída: %s. Reintentando en %ss...", e, args.retry)
            time.sleep(args.retry)

if __name__ == "__main__":
    main()
