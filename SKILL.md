---
name: qradar
description: "Usa la librería ruvic_qradar_connector para gestionar ofensas en IBM QRadar - listar ofensas con filtro de estado (list_offenses), consultar el detalle completo de una ofensa (get_offense_detail), y actualizar su estado (update_offense_status). Úsala cuando el usuario pida revisar ofensas de seguridad en QRadar o cambiar su estado. No elimina ofensas ni gestiona reglas de correlación."
triggers:
- qradar
- ibm qradar
- ofensa
- offense qradar
---

# Conector IBM QRadar (ruvic_qradar_connector)

Librería Python para gestionar ofensas en IBM QRadar, autenticada con un SEC token. Está **preinstalada en el runtime** cuando el conector está configurado (si no, instálala con `pip install git+https://github.com/tu-org/conector-qradar.git#subdirectory=lib`).

## Regla crítica de credenciales

El código generado **NUNCA hardcodea credenciales**. Siempre se leen de variables de entorno, disponibles cuando el conector `qradar` está configurado:

| Variable | Contenido |
|----------|-----------|
| `RUVIC_QRADAR_CONSOLE_HOST` / `..._SEC_TOKEN` | Siempre requeridas |
| `RUVIC_QRADAR_API_VERSION` | (opcional) default `20.0` |
| `RUVIC_QRADAR_VERIFY_SSL` | (opcional) `true`/`false`, default `true` |
| `RUVIC_QRADAR_REQUEST_TIMEOUT` | (opcional) segundos, default `30` |

Si estas variables NO existen, el conector no está configurado: no generes código que lo use; indica al usuario que lo configure en **Settings → Conectores**.

El código generado **NUNCA** usa nombres de variable con segmento de alias (`_DEFAULT_`, `_TEST_`, `_PRODUCCION_`, etc.) — siempre `{ENV_PREFIX}{CAMPO}` tal cual, sin importar cuántas instancias de este conector haya configuradas. Esto aplica salvo que dichos nombres aparezcan explícitamente en una sección autogenerada al final de este skill.

## Conexión (siempre igual)

```python
from ruvic_qradar_connector import QRadarClient

client = QRadarClient()  # lee RUVIC_QRADAR_* del entorno automáticamente
```

## Capacidad 1 — Listar ofensas

```python
ofensas = client.list_offenses(status="OPEN", max_results=20)
for o in ofensas:
    print(f"#{o['id']}: {o['description']} (severidad {o['severity']})")
```

## Capacidad 2 — Consultar el detalle de una ofensa

```python
detalle = client.get_offense_detail(123)
print(detalle)
```

## Capacidad 3 — Actualizar el estado de una ofensa

```python
client.update_offense_status(123, "CLOSED")
```

Estados válidos: `"OPEN"`, `"HIDDEN"`, `"CLOSED"`. Antes de cerrar/ocultar una ofensa, confirma la intención del usuario — es una acción con impacto real en el seguimiento de seguridad.

## Manejo de errores

```python
from ruvic_qradar_connector import QRadarAuthError, QRadarNetworkError, QRadarDataError

try:
    client.list_offenses()
except QRadarAuthError:
    print("SEC token inválido o permisos insuficientes — revisa la configuración del conector")
except QRadarNetworkError:
    print("No se pudo conectar a la consola de QRadar — revisa la red/VPN")
except QRadarDataError as e:
    print(f"Error de datos: {e}")  # ej. ofensa no encontrada, estado inválido
```

## Buenas prácticas al generar código

1. Lee credenciales SOLO de las variables `RUVIC_QRADAR_*` (el constructor de `QRadarClient` ya lo hace).
2. Nunca imprimas `RUVIC_QRADAR_SEC_TOKEN` en logs ni en la salida.
3. Antes de cerrar/ocultar una ofensa, confirma la intención del usuario.
4. No intentes eliminar ofensas ni gestionar reglas de correlación: este conector no lo soporta.
5. QRadar es siempre una instalación específica del cliente — nunca asumas una URL genérica, siempre viene de la configuración del conector.
