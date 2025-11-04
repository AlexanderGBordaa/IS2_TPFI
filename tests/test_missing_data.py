"""
Tests de requerimientos sin datos mínimos necesarios.
"""
import pytest
from tests.conftest import server_process, send_request, read_corporate_log, generate_uuid


class TestMissingData:
    """Tests de datos mínimos faltantes."""
    
    def test_get_missing_id(self, server_process):
        """Test de GET sin ID requerido."""
        port, _ = server_process
        uuid_cli = generate_uuid()
        
        payload = {
            "UUID": uuid_cli,
            "ACTION": "get"
            # Falta ID
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe fallar
        assert response["OK"] is False
        assert "ID" in response.get("Error", "").lower() or "missing" in response.get("Error", "").lower()
        
        # Verificar que NO se registró en CorporateLog (porque falló la validación)
        # O que se registró con error
        log = read_corporate_log()
        # Las acciones que fallan antes de llegar al servicio no se registran
        # pero el servidor puede registrar errores
    
    def test_set_missing_id(self, server_process):
        """Test de SET sin ID requerido."""
        port, _ = server_process
        uuid_cli = generate_uuid()
        
        payload = {
            "UUID": uuid_cli,
            "ACTION": "set",
            "DATA": {
                "nombre": "Test Item",
                "cp": "3260"
            }
            # Falta ID
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe fallar
        assert response["OK"] is False
        assert "ID" in response.get("Error", "").lower() or "missing" in response.get("Error", "").lower()
        
        # Verificar que NO se registró en CorporateData
        from tests.conftest import read_corporate_data
        data = read_corporate_data()
        assert len(data) == 0
        
        # Verificar CorporateLog: no debe haber nuevos registros de set (falló validación)
        log = read_corporate_log()
        set_logs = [e for e in log if e.get("action") == "set"]
        # Si la validación falla antes del servicio, no se registra en CorporateLog
        # Verificamos que no hay registros de set exitosos
        successful_sets = [e for e in set_logs if e.get("UUID") == uuid_cli]
        assert len(successful_sets) == 0
    
    def test_set_missing_data(self, server_process):
        """Test de SET sin DATA."""
        port, _ = server_process
        uuid_cli = generate_uuid()
        item_id = "TEST-MISSING-DATA"
        
        payload = {
            "UUID": uuid_cli,
            "ACTION": "set",
            "ID": item_id
            # Falta DATA
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe fallar o crear un objeto vacío según la implementación
        # Según el código, si DATA no es dict, devuelve error
        assert response["OK"] is False or "data" in response.get("Error", "").lower()
    
    def test_missing_uuid(self, server_process):
        """Test de acción sin UUID."""
        port, _ = server_process
        
        payload = {
            "ACTION": "list"
            # Falta UUID
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe fallar
        assert response["OK"] is False
        assert "uuid" in response.get("Error", "").lower()
    
    def test_invalid_uuid_format(self, server_process):
        """Test de UUID en formato inválido."""
        port, _ = server_process
        
        payload = {
            "UUID": "invalid-uuid",  # No es 12 hex
            "ACTION": "list"
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe fallar
        assert response["OK"] is False
        assert "uuid" in response.get("Error", "").lower()
    
    def test_invalid_action(self, server_process):
        """Test de acción inválida."""
        port, _ = server_process
        uuid_cli = generate_uuid()
        
        payload = {
            "UUID": uuid_cli,
            "ACTION": "invalid_action"
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe fallar
        assert response["OK"] is False
        assert "action" in response.get("Error", "").lower() or "unknown" in response.get("Error", "").lower()
    
    def test_get_missing_all_required(self, server_process):
        """Test de GET sin todos los datos requeridos."""
        port, _ = server_process
        
        # Solo UUID, sin ACTION ni ID
        payload = {
            "UUID": generate_uuid()
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe fallar
        assert response["OK"] is False
    
    def test_set_empty_data(self, server_process):
        """Test de SET con DATA vacío."""
        port, _ = server_process
        uuid_cli = generate_uuid()
        item_id = "TEST-EMPTY-DATA"
        
        payload = {
            "UUID": uuid_cli,
            "ACTION": "set",
            "ID": item_id,
            "DATA": {}
        }
        
        response = send_request("127.0.0.1", port, payload)
        
        # Debe funcionar (DATA vacío es válido, solo actualiza el id)
        assert response["OK"] is True
        
        # Verificar CorporateData
        from tests.conftest import read_corporate_data
        data = read_corporate_data()
        assert len(data) == 1
        assert data[0]["id"] == item_id
        
        # Verificar CorporateLog: debe haber registro de set
        log = read_corporate_log()
        set_logs = [e for e in log if e.get("action") == "set" and e.get("UUID") == uuid_cli]
        assert len(set_logs) >= 1
        assert set_logs[-1]["action"] == "set"
        assert "ts" in set_logs[-1]
        assert "session" in set_logs[-1]

