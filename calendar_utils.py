import datetime
from typing import List, Tuple

def obtener_fines_de_semana(inicio: str, fin: str) -> List[Tuple[datetime.date, datetime.date]]:
    """
    Devuelve una lista de tuplas (sabado, domingo) dentro del rango dado.
    Si no hay domingo en el periodo, se pone None.
    """
    fecha_inicio = datetime.datetime.strptime(inicio, "%Y-%m-%d").date()
    fecha_fin = datetime.datetime.strptime(fin, "%Y-%m-%d").date()
    actuales = fecha_inicio
    fines_de_semana = []
    while actuales <= fecha_fin:
        if actuales.weekday() == 5:  # Sábado
            sabado = actuales
            domingo = sabado + datetime.timedelta(days=1)
            if domingo > fecha_fin:
                domingo = None
            fines_de_semana.append((sabado, domingo))
        actuales += datetime.timedelta(days=1)
    return fines_de_semana


def contar_fines_de_semana(inicio: str, fin: str) -> int:
    return len(obtener_fines_de_semana(inicio, fin))
