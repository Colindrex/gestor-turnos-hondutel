import random
from typing import List, Dict, Any
from config import GRUPOS, REGLAS
from calendar_utils import obtener_fines_de_semana

class TurnoError(Exception):
    pass


def asignar_turnos(periodo_inicio: str, periodo_fin: str) -> Dict:
    import time
    fines_de_semana = obtener_fines_de_semana(periodo_inicio, periodo_fin)
    total_turnos = len(fines_de_semana) * 2 * 2  # 2 días x 2 turnos
    integrantes_g1 = GRUPOS['grupo_1']['integrantes']
    integrantes_g2 = GRUPOS['grupo_2']['integrantes']
    reglas_g1 = GRUPOS['grupo_1']['disponibilidad']
    reglas_g2 = GRUPOS['grupo_2']['disponibilidad']
    capacidad_g1 = len(integrantes_g1) * (reglas_g1['sabados'] + reglas_g1['domingos'])
    capacidad_g2 = len(integrantes_g2) * (reglas_g2['sabados'] + reglas_g2['domingos'])
    if reglas_g2.get('extra_finde') and len(fines_de_semana) == 5:
        capacidad_g2 += len(integrantes_g2)
    capacidad_total = capacidad_g1 + capacidad_g2
    if capacidad_total < total_turnos:
        raise TurnoError(f"Capacidad insuficiente: se requieren {total_turnos} turnos, pero solo hay {capacidad_total} disponibles.")

    intentos = 0
    max_intentos = 1000
    error_sab_dom = False
    while intentos < max_intentos:
        intentos += 1
        # Inicialización de asignaciones
        asignaciones = {}
        for idx, (sab, dom) in enumerate(fines_de_semana):
            asignaciones[(sab, 'A')] = None
            asignaciones[(sab, 'B')] = None
            if dom:
                asignaciones[(dom, 'A')] = None
                asignaciones[(dom, 'B')] = None
        indices_fds = list(range(len(fines_de_semana)))
        random.shuffle(indices_fds)
        # --- Asignación Grupo 1 ---
        g1_cupos = {nombre: {'sabados': 0, 'domingos': 0} for nombre in integrantes_g1}
        sabados_g1 = [sab for sab, dom in fines_de_semana]
        domingos_g1 = [dom for sab, dom in fines_de_semana if dom]
        random.shuffle(sabados_g1)
        random.shuffle(domingos_g1)
        # Repartir sábados
        for i, sab in enumerate(sabados_g1):
            for j, nombre in enumerate(integrantes_g1):
                if g1_cupos[nombre]['sabados'] < reglas_g1['sabados']:
                    turno = 'A' if (i + j) % 2 == 0 else 'B'
                    # Verifica que no tenga ya turno el domingo de ese finde
                    dom = None
                    for sab_, dom_ in fines_de_semana:
                        if sab_ == sab:
                            dom = dom_
                            break
                    tiene_dom = False
                    if dom:
                        for t in ['A','B']:
                            if asignaciones.get((dom, t)) == nombre:
                                tiene_dom = True
                                break
                    if asignaciones.get((sab, turno)) is None and not tiene_dom:
                        asignaciones[(sab, turno)] = nombre
                        g1_cupos[nombre]['sabados'] += 1
                        break
        # Repartir domingos
        for i, dom in enumerate(domingos_g1):
            for j, nombre in enumerate(integrantes_g1):
                if g1_cupos[nombre]['domingos'] < reglas_g1['domingos']:
                    turno = 'A' if (i + j) % 2 == 0 else 'B'
                    # Verifica que no tenga ya turno el sábado de ese finde
                    sab = None
                    for sab_, dom_ in fines_de_semana:
                        if dom_ == dom:
                            sab = sab_
                            break
                    tiene_sab = False
                    if sab:
                        for t in ['A','B']:
                            if asignaciones.get((sab, t)) == nombre:
                                tiene_sab = True
                                break
                    if asignaciones.get((dom, turno)) is None and not tiene_sab:
                        asignaciones[(dom, turno)] = nombre
                        g1_cupos[nombre]['domingos'] += 1
                        break
        # El resto de turnos lo cubre Grupo 2
        turnos_libres = []
        for sab, dom in fines_de_semana:
            for turno in ['A', 'B']:
                if asignaciones.get((sab, turno)) is None:
                    turnos_libres.append((sab, turno))
                if dom and asignaciones.get((dom, turno)) is None:
                    turnos_libres.append((dom, turno))
        g2_disponible = {e['nombre']: {'sabados': reglas_g2['sabados'], 'domingos': reglas_g2['domingos']} for e in integrantes_g2}
        # --- Ajuste para cortes de 5 fines de semana ---
        modo_extendido = reglas_g2.get('extra_finde') and len(fines_de_semana) == 5
        if modo_extendido:
            for e in integrantes_g2:
                # Permite un turno extra tanto en sábados como en domingos
                g2_disponible[e['nombre']]['sabados'] += 1
                g2_disponible[e['nombre']]['domingos'] += 1
        random.shuffle(turnos_libres)
        # Asignar por prioridad textual: alta=1, media=2, normal=3, baja=4
        prioridad_map = {'alta': 1, 'media': 2, 'normal': 3, 'baja': 4}
        # Calcular máximo de turnos para cada prioridad
        prioridad_turnos = {1: [], 2: [], 3: [], 4: []}
        for e in integrantes_g2:
            prio = e.get('prioridad', 'normal')
            prioridad_turnos[prioridad_map.get(prio, 3)].append(e['nombre'])
        # El mínimo de integrantes por prioridad
        min_turnos_baja = max(1, (reglas_g2['sabados'] + reglas_g2['domingos']) // len(prioridad_turnos[4]) if prioridad_turnos[4] else 1)
        turnos_asignados = {e['nombre']: 0 for e in integrantes_g2}
        for prioridad in range(1, 5):
            for e in integrantes_g2:
                prio = e.get('prioridad', 'normal')
                if prioridad_map.get(prio, 3) != prioridad:
                    continue
                nombre = e['nombre']
                for k in turnos_libres:
                    fecha, turno = k
                    if nombre in prioridad_turnos[4] and turnos_asignados[nombre] >= min_turnos_baja:
                        continue
                    if modo_extendido and 'total' in g2_disponible[nombre]:
                        if g2_disponible[nombre]['total'] > 0 and asignaciones.get(k) is None:
                            asignaciones[k] = nombre
                            g2_disponible[nombre]['total'] -= 1
                            turnos_asignados[nombre] += 1
                    else:
                        if fecha.weekday() == 5 and g2_disponible[nombre]['sabados'] > 0 and asignaciones.get(k) is None:
                            asignaciones[k] = nombre
                            g2_disponible[nombre]['sabados'] -= 1
                            turnos_asignados[nombre] += 1
                        elif fecha.weekday() == 6 and g2_disponible[nombre]['domingos'] > 0 and asignaciones.get(k) is None:
                            asignaciones[k] = nombre
                            g2_disponible[nombre]['domingos'] -= 1
                            turnos_asignados[nombre] += 1
        # Validar que todos los turnos estén asignados
        if any(v is None for v in asignaciones.values()):
            continue  # Intentar de nuevo
        # Validación: nadie puede cubrir sábado y domingo del mismo fin de semana
        error_sab_dom = False
        for sab, dom in fines_de_semana:
            if sab and dom:
                for turno in ['A', 'B']:
                    persona_sab = asignaciones.get((sab, turno))
                    persona_dom = asignaciones.get((dom, turno))
                    if persona_sab and persona_dom and persona_sab == persona_dom:
                        error_sab_dom = True
                        break
            if error_sab_dom:
                break
        if not error_sab_dom:
            return asignaciones
    # Si llegamos aquí, relajar la restricción y asignar todos los turnos posibles
    # Buscar si hay turnos sin asignar
    turnos_no_asignados = [k for k, v in asignaciones.items() if v is None]
    if turnos_no_asignados:
        detalle = '\n'.join([f"{k[0]} turno {k[1]}" for k in turnos_no_asignados])
        raise TurnoError(f"No se pudieron asignar los siguientes turnos tras {max_intentos} intentos:\n{detalle}\nRevisa la configuración de empleados y reglas.")
    # Si el problema fue solo la restricción sábado-domingo, devolver igualmente
    return asignaciones
