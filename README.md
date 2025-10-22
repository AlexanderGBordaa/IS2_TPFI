# IS2 TPFI – Proxy / Singleton / Observer (Python)

Este proyecto implementa los tres ejecutables requeridos:

- `clients/singletonclient.py`
- `clients/observerclient.py`
- `server/singletonproxyobserver.py`

cumpliendo con **Proxy**, **Singleton** (acceso a tablas `CorporateData` y `CorporateLog`) y **Observer** (subscripciones con notificaciones).

## Requisitos

- Python 3.10+
- (Opcional) `boto3` si utilizarás AWS DynamoDB real.
- Variables de entorno AWS estándar (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_DEFAULT_REGION`).

> Para ejecutar sin AWS, puedes usar el modo **mock** exportando `MOCK_DB=1`. En ese modo se persiste en `mock_db/*.json`.

## Ejecución

### Servidor
```bash
python server/singletonproxyobserver.py -p 8080 -v
```

### Cliente (get/set/list)
```bash
python clients/singletonclient.py -i input.json -o output.json -s 127.0.0.1 -p 8080 -v
```

Ejemplos de `input.json`:
```json
{ "UUID":"<uuid4>", "ACTION":"get", "ID":"UADER-FCyT-IS2" }
```
```json
{ "UUID":"<uuid4>", "ACTION":"list" }
```
```json
{
  "UUID":"<uuid4>",
  "ACTION":"set",
  "DATA": {
    "id": "UADER-FCyT-IS2",
    "cp": "3260",
    "CUIT": "30-70925411-8",
    "domicilio": "25 de Mayo 385-1P",
    "idreq": "473",
    "idSeq": "1146",
    "localidad": "Concepción del Uruguay",
    "provincia": "Entre Rios",
    "sede": "FCyT",
    "seqID": "23",
    "telefono": "03442 43-1442",
    "web": "http://www.uader.edu.ar"
  }
}
```

### Observer
```bash
python clients/observerclient.py -s 127.0.0.1 -p 8080 -o observer_out.json -v
```

## Framing del protocolo
Mensajes **JSON** con *prefijo de longitud* de 4 bytes **big‑endian** para evitar pegado/fragmentación de tramas.

## Tests rápidos (mock)
En una terminal:
```bash
export MOCK_DB=1
python server/singletonproxyobserver.py -p 8080 -v
```
En otra:
```bash
python clients/observerclient.py -p 8080 -o /mnt/data/observer.json -v
```
En otra:
```bash
python clients/singletonclient.py -i samples/set.json -p 8080 -v
python clients/singletonclient.py -i samples/get.json -p 8080 -v
python clients/singletonclient.py -i samples/list.json -p 8080 -v
```

## Estructura
- `common/net.py`: send/recv con longitud 4 bytes big endian.
- `common/logging_setup.py`: logging con `-v`.
- `storage/adapter.py`: Singleton para `CorporateData` y `CorporateLog` con backend AWS o mock JSON.
- `server/observer.py`: registro de subscriptores (Observer pattern).
- `server/singletonproxyobserver.py`: servidor TCP (proxy) + uso de Singletons + Observer.
- `clients/singletonclient.py`: CLI para get/set/list.
- `clients/observerclient.py`: CLI para subscribe.
- `samples/*.json`: ejemplos.
