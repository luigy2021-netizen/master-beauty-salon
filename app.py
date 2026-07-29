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
        ("Experiencia Master", "Combina tus servicios favoritos en una sola visita."),
        ("Color y cuidado", "Consulta las opciones disponibles para renovar tu color."),
        (
            "Tu próxima visita",
            "Agenda con anticipación y elige el horario que más te convenga.",
        ),
    ]

    COLUMNAS = [
        "Fecha",
        "Hora",
        "Servicio",
        "Duracion",
        "Nombre",
        "WhatsApp",
        "Estado",
    ]

    HORA_APERTURA = time(10, 0)
    HORA_CIERRE = time(20, 0)
    COMIDA_INICIO = time(14, 0)
    COMIDA_FIN = time(15, 0)
    INTERVALO = 30

    KRONIQ_WHATSAPP = "526563079754"
    KRONIQ_MENSAJE = (
        "Hola, quiero información sobre una agenda digital para mi negocio."
    )


    st.set_page_config(
        page_title=f"Agenda | {MARCA}",
        page_icon="✨",
        layout="centered",
    )

    st.markdown(
        """
        <style>
        :root {
            --gold: #d6a93f;
            --gold-light: #f6dc8b;
            --ink: #090909;
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
            width: min(100%, 540px);
            margin: 0 auto 0.5rem;
            border-radius: 18px;
            box-shadow: 0 18px 60px rgba(0, 0, 0, 0.45);
        }

        .master-title {
            margin: 0.4rem 0 0;
            color: var(--gold-light);
            text-align: center;
            font-family: Georgia, serif;
            font-size: clamp(1.7rem, 5vw, 2.5rem);
            letter-spacing: 0.08em;
        }

        .master-subtitle {
            margin: 0.35rem 0 1.8rem;
            color: #cfc7b5;
            text-align: center;
        }

        .service-card,
        .promotion-card {
            height: 100%;
            padding: 1rem;
            border: 1px solid rgba(214, 169, 63, 0.38);
            border-radius: 14px;
            background: rgba(17, 17, 17, 0.82);
        }

        .service-card strong,
        .promotion-card strong {
            color: var(--gold-light);
        }

        .service-card p,
        .promotion-card p {
            margin: 0.35rem 0 0;
            color: #cfc7b5;
            font-size: 0.9rem;
        }

        .service-time {
            display: block;
            margin-top: 0.7rem;
            color: #a99d86;
            font-size: 0.78rem;
        }

        div[data-testid="stForm"] {
            border-color: rgba(214, 169, 63, 0.5);
            background: rgba(17, 17, 17, 0.85);
        }

        .stButton > button,
        .stFormSubmitButton > button {
            border: 1px solid var(--gold);
            background: linear-gradient(135deg, #b88322, #f0d379);
            color: var(--ink);
            font-weight: 700;
        }

        .kroniq-footer {
            margin-top: 2.8rem;
            padding: 1.15rem;
            border-top: 1px solid rgba(214, 169, 63, 0.32);
            color: #aaa08e;
            text-align: center;
        }

        .kroniq-footer strong {
            color: var(--gold-light);
        }

        .kroniq-button {
            display: inline-block;
            margin-top: 0.8rem;
            padding: 0.62rem 1rem;
            border: 1px solid var(--gold);
            border-radius: 10px;
            color: #f4d982 !important;
            font-weight: 700;
            text-decoration: none !important;
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


    @st.cache_resource
    def autorizar_google():
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive",
        ]

        credenciales = Credentials.from_service_account_info(
            dict(st.secrets["gcp_service_account"]),
            scopes=scopes,
        )

        return gspread.authorize(credenciales)


    def obtener_hoja():
        cliente = autorizar_google()
        spreadsheet_id = str(
            st.secrets.get("spreadsheet_id", "")
        ).strip()

        if spreadsheet_id:
            libro = cliente.open_by_key(spreadsheet_id)
        else:
            libro = cliente.open(
                st.secrets["spreadsheet_name"]
            )

        nombre = str(
            st.secrets.get("worksheet_name", "Citas")
        )

        try:
            hoja = libro.worksheet(nombre)
        except gspread.WorksheetNotFound:
            hoja = libro.add_worksheet(
                title=nombre,
                rows=1000,
                cols=7,
            )

        encabezados = hoja.row_values(1)

        if encabezados[: len(COLUMNAS)] != COLUMNAS:
            hoja.update(
                values=[COLUMNAS],
                range_name="A1:G1",
            )

        return hoja


    def leer_citas(hoja):
        if hoja is None:
            return pd.DataFrame(columns=COLUMNAS)

        registros = hoja.get_all_records(
            expected_headers=COLUMNAS
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
        resultado = []
        fecha_texto = fecha.strftime("%Y-%m-%d")

        for _, cita in citas.iterrows():
            if (
                str(cita.get("Fecha", "")).strip()
                != fecha_texto
            ):
                continue

            if (
                str(cita.get("Estado", "")).strip().lower()
                in {"cancelada", "cancelado"}
            ):
                continue

            try:
                inicio = datetime.combine(
                    fecha,
                    datetime.strptime(
                        str(cita["Hora"]).strip(),
                        "%H:%M",
                    ).time(),
                )

                duracion = int(
                    cita["Duracion"]
                )

            except (
                KeyError,
                TypeError,
                ValueError,
            ):
                continue

            resultado.append(
                (
                    inicio,
                    inicio + timedelta(
                        minutes=duracion
                    ),
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

            if (
                not toca_comida
                and not toca_cita
            ):
                disponibles.append(
                    inicio.strftime("%H:%M")
                )

            inicio += timedelta(
                minutes=INTERVALO
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

        hoja.append_row(
            [
                fecha.strftime("%Y-%m-%d"),
                hora,
                servicio,
                duracion,
                nombre.strip(),
                whatsapp,
                "Confirmada",
            ],
            value_input_option="RAW",
        )

        return True


    def mostrar_encabezado():
        if LOGO.exists():
            st.image(
                str(LOGO),
                use_container_width=True,
            )

        st.markdown(
            f'<h1 class="master-title">Agenda {MARCA}</h1>',
            unsafe_allow_html=True,
        )

        st.markdown(
            '<p class="master-subtitle">'
            'Reserva tu momento de belleza.'
            '</p>',
            unsafe_allow_html=True,
        )

        if BANNER.exists():
            st.image(
                str(BANNER),
                use_container_width=True,
            )


    def mostrar_servicios():
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


    def mostrar_reserva(hoja, citas):
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
                "este servicio en esta fecha."
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
            if hoja is None:
                st.error(
                    "El registro de citas está "
                    "temporalmente fuera de servicio."
                )

            elif not nombre.strip():
                st.error(
                    "Escribe tu nombre."
                )

            elif not (
                whatsapp.isdigit()
                and len(whatsapp) == 10
            ):
                st.error(
                    "El WhatsApp debe contener "
                    "exactamente 10 dígitos."
                )

            else:
                try:
                    guardada = guardar_cita(
                        hoja,
                        fecha,
                        hora,
                        servicio,
                        duracion,
                        nombre,
                        whatsapp,
                    )

                    if guardada:
                        st.success(
                            f"Cita confirmada para "
                            f"{nombre.strip()} el "
                            f"{fecha.strftime('%d/%m/%Y')} "
                            f"a las {hora}."
                        )

                    else:
                        st.error(
                            "Ese horario acaba de ser ocupado. "
                            "Recarga la página y elige otro."
                        )

                except Exception:
                    st.error(
                        "No fue posible guardar la cita. "
                        "Espera unos segundos e intenta nuevamente."
                    )


    def mostrar_promociones():
        st.markdown(
            "### Promociones y novedades"
        )

        st.caption(
            "Este espacio puede actualizarse "
            "cada temporada."
        )

        for titulo, detalle in PROMOCIONES:
            st.markdown(
                f"""
                <div class="promotion-card">
                    <strong>
                        {escape(titulo)}
                    </strong>

                    <p>
                        {escape(detalle)}
                    </p>
                </div>
                """,
                unsafe_allow_html=True,
            )

            st.write("")


    def mostrar_kroniq():
        enlace = (
            f"https://wa.me/{KRONIQ_WHATSAPP}"
            f"?text={quote_plus(KRONIQ_MENSAJE)}"
        )

        st.markdown(
            f"""
            <div class="kroniq-footer">
                <div>
                    Agenda digital desarrollada por
                    <strong>Kroniq</strong>
                </div>

                <div>
                    Convierte tus citas en una
                    experiencia profesional.
                </div>

                <a
                    class="kroniq-button"
                    href="{escape(enlace)}"
                    target="_blank"
                    rel="noopener noreferrer"
                >
                    Quiero una agenda para mi negocio
                </a>
            </div>
            """,
            unsafe_allow_html=True,
        )


    def main():
        mostrar_encabezado()

        hoja = None
        citas = pd.DataFrame(
            columns=COLUMNAS
        )

        try:
            hoja = obtener_hoja()
            citas = leer_citas(hoja)

        except Exception:
            st.warning(
                "La agenda está visible, pero "
                "Google Sheets no respondió. "
                "Las reservaciones se reactivarán "
                "cuando vuelva la conexión."
            )

        reservar, promociones = st.tabs(
            [
                "Reservar cita",
                "Promociones",
            ]
        )

        with reservar:
            mostrar_servicios()
            st.divider()
            mostrar_reserva(
                hoja,
                citas,
            )

        with promociones:
            mostrar_promociones()

        mostrar_kroniq()


    if __name__ == "__main__":
        main()
