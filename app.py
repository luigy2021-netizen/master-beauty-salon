from datetime import date, datetime, time, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote_plus

import gspread
import pandas as pd
import streamlit as st
from google.oauth2.service_account import Credentials


MARCA = "Master Beauty Salon"
LOGO = Path(__file__).parent / "assets" / "master-beauty-salon.png"
BANNER = Path(__file__).parent / "assets" / "promo-banner.png"

SERVICIO_DIA_COMPLETO = "Mechas"

SERVICIOS = {
    "Mechas": {
        "duracion": 480,
        "descripcion": "Servicio de mechas con atenci\u00f3n dedicada durante todo el d\u00eda.",
    },
    "Tintes": {
        "duracion": 180,
        "descripcion": "Servicio de color con atenci\u00f3n dedicada.",
    },
    "Extensiones": {
        "duracion": 360,
        "descripcion": "Aplicaci\u00f3n de extensiones con acabado profesional.",
    },
    "Peinado y maquillaje": {
        "duracion": 240,
        "descripcion": "Peinado y maquillaje para una ocasi\u00f3n especial.",
    },
    "Tratamiento capilar": {
        "duracion": 300,
        "descripcion": "Cuidado intensivo para renovar y fortalecer tu cabello.",
    },
    "Cortes": {
        "duracion": 60,
        "descripcion": "Dise\u00f1o de corte adaptado a tu estilo.",
    },
}

PROMOCIONES = [
    ("Experiencia Master", "Combina tus servicios favoritos en una sola visita."),
    ("Color y cuidado", "Consulta las opciones disponibles para renovar tu color."),
    ("Tu pr\u00f3xima visita", "Agenda con anticipaci\u00f3n y elige el horario que m\u00e1s te convenga."),
]

COLUMNAS = ["Fecha", "Hora", "Servicio", "Duracion", "Nombre", "WhatsApp", "Estado"]

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(20, 0)
COMIDA_INICIO = time(14, 0)
COMIDA_FIN = time(15, 0)
INTERVALO = 30

KRONIQ_WHATSAPP = "526563079754"
KRONIQ_MENSAJE = "Hola, quiero informaci\u00f3n sobre una agenda digital para mi negocio."


st.set_page_config(page_title=f"Agenda | {MARCA}", page_icon="\u2728", layout="centered")

st.markdown(
    """
    <style>
    :root { --gold: #d6a93f; --gold-light: #f6dc8b; --ink: #090909; }
    .stApp { background: radial-gradient(circle at 50% 0%, #29200f 0, #111 30%, #050505 72%); color: #f7f2e7; }
    [data-testid="stHeader"] { background: transparent; }
    #MainMenu, footer, [data-testid="stToolbar"], .stDeployButton { display: none !important; }
    [data-testid="stAppViewBlockContainer"] { max-width: 860px; padding-top: 1rem; padding-bottom: 3rem; }
    [data-testid="stImage"] img { display: block; width: min(100%, 540px); margin: 0 auto 0.5rem; border-radius: 18px; box-shadow: 0 18px 60px rgba(0, 0, 0, 0.45); }
    .master-title { margin: 0.4rem 0 0; color: var(--gold-light); text-align: center; font-family: Georgia, serif; font-size: clamp(1.7rem, 5vw, 2.5rem); letter-spacing: 0.08em; }
    .master-subtitle { margin: 0.35rem 0 1.8rem; color: #cfc7b5; text-align: center; }
    .service-card, .promotion-card { height: 100%; padding: 1rem; border: 1px solid rgba(214, 169, 63, 0.38); border-radius: 14px; background: rgba(17, 17, 17, 0.82); }
    .service-card strong, .promotion-card strong { color: var(--gold-light); }
    .service-card p, .promotion-card p { margin: 0.35rem 0 0; color: #cfc7b5; font-size: 0.9rem; }
    .service-time { display: block; margin-top: 0.7rem; color: #a99d86; font-size: 0.78rem; }
    div[data-testid="stForm"] { border-color: rgba(214, 169, 63, 0.5); background: rgba(17, 17, 17, 0.85); }
    .stButton > button, .stFormSubmitButton > button { border: 1px solid var(--gold); background: linear-gradient(135deg, #b88322, #f0d379); color: var(--ink); font-weight: 700; }
    .kroniq-footer { margin-top: 2.8rem; padding: 1.15rem; border-top: 1px solid rgba(214, 169, 63, 0.32); color: #aaa08e; text-align: center; }
    .kroniq-footer strong { color: var(--gold-light); }
    .kroniq-button { display: inline-block; margin-top: 0.8rem; padding: 0.62rem 1rem; border: 1px solid var(--gold); border-radius: 10px; color: #f4d982 !important; font-weight: 700; text-decoration: none !important; }
    @media (max-width: 640px) { [data-testid="stAppViewBlockContainer"] { padding: 0.7rem 0.8rem 2rem; } }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def autorizar_google():
    scopes = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    credenciales = Credentials.from_service_account_info(dict(st.secrets["gcp_service_account"]), scopes=scopes)
    return gspread.authorize(credenciales)


def obtener_hoja():
    cliente = autorizar_google()
    spreadsheet_id = str(st.secrets.get("spreadsheet_id", "")).strip()
    libro = cliente.open_by_key(spreadsheet_id) if spreadsheet_id else cliente.open(st.secrets["spreadsheet_name"])
    nombre = str(st.secrets.get("worksheet_name", "Citas"))
    try:
        hoja = libro.worksheet(nombre)
    except gspread.WorksheetNotFound:
        hoja = libro.add_worksheet(title=nombre, rows=1000, cols=7)
    if hoja.row_values(1)[: len(COLUMNAS)] != COLUMNAS:
        hoja.update(values=[COLUMNAS], range_name="A1:G1")
    return hoja


def leer_citas(hoja):
    if hoja is None:
        return pd.DataFrame(columns=COLUMNAS)
    return pd.DataFrame(hoja.get_all_records(expected_headers=COLUMNAS), columns=COLUMNAS)


def se_empalman(inicio_a, fin_a, inicio_b, fin_b):
    return inicio_a < fin_b and inicio_b < fin_a


def citas_activas_del_dia(citas, fecha):
    fecha_texto = fecha.strftime("%Y-%m-%d")
    activas = []
    for _, cita in citas.iterrows():
        if str(cita.get("Fecha", "")).strip() != fecha_texto:
            continue
        if str(cita.get("Estado", "")).strip().lower() in {"cancelada", "cancelado"}:
            continue
        activas.append(cita)
    return activas


def citas_del_dia(citas, fecha):
    resultado = []
    for cita in citas_activas_del_dia(citas, fecha):
        try:
            inicio = datetime.combine(fecha, datetime.strptime(str(cita["Hora"]).strip(), "%H:%M").time())
            duracion = int(cita["Duracion"])
        except (KeyError, TypeError, ValueError):
            continue
        resultado.append((inicio, inicio + timedelta(minutes=duracion)))
    return resultado


def dia_bloqueado_por_mechas(citas, fecha):
    return any(
        str(cita.get("Servicio", "")).strip().casefold() == SERVICIO_DIA_COMPLETO.casefold()
        for cita in citas_activas_del_dia(citas, fecha)
    )


def horarios_disponibles(fecha, servicio, duracion, citas):
    if fecha.weekday() == 6:
        return []

    citas_activas = citas_activas_del_dia(citas, fecha)

    # Mechas ocupa el dia completo y solo puede reservarse en un dia vacio.
    if servicio == SERVICIO_DIA_COMPLETO:
        return [HORA_APERTURA.strftime("%H:%M")] if not citas_activas else []

    # Ningun otro servicio puede reservarse si ya hay Mechas ese dia.
    if dia_bloqueado_por_mechas(citas, fecha):
        return []

    apertura = datetime.combine(fecha, HORA_APERTURA)
    cierre = datetime.combine(fecha, HORA_CIERRE)
    comida_inicio = datetime.combine(fecha, COMIDA_INICIO)
    comida_fin = datetime.combine(fecha, COMIDA_FIN)
    ocupadas = citas_del_dia(citas, fecha)
    disponibles = []
    inicio = apertura

    while inicio + timedelta(minutes=duracion) <= cierre:
        fin = inicio + timedelta(minutes=duracion)
        toca_comida = se_empalman(inicio, fin, comida_inicio, comida_fin)
        toca_cita = any(se_empalman(inicio, fin, inicio_ocupado, fin_ocupado) for inicio_ocupado, fin_ocupado in ocupadas)
        if not toca_comida and not toca_cita:
            disponibles.append(inicio.strftime("%H:%M"))
        inicio += timedelta(minutes=INTERVALO)

    return disponibles


def guardar_cita(hoja, fecha, hora, servicio, duracion, nombre, whatsapp):
    citas_actuales = leer_citas(hoja)
    if hora not in horarios_disponibles(fecha, servicio, duracion, citas_actuales):
        return False
    hoja.append_row(
        [fecha.strftime("%Y-%m-%d"), hora, servicio, duracion, nombre.strip(), whatsapp, "Confirmada"],
        value_input_option="RAW",
    )
    return True


def mostrar_encabezado():
    if LOGO.exists():
        st.image(str(LOGO), use_container_width=True)
    st.markdown(f'<h1 class="master-title">Agenda {MARCA}</h1>', unsafe_allow_html=True)
    st.markdown('<p class="master-subtitle">Reserva tu momento de belleza.</p>', unsafe_allow_html=True)
    if BANNER.exists():
        st.image(str(BANNER), use_container_width=True)


def texto_duracion(minutos):
    horas = minutos // 60
    return f"{horas} hora" if horas == 1 else f"{horas} horas"


def mostrar_servicios():
    st.markdown("### Nuestros servicios")
    for fila_inicio in range(0, len(SERVICIOS), 3):
        columnas = st.columns(3)
        servicios_fila = list(SERVICIOS.items())[fila_inicio : fila_inicio + 3]
        for columna, (nombre, datos) in zip(columnas, servicios_fila):
            with columna:
                nota = " \u00b7 Bloquea todo el d\u00eda" if nombre == SERVICIO_DIA_COMPLETO else ""
                st.markdown(
                    f'<div class="service-card"><strong>{escape(nombre)}</strong><p>{escape(datos["descripcion"])}</p><span class="service-time">Duraci\u00f3n aproximada: {texto_duracion(datos["duracion"])}{nota}</span></div>',
                    unsafe_allow_html=True,
                )


def mostrar_reserva(hoja, citas):
    st.markdown("### Reserva tu cita")
    st.caption("Elige tu servicio, fecha y horario disponible.")
    servicio = st.selectbox("1. Selecciona servicio", list(SERVICIOS))
    duracion = SERVICIOS[servicio]["duracion"]
    fecha = st.date_input("2. Selecciona fecha", min_value=date.today())

    if fecha.weekday() == 6:
        st.warning(f"{MARCA} permanece cerrado los domingos.")
        return

    horarios = horarios_disponibles(fecha, servicio, duracion, citas)
    if not horarios:
        st.info("No hay horarios disponibles para este servicio en esta fecha.")
        return

    if servicio == SERVICIO_DIA_COMPLETO:
        st.info("El servicio de Mechas ocupa y bloquea todo el d\u00eda.")

    with st.form("formulario_cita", clear_on_submit=True):
        hora = st.selectbox("3. Selecciona hora disponible", horarios)
        nombre = st.text_input("4. Escribe tu nombre")
        whatsapp = st.text_input("5. Escribe tu WhatsApp (10 d\u00edgitos)", max_chars=10)
        confirmar = st.form_submit_button("6. Confirmar cita")

    if confirmar:
        if hoja is None:
            st.error("El registro de citas est\u00e1 temporalmente fuera de servicio.")
        elif not nombre.strip():
            st.error("Escribe tu nombre.")
        elif not (whatsapp.isdigit() and len(whatsapp) == 10):
            st.error("El WhatsApp debe contener exactamente 10 d\u00edgitos.")
        else:
            try:
                guardada = guardar_cita(hoja, fecha, hora, servicio, duracion, nombre, whatsapp)
                if guardada:
                    st.success(f"Cita confirmada para {nombre.strip()} el {fecha.strftime('%d/%m/%Y')} a las {hora}.")
                else:
                    st.error("Ese d\u00eda u horario acaba de ser ocupado. Recarga la p\u00e1gina y elige otro.")
            except Exception:
                st.error("No fue posible guardar la cita. Espera unos segundos e intenta nuevamente.")


def mostrar_promociones():
    st.markdown("### Promociones y novedades")
    st.caption("Este espacio puede actualizarse cada temporada.")
    for titulo, detalle in PROMOCIONES:
        st.markdown(f'<div class="promotion-card"><strong>{escape(titulo)}</strong><p>{escape(detalle)}</p></div>', unsafe_allow_html=True)
        st.write("")


def mostrar_kroniq():
    enlace = f"https://wa.me/{KRONIQ_WHATSAPP}?text={quote_plus(KRONIQ_MENSAJE)}"
    st.markdown(
        f'<div class="kroniq-footer"><div>Agenda digital desarrollada por <strong>Kroniq</strong></div><div>Convierte tus citas en una experiencia profesional.</div><a class="kroniq-button" href="{escape(enlace)}" target="_blank" rel="noopener noreferrer">Quiero una agenda para mi negocio</a></div>',
        unsafe_allow_html=True,
    )


def main():
    mostrar_encabezado()
    hoja = None
    citas = pd.DataFrame(columns=COLUMNAS)
    try:
        hoja = obtener_hoja()
        citas = leer_citas(hoja)
    except Exception:
        st.warning("La agenda est\u00e1 visible, pero Google Sheets no respondi\u00f3. Las reservaciones se reactivar\u00e1n cuando vuelva la conexi\u00f3n.")

    reservar, promociones = st.tabs(["Reservar cita", "Promociones"])
    with reservar:
        mostrar_servicios()
        st.divider()
        mostrar_reserva(hoja, citas)
    with promociones:
        mostrar_promociones()
    mostrar_kroniq()


if __name__ == "__main__":
    main()
