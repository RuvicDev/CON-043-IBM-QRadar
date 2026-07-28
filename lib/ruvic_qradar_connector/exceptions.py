"""Excepciones propias del conector IBM QRadar.

Separan los tipos de fallo que el usuario debe distinguir: configuración
inválida, autenticación (SEC token), red, y datos (ofensa inexistente,
estado inválido).
"""


class QRadarConnectorError(Exception):
    """Error base del conector."""


class QRadarConfigError(QRadarConnectorError):
    """Configuración inválida: falta un campo requerido."""


class QRadarAuthError(QRadarConnectorError):
    """El SEC token es inválido, expiró, o no tiene permisos suficientes."""


class QRadarNetworkError(QRadarConnectorError):
    """No se pudo alcanzar la consola de QRadar (DNS, timeout, red, TLS)."""


class QRadarDataError(QRadarConnectorError):
    """La operación es válida pero la ofensa no existe, o QRadar rechazó
    la operación por otra razón."""
