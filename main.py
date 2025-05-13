import streamlit as st
import pandas as pd
import datetime
from config import GRUPOS, REGLAS, PERIODO_DEFECTO
from scheduler import asignar_turnos, TurnoError
from calendar_utils import obtener_fines_de_semana

import os
st.set_page_config(page_title="Gestor de Turnos de Fin de Semana", layout="wide")

# Mostrar logo si existe
logo_path = "hondutel_logo.png"
if os.path.exists(logo_path):
    st.image(logo_path, width=180)

st.sidebar.title("Menú")
menu = st.sidebar.radio("Ir a...", [
    "Generar turnos",
    "Ver calendario",
    "Gestionar grupos",
    "Gestionar cortes anteriores",
    "Salir"
])

# --- Estilo Apple-like ---
APPLE_STYLE = """
<style>
body, .stApp {
    background: #181A1B !important;
    color: #F5F6F7 !important;
    font-family: -apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,Arial,sans-serif !important;
}
.stButton>button, .stDownloadButton>button {
    background: linear-gradient(90deg, #f4f4f4 0%, #e5e5e7 100%);
    color: #222;
    border: none;
    border-radius: 12px;
    padding: 0.5em 1.2em;
    font-weight: 600;
    box-shadow: 0 2px 8px #0002;
    transition: background 0.2s, box-shadow 0.2s, transform 0.2s;
}
.stButton>button:hover, .stDownloadButton>button:hover {
    background: linear-gradient(90deg, #e5e5e7 0%, #f4f4f4 100%);
    box-shadow: 0 4px 16px #007aff55;
    transform: scale(1.04);
    animation: pulseBtn 0.4s;
}
@keyframes pulseBtn {0%{box-shadow:0 0 0 0 #007aff33;} 70%{box-shadow:0 0 0 10px #007aff11;} 100%{box-shadow:0 4px 16px #007aff55;}}
.st-bw, .st-cg, .st-c6, .st-c4 {
    border-radius: 14px !important;
    background: #23272F !important;
    color: #F5F6F7 !important;
}
.stDataFrame thead tr th {
    background: #23272F !important;
    color: #fff !important;
    border-bottom: 2px solid #e0e0e0;
}
.stDataFrame tbody tr td {
    background: #23272F !important;
    color: #F5F6F7 !important;
}
/* --- Pestañas modernas y anchas con animación --- */
.stTabs [data-baseweb="tab"] {
    font-size: 1.14em;
    font-weight: 600;
    color: #222;
    border-radius: 16px 16px 0 0;
    background: #f8f8fa;
    min-width: 220px;
    padding: 0.7em 1.5em;
    margin-right: 16px;
    text-align: center;
    transition: background 0.25s, color 0.25s, box-shadow 0.25s, transform 0.25s;
    box-shadow: 0 2px 8px #e0e0e0cc;
    letter-spacing: 0.01em;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.7em;
}
.stTabs [aria-selected="true"] {
    background: #fff !important;
    color: #007aff !important;
    border-bottom: 3px solid #007aff !important;
    box-shadow: 0 6px 24px #e0e0e0cc;
    font-size: 1.17em;
    z-index: 2;
    animation: fadeTabIn 0.5s;
}
.stTabs [data-baseweb="tab"]:hover {
    background: #eaf2fb !important;
    color: #007aff !important;
    box-shadow: 0 6px 18px #b1d9fc55;
    transform: translateY(-2px) scale(1.03);
}
@keyframes fadeTabIn {from{opacity:0;transform:translateY(-10px);} to{opacity:1;transform:translateY(0);}}
.stAlert {
    border-radius: 12px !important;
    font-size: 1.1em;
}
.stMarkdown h1, .stMarkdown h2, .stMarkdown h3, .stMarkdown h4 {
    color: #fff !important;
    letter-spacing: -0.01em;
    font-weight: 700;
}
.stMarkdown strong {
    color: #007aff !important;
}
/* Resumen calendario moderno */
.cal-resumen {
    background: rgba(255,255,255,0.92);
    color: #23272F;
    border-radius: 22px;
    margin-bottom: 1.2em;
    font-size: 1.14em;
    box-shadow: 0 6px 36px #a0a0a0cc;
    padding: 2em 2.5em 1.5em 2.5em;
    font-weight: 500;
    transition: box-shadow 0.4s, background 0.4s;
    animation: fadeInResumen 0.7s;
}
@keyframes fadeInResumen {from{opacity:0;transform:translateY(-20px);} to{opacity:1;transform:translateY(0);}}
</style>
"""
st.markdown(APPLE_STYLE, unsafe_allow_html=True)

import json
import os
CORTES_PATH = os.path.join(os.path.dirname(__file__), 'cortes.json')

def cargar_cortes():
    if not os.path.exists(CORTES_PATH):
        return []
    with open(CORTES_PATH, 'r', encoding='utf-8') as f:
        try:
            return json.load(f)
        except Exception:
            return []

def guardar_cortes(cortes):
    with open(CORTES_PATH, 'w', encoding='utf-8') as f:
        json.dump(cortes, f, ensure_ascii=False, indent=2, default=str)

# Inicializar cortes en session_state
if 'cortes' not in st.session_state:
    st.session_state['cortes'] = cargar_cortes()

# Utilidad para agregar un corte
def agregar_corte(periodo, asignaciones):
    nuevo = {
        'periodo': periodo,
        'asignaciones': {f"{str(k[0])}|{k[1]}": v for k, v in asignaciones.items()}
    }
    cortes = cargar_cortes()
    cortes.append(nuevo)
    guardar_cortes(cortes)
    st.session_state['cortes'] = cortes

if 'asignaciones' not in st.session_state:
    st.session_state['asignaciones'] = None
if 'periodo' not in st.session_state:
    st.session_state['periodo'] = PERIODO_DEFECTO

# Traducción de días al español (forzar utf-8 y acentos)
def dia_espanol(dt):
    dias = {
        'Monday': 'Lunes', 'Tuesday': 'Martes', 'Wednesday': 'Miércoles',
        'Thursday': 'Jueves', 'Friday': 'Viernes',
        'Saturday': 'Sábado', 'Sunday': 'Domingo'
    }
    return dias.get(dt.strftime('%A'), dt.strftime('%A'))

# Mostrar calendario como pantalla principal
if menu == "Gestionar grupos":
    st.title("Gestionar grupos de turnos")
    st.markdown("---")
    grupo_sel = st.selectbox("Selecciona el grupo a editar", list(GRUPOS.keys()), format_func=lambda x: GRUPOS[x]['nombre'])
    grupo = GRUPOS[grupo_sel]
    st.subheader(f"Integrantes de {grupo['nombre']}")
    integrantes = grupo['integrantes']
    if isinstance(integrantes[0], dict):
        integrantes_list = [f"{p['nombre']} (Prioridad: {p.get('prioridad','')})" for p in integrantes]
    else:
        integrantes_list = integrantes
    st.write("\n".join([f"- {i}" for i in integrantes_list]))
    st.markdown("---")
    with st.form("agregar_integrante"):
        nuevo_nombre = st.text_input("Nombre del integrante a agregar")
        nueva_prioridad = st.text_input("Prioridad (opcional, solo para Grupo 2)") if grupo_sel == 'grupo_2' else None
        agregar = st.form_submit_button("Agregar integrante")
        if agregar and nuevo_nombre:
            if grupo_sel == 'grupo_2':
                integrantes.append({"nombre": nuevo_nombre, "prioridad": nueva_prioridad or "normal"})
            else:
                integrantes.append(nuevo_nombre)
            st.success(f"Integrante {nuevo_nombre} agregado a {grupo['nombre']}")
    with st.form("quitar_integrante"):
        quitar_nombre = st.text_input("Nombre EXACTO del integrante a quitar")
        quitar = st.form_submit_button("Quitar integrante")
        if quitar and quitar_nombre:
            if grupo_sel == 'grupo_2':
                idx = next((i for i, p in enumerate(integrantes) if p['nombre'] == quitar_nombre), None)
                if idx is not None:
                    integrantes.pop(idx)
                    st.success(f"Integrante {quitar_nombre} eliminado de {grupo['nombre']}")
                else:
                    st.error(f"No se encontró a {quitar_nombre} en {grupo['nombre']}")
            else:
                if quitar_nombre in integrantes:
                    integrantes.remove(quitar_nombre)
                    st.success(f"Integrante {quitar_nombre} eliminado de {grupo['nombre']}")
                else:
                    st.error(f"No se encontró a {quitar_nombre} en {grupo['nombre']}")
    st.info("Los cambios solo estarán en memoria hasta que se reinicie la app. Para persistir, se debe actualizar el archivo config.py.")

if menu == "Generar turnos" and st.session_state['asignaciones']:
    st.title("Calendario de turnos")
    asignaciones = st.session_state.get('asignaciones')
    periodo = st.session_state['periodo']
    fines_de_semana = obtener_fines_de_semana(periodo['inicio'], periodo['fin'])
    data = []
    for (fecha, turno), nombre in asignaciones.items():
        data.append({
            'Fecha': fecha,
            'Día': dia_espanol(fecha),
            'Turno': turno,
            'Empleado': nombre
        })
    df = pd.DataFrame(data)
    st.dataframe(df.sort_values(['Fecha', 'Turno']), use_container_width=True)
    st.info("Próximamente: edición interactiva de turnos.")
    st.markdown("---")
    st.subheader("¿Desea generar nuevos turnos?")

if menu == "Generar turnos":
    st.title("Generar turnos para un periodo")
    import datetime
    # --- Nuevo selector de mes y año ---
    import calendar
    hoy = datetime.date.today()
    anio_actual = hoy.year
    # Opciones de años: desde el actual -1 hasta actual +2
    opciones_anio = [anio_actual-1, anio_actual, anio_actual+1, anio_actual+2]
    meses = [
        (1, 'Enero'), (2, 'Febrero'), (3, 'Marzo'), (4, 'Abril'),
        (5, 'Mayo'), (6, 'Junio'), (7, 'Julio'), (8, 'Agosto'),
        (9, 'Septiembre'), (10, 'Octubre'), (11, 'Noviembre'), (12, 'Diciembre')
    ]
    # Persistencia de mes/año seleccionado
    if 'mes_idx' not in st.session_state:
        st.session_state['mes_idx'] = 'Mayo'
    if 'anio_sel' not in st.session_state:
        st.session_state['anio_sel'] = anio_actual
    col1, col2, col3 = st.columns([2,2,2])
    with col1:
        mes_idx = st.selectbox('Mes', [m[1] for m in meses], index=[m[1] for m in meses].index(st.session_state['mes_idx']), key='mes_select')
        if mes_idx != st.session_state['mes_idx']:
            st.session_state['mes_idx'] = mes_idx
            st.rerun()
    with col2:
        anio_sel = st.selectbox('Año', opciones_anio, index=opciones_anio.index(st.session_state['anio_sel']), key='anio_select')
        if anio_sel != st.session_state['anio_sel']:
            st.session_state['anio_sel'] = anio_sel
            st.rerun()
    col_a, col_b = st.columns(2)
    if col_a.button('⏪ Mes anterior'):
        idx = [m[1] for m in meses].index(st.session_state['mes_idx'])
        if idx == 0:
            st.session_state['mes_idx'] = meses[-1][1]
            st.session_state['anio_sel'] -= 1
        else:
            st.session_state['mes_idx'] = meses[idx-1][1]
        st.rerun()
    if col_b.button('Mes siguiente ⏩'):
        idx = [m[1] for m in meses].index(st.session_state['mes_idx'])
        if idx == 11:
            st.session_state['mes_idx'] = meses[0][1]
            st.session_state['anio_sel'] += 1
        else:
            st.session_state['mes_idx'] = meses[idx+1][1]
        st.rerun()
    # Actualiza variables locales
    mes_idx = st.session_state['mes_idx']
    anio_sel = st.session_state['anio_sel']
    mes_num = [m[0] for m in meses if m[1] == mes_idx][0]
    # Calcular fecha de inicio y fin para corte 21 de mes actual al 20 del siguiente mes
    fecha_inicio = datetime.date(anio_sel, mes_num, 21)
    # Calcular mes y año siguiente
    if mes_num == 12:
        mes_siguiente = 1
        anio_siguiente = anio_sel + 1
    else:
        mes_siguiente = mes_num + 1
        anio_siguiente = anio_sel
    fecha_fin = datetime.date(anio_siguiente, mes_siguiente, 20)
    st.markdown(f"<div style='margin-bottom:0.7em;font-size:1.08em;color:#007aff;background:#f8faff;padding:0.7em 1.2em;border-radius:12px;display:inline-block;'>\n<b>Periodo seleccionado:</b> {fecha_inicio} → {fecha_fin}</div>", unsafe_allow_html=True)

    if st.button("Generar turnos"):
        try:
            fecha_inicio_str = fecha_inicio.strftime("%Y-%m-%d")
            fecha_fin_str = fecha_fin.strftime("%Y-%m-%d")
            asignaciones = asignar_turnos(fecha_inicio_str, fecha_fin_str)
            agregar_corte({'inicio': fecha_inicio_str, 'fin': fecha_fin_str}, asignaciones)
            st.session_state['asignaciones'] = asignaciones
            st.session_state['periodo'] = {'inicio': fecha_inicio_str, 'fin': fecha_fin_str}
            st.success("Turnos generados correctamente.")
        except Exception as e:
            st.markdown("""
                <div style='background:#ffeaea;color:#b00020;padding:1em 1.5em;border-radius:14px;margin-bottom:1.2em;font-size:1.08em;box-shadow:0 2px 12px #b0002022;animation:fadeInError 0.7s;'>
                <b>Error:</b> No se pudieron asignar todos los turnos. Revise la configuración.<br>
                <span style='font-size:0.96em;color:#a00020;'>""" + str(e) + "</span></div>\n<style>@keyframes fadeInError {from{opacity:0;transform:translateY(-10px);} to{opacity:1;transform:translateY(0);}}</style>\n", unsafe_allow_html=True)

if menu == "Ver calendario":
    st.title("Calendario de turnos")
    asignaciones = st.session_state.get('asignaciones')
    if not asignaciones or len(asignaciones) == 0:
        st.info("No hay turnos generados. Por favor, genera un nuevo corte para ver el calendario.")
    else:
        periodo = st.session_state['periodo']
        fines_de_semana = obtener_fines_de_semana(periodo['inicio'], periodo['fin'])
        data = []
        empleados_grupo = {}
        for n in GRUPOS['grupo_1']['integrantes']:
            # Grupo 1 son solo nombres (str)
            if isinstance(n, str):
                empleados_grupo[n] = 'G1'
        for e in GRUPOS['grupo_2']['integrantes']:
            # Grupo 2 son dicts con nombre
            if isinstance(e, dict):
                empleados_grupo[e['nombre']] = 'G2'
        for (fecha, turno), nombre in asignaciones.items():
            data.append({
                'Fecha': fecha,
                'Día': dia_espanol(fecha),
                'Turno': turno,
                'Empleado': nombre,
                'Grupo': empleados_grupo.get(nombre, '')
            })
        df = pd.DataFrame(data)
        total_turnos = len(df)
        resumen = f"<b>Periodo:</b> {periodo['inicio']} - {periodo['fin']}<br>"
        resumen += f"<b>Fines de semana:</b> {len(fines_de_semana)}<br>"
        resumen += f"<b>Total de turnos:</b> {total_turnos}"
        st.markdown(f"<div class='cal-resumen'>" + resumen + "</div>", unsafe_allow_html=True)
        # Pestañas con iconos
        tab1, tab2 = st.tabs([
            "📅 Vista calendario mensual",
            "📋 Vista tabla"
        ])
        # ----------- Vista calendario mensual -----------
        with tab1:
            import calendar
            import locale
            try:
                locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
            except:
                pass
            meses = sorted(set([f.strftime('%Y-%m') for f in df['Fecha']]))
            for mes in meses:
                anio, mes_n = map(int, mes.split('-'))
                cal = calendar.Calendar(firstweekday=0)
                dias_mes = list(cal.itermonthdates(anio, mes_n))
                st.markdown(f"<h4 style='margin-top:1.5em'>{calendar.month_name[mes_n].capitalize()} {anio}</h4>", unsafe_allow_html=True)
                # Tabla calendario
                html = "<style>"
                html += ".cal-dia{padding:6px 2px 2px 2px;min-width:100px;min-height:80px;border-radius:14px;border:1px solid #eee;vertical-align:top;position:relative;transition:box-shadow 0.2s;}"
                html += ".cal-dia:hover{box-shadow:0 0 12px 2px #b0b0b0;z-index:2;transform:scale(1.03);transition:box-shadow 0.2s, transform 0.2s;}"
                html += ".cal-turnoA{background:#fffbe6;padding:2px 6px 2px 6px;border-radius:8px;margin-bottom:2px;display:block;box-shadow:0 1px 4px #f3e9c3;animation:fadeIn 0.5s;}"
                html += ".cal-turnoB{background:#eaf6ff;padding:2px 6px 2px 6px;border-radius:8px;display:block;box-shadow:0 1px 4px #c9e4fa;animation:fadeIn 0.5s;}"
                html += ".cal-turnoA b, .cal-turnoB b{color:#23272F;font-weight:700;}"
                html += ".cal-turnoA span, .cal-turnoB span{font-weight:600;}"
                html += ".etiqueta-g1{background:#FFD59E;color:#23272F;padding:1px 7px;border-radius:10px;font-size:0.8em;margin-left:4px;font-weight:700;}"
                html += ".etiqueta-g2{background:#B1D9FC;color:#23272F;padding:1px 7px;border-radius:10px;font-size:0.8em;margin-left:4px;font-weight:700;}"
                html += "@keyframes fadeIn {from{opacity:0;} to{opacity:1;}} .cal-dia,.cal-turnoA,.cal-turnoB{animation:fadeIn 0.7s;}"
                html += "</style>"
                html += "<table style='border-spacing:6px;width:100%'><tr>"
                for d in ['Lun','Mar','Mié','Jue','Vie','Sáb','Dom']:
                    html += f"<th style='text-align:center;color:#888'>{d}</th>"
                html += "</tr>"
                semana = []
                for i, dia in enumerate(dias_mes):
                    if i % 7 == 0:
                        if semana:
                            html += "<tr>" + ''.join(semana) + "</tr>"
                        semana = []
                    contenido = ""
                    if dia.month == mes_n:
                        # Mostrar turnos si es sábado o domingo
                        turnos = df[(df['Fecha']==dia) & (df['Turno'].isin(['A','B']))]
                        if not turnos.empty:
                            for idx, row in turnos.iterrows():
                                color = "cal-turnoA" if row['Turno']=='A' else "cal-turnoB"
                                grupo = row['Grupo']
                                etiqueta = f"<span class='etiqueta-g1'>G1</span>" if grupo=='G1' else f"<span class='etiqueta-g2'>G2</span>"
                                contenido += f"<div class='{color}'><b>Turno {row['Turno']}</b>: <span style='color:#23272F;font-weight:700'>{row['Empleado']}</span> {etiqueta}</div>"
                        else:
                            contenido = ""
                        semana.append(f"<td class='cal-dia'>{dia.day}{contenido}</td>")
                    else:
                        semana.append("<td></td>")
                if semana:
                    html += "<tr>" + ''.join(semana) + "</tr>"
                html += "</table>"
                st.markdown(html, unsafe_allow_html=True)
        # ----------- Vista tabla -----------
        with tab2:
            st.dataframe(df.sort_values(['Fecha', 'Turno']), use_container_width=True)

if menu == "Exportar turnos":
    st.title("Exportar turnos")
    asignaciones = st.session_state.get('asignaciones')
    if not asignaciones:
        st.warning("Primero debe generar los turnos.")
    else:
        data = []
        for (fecha, turno), nombre in asignaciones.items():
            data.append({
                'Fecha': fecha.strftime('%Y-%m-%d'),
                'Turno': turno,
                'Empleado': nombre
            })

if menu == "Gestionar cortes anteriores":
    st.title("Gestionar cortes anteriores")
    cortes = st.session_state.get('cortes', [])
    if not cortes:
        st.info("No hay cortes guardados todavía.")
    else:
        for idx, corte in enumerate(cortes):
            periodo = corte['periodo']
            label = f"{periodo['inicio']} - {periodo['fin']}"
            col1, col2, col3 = st.columns([4,2,2])
            with col1:
                st.markdown(f"<b>Periodo:</b> {label}", unsafe_allow_html=True)
            with col2:
                if st.button(f"📅 Ver calendario", key=f"ver_{idx}"):
                    # Cargar asignaciones de este corte
                    asig = {tuple([pd.to_datetime(k.split('|')[0]).date(), k.split('|')[1]]): v for k,v in corte['asignaciones'].items()}
                    st.session_state['asignaciones'] = asig
                    st.session_state['periodo'] = periodo
                    st.success(f"Mostrando calendario del periodo {label}")
            with col3:
                delete_clicked = st.session_state.get(f'delete_clicked_{idx}', False)
                eliminado = st.session_state.get(f'eliminado_{idx}', False)
                if not delete_clicked and not eliminado:
                    if st.button(f"🗑️ Eliminar corte", key=f"del_{idx}"):
                        st.session_state[f'delete_clicked_{idx}'] = True
                        st.session_state[f'eliminado_{idx}'] = False
                elif delete_clicked and not eliminado:
                    st.warning(f"¿Seguro que deseas eliminar el corte del periodo {label}? Esta acción no se puede deshacer.")
                    if st.button(f"Confirmar eliminación {label}", key=f"confirm_del_{idx}"):
                        cortes.pop(idx)
                        guardar_cortes(cortes)
                        st.session_state['cortes'] = cortes
                        st.session_state[f'delete_clicked_{idx}'] = False
                        st.session_state[f'eliminado_{idx}'] = True
                        st.success(f"Corte {label} eliminado.")
                elif eliminado:
                    st.success(f"Corte {label} eliminado.")
                    # Limpiar estado tras mostrar feedback
                    st.session_state[f'eliminado_{idx}'] = False
                    st.session_state[f'delete_clicked_{idx}'] = False
            st.markdown("---")
        # Si quieres exportar todos los cortes, puedes hacerlo aquí
        if cortes:
            cortes_export = []
            for corte in cortes:
                periodo = corte['periodo']
                for k, v in corte['asignaciones'].items():
                    fecha, turno = k.split('|')
                    cortes_export.append({
                        'Periodo_inicio': periodo['inicio'],
                        'Periodo_fin': periodo['fin'],
                        'Fecha': fecha,
                        'Turno': turno,
                        'Empleado': v
                    })
            df_cortes = pd.DataFrame(cortes_export)
            csv = df_cortes.to_csv(index=False).encode('utf-8')
            st.download_button("Descargar todos los cortes (CSV)", csv, "cortes.csv", "text/csv")
            st.download_button("Descargar todos los cortes (JSON)", df_cortes.to_json(orient='records'), "cortes.json", "application/json")

if menu == "Salir":
    st.stop()
