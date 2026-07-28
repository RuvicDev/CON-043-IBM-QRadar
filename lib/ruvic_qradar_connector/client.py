"""Cliente para gestionar ofensas en IBM QRadar.

Capacidades:
- list_offenses():         listar ofensas, con filtro opcional.
- get_offense_detail():    consultar el detalle completo de una ofensa.
- update_offense_status(): actualizar el estado de una ofensa.

Autenticación: SEC token (Authorized Service Token), enviado en el
header `SEC`. QRadar es siempre una instalación on-premise del cliente
— no existe un endpoint SaaS compartido. Las credenciales SIEMPRE
provienen de variables de entorno RUVIC_QRADAR_* (ver
config.QRadarConfig.from_env). Prohibido hardcodearlas.
"""

from __future__ import annotations

from typing import Any

import requests
from requests.exceptions import ConnectionError as RequestsConnectionError
from requests.exceptions import RequestException, Timeout

from .config import QRadarConfig
from .exceptions import QRadarAuthError, QRadarDataError, QRadarNetworkError
from .logging_utils import get_logger

# Mapa de códigos de estado de QRadar (offense.status es numérico en
# algunas versiones, textual en otras vía closing_reason) — se maneja
# el valor textual estándar de la API REST moderna.
_VALID_STATUSES = ("OPEN", "HIDDEN", "CLOSED")


class QRadarClient:
    """Cliente de IBM QRadar autenticado con un SEC token.

    Args:
        config: configuración de conexión. Si se omite, se lee de las
            variables de entorno RUVIC_QRADAR_* (comportamiento estándar
            en el runtime de la plataforma).

    Ejemplo:
        >>> client = QRadarClient()  # lee RUVIC_QRADAR_* del entorno
        >>> client.list_offenses(status="OPEN")
        [{'id': 123, 'description': '...', 'severity': 7, ...}, ...]
    """

    def __init__(self, config: QRadarConfig | None = None) -> None:
        self.config = config or QRadarConfig.from_env()
        self._logger = get_logger()

    # ------------------------------------------------------------------ #
    # Peticiones HTTP
    # ------------------------------------------------------------------ #

    def _headers(self) -> dict[str, str]:
        return {
            "SEC": self.config.sec_token,
            "Version": self.config.api_version,
            "Accept": "application/json",
        }

    def _request(self, method: str, path: str, **extra: Any) -> requests.Response:
        url = f"{self.config.console_host}{path}"
        headers = extra.pop("headers", {})
        headers.update(self._headers())
        try:
            return requests.request(
                method, url, headers=headers, verify=self.config.verify_ssl,
                timeout=self.config.timeout, **extra,
            )
        except Timeout as exc:
            raise QRadarNetworkError(
                f"Tiempo de espera agotado ({self.config.timeout}s) llamando a {path}."
            ) from exc
        except RequestsConnectionError as exc:
            raise QRadarNetworkError(f"No se pudo conectar a {url}: {exc}") from exc
        except RequestException as exc:
            raise QRadarNetworkError(f"Error de red: {exc}") from exc

    def _raise_for_error(self, resp: requests.Response, context: str) -> None:
        try:
            payload = resp.json()
            message = payload.get("message", resp.text[:300])
        except ValueError:
            message = resp.text[:300] or "Error desconocido"

        if resp.status_code in (401, 403):
            raise QRadarAuthError(
                f"SEC token inválido o permisos insuficientes en {context} "
                f"(HTTP {resp.status_code}): {message}"
            )
        if resp.status_code == 404:
            raise QRadarDataError(f"No encontrado en {context}: {message}")
        if resp.status_code == 422:
            raise QRadarDataError(f"Solicitud inválida en {context}: {message}")
        raise QRadarDataError(f"Error de QRadar en {context} (HTTP {resp.status_code}): {message}")

    # ------------------------------------------------------------------ #
    # Ping / prueba de conexión
    # ------------------------------------------------------------------ #

    def ping(self) -> bool:
        """Verifica el SEC token listando 1 ofensa (barato)."""
        self.list_offenses(max_results=1)
        self._logger.info("Ping exitoso a QRadar (%s)", self.config.console_host)
        return True

    # ------------------------------------------------------------------ #
    # Capacidad 1: listar ofensas
    # ------------------------------------------------------------------ #

    def list_offenses(self, status: str | None = None, max_results: int = 50) -> list[dict[str, Any]]:
        """Lista ofensas, opcionalmente filtradas por estado.

        Args:
            status: filtra por estado ("OPEN", "HIDDEN", "CLOSED"). Opcional.
            max_results: máximo de resultados (default 50).

        Returns:
            Lista de dicts con "id", "description", "severity", "status",
            "offense_type", "start_time", "assigned_to".

        Ejemplo:
            >>> client.list_offenses(status="OPEN", max_results=10)
            [{'id': 123, 'description': 'Multiple login failures', ...}, ...]
        """
        params: dict[str, Any] = {}
        if status:
            if status.upper() not in _VALID_STATUSES:
                raise QRadarDataError(
                    f"status inválido: {status!r}. Debe ser uno de: {', '.join(_VALID_STATUSES)}."
                )
            params["filter"] = f"status={status.upper()}"

        headers = {"Range": f"items=0-{max(0, max_results - 1)}"}
        resp = self._request("GET", "/api/siem/offenses", params=params, headers=headers)
        if resp.status_code not in (200, 206):
            self._raise_for_error(resp, "list_offenses")

        items = resp.json()
        offenses = [self._offense_to_dict(item) for item in items]
        self._logger.info("list_offenses: %d ofensa(s)", len(offenses))
        return offenses

    @staticmethod
    def _offense_to_dict(item: dict[str, Any]) -> dict[str, Any]:
        return {
            "id": item.get("id"),
            "description": item.get("description"),
            "severity": item.get("severity"),
            "status": item.get("status"),
            "offense_type": item.get("offense_type"),
            "start_time": item.get("start_time"),
            "assigned_to": item.get("assigned_to"),
        }

    # ------------------------------------------------------------------ #
    # Capacidad 2: consultar el detalle de una ofensa
    # ------------------------------------------------------------------ #

    def get_offense_detail(self, offense_id: int | str) -> dict[str, Any]:
        """Consulta el detalle completo de una ofensa.

        Args:
            offense_id: Id numérico de la ofensa.

        Returns:
            Dict con los datos completos de la ofensa (los mismos campos
            que `list_offenses`, más detalle adicional que QRadar reporte).

        Ejemplo:
            >>> client.get_offense_detail(123)
            {'id': 123, 'description': '...', 'severity': 7, ...}
        """
        resp = self._request("GET", f"/api/siem/offenses/{offense_id}")
        if resp.status_code != 200:
            self._raise_for_error(resp, f"get_offense_detail {offense_id}")

        data = resp.json()
        self._logger.info("get_offense_detail %s: OK", offense_id)
        return data

    # ------------------------------------------------------------------ #
    # Capacidad 3: actualizar el estado de una ofensa
    # ------------------------------------------------------------------ #

    def update_offense_status(self, offense_id: int | str, status: str) -> dict[str, Any]:
        """Actualiza el estado de una ofensa.

        Args:
            offense_id: Id numérico de la ofensa.
            status: nuevo estado ("OPEN", "HIDDEN", "CLOSED").

        Returns:
            Dict con la ofensa actualizada.

        Ejemplo:
            >>> client.update_offense_status(123, "CLOSED")
            {'id': 123, 'status': 'CLOSED', ...}
        """
        if status.upper() not in _VALID_STATUSES:
            raise QRadarDataError(
                f"status inválido: {status!r}. Debe ser uno de: {', '.join(_VALID_STATUSES)}."
            )

        resp = self._request(
            "POST", f"/api/siem/offenses/{offense_id}", params={"status": status.upper()}
        )
        if resp.status_code != 200:
            self._raise_for_error(resp, f"update_offense_status {offense_id}")

        data = resp.json()
        self._logger.info("Ofensa %s actualizada a estado %r", offense_id, status)
        return self._offense_to_dict(data)
