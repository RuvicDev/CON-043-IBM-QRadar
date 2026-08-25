# conector-qradar

Conector Ruvic para IBM QRadar: listar ofensas, consultar detalle de ofensa, y actualizar su estado.

## Capacidades

`list_offenses`, `get_offense_detail`, `update_offense_status`. No elimina ofensas ni gestiona reglas de correlación.

## Instalación

Requiere **Python ≥ 3.10**.

```bash
pip install git+https://github.com/tu-org/conector-qradar.git#subdirectory=lib
```

Para desarrollo local (editable, en un venv limpio):

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ./lib
```

## Variables de entorno

| Variable | Obligatoria | Descripción |
|----------|-------------|-------------|
| `RUVIC_QRADAR_CONSOLE_HOST` | Sí | URL de la consola QRadar del cliente (siempre on-premise, sin endpoint compartido) |
| `RUVIC_QRADAR_SEC_TOKEN` | Sí | Authorized Service Token |
| `RUVIC_QRADAR_API_VERSION` | No | Default `20.0` |
| `RUVIC_QRADAR_VERIFY_SSL` | No | `true`/`false`, default `true` |
| `RUVIC_QRADAR_REQUEST_TIMEOUT` | No | Segundos, default `30` |

## Permisos / prerrequisitos en QRadar

1. En QRadar: **Admin → User Management → Authorized Services**.
2. Clic en **"Add Authorized Service"**.
3. Nombre descriptivo, ej. "Ruvic QRadar Connector".
4. **User Role**: uno con capacidad "Offenses" habilitada (no necesariamente Admin completo).
5. **Security Profile**: acótalo a los dominios/redes que el agente realmente necesita ver.
6. Define fecha de expiración (recomendado) o "No Expiry" si prefieres renovarlo manualmente cuando haga falta.
7. Copia el **Authentication Token** generado — es el SEC token.
8. Vuelve a Admin → **"Deploy Changes"** para que el servicio autorizado quede activo.

## Cómo correr las pruebas locales

QRadar no tiene una versión local/Docker oficial (es un appliance/VM completo de IBM) — hace falta una consola real, idealmente de prueba.

```bash
export RUVIC_QRADAR_CONSOLE_HOST=https://qradar-pruebas.miempresa.com
export RUVIC_QRADAR_SEC_TOKEN=xxxxxxxx

python test_connection.py
python validate_local.py
```

## Limitaciones conocidas

- No elimina ofensas ni gestiona reglas de correlación, log sources, ni referencia de activos.
- No implementa búsquedas AQL/Ariel (consultas de eventos crudos) — solo la API de ofensas.
- Muchas instalaciones de QRadar usan certificados autofirmados — si tu instancia los usa, considera desactivar `VERIFY_SSL` (con el riesgo correspondiente) o instalar un certificado válido.

## Notas de integración

- El paquete pip es `ruvic-qradar-connector`; el import name es `ruvic_qradar_connector`.
- Única dependencia externa: `requests`.
- Ver `SKILL.md` para los ejemplos de uso que consume el agente.
