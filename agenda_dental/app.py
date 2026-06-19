from flask import Flask, render_template, redirect, request, session, send_file
import calendar
import sqlite3
import csv
from datetime import datetime, timedelta
import smtplib
from email.message import EmailMessage

app = Flask(__name__)
app.secret_key = "belinda2026"

MESES = {
    1: "Enero", 2: "Febrero", 3: "Marzo", 4: "Abril",
    5: "Mayo", 6: "Junio", 7: "Julio", 8: "Agosto",
    9: "Septiembre", 10: "Octubre", 11: "Noviembre", 12: "Diciembre"
}

DIAS = {
    0: "Lunes", 1: "Martes", 2: "Miércoles", 3: "Jueves",
    4: "Viernes", 5: "Sábado", 6: "Domingo"
}

USUARIO_ADMIN = "belinda"
PASSWORD_ADMIN = "123456"

EMAIL_SISTEMA = "od.belindaballerini@gmail.com"
PASSWORD_EMAIL = "brcgmahneiawziel"
EMAIL_BELINDA = "od.belindaballerini@gmail.com"


def conectar_bd():
    return sqlite3.connect("reservas.db")


def crear_bd():
    conn = conectar_bd()

    conn.execute("""
    CREATE TABLE IF NOT EXISTS reservas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        fecha TEXT,
        hora TEXT,
        centro TEXT,
        direccion TEXT,
        servicio TEXT,
        nombre TEXT,
        rut TEXT,
        edad INTEGER,
        correo TEXT,
        telefono TEXT,
        fecha_creacion TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    conn.execute("""
    CREATE TABLE IF NOT EXISTS horarios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        dia_semana TEXT,
        hora_inicio TEXT,
        hora_fin TEXT,
        centro TEXT,
        direccion TEXT,
        activo INTEGER DEFAULT 1
    )
    """)

    conn.commit()
    conn.close()


def cargar_horarios_iniciales():
    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM horarios")
    cantidad = cursor.fetchone()[0]

    if cantidad == 0:
        horarios = [
            ("Lunes", "08:00", "13:00", "Centro Integral Cresser", "Lautaro 1070"),
            ("Martes", "08:00", "13:00", "Centro Integral Cresser", "Lautaro 1070"),
            ("Martes", "14:00", "21:30", "Centro Integral Cresser", "Lautaro 1070"),
            ("Miércoles", "08:00", "13:00", "Centro Integral Cresser", "Lautaro 1070"),
            ("Miércoles", "14:00", "21:30", "Centro Integral Cresser", "Lautaro 1070"),
            ("Viernes", "08:00", "13:00", "Centro Integral Cresser", "Lautaro 1070"),
            ("Viernes", "14:00", "21:30", "Centro Médico Aysén", "Carrera 231"),
            ("Sábado", "08:00", "13:00", "Centro Integral Cresser", "Lautaro 1070"),
            ("Sábado", "14:00", "21:30", "Centro Médico Aysén", "Carrera 231"),
            ("Domingo", "08:00", "13:00", "Centro Integral Cresser", "Lautaro 1070")
        ]

        cursor.executemany("""
            INSERT INTO horarios (
                dia_semana, hora_inicio, hora_fin, centro, direccion
            )
            VALUES (?, ?, ?, ?, ?)
        """, horarios)

        conn.commit()

    conn.close()


def enviar_correo_reserva(
    nombre,
    correo,
    fecha,
    hora,
    centro,
    direccion,
    servicio,
    telefono,
    rut,
    edad
):
    asunto_paciente = "Confirmación de Reserva Odontológica"

    cuerpo_paciente = f"""
Hola {nombre},

Su reserva ha sido registrada correctamente.

Fecha: {fecha}
Hora: {hora}
Lugar: {centro}
Dirección: {direccion}
Tipo de atención: {servicio}

Le solicitamos presentarse 15 minutos antes de su hora agendada para realizar el registro correspondiente.

Ante cualquier inconveniente o necesidad de modificación de la cita, por favor comuníquese directamente con la profesional.

WhatsApp: +56 9 5372 3630

Belinda Ballerini
Odontóloga
"""

    asunto_belinda = "Nueva reserva registrada"

    cuerpo_belinda = f"""
Nueva reserva registrada.

Paciente: {nombre}
RUT: {rut}
Edad: {edad}
Teléfono: {telefono}
Correo: {correo}

Fecha: {fecha}
Hora: {hora}
Lugar: {centro}
Dirección: {direccion}
Tipo de atención: {servicio}
"""

    try:
        msg_paciente = EmailMessage()
        msg_paciente["Subject"] = asunto_paciente
        msg_paciente["From"] = EMAIL_SISTEMA
        msg_paciente["To"] = correo
        msg_paciente.set_content(cuerpo_paciente)

        msg_belinda = EmailMessage()
        msg_belinda["Subject"] = asunto_belinda
        msg_belinda["From"] = EMAIL_SISTEMA
        msg_belinda["To"] = EMAIL_BELINDA
        msg_belinda.set_content(cuerpo_belinda)

        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as smtp:
            smtp.login(EMAIL_SISTEMA, PASSWORD_EMAIL)
            smtp.send_message(msg_paciente)
            smtp.send_message(msg_belinda)

    except Exception as e:
        print("Error enviando correo:", e)


crear_bd()
cargar_horarios_iniciales()


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        usuario = request.form.get("usuario")
        password = request.form.get("password")

        if usuario == USUARIO_ADMIN and password == PASSWORD_ADMIN:
            session["admin"] = True
            return redirect("/admin")

        return render_template("login.html", error=True)

    return render_template("login.html", error=False)


@app.route("/logout")
def logout():
    session.pop("admin", None)
    return redirect("/login")


@app.route("/")
def inicio():
    return redirect("/calendario/2026/6")


@app.route("/calendario/<int:anio>/<int:mes>")
def calendario_mes(anio, mes):
    if mes < 6:
        mes = 6

    if mes > 12:
        mes = 12

    cal = calendar.monthcalendar(anio, mes)

    mes_anterior = mes - 1 if mes > 6 else None
    mes_siguiente = mes + 1 if mes < 12 else None

    return render_template(
        "inicio.html",
        calendario=cal,
        mes=MESES[mes],
        numero_mes=mes,
        anio=anio,
        mes_anterior=mes_anterior,
        mes_siguiente=mes_siguiente
    )

@app.route("/dia/<int:anio>/<int:mes>/<int:dia>")
def ver_dia(anio, mes, dia):
    fecha_numero = calendar.weekday(anio, mes, dia)
    nombre_dia = DIAS[fecha_numero]

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT hora_inicio, hora_fin, centro, direccion
        FROM horarios
        WHERE dia_semana = ?
        AND activo = 1
        ORDER BY hora_inicio
    """, (nombre_dia,))

    bloques = cursor.fetchall()

    horas = []

    for bloque in bloques:
        hora_inicio = bloque[0]
        hora_fin = bloque[1]
        centro = bloque[2]
        direccion = bloque[3]

        horas += generar_horas(hora_inicio, hora_fin, centro, direccion)

    fecha_texto = f"{nombre_dia} {dia} de {MESES[mes]}"

    cursor.execute("""
        SELECT hora
        FROM reservas
        WHERE fecha = ?
    """, (fecha_texto,))

    horas_reservadas = [fila[0] for fila in cursor.fetchall()]

    conn.close()

    horas = [
        hora for hora in horas
        if hora["hora"] not in horas_reservadas
    ]

    return render_template(
        "dia.html",
        nombre_dia=nombre_dia,
        dia=dia,
        mes=MESES[mes],
        horas=horas
    )


def generar_horas(inicio, fin, centro, direccion):
    horas = []

    hora_actual = datetime.strptime(inicio, "%H:%M")
    hora_fin = datetime.strptime(fin, "%H:%M")

    while hora_actual < hora_fin:
        horas.append({
            "hora": hora_actual.strftime("%H:%M"),
            "centro": centro,
            "direccion": direccion
        })

        hora_actual += timedelta(hours=1)

    return horas


@app.route("/reservar")
def reservar():
    fecha = request.args.get("fecha")
    hora = request.args.get("hora")
    centro = request.args.get("centro")
    direccion = request.args.get("direccion")

    return render_template(
        "reservar.html",
        fecha=fecha,
        hora=hora,
        centro=centro,
        direccion=direccion
    )


@app.route("/confirmacion", methods=["POST"])
def confirmacion():
    fecha = request.form.get("fecha")
    hora = request.form.get("hora")
    centro = request.form.get("centro")
    direccion = request.form.get("direccion")
    servicio = request.form.get("servicio")
    nombre = request.form.get("nombre")
    rut = request.form.get("rut")
    edad = request.form.get("edad")
    correo = request.form.get("correo")
    telefono = request.form.get("telefono")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id
        FROM reservas
        WHERE fecha = ? AND hora = ?
    """, (fecha, hora))

    reserva_existente = cursor.fetchone()

    if reserva_existente:
        conn.close()
        return "Lo sentimos, esta hora acaba de ser reservada por otro paciente. Por favor vuelva al calendario y seleccione otra hora."

    cursor.execute("""
        INSERT INTO reservas (
            fecha, hora, centro, direccion, servicio,
            nombre, rut, edad, correo, telefono
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        fecha, hora, centro, direccion, servicio,
        nombre, rut, edad, correo, telefono
    ))

    conn.commit()
    conn.close()

    enviar_correo_reserva(
        nombre,
        correo,
        fecha,
        hora,
        centro,
        direccion,
        servicio,
        telefono,
        rut,
        edad
    )

    return render_template(
        "confirmacion.html",
        fecha=fecha,
        hora=hora,
        centro=centro,
        direccion=direccion
    )


@app.route("/admin")
def admin():
    if not session.get("admin"):
        return redirect("/login")

    busqueda = request.args.get("buscar", "")

    conn = conectar_bd()
    cursor = conn.cursor()

    if busqueda:
        cursor.execute("""
            SELECT *
            FROM reservas
            WHERE nombre LIKE ?
               OR rut LIKE ?
               OR telefono LIKE ?
            ORDER BY fecha, hora
        """, (
            f"%{busqueda}%",
            f"%{busqueda}%",
            f"%{busqueda}%"
        ))
    else:
        cursor.execute("""
            SELECT *
            FROM reservas
            ORDER BY fecha, hora
        """)

    reservas = cursor.fetchall()

    total_reservas = len(reservas)
    total_adulto = sum(1 for r in reservas if r[5] == "Ingreso Adulto")
    total_pediatrico = sum(1 for r in reservas if r[5] == "Ingreso Pediátrico")
    total_cresser = sum(1 for r in reservas if r[3] == "Centro Integral Cresser")
    total_aysen = sum(1 for r in reservas if r[3] == "Centro Médico Aysén")

    conn.close()

    return render_template(
        "admin.html",
        reservas=reservas,
        busqueda=busqueda,
        total_reservas=total_reservas,
        total_adulto=total_adulto,
        total_pediatrico=total_pediatrico,
        total_cresser=total_cresser,
        total_aysen=total_aysen
    )


@app.route("/admin/eliminar/<int:id>")
def eliminar_reserva(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM reservas WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin")


@app.route("/admin/horarios")
def admin_horarios():
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM horarios
        ORDER BY
            CASE dia_semana
                WHEN 'Lunes' THEN 1
                WHEN 'Martes' THEN 2
                WHEN 'Miércoles' THEN 3
                WHEN 'Jueves' THEN 4
                WHEN 'Viernes' THEN 5
                WHEN 'Sábado' THEN 6
                WHEN 'Domingo' THEN 7
            END,
            hora_inicio
    """)

    horarios = cursor.fetchall()

    conn.close()

    return render_template(
        "horarios.html",
        horarios=horarios
    )


@app.route("/admin/horarios/agregar", methods=["POST"])
def agregar_horario():
    if not session.get("admin"):
        return redirect("/login")

    dia_semana = request.form.get("dia_semana")
    hora_inicio = request.form.get("hora_inicio")
    hora_fin = request.form.get("hora_fin")
    centro = request.form.get("centro")
    direccion = request.form.get("direccion")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO horarios (
            dia_semana, hora_inicio, hora_fin, centro, direccion, activo
        )
        VALUES (?, ?, ?, ?, ?, 1)
    """, (
        dia_semana, hora_inicio, hora_fin, centro, direccion
    ))

    conn.commit()
    conn.close()

    return redirect("/admin/horarios")


@app.route("/admin/horarios/editar/<int:id>", methods=["POST"])
def editar_horario(id):
    if not session.get("admin"):
        return redirect("/login")

    dia_semana = request.form.get("dia_semana")
    hora_inicio = request.form.get("hora_inicio")
    hora_fin = request.form.get("hora_fin")
    centro = request.form.get("centro")
    direccion = request.form.get("direccion")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        UPDATE horarios
        SET dia_semana = ?,
            hora_inicio = ?,
            hora_fin = ?,
            centro = ?,
            direccion = ?
        WHERE id = ?
    """, (
        dia_semana, hora_inicio, hora_fin, centro, direccion, id
    ))

    conn.commit()
    conn.close()

    return redirect("/admin/horarios")


@app.route("/admin/horarios/estado/<int:id>")
def cambiar_estado_horario(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("SELECT activo FROM horarios WHERE id = ?", (id,))
    resultado = cursor.fetchone()

    if resultado:
        nuevo_estado = 0 if resultado[0] == 1 else 1

        cursor.execute("""
            UPDATE horarios
            SET activo = ?
            WHERE id = ?
        """, (nuevo_estado, id))

        conn.commit()

    conn.close()

    return redirect("/admin/horarios")


@app.route("/admin/horarios/eliminar/<int:id>")
def eliminar_horario(id):
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("DELETE FROM horarios WHERE id = ?", (id,))

    conn.commit()
    conn.close()

    return redirect("/admin/horarios")

@app.route("/admin/exportar")
def exportar_reservas():
    if not session.get("admin"):
        return redirect("/login")

    conn = conectar_bd()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT fecha, hora, centro, direccion, servicio, nombre, rut, edad, correo, telefono, fecha_creacion
        FROM reservas
        ORDER BY fecha, hora
    """)

    reservas = cursor.fetchall()
    conn.close()

    archivo = "reservas_exportadas.csv"

    with open(archivo, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.writer(f, delimiter=";")

        writer.writerow([
            "Fecha",
            "Hora",
            "Centro",
            "Dirección",
            "Servicio",
            "Nombre",
            "RUT",
            "Edad",
            "Correo",
            "Teléfono",
            "Fecha creación"
        ])

        writer.writerows(reservas)

    return send_file(
        archivo,
        as_attachment=True,
        download_name="reservas_belinda.csv"
    )


if __name__ == "__main__":
    app.run(debug=True)
