from base64 import b64encode
from datetime import date, datetime, time, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote_plus

import gspread
import pandas as pd
import streamlit as st
from oauth2client.service_account import ServiceAccountCredentials


SERVICIOS = {
    "Corte caballero": {
        "duracion": 30,
        "descripcion": "Corte personalizado y acabado profesional.",
    },
    "Corte mujer": {
        "duracion": 60,
        "descripcion": "DiseÃ±o de corte adaptado a tu estilo.",
    },
    "Tinte": {
        "duracion": 120,
        "descripcion": "Servicio de color con atenciÃ³n dedicada.",
    },
}

PROMOCION_PRINCIPAL = {
    "etiqueta": "PromociÃ³n destacada",
    "titulo": "Renueva tu estilo en Master Beauty Salon",
    "detalle": "Pregunta por nuestros paquetes y promociones disponibles al reservar.",
}

PROMOCIONES = [
    {
        "titulo": "Experiencia Master",
        "detalle": "Combina tus servicios favoritos en una sola visita.",
    },
    {
        "titulo": "Color y cuidado",
        "detalle": "Consulta las opciones disponibles para renovar tu color.",
    },
    {
        "titulo": "Tu prÃ³xima visita",
        "detalle": "Agenda con anticipaciÃ³n y elige el horario que mÃ¡s te convenga.",
    },
]

KRONIQ_WHATSAPP = "526563079754"
KRONIQ_MENSAJE = "Hola, quiero informaciÃ³n sobre una agenda digital para mi negocio."

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(17, 30)
COMIDA_INICIO = time(14, 0)
COMIDA_FIN = time(15, 0)
INTERVALO_MINUTOS = 30
COLUMNAS = [
    "Fecha",
    "Hora",
    "Servicio",
    "DuraciÃ³n",
    "Nombre",
    "WhatsApp",
    "Estado",
]

MARCA = "Master Beauty Salon"
LOGO = Path(__file__).parent / "assets" / "master-beauty-salon.png"
PROMO_BANNER_IMAGEN = Path(__file__).parent / "assets" / "promo-banner.png"


def normalizar_encabezados(encabezados):
    equivalencias = {
        "Duracion": "DuraciÃ³n",
        "DuraciÃƒÂ³n": "DuraciÃ³n",
    }
    return [equivalencias.get(str(valor).strip(), str(valor).strip()) for valor in encabezados]

COLUMNAS = [
    "Fecha",
    "Hora",
    "Servicio",
    "Duracion",
    "Nombre",
    "WhatsApp",
    "Estado",
]


def normalizar_encabezados(encabezados):
    equivalencias = {
        "DuraciÃ³n": "Duracion",
        "DuraciÃƒÂ³n": "Duracion",
        "DuraciÃƒÆ’Ã‚Â³n": "Duracion",
    }
    return [equivalencias.get(str(valor).strip(), str(valor).strip()) for valor in encabezados]


st.set_page_config(
    page_title=f"Agenda | {MARCA}",
    page_icon="âœ¨",
    layout="centered",
)

st.markdown(
    """
    <style>
        :root {
            --master-gold: #d6a93f;
            --master-gold-light: #f6dc8b;
            --master-black: #090909;
        }

        .stApp {
            background:
                radial-gradient(circle at 50% 0%, #29200f 0, #111 30%, #050505 72%);
            color: #f7f2e7;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        #MainMenu, footer, [data-testid="stToolbar"], .stDeployButton {
            display: none !important;
        }

        [data-testid="stAppViewBlockContainer"] {
            max-width: 860px;
            padding-top: 1rem;
            padding-bottom: 3rem;
        }

        [data-testid="stImage"] img {
            display: block;
            width: min(100%, 430px);
            margin: 0 auto 0.35rem;
            border-radius: 18px;
            box-shadow: 0 18px 60px rgba(0, 0, 0, 0.45);
        }

        .master-heading,
        .master-subheading {
            text-align: center;
        }

        .master-heading {
            margin: 0.35rem 0 0;
            color: var(--master-gold-light);
            font-family: Georgia, serif;
            font-size: clamp(1.65rem, 5vw, 2.35rem);
            letter-spacing: 0.08em;
        }

        .master-subheading {
            margin: 0.35rem 0 2rem;
            color: #cfc7b5;
            letter-spacing: 0.04em;
        }

        .promo-banner {
            position: relative;
            overflow: hidden;
            margin: 0 0 1.4rem;
            padding: 1.25rem 1.35rem;
            border: 1px solid rgba(246, 220, 139, 0.62);
            border-radius: 18px;
            background:
                linear-gradient(120deg, rgba(214, 169, 63, 0.25), transparent 60%),
                #111;
            box-shadow: 0 18px 50px rgba(0, 0, 0, 0.35);
        }

        .promo-banner::after {
            content: "M";
            position: absolute;
            right: 1rem;
            top: -1.1rem;
            color: rgba(246, 220, 139, 0.09);
            font-family: Georgia, serif;
            font-size: 8rem;
            line-height: 1;
        }

        .promo-label {
            color: var(--master-gold-light);
            font-size: 0.72rem;
            font-weight: 800;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }

        .promo-banner h2 {
            position: relative;
            z-index: 1;
            margin: 0.35rem 0;
            color: #fff4d4;
            font-family: Georgia, serif;
            font-size: 1.4rem;
        }

        .promo-banner p {
            position: relative;
            z-index: 1;
            margin: 0;
            max-width: 620px;
            color: #d8d0c0;
        }

        .monthly-promo-banner {
            margin: -0.35rem 0 1.5rem;
            border: 1px solid rgba(246, 220, 139, 0.72);
            border-radius: 18px;
            overflow: hidden;
            background: rgba(10, 10, 10, 0.88);
            box-shadow: 0 14px 36px rgba(0, 0, 0, 0.28);
        }

        .monthly-promo-banner img {
            display: block;
            width: 100%;
            height: auto;
        }

        .service-card, .promotion-card {
            height: 100%;
            padding: 1rem;
            border: 1px solid rgba(214, 169, 63, 0.35);
            border-radius: 14px;
            background: rgba(17, 17, 17, 0.78);
        }

        .service-card strong, .promotion-card strong {
            color: var(--master-gold-light);
        }

        .service-card p, .promotion-card p {
            margin: 0.35rem 0 0;
            color: #cfc7b5;
            font-size: 0.9rem;
        }

        .service-time {
            display: inline-block;
            margin-top: 0.7rem;
            color: #a99d86;
            font-size: 0.78rem;
        }

        div[data-testid="stForm"] {
            border-color: rgba(214, 169, 63, 0.5);
            background: rgba(17, 17, 17, 0.82);
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border: 1px solid var(--master-gold);
            background: linear-gradient(135deg, #b88322, #f0d379);
            color: var(--master-black);
            font-weight: 700;
        }

        .stButton > button:hover,
        .stFormSubmitButton > button:hover {
            border-color: var(--master-gold-light);
            color: #000;
        }

        .kroniq-footer {
            margin-top: 2.8rem;
            padding: 1.15rem;
            border-top: 1px solid rgba(214, 169, 63, 0.32);
            color: #aaa08e;
            text-align: center;
        }

        .kroniq-footer strong {
            color: var(--master-gold-light);
        }

        .kroniq-button {
            display: inline-block;
            margin-top: 0.8rem;
            padding: 0.62rem 1rem;
            border: 1px solid var(--master-gold);
            border-radius: 10px;
            color: #f4d982 !important;
            font-weight: 700;
            text-decoration: none !important;
        }

        .kroniq-button:hover {
            background: rgba(214, 169, 63, 0.14);
        }

        @media (max-width: 640px) {
            [data-testid="stAppViewBlockContainer"] {
                padding: 0.7rem 0.8rem 2rem;
            }

            .promo-banner {
                padding: 1rem;
            }

        }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_resource
def obtener_hoja():
    """Conecta con Google Sheets usando las credenciales de Streamlit Secrets."""
    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]
    credenciales = ServiceAccountCredentials.from_json_keyfile_dict(
        dict(st.secrets["gcp_service_account"]), scopes
    )
    cliente = gspread.authorize(credenciales)
    spreadsheet_id = st.secrets.get("spreadsheet_id", "").strip()
    if spreadsheet_id:
        libro = cliente.open_by_key(spreadsheet_id)
    else:
        libro = cliente.open(st.secrets["spreadsheet_name"])
    nombre_hoja = st.secrets.get("worksheet_name", "Citas")
    try:
        hoja = libro.worksheet(nombre_hoja)
    except gspread.WorksheetNotFound:
        hoja = libro.add_worksheet(title=nombre_hoja, rows=1000, cols=7)

    encabezados = hoja.row_values(1)
    if not encabezados:
        hoja.append_row(COLUMNAS)
    elif normalizar_encabezados(encabezados[: len(COLUMNAS)]) != COLUMNAS:
        hoja.update("A1:G1", [COLUMNAS])
        if len(encabezados) > len(COLUMNAS):
            hoja.batch_clear(["H1:Z1"])
    elif encabezados[: len(COLUMNAS)] != COLUMNAS:
        hoja.update("A1:G1", [COLUMNAS])
    return hoja


def leer_citas(hoja) -> pd.DataFrame:
    registros = hoja.get_all_records(expected_headers=COLUMNAS)
    return pd.DataFrame(registros, columns=COLUMNAS)


def se_empalman(inicio_a, fin_a, inicio_b, fin_b) -> bool:
    return inicio_a < fin_b and inicio_b < fin_a


def citas_del_dia(citas: pd.DataFrame, fecha: date):
    if citas.empty:
        return []

    fecha_texto = fecha.strftime("%Y-%m-%d")
    resultado = []
    for _, cita in citas.iterrows():
        if str(cita["Fecha"]).strip() != fecha_texto:
            continue
        if str(cita["Estado"]).strip().lower() in {"cancelada", "cancelado"}:
            continue
        try:
            inicio = datetime.combine(
                fecha, datetime.strptime(str(cita["Hora"]).strip(), "%H:%M").time()
            )
            duracion = int(cita["DuraciÃ³n"])
        except (TypeError, ValueError):
            continue
        resultado.append((inicio, inicio + timedelta(minutes=duracion)))
    return resultado


def citas_del_dia(citas: pd.DataFrame, fecha: date):
    if citas.empty:
        return []

    fecha_texto = fecha.strftime("%Y-%m-%d")
    resultado = []
    for _, cita in citas.iterrows():
        if str(cita["Fecha"]).strip() != fecha_texto:
            continue
        if str(cita["Estado"]).strip().lower() in {"cancelada", "cancelado"}:
            continue
        try:
            inicio = datetime.combine(
                fecha, datetime.strptime(str(cita["Hora"]).strip(), "%H:%M").time()
            )
            duracion = int(cita["Duracion"])
        except (KeyError, TypeError, ValueError):
            continue
        resultado.append((inicio, inicio + timedelta(minutes=duracion)))
    return resultado


def horarios_disponibles(fecha: date, duracion: int, citas: pd.DataFrame):
    if fecha.weekday() in (6, 0):  # domingo y lunes
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
        toca_cita = any(
            se_empalman(inicio, fin, inicio_ocupado, fin_ocupado)
            for inicio_ocupado, fin_ocupado in ocupadas
        )
        if not toca_comida and not toca_cita:
            disponibles.append(inicio.strftime("%H:%M"))
        inicio += timedelta(minutes=INTERVALO_MINUTOS)
    return disponibles


def guardar_cita(hoja, fecha, hora, servicio, duracion, nombre, whatsapp):
    # Se vuelve a consultar justo antes de guardar para evitar usar datos obsoletos.
    citas_actuales = leer_citas(hoja)
    if hora not in horarios_disponibles(fecha, duracion, citas_actuales):
        return False

    fila = [
        fecha.strftime("%Y-%m-%d"),
        hora,
        servicio,
        duracion,
        nombre.strip(),
        whatsapp,
        "Confirmada",
    ]
    hoja.append_row(fila, value_input_option="RAW")

    ultima_fila = hoja.row_values(len(hoja.get_all_values()))
    if ultima_fila[: len(fila)] != [str(valor) for valor in fila]:
        raise RuntimeError("La cita se envio a Google Sheets, pero no se pudo verificar.")
    return True


def imagen_data_uri(ruta: Path):
    if not ruta.exists():
        return None

    mime = "image/png"
    if ruta.suffix.lower() in {".jpg", ".jpeg"}:
        mime = "image/jpeg"
    elif ruta.suffix.lower() == ".webp":
        mime = "image/webp"

    contenido = b64encode(ruta.read_bytes()).decode("ascii")
    return f"data:{mime};base64,{contenido}"


def render_banner_promociones():
    banner = imagen_data_uri(PROMO_BANNER_IMAGEN)
    if not banner:
        return

    st.markdown(
        f"""
        <div class="monthly-promo-banner">
            <img src="{banner}" alt="Promociones del mes">
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_encabezado():
    st.image(str(LOGO), use_container_width=True)
    st.markdown(
        f'<h1 class="master-heading">Agenda {MARCA}</h1>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<p class="master-subheading">Reserva tu momento de belleza.</p>',
        unsafe_allow_html=True,
    )
    st.markdown(
        f"""
        <div class="promo-banner">
            <div class="promo-label">{escape(PROMOCION_PRINCIPAL['etiqueta'])}</div>
            <h2>{escape(PROMOCION_PRINCIPAL['titulo'])}</h2>
            <p>{escape(PROMOCION_PRINCIPAL['detalle'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    render_banner_promociones()


def render_catalogo():
    st.markdown("### Nuestros servicios")
    columnas = st.columns(len(SERVICIOS))
    for columna, (nombre, datos) in zip(columnas, SERVICIOS.items()):
        with columna:
            st.markdown(
                f"""
                <div class="service-card">
                    <strong>{escape(nombre)}</strong>
                    <p>{escape(datos['descripcion'])}</p>
                    <span class="service-time">DuraciÃ³n aproximada: {datos['duracion']} min</span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_promociones():
    st.markdown("### Promociones y novedades")
    st.caption("Este espacio puede actualizarse cada temporada sin modificar la agenda.")
    for promocion in PROMOCIONES:
        st.markdown(
            f"""
            <div class="promotion-card">
                <strong>{escape(promocion['titulo'])}</strong>
                <p>{escape(promocion['detalle'])}</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.write("")


def render_reserva(hoja, citas):
    st.markdown('<div id="reservar"></div>', unsafe_allow_html=True)
    st.markdown("### Reserva tu cita")
    st.caption("Elige tu servicio, fecha y horario disponible.")

    servicio = st.selectbox("1. Selecciona servicio", list(SERVICIOS))
    duracion = SERVICIOS[servicio]["duracion"]
    fecha = st.date_input("2. Selecciona fecha", min_value=date.today())

    if fecha.weekday() in (6, 0):
        st.warning(f"{MARCA} permanece cerrado los domingos y lunes.")
        return

    horarios = horarios_disponibles(fecha, duracion, citas)
    if not horarios:
        st.info("No hay horarios disponibles para ese servicio en esta fecha.")
        return

    with st.form("formulario_cita", clear_on_submit=True):
        hora = st.selectbox("3. Selecciona hora disponible", horarios)
        nombre = st.text_input("4. Escribe tu nombre")
        whatsapp = st.text_input(
            "5. Escribe tu WhatsApp (10 dÃ­gitos)", max_chars=10
        )
        confirmar = st.form_submit_button("6. Confirmar cita")

    if confirmar:
        if not nombre.strip():
            st.error("Escribe tu nombre.")
        elif not (whatsapp.isdigit() and len(whatsapp) == 10):
            st.error("El WhatsApp debe contener exactamente 10 dÃ­gitos.")
        else:
            try:
                guardada = guardar_cita(
                    hoja, fecha, hora, servicio, duracion, nombre, whatsapp
                )
                if guardada:
                    st.success(
                        f"Cita confirmada para {nombre.strip()} el "
                        f"{fecha.strftime('%d/%m/%Y')} a las {hora}."
                    )
                else:
                    st.error(
                        "Ese horario acaba de ser ocupado. Recarga la pÃ¡gina y elige otro."
                    )
            except Exception as error:
                st.error("No se pudo guardar la cita. Intenta nuevamente.")
                st.exception(error)


def render_kroniq():
    enlace = (
        f"https://wa.me/{KRONIQ_WHATSAPP}?text="
        f"{quote_plus(KRONIQ_MENSAJE)}"
    )
    st.markdown(
        f"""
        <div class="kroniq-footer">
            <div>Agenda digital desarrollada por <strong>Kroniq</strong></div>
            <div>Convierte tus citas en una experiencia profesional.</div>
            <a class="kroniq-button" href="{escape(enlace)}" target="_blank"
               rel="noopener noreferrer">Quiero una agenda para mi negocio</a>
        </div>
        """,
        unsafe_allow_html=True,
    )


def main():
    render_encabezado()

    try:
        hoja = obtener_hoja()
        citas = leer_citas(hoja)
    except Exception as error:
        st.error("No fue posible conectar con Google Sheets. Revisa los Secrets y permisos.")
        st.exception(error)
        render_kroniq()
        st.stop()

    reservar, promociones = st.tabs(["Reservar cita", "Promociones"])
    with reservar:
        render_catalogo()
        st.divider()
        render_reserva(hoja, citas)
    with promociones:
        render_promociones()

    render_kroniq()


if __name__ == "__main__":
    main()
