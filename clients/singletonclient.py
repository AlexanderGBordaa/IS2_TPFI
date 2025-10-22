import argparse, json, socket, uuid
from common.logging_setup import setup
from common.net import send_json, recv_json

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--input", required=True, help="input JSON file")
    ap.add_argument("-o", "--output", help="output JSON file")
    ap.add_argument("-s", "--server", default="127.0.0.1")
    ap.add_argument("-p", "--port", type=int, default=8080)
    ap.add_argument("-v", "--verbose", action="store_true")
    args = ap.parse_args()
    log = setup(args.verbose)

    # cargar request base
    with open(args.input, "r", encoding="utf-8") as f:
        req = json.load(f)

    # siempre asignar un UUID random nuevo
    req["UUID"] = str(uuid.uuid4())

    with socket.create_connection((args.server, args.port)) as sock:
        send_json(sock, req)
        resp = recv_json(sock)

    out = json.dumps(resp, ensure_ascii=False, indent=2)
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(out)
    print(out)

if __name__ == "__main__":
    main()
