import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import os
from io import BytesIO
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ========== CONFIGURACIÓN ==========
capacidad_bus = 30
inicio = datetime.strptime("06:00", "%H:%M")
fin = datetime.strptime("10:00", "%H:%M")
frecuencia = 10
archivo_reservas = "reservas.csv"

# Estado inicial
if "reserva_exitosa" not in st.session_state:
    st.session_state.reserva_exitosa = None
if "nombre_usuario" not in st.session_state:
    st.session_state.nombre_usuario = ""

# ========== FUNCIONES ==========
def generar_horarios():
    horarios = []
    actual = inicio
    while actual <= fin:
        horarios.append(actual.strftime("%H:%M"))
        actual += timedelta(minutes=frecuencia)
    return horarios

def cargar_reservas():
    if os.path.exists(archivo_reservas):
        return pd.read_csv(archivo_reservas)
    else:
        return pd.DataFrame(columns=["Horario", "Nombre", "Fecha", "TicketID"])

def guardar_reserva(horario, nombre):
    fecha = datetime.now().strftime("%Y-%m-%d")
    ultimo_id = 1 if reservas.empty else reservas["TicketID"].max() + 1
    nueva_reserva = pd.DataFrame([[horario, nombre, fecha, ultimo_id]],
                                 columns=["Horario", "Nombre", "Fecha", "TicketID"])
    reservas_actualizadas = pd.concat([reservas, nueva_reserva], ignore_index=True)
    reservas_actualizadas.to_csv(archivo_reservas, index=False)
    return reservas_actualizadas, nuevo_ticket(nueva_reserva.iloc[0])

def nuevo_ticket(reserva):
    return {
        "nombre": reserva["Nombre"],
        "horario": reserva["Horario"],
        "fecha": reserva["Fecha"],
        "ticket_id": int(reserva["TicketID"])
    }

def generar_pdf(ticket):
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 750, "TICKET DE RESERVA – RUTA UTC- El SALTO")
    c.setFont("Helvetica", 12)
    c.drawString(50, 700, f"Nombre: {ticket['nombre']}")
    c.drawString(50, 680, f"Horario reservado: {ticket['horario']}")
    c.drawString(50, 660, f"Fecha: {ticket['fecha']}")
    c.drawString(50, 640, f"Número de Ticket: #{ticket['ticket_id']}")
    c.save()
    buffer.seek(0)
    return buffer

# ========== INTERFAZ ==========
st.title("Sistema de Tickets – Ruta UTC- EL SALTO")
st.caption("Reserva tu puesto para el bus universitario. Capacidad máxima por unidad: 30 pasajeros.")

# Mostrar ticket
if st.session_state.reserva_exitosa:
    ticket = st.session_state.reserva_exitosa
    st.success(f"¡Reserva exitosa! Ticket #{ticket['ticket_id']} para {ticket['nombre']} – {ticket['horario']}")

    # Descargar PDF
    pdf = generar_pdf(ticket)
    st.download_button(
        label="Descargar ticket en PDF",
        data=pdf,
        file_name=f"ticket_{ticket['ticket_id']}.pdf",
        mime="application/pdf"
    )

    if st.button("Hacer nueva reserva"):
        st.session_state.reserva_exitosa = None
        st.session_state.nombre_usuario = ""
        st.rerun()

# Cargar y mostrar horarios
reservas = cargar_reservas()
horarios = generar_horarios()

if not st.session_state.reserva_exitosa:
    st.session_state.nombre_usuario = st.text_input("Ingresa tu nombre para reservar", st.session_state.nombre_usuario)

    st.subheader("Horarios disponibles:")
    for hora in horarios:
        cantidad_reservas = reservas[reservas["Horario"] == hora].shape[0]
        libres = capacidad_bus - cantidad_reservas
        ya_registrado = not reservas[
            (reservas["Horario"] == hora) &
            (reservas["Nombre"].str.lower() == st.session_state.nombre_usuario.strip().lower())
        ].empty
        estado = "LLENO" if libres == 0 else f"{libres} puestos disponibles"

        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            st.write(f"Bus de las {hora}")
        with col2:
            st.write(estado)
        with col3:
            if libres > 0:
                if ya_registrado:
                    st.write("Ya reservado")
                else:
                    if st.button(f"Reservar {hora}"):
                        if st.session_state.nombre_usuario.strip() == "":
                            st.warning("Por favor, ingresa tu nombre antes de reservar.")
                        else:
                            reservas, ticket = guardar_reserva(hora, st.session_state.nombre_usuario)
                            st.session_state.reserva_exitosa = ticket
                            st.rerun()
            else:
                st.write("No disponible")

# Panel admin
st.markdown("---")
st.subheader("Panel de administración")

with st.expander("Mostrar todas las reservas"):
    if reservas.empty:
        st.info("No hay reservas registradas.")
    else:
        st.dataframe(reservas.sort_values(by=["Horario"]))

with st.expander("Opciones avanzadas"):
    if st.button("Borrar todas las reservas"):
        try:
            os.remove(archivo_reservas)
            st.success("Todas las reservas han sido eliminadas.")
            st.session_state.nombre_usuario = ""
            st.session_state.reserva_exitosa = None
            st.rerun()
        except FileNotFoundError:
            st.warning("No hay reservas registradas aún.")