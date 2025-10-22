import os, json, threading, time
from typing import Any, Dict, List, Optional
try:
    import boto3  # type: ignore
except Exception:  # boto3 opcional
    boto3 = None

# 🔽 Añadido: para normalizar Decimals de DynamoDB
try:
    from decimal import Decimal
except Exception:
    Decimal = None  # fallback por si acaso

_MOCK = os.getenv("MOCK_DB") == "1"

def _to_native(obj):
    """
    Convierte recursivamente:
      - Decimal -> int si es entero, sino float
      - list/dict -> procesa elementos
      - otros tipos -> igual
    """
    if Decimal is not None and isinstance(obj, Decimal):
        # si es entero (ej. Decimal('5')), devolvemos int; sino float
        return int(obj) if obj % 1 == 0 else float(obj)
    if isinstance(obj, list):
        return [_to_native(x) for x in obj]
    if isinstance(obj, dict):
        return {k: _to_native(v) for k, v in obj.items()}
    return obj


class _Singleton(type):
    _instances = {}
    _lock = threading.Lock()
    def __call__(cls, *args, **kwargs):
        with cls._lock:
            if cls not in cls._instances:
                cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]


class CorporateData(metaclass=_Singleton):
    def __init__(self):
        if _MOCK or boto3 is None:
            self.path = os.path.join(os.path.dirname(__file__), "..", "mock_db", "corporate_data.json")
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            if not os.path.exists(self.path):
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump([], f)
            self.backend = "mock"
        else:
            self.dynamodb = boto3.resource("dynamodb")
            self.table = self.dynamodb.Table("CorporateData")
            self.backend = "aws"

    def get(self, id_: str) -> Optional[Dict[str, Any]]:
        if self.backend == "mock":
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            for item in data:
                if item.get("id") == id_:
                    return item
            return None
        resp = self.table.get_item(Key={"id": id_})
        item = resp.get("Item")
        return _to_native(item) if item is not None else None  # 🔽 normalizamos

    def list_all(self) -> List[Dict[str, Any]]:
        if self.backend == "mock":
            with open(self.path, "r", encoding="utf-8") as f:
                return json.load(f)
        items: List[Dict[str, Any]] = []
        scan_kwargs: Dict[str, Any] = {}
        while True:
            resp = self.table.scan(**scan_kwargs)
            items.extend(resp.get("Items", []))
            if "LastEvaluatedKey" in resp:
                scan_kwargs["ExclusiveStartKey"] = resp["LastEvaluatedKey"]
            else:
                break
        return _to_native(items)  # 🔽 normalizamos

    def upsert(self, item: Dict[str, Any]) -> Dict[str, Any]:
        if self.backend == "mock":
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            existing = None
            for i, it in enumerate(data):
                if it.get("id") == item.get("id"):
                    existing = i
                    break
            if existing is None:
                data.append(item)
            else:
                data[existing].update(item)
                item = data[existing]
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return item

        # 🔹 AWS: merge parcial en vez de reemplazo total
        existing = self.get(item["id"])
        if existing:
            merged = dict(existing)
            merged.update(item)  # pisa solo lo que mandaste
            self.table.put_item(Item=merged)
            return merged
        else:
            # no existía: inserción completa
            self.table.put_item(Item=item)
            return item


class CorporateLog(metaclass=_Singleton):
    def __init__(self):
        if _MOCK or boto3 is None:
            self.path = os.path.join(os.path.dirname(__file__), "..", "mock_db", "corporate_log.json")
            os.makedirs(os.path.dirname(self.path), exist_ok=True)
            if not os.path.exists(self.path):
                with open(self.path, "w", encoding="utf-8") as f:
                    json.dump([], f)
            self.backend = "mock"
        else:
            self.dynamodb = boto3.resource("dynamodb")
            self.table = self.dynamodb.Table("CorporateLog")
            self.backend = "aws"

    def append(self, record: Dict[str, Any]) -> None:
        record = dict(record)
        record["ts"] = record.get("ts") or int(time.time() * 1000)
        if self.backend == "mock":
            with open(self.path, "r", encoding="utf-8") as f:
                data = json.load(f)
            data.append(record)
            with open(self.path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            return
        # Compatibilidad: si la tabla del profe usa PK 'id', la completamos
        if "id" not in record:
            record["id"] = str(record["ts"])
        self.table.put_item(Item=record)
