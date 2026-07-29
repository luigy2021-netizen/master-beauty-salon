from datetime import date, datetime, time, timedelta
from html import escape
from pathlib import Path
from urllib.parse import quote_plus
import time as time_module

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
        "descripcion": "Diseño de corte adaptado a tu estilo.",
    },
    "Tinte": {
        "duracion": 120,
        "descripcion": "Servicio de color con atención dedicada.",
    },
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
        "titulo": "Tu próxima visita",
        "detalle": "Agenda con anticipación y elige el horario que más te convenga.",
    },
]

KRONIQ_WHATSAPP = "526563079754"
KRONIQ_MENSAJE = (
    "Hola, quiero información sobre una agenda digital para mi negocio."
)

HORA_APERTURA = time(10, 0)
HORA_CIERRE = time(20, 0)
COMIDA_INICIO = time(14, 0)
COMIDA_FIN = time(15, 0)
INTERVALO_MINUTOS = 30

COLUMNAS = [
    "Fecha",
    "Hora",
    "Servicio",
    "Duracion",
    "Nombre",
    "WhatsApp",
    "Estado",
]

MARCA = "Master Beauty Salon"

LOGO = (
    Path(__file__).parent
    / "assets"
    / "master-beauty-salon.png"
)

PROMO_BANNER_IMAGEN = (
    Path(__file__).parent
    / "assets"
    / "promo-banner.png"
)


def normalizar_encabezados(encabezados):
    equivalencias = {
        "Duración": "Duracion",
        "DuraciÃ³n": "Duracion",
        "DuraciÃƒÂ³n": "Duracion",
    }

    return [
        equivalencias.get(
            str(valor).strip(),
            str(valor).strip(),
        )
        for valor in encabezados
    ]


st.set_page_config(
    page_title=f"Agenda | {MARCA}",
    page_icon="✨",
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
                radial-gradient(
                    circle at 50% 0%,
                    #29200f 0,
                    #111 30%,
                    #050505 72%
                );
            color: #f7f2e7;
        }

        [data-testid="stHeader"] {
            background: transparent;
        }

        #MainMenu,
        footer,
        [data-testid="stToolbar"],
        .stDeployButton {
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

        .service-card,
        .promotion-card {
            height: 100%;
            padding: 1rem;
            border: 1px solid rgba(214, 169, 63, 0.35);
            border-radius: 14px;
            background: rgba(17, 17, 17, 0.78);
        }

        .service-card strong,
        .promotion-card strong {
            color: var(--master-gold-light);
        }

        .service-card p,
        .promotion-card p {
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
            background: linear-gradient(
                135deg,
                #b88322,
                #f0d379
            );
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
        }
    </style>
    """,
    unsafe_allow_html=True,
)


def ejecutar_google(operacion, *args, **kwargs):
    """
    Reintenta automáticamente las solicitudes cuando
    Google Sheets responde con un error temporal.
    """

    for intento in range(4):
        try:
            return operacion(*args, **kwargs)

        except gspread.exceptions.APIError as error:
            codigo = getattr(
                error.response,
                "status_code",
                None,
            )

            error_temporal = codigo in (
                429,
                500,
                502,
                503,
                504,
            )

            if not error_temporal or intento == 3:
                raise

            segundos = 2 ** intento
            time_module.sleep(segundos)


@st.cache_resource
def obtener_hoja():
    """
    Conecta con Google Sheets usando las credenciales
    guardadas en Streamlit Secrets.
    """

    scopes = [
        "https://spreadsheets.google.com/feeds",
        "https://www.googleapis.com/auth/drive",
    ]

    credenciales = (
        ServiceAccountCredentials.from_json_keyfile_dict(
            dict(st.secrets["gcp_service_account"]),
            scopes,
        )
    )

    cliente = gspread.authorize(credenciales)

    spreadsheet_id = st.secrets.get(
        "spreadsheet_id",
        "",
    ).strip()

    if spreadsheet_id:
        libro = ejecutar_google(
            cliente.open_by_key,
            spreadsheet_id,
        )
    else:
        libro = ejecutar_google(
            cliente.open,
            st.secrets["spreadsheet_name"],
        )

    nombre_hoja = st.secrets.get(
        "worksheet_name",
        "Citas",
    )

    try:
        hoja = ejecutar_google(
            libro.worksheet,
            nombre_hoja,
        )

    except gspread.WorksheetNotFound:
        hoja = ejecutar_google(
            libro.add_worksheet,
            title=nombre_hoja,
            rows=1000,
            cols=7,
        )

    encabezados = ejecutar_google(
        hoja.row_values,
        1,
    )

    if not encabezados:
        ejecutar_google(
            hoja.append_row,
            COLUMNAS,
        )

    elif (
        normalizar_encabezados(
            encabezados[: len(COLUMNAS)]
        )
        != COLUMNAS
    ):
        ejecutar_google(
            hoja.update,
            "A1:G1",
            [COLUMNAS],
        )

        if len(encabezados) > len(COLUMNAS):
            ejecutar_google(
                hoja.batch_clear,
                ["H1:Z1"],
            )

    elif encabezados[: len(COLUMNAS)] != COLUMNAS:
        ejecutar_google(
            hoja.update,
            "A1:G1",
            [COLUMNAS],
        )

    return hoja


def leer_citas(hoja):
    registros = ejecutar_google(
        hoja.get_all_records,
        expected_headers=COLUMNAS,
    )

    return pd.DataFrame(
        registros,
        columns=COLUMNAS,
    )


def se_empalman(
    inicio_a,
    fin_a,
    inicio_b,
    fin_b,
):
    return (
        inicio_a < fin_b
        and inicio_b < fin_a
    )


def citas_del_dia(citas, fecha):
    if citas.empty:
        return []

    fecha_texto = fecha.strftime("%Y-%m-%d")
    resultado = []

    for _, cita in citas.iterrows():
        if str(cita["Fecha"]).strip() != fecha_texto:
            continue

        if str(cita["Estado"]).strip().lower() in {
            "cancelada",
            "cancelado",
        }:
            continue

        try:
            inicio = datetime.combine(
                fecha,
                datetime.strptime(
                    str(cita["Hora"]).strip(),
                    "%H:%M",
                ).time(),
            )

            duracion = int(cita["Duracion"])

        except (
            KeyError,
            TypeError,
            ValueError,
        ):
            continue

        resultado.append(
            (
                inicio,
                inicio + timedelta(minutes=duracion),
            )
        )

    return resultado


def horarios_disponibles(
    fecha,
    duracion,
    citas,
):
    if fecha.weekday() == 6:
        return []

    apertura = datetime.combine(
        fecha,
        HORA_APERTURA,
    )

    cierre = datetime.combine(
        fecha,
        HORA_CIERRE,
    )

    comida_inicio = datetime.combine(
        fecha,
        COMIDA_INICIO,
    )

    comida_fin = datetime.combine(
        fecha,
        COMIDA_FIN,
    )

    ocupadas = citas_del_dia(
        citas,
        fecha,
    )

    disponibles = []
    inicio = apertura

    while (
        inicio + timedelta(minutes=duracion)
        <= cierre
    ):
        fin = inicio + timedelta(
            minutes=duracion
        )

        toca_comida = se_empalman(
            inicio,
            fin,
            comida_inicio,
            comida_fin,
        )

        toca_cita = any(
            se_empalman(
                inicio,
                fin,
                inicio_ocupado,
                fin_ocupado,
            )
            for inicio_ocupado, fin_ocupado
            in ocupadas
        )

        if not toca_comida and not toca_cita:
            disponibles.append(
                inicio.strftime("%H:%M")
            )

        inicio += timedelta(
            minutes=INTERVALO_MINUTOS
        )

    return disponibles


def guardar_cita(
    hoja,
    fecha,
    hora,
    servicio,
    duracion,
    nombre,
    whatsapp,
):
    citas_actuales = leer_citas(hoja)

    if hora not in horarios_disponibles(
        fecha,
        duracion,
        citas_actuales,
    ):
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

    ejecutar_google(
        hoja.append_row,
        fila,
        value_input_option="RAW",
    )

    valores = ejecutar_google(
        hoja.get_all_values
    )

    ultima_fila = ejecutar_google(
        hoja.row_values,
        len(valores),
    )

    if (
        ultima_fila[: len(fila)]
        != [str(valor) for valor in fila]
    ):
        raise RuntimeError(
            "La cita llegó a Google Sheets, "
            "pero no fue posible verificarla."
        )

    return True


def render_banner_promociones():
    if not PROMO_BANNER_IMAGEN.exists():
        st.warning(
            "Banner de promociones no encontrado."
        )
        return

    st.image(
        str(PROMO_BANNER_IMAGEN),
        use_container_width=True,
    )


def render_encabezado():
    st.image(
        str(LOGO),
        use_container_width=True,
    )

    st.markdown(
        f"""
        <h1 class="master-heading">
            Agenda {MARCA}
        </h1>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <p class="master-subheading">
            Reserva tu momento de belleza.
        </p>
        """,
        unsafe_allow_html=True,
    )

    render_banner_promociones()


def render_catalogo():
    st.markdown("### Nuestros servicios")

    columnas = st.columns(
        len(SERVICIOS)
    )

    for columna, (
        nombre,
        datos,
    ) in zip(
        columnas,
        SERVICIOS.items(),
    ):
        with columna:
            st.markdown(
                f"""
                <div class="service-card">
                    <strong>
                        {escape(nombre)}
                    </strong>

                    <p>
                        {escape(datos["descripcion"])}
                    </p>

                    <span class="service-time">
                        Duración aproximada:
                        {datos["duracion"]} min
                    </span>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_promociones():
    st.markdown(
        "### Promociones y novedades"
    )

    st.caption(
        "Este espacio puede actualizarse "
        "cada temporada sin modificar la agenda."
    )

    for promocion in PROMOCIONES:
        st.markdown(
            f"""
            <div class="promotion-card">
                <strong>
                    {escape(promocion["titulo"])}
                </strong>

                <p>
                    {escape(promocion["detalle"])}
                </p>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.write("")


def render_reserva(
    hoja,
    citas,
):
    st.markdown(
        '<div id="reservar"></div>',
        unsafe_allow_html=True,
    )

    st.markdown("### Reserva tu cita")

    st.caption(
        "Elige tu servicio, fecha "
        "y horario disponible."
    )

    servicio = st.selectbox(
        "1. Selecciona servicio",
        list(SERVICIOS),
    )

    duracion = SERVICIOS[
        servicio
    ]["duracion"]

    fecha = st.date_input(
        "2. Selecciona fecha",
        min_value=date.today(),
    )

    if fecha.weekday() == 6:
        st.warning(
            f"{MARCA} permanece cerrado "
            "los domingos."
        )
        return

    horarios = horarios_disponibles(
        fecha,
        duracion,
        citas,
    )

    if not horarios:
        st.info(
            "No hay horarios disponibles para "
            "ese servicio en esta fecha."
        )
        return

    with st.form(
        "formulario_cita",
        clear_on_submit=True,
    ):
        hora = st.selectbox(
            "3. Selecciona hora disponible",
            horarios,
        )

        nombre = st.text_input(
            "4. Escribe tu nombre"
        )

        whatsapp = st.text_input(
            "5. Escribe tu WhatsApp (10 dígitos)",
            max_chars=10,
        )

        confirmar = st.form_submit_button(
            "6. Confirmar cita"
        )

    if confirmar:
        if not nombre.strip():
            s
