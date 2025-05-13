# Configuración de empleados, reglas y periodos para el sistema de turnos

# Grupos y reglas
GRUPOS = {
    "grupo_1": {
        "nombre": "Alta disponibilidad",
        "disponibilidad": {"sabados": 2, "domingos": 2},
        "integrantes": ["Claudia", "Melvin Perdomo"],
        "prioridad": "más alta"
    },
    "grupo_2": {
        "nombre": "Disponibilidad limitada",
        "disponibilidad": {"sabados": 1, "domingos": 1, "extra_finde": True},
        "integrantes": [
            {"nombre": "Maynor", "prioridad": "normal"},
            {"nombre": "Vanesa Pérez", "prioridad": "alta"},
            {"nombre": "Melvin Ramírez", "prioridad": "media"},
            {"nombre": "Rosa", "prioridad": "baja"}
        ]
    }
}

# Reglas generales
REGLAS = {
    'no_coincidir_grupo_1': True,
    'no_doble_turno_fin_semana': True,
    'prioridad_grupo_2': True
}

# Periodo por defecto (puede ser modificado en la app)
PERIODO_DEFECTO = {
    'inicio': '2025-05-21',  # AAAA-MM-DD
    'fin': '2025-06-20'
}
