"""Validación local del conector qradar: ejercita las 3 capacidades.

Requiere las env vars RUVIC_QRADAR_* exportadas contra una consola de
QRadar real (no existe una versión local/Docker oficial de QRadar — es
un appliance/VM completo). Usa una consola de prueba, no una productiva.
"""

from ruvic_qradar_connector import QRadarClient, setup_logging

setup_logging("INFO")
client = QRadarClient()

print("== 1. Listar ofensas ==")
ofensas = client.list_offenses(max_results=5)
print(f"  {len(ofensas)} ofensa(s)")
for o in ofensas:
    print(f"    {o}")

if ofensas:
    primer_id = ofensas[0]["id"]
    print(f"== 2. Consultar el detalle de la ofensa {primer_id} ==")
    detalle = client.get_offense_detail(primer_id)
    print(f"  {detalle.get('description')}")

    print(f"== 3. Actualizar el estado de la ofensa {primer_id} (al mismo estado, solo para probar el flujo) ==")
    actualizado = client.update_offense_status(primer_id, ofensas[0]["status"])
    print(f"  {actualizado}")
else:
    print("== 2 y 3. Se omiten (no hay ofensas en esta consola de prueba) ==")

print("\nValidación completa.")
