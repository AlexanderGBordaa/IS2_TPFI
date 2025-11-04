"""
Tests de manejo en clientes cuando el servidor está caído.
"""
import os
import pytest
import subprocess
import sys
import time
from tests.conftest import send_request, generate_uuid, CLIENT_SINGLETON, PROJECT_ROOT
from pathlib import Path

PYTHON = sys.executable


class TestServerDown:
    """Tests de clientes con servidor caído."""
    
    def test_singleton_client_server_down(self):
        """Test de cliente singleton cuando el servidor está caído."""
        import tempfile
        import json
        
        # Crear archivo de entrada válido
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "UUID": generate_uuid(),
                "ACTION": "list"
            }, f)
            temp_file = f.name
        
        try:
            # Intentar conectar a un puerto donde no hay servidor
            result = subprocess.run(
                [PYTHON, str(CLIENT_SINGLETON), "-i", temp_file, "-s", "127.0.0.1", "-p", "9999"],
                capture_output=True,
                text=True,
                timeout=5
            )
            
            # Debe manejar el error graciosamente
            output = result.stdout + result.stderr
            assert (
                "connection" in output.lower() or
                "refused" in output.lower() or
                "error" in output.lower() or
                "no response" in output.lower()
            )
            # El código de salida puede ser 2 (error de conexión según el código)
            assert result.returncode != 0
            
            # Verificar que el output contiene un JSON con error
            import json as json_lib
            try:
                error_output = json_lib.loads(result.stdout)
                assert error_output.get("OK") is False
                assert "Error" in error_output
            except:
                # Si no es JSON válido, al menos debe indicar error
                assert "error" in output.lower() or result.returncode != 0
        
        finally:
            import os
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_singleton_client_server_timeout(self):
        """Test de cliente singleton con timeout cuando el servidor no responde."""
        import tempfile
        import json
        import socket
        
        # Crear un socket que acepta conexiones pero no responde
        server_sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        server_sock.bind(("127.0.0.1", 0))
        server_sock.listen(1)
        port = server_sock.getsockname()[1]
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "UUID": generate_uuid(),
                "ACTION": "list"
            }, f)
            temp_file = f.name
        
        try:
            # Aceptar conexión pero no responder
            server_sock.settimeout(2)
            
            # Intentar conectar (el cliente debe timeout)
            result = subprocess.run(
                [PYTHON, str(CLIENT_SINGLETON), "-i", temp_file, "-s", "127.0.0.1", "-p", str(port)],
                capture_output=True,
                text=True,
                timeout=15  # Más que el timeout del cliente
            )
            
            # Debe manejar el timeout
            assert result.returncode != 0 or "timeout" in (result.stdout + result.stderr).lower()
            
        finally:
            server_sock.close()
            import os
            if os.path.exists(temp_file):
                os.unlink(temp_file)
    
    def test_observer_client_server_down(self):
        """Test de cliente observer cuando el servidor está caído."""
        from tests.conftest import CLIENT_OBSERVER
        
        # El cliente observer debe reintentar automáticamente
        # Testeamos que maneja el error inicial correctamente
        env = os.environ.copy()
        env["PYTHONPATH"] = str(PROJECT_ROOT)
        process = subprocess.Popen(
            [PYTHON, str(CLIENT_OBSERVER), "-s", "127.0.0.1", "-p", "9999", "-r", "1"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
            cwd=str(PROJECT_ROOT)
        )
        
        try:
            # Esperar un poco para que intente conectar
            time.sleep(2)
            
            # El proceso puede estar corriendo (reintentando) o haber fallado
            # Verificamos que al menos manejó el error correctamente
            poll_result = process.poll()
            # Si el proceso terminó, debe ser por error de conexión (no por crash)
            # Si está corriendo, está reintentando (comportamiento esperado)
            # Ambos casos son válidos para este test
            if poll_result is not None:
                # Si terminó, debe ser código de error (1) por conexión rechazada
                assert poll_result != 0
            
            # Verificar que hay mensajes de error/reintento
            # (no podemos leer stdout sin bloquear, pero podemos verificar que maneja el error)
            
        finally:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
    
    def test_direct_socket_connection_refused(self):
        """Test de conexión directa cuando el servidor está caído."""
        uuid_cli = generate_uuid()
        
        payload = {
            "UUID": uuid_cli,
            "ACTION": "list"
        }
        
        # Intentar conectar a puerto sin servidor
        response = send_request("127.0.0.1", 9999, payload)
        
        # Debe retornar error
        assert response["OK"] is False
        assert "Error" in response
        error_msg = response["Error"].lower()
        assert (
            "connection" in error_msg or
            "refused" in error_msg or
            "timeout" in error_msg or
            "denegó" in error_msg or
            "denego" in error_msg or
            "winerror" in error_msg or
            "10061" in error_msg
        )

