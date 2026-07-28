"""Prueba de conexión estándar del conector qradar.

Firma estándar Ruvic: def test_connection() -> tuple[bool, str]
- Lee la configuración EXCLUSIVAMENTE de las env vars RUVIC_QRADAR_*.
- Nunca lanza excepciones; retorna (ok, mensaje).

Ejecutable también como script para pruebas locales:
    python test_connection.py
"""

from __future__ import annotations


def test_connection() -> tuple[bool, str]:
    """Verifica el SEC token listando 1 ofensa."""
    try:
        from ruvic_qradar_connector import (
            QRadarAuthError,
            QRadarClient,
            QRadarDataError,
            QRadarNetworkError,
        )
    except ImportError:
        return (
            False,
            "La librería ruvic-qradar-connector no está instalada. "
            "Instala con: pip install git+https://github.com/tu-org/"
            "conector-qradar.git#subdirectory=lib",
        )

    try:
        client = QRadarClient()  # valida config
    except ValueError as exc:
        return False, str(exc)

    try:
        client.ping()
    except QRadarAuthError as exc:
        return False, f"Autenticación fallida: {exc}"
    except QRadarNetworkError as exc:
        return False, f"Error de red: {exc}"
    except QRadarDataError as exc:
        return False, f"Error de datos: {exc}"
    except Exception as exc:  # red de seguridad: jamás propagar
        return False, f"Error inesperado: {exc}"

    return True, f"Conexión exitosa a {client.config.console_host}"


if __name__ == "__main__":
    ok, message = test_connection()
    print(f"{'OK' if ok else 'FALLO'}: {message}")
    raise SystemExit(0 if ok else 1)
