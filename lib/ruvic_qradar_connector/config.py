"""Configuración del conector leída desde variables de entorno.

Convención de la plataforma: cada campo del formulario de configuración
llega como variable de entorno {ENV_PREFIX}{CAMPO} en mayúsculas.
Para este conector el prefijo es RUVIC_QRADAR_.

QRadar es siempre una instalación on-premise del cliente — no existe un
endpoint SaaS compartido, así que `console_host` es obligatorio y varía
por cliente.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

ENV_PREFIX = "RUVIC_QRADAR_"

_DEFAULT_API_VERSION = "20.0"


@dataclass(frozen=True)
class QRadarConfig:
    """Parámetros de conexión a una consola de IBM QRadar."""

    console_host: str
    sec_token: str
    api_version: str = _DEFAULT_API_VERSION
    verify_ssl: bool = True
    timeout: int = 30

    @classmethod
    def from_env(cls) -> "QRadarConfig":
        """Construye la configuración desde las variables RUVIC_QRADAR_*.

        Raises:
            ValueError: si falta CONSOLE_HOST o SEC_TOKEN.
        """
        console_host = os.environ.get(f"{ENV_PREFIX}CONSOLE_HOST", "").strip()
        sec_token = os.environ.get(f"{ENV_PREFIX}SEC_TOKEN", "").strip()

        missing = [
            name for name, val in (
                (f"{ENV_PREFIX}CONSOLE_HOST", console_host),
                (f"{ENV_PREFIX}SEC_TOKEN", sec_token),
            ) if not val
        ]
        if missing:
            raise ValueError(
                "Faltan variables de entorno del conector qradar: "
                + ", ".join(missing)
                + ". Configura el conector en Settings → Conectores."
            )
        if not (console_host.startswith("https://") or console_host.startswith("http://")):
            raise ValueError(
                f"{ENV_PREFIX}CONSOLE_HOST debe incluir el esquema (https:// o http://): {console_host!r}"
            )

        verify_ssl_raw = os.environ.get(f"{ENV_PREFIX}VERIFY_SSL", "true").strip().lower()

        return cls(
            console_host=console_host.rstrip("/"),
            sec_token=sec_token,
            api_version=os.environ.get(f"{ENV_PREFIX}API_VERSION", "").strip() or _DEFAULT_API_VERSION,
            verify_ssl=verify_ssl_raw not in ("false", "0", "no"),
            timeout=int(os.environ.get(f"{ENV_PREFIX}REQUEST_TIMEOUT", "30")),
        )
