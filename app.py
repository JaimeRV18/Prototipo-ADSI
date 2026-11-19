"""
Sistema de Préstamo de Cubículos y Componentes Electrónicos
Backend Flask - Configurado para SQL Server (pyodbc).
"""
import datetime as dt
import os
import sys
from functools import wraps

from flask import Flask, g, jsonify, request, session
from werkzeug.security import check_password_hash, generate_password_hash
import pyodbc

# CONFIGURACIÓN DE TU BASE DE DATOS SQL SERVER
DB_CONFIG = {
    'server': 'localhost',
    'database': 'SistemaPrestamos',
    'username': '',
    'password': ''
}

app = Flask(__name__, static_folder="static", static_url_path="")
app.secret_key = os.environ.get("SECRET_KEY", "prototipo-cambiar-en-produccion")

MAX_HORAS_CUBICULO = 3
DIAS_PRESTAMO_COMPONENTES = 7

# =====================================================================
# Capa de base de datos (SQL Server)
# =====================================================================
def db():
    if "db" not in g:
        conn_str = (
            f"DRIVER={{ODBC Driver 17 for SQL Server}};"
            f"SERVER={DB_CONFIG['server']};"
            f"DATABASE={DB_CONFIG['database']};"
            "Trusted_Connection=yes;"
            "TrustServerCertificate=yes;"
        )
        g.db = pyodbc.connect(conn_str)
        g.db.setdecoding(pyodbc.SQL_CHAR, encoding='utf-8')
        g.db.setdecoding(pyodbc.SQL_WCHAR, encoding='utf-8')
        g.db.setencoding('utf-8')
    return g.db

def q(sql, args=(), one=False):
    cur = db().cursor()
    cur.execute(sql, tuple(args))
    if not cur.description:
        return [] if not one else None
    cols = [column[0].split('.')[-1].lower() for column in cur.description]
    filas = [dict(zip(cols, row)) for row in cur.fetchall()]
    if one:
        return filas[0] if filas else None
    return filas

def rows(sql, args=()):
    return q(sql, args)

def ex(sql, args=()):
    cur = db().cursor()
    cur.execute(sql, tuple(args))
    if sql.strip().upper().startswith("INSERT"):
        cur.execute("SELECT SCOPE_IDENTITY() AS id")
        row = cur.fetchone()
        return int(row[0]) if row and row[0] is not None else None
    return None

@app.teardown_appcontext
def cerrar_db(_):
    conexion = g.pop("db", None)
    if conexion is not None:
        conexion.close()

@app.after_request
def confirmar(resp):
    conexion = g.get("db")
    if conexion is not None:
        if resp.status_code < 400:
            conexion.commit()
        else:
            conexion.rollback()
    return resp

# =====================================================================
# Inicialización y Datos de Ejemplo
# =====================================================================
def init_db():
    try:
        existe = q("SELECT id FROM centro_acopio")
        if not existe:
            cargar_datos_ejemplo()
            print(" Datos de ejemplo insertados correctamente.")
        else:
            print("ℹ La base de datos ya tiene datos, no se insertó nada.")
    except Exception as e:
        print("⚠️ Error al inicializar la BD. Asegúrate de haber ejecutado el script SQL en SSMS.")
        print(f"Detalle del error: {e}")

def cargar_datos_ejemplo():
    con = db()
    cur = con.cursor()
    cur.execute("INSERT INTO centro_acopio(nombre, ubicacion) VALUES (?, ?)", ("Centro de acopio de Electrónica", "Edificio administrativo, planta baja"))
    cur.execute("INSERT INTO centro_acopio(nombre, ubicacion) VALUES (?, ?)", ("Centro de acopio de Redes", "Edificio administrativo, primer piso"))
    
    # Alumnos con su matrícula como contraseña
    cur.execute("INSERT INTO alumno VALUES (?, ?, ?, ?, ?)", ("2023001", "Juan Pérez Soto", "Informática", "juan@alumnos.uan.edu.mx", "2023001"))
    cur.execute("INSERT INTO alumno VALUES (?, ?, ?, ?, ?)", ("2023002", "María López Ruiz", "Informática", "maria@alumnos.uan.edu.mx", "2023002"))
    cur.execute("INSERT INTO alumno VALUES (?, ?, ?, ?, ?)", ("2023003", "Luis Ramírez Díaz", "Informática", "luis@alumnos.uan.edu.mx", "2023003"))
    
    # Docentes con su clave como contraseña
    cur.execute("INSERT INTO docente VALUES (?, ?, ?, ?)", ("D001", "Dra. Laura Ríos", "laura@uan.edu.mx", "D001"))
    cur.execute("INSERT INTO docente VALUES (?, ?, ?, ?)", ("D002", "Mtro. Carlos Pérez", "carlos@uan.edu.mx", "D002"))
    cur.execute("INSERT INTO docente VALUES (?, ?, ?, ?)", ("D003", "Mtra. Ana López", "ana@uan.edu.mx", "D003"))
    
    # Usuarios (Admin y Encargados)
    cur.execute("INSERT INTO usuario(nombre, usuario, contrasena_hash, rol, centro_id, contrasena) VALUES (?, ?, ?, ?, ?, ?)", ("Administración", "admin", generate_password_hash("admin123"), "administrador", None, "admin123"))
    cur.execute("INSERT INTO usuario(nombre, usuario, contrasena_hash, rol, centro_id, contrasena) VALUES (?, ?, ?, ?, ?, ?)", ("Encargado de Electrónica", "acopio1", generate_password_hash("acopio123"), "encargado", 1, "acopio123"))
    cur.execute("INSERT INTO usuario(nombre, usuario, contrasena_hash, rol, centro_id, contrasena) VALUES (?, ?, ?, ?, ?, ?)", ("Encargado de Redes", "acopio2", generate_password_hash("acopio123"), "encargado", 2, "acopio123"))
    
    # Cubículos 
    for piso in (1, 2):
        for n in range(1, 7):
            numero = f"{piso}0{n}"
            lado = "izquierdo" if n % 2 else "derecho"
            docente = {"104": "D001", "202": "D002", "206": "D003"}.get(numero)
            cur.execute("INSERT INTO cubiculo(numero, piso, lado, docente_clave) VALUES (?, ?, ?, ?)", (numero, piso, lado, docente))
            
    # Componentes
    comps = [
        ("E-001", "Resistencia 220 Ω", "1/4 W", 50, 50, 1), ("E-002", "Capacitor 100 µF", "Electrolítico 25 V", 30, 30, 1),
        ("E-003", "LED rojo 5 mm", "", 80, 80, 1), ("E-004", "Protoboard 830 puntos", "", 10, 10, 1),
        ("E-005", "Arduino UNO R3", "", 6, 6, 1), ("E-006", "Sensor ultrasónico HC-SR04", "", 8, 8, 1),
        ("E-007", "Cables Dupont (paquete)", "40 piezas", 20, 20, 1), ("E-008", "Multímetro digital", "", 4, 4, 1),
        ("R-001", "Cable UTP (tramo 1 m)", "Cat 5e", 20, 20, 2), ("R-002", "Conector RJ45", "", 60, 60, 2),
        ("R-003", "Pinzas para crimpar", "", 3, 3, 2), ("R-004", "Probador de cable de red", "", 3, 3, 2),
    ]
    for c in comps:
        cur.execute("INSERT INTO componente(codigo, nombre, descripcion, cantidad_total, cantidad_disponible, centro_id) VALUES (?, ?, ?, ?, ?, ?)", c)
    con.commit()

# =====================================================================
# Errores y utilidades
# =====================================================================
class ApiError(Exception):
    def __init__(self, mensaje, status=400):
        super().__init__(mensaje)
        self.mensaje, self.status = mensaje, status

@app.errorhandler(ApiError)
def error_api(e):
    return jsonify({"error": e.mensaje}), e.status

@app.errorhandler(404)
def no_encontrado(_):
    return jsonify({"error": "No encontrado."}), 404

def cuerpo():
    return request.get_json(silent=True) or {}

def entero(valor, mensaje):
    try:
        return int(valor)
    except (TypeError, ValueError):
        raise ApiError(mensaje)

def hhmm(texto):
    try:
        return dt.datetime.strptime(texto, "%H:%M")
    except (TypeError, ValueError):
        raise ApiError("Hora no válida (usa el formato HH:MM).")

def hoy():
    return dt.date.today().isoformat()

def ahora_hhmm():
    return dt.datetime.now().strftime("%H:%M")

def usuario_actual():
    return session.get("usuario")

def requiere(*roles):
    def decorador(f):
        @wraps(f)
        def envoltura(*a, **k):
            u = usuario_actual()
            if not u:
                raise ApiError("Inicia sesión para continuar.", 401)
            if roles and u["rol"] not in roles:
                raise ApiError("No tienes permiso para esta acción.", 403)
            return f(*a, **k)
        return envoltura
    return decorador

# =====================================================================
# CU-01 Iniciar sesión
# =====================================================================
@app.post("/api/login")
def login():
    d = cuerpo()
    rol = d.get("rol")
    ident = (d.get("identificador") or "").strip()
    pwd_ingresada = d.get("contrasena") or ""
    
    if rol == "alumno":
        r = q("SELECT * FROM alumno WHERE matricula = ?", (ident,), True)
        if not r: raise ApiError("Matrícula no registrada.", 401)
        pwd_db = next((v for k, v in r.items() if 'contrasena' in k), None)
        if pwd_db is None or pwd_db != pwd_ingresada:
            raise ApiError("Contraseña incorrecta.", 401)
        mat = next((v for k, v in r.items() if 'matricula' in k), ident)
        nom = next((v for k, v in r.items() if 'nombre' in k), "")
        u = {"rol": "alumno", "id": mat, "nombre": nom}
    elif rol == "docente":
        r = q("SELECT * FROM docente WHERE clave = ?", (ident,), True)
        if not r: raise ApiError("Clave de docente no registrada.", 401)
        pwd_db = next((v for k, v in r.items() if 'contrasena' in k), None)
        if pwd_db is None or pwd_db != pwd_ingresada:
            raise ApiError("Contraseña incorrecta.", 401)
        clv = next((v for k, v in r.items() if 'clave' in k), ident)
        nom = next((v for k, v in r.items() if 'nombre' in k), "")
        u = {"rol": "docente", "id": clv, "nombre": nom, "clave": clv}
    elif rol in ("administrador", "encargado"):
        r = q("SELECT * FROM usuario WHERE usuario = ? AND rol = ?", (ident, rol), True)
        if not r: raise ApiError("Usuario o contraseña incorrectos.", 401)
        pwd_hash = next((v for k, v in r.items() if 'contrasena' in k or 'password' in k), "")
        if pwd_hash:
            if not check_password_hash(pwd_hash, pwd_ingresada):
                raise ApiError("Usuario o contraseña incorrectos.", 401)
        u_id = next((v for k, v in r.items() if k == 'id'), 0)
        nom = next((v for k, v in r.items() if 'nombre' in k), "")
        centro = next((v for k, v in r.items() if 'centro' in k), None)
        u = {"rol": rol, "id": u_id, "nombre": nom, "centro_id": centro}
    else:
        raise ApiError("Rol no válido.")
    session["usuario"] = u
    return jsonify(u)

@app.post("/api/logout")
def logout():
    session.clear()
    return jsonify({"ok": True})

@app.get("/api/yo")
def yo():
    return jsonify(usuario_actual())

# =====================================================================
# Módulo de cubículos
# =====================================================================
@app.get("/api/pisos")
@requiere()
def pisos():
    return jsonify([r["piso"] for r in q("SELECT DISTINCT piso FROM cubiculo ORDER BY piso")])

@app.get("/api/docentes")
@requiere("administrador")
def docentes():
    return jsonify(rows("SELECT clave, nombre FROM docente ORDER BY nombre"))

@app.get("/api/cubiculos")
@requiere()
def cubiculos():
    u = usuario_actual()
    sql = """SELECT c.id, c.numero, c.piso, c.lado, c.docente_clave, d.nombre AS docente,
                    CASE WHEN EXISTS(
                        SELECT 1 FROM prestamo_cubiculo p
                        JOIN solicitud_cubiculo s ON s.id = p.solicitud_id
                        WHERE s.cubiculo_id = c.id
                          AND p.hora_entrada IS NOT NULL AND p.hora_salida IS NULL
                    ) THEN 1 ELSE 0 END AS en_uso,
                    CASE WHEN EXISTS(
                        SELECT 1 FROM solicitud_cubiculo s
                        WHERE s.cubiculo_id = c.id AND s.alumno_matricula = ? 
                          AND s.estado = 'autorizada' AND s.fecha = ?
                    ) THEN 1 ELSE 0 END AS mi_reserva
             FROM cubiculo c LEFT JOIN docente d ON d.clave = c.docente_clave"""
    args = [u["id"] if u["rol"] == "alumno" else "", dt.date.today().isoformat()]
    if request.args.get("piso"):
        sql += " WHERE c.piso = ?"
        args.append(request.args["piso"])
    sql += " ORDER BY c.piso, c.lado, c.numero"
    salida = rows(sql, args)
    for c in salida:
        if c["docente_clave"]: c["estado"] = "asignado"
        elif c["en_uso"]: c["estado"] = "en_uso"
        elif c["mi_reserva"] and u["rol"] == "alumno": c["estado"] = "mi_reserva"
        else: c["estado"] = "disponible"
        del c["en_uso"]
        del c["mi_reserva"]
    return jsonify(salida)

def datos_cubiculo(d):
    numero = (d.get("numero") or "").strip()
    piso = entero(d.get("piso"), "El piso debe ser un número.")
    lado = d.get("lado")
    if not numero: raise ApiError("Escribe el número del cubículo.")
    if lado not in ("izquierdo", "derecho"): raise ApiError("El lado debe ser izquierdo o derecho.")
    docente = d.get("docente_clave") or None
    if docente and not q("SELECT 1 FROM docente WHERE clave = ?", (docente,), True): raise ApiError("El docente no existe.", 404)
    return numero, piso, lado, docente

@app.post("/api/cubiculos")
@requiere("administrador")
def alta_cubiculo():
    numero, piso, lado, docente = datos_cubiculo(cuerpo())
    cid = ex("INSERT INTO cubiculo(numero, piso, lado, docente_clave) VALUES (?, ?, ?, ?)", (numero, piso, lado, docente))
    return jsonify({"id": cid}), 201

@app.put("/api/cubiculos/<int:cid>")
@requiere("administrador")
def cambio_cubiculo(cid):
    if not q("SELECT 1 FROM cubiculo WHERE id = ?", (cid,), True): raise ApiError("El cubículo no existe.", 404)
    numero, piso, lado, docente = datos_cubiculo(cuerpo())
    ex("UPDATE cubiculo SET numero = ?, piso = ?, lado = ?, docente_clave = ? WHERE id = ?", (numero, piso, lado, docente, cid))
    return jsonify({"ok": True})

@app.delete("/api/cubiculos/<int:cid>")
@requiere("administrador")
def baja_cubiculo(cid):
    if not q("SELECT 1 FROM cubiculo WHERE id = ?", (cid,), True): raise ApiError("El cubículo no existe.", 404)
    if q("SELECT 1 FROM solicitud_cubiculo WHERE cubiculo_id = ?", (cid,), True): raise ApiError("No se puede eliminar: el cubículo tiene solicitudes registradas.", 409)
    ex("DELETE FROM cubiculo WHERE id = ?", (cid,))
    return jsonify({"ok": True})

def verificar_disponibilidad_cubiculo(cid, fecha, inicio, fin, excluir=None):
    c = q("SELECT * FROM cubiculo WHERE id = ?", (cid,), True)
    if not c: raise ApiError("El cubículo no existe.", 404)
    if c["docente_clave"]: raise ApiError("Ese cubículo está asignado a un docente.", 409)
    solicitudes = q("SELECT id, hora_inicio, hora_fin FROM solicitud_cubiculo WHERE cubiculo_id = ? AND fecha = ? AND estado = 'autorizada'", (cid, fecha))
    for s in solicitudes:
        if excluir is not None and s["id"] == excluir: continue
        if (s["hora_inicio"] < fin) and (inicio < s["hora_fin"]):
            raise ApiError(f"El cubículo ya está reservado de {s['hora_inicio']} a {s['hora_fin']}.", 409)

SOLICITUD_CUBICULO_SQL = """
    SELECT s.id, s.alumno_matricula, a.nombre AS alumno, s.cubiculo_id, c.piso, c.numero, c.lado,
           s.fecha, s.hora_inicio, s.hora_fin, s.estado, s.motivo_rechazo,
           p.id AS prestamo_id, p.hora_entrada, p.hora_salida
    FROM solicitud_cubiculo s
    JOIN alumno a ON a.matricula = s.alumno_matricula
    JOIN cubiculo c ON c.id = s.cubiculo_id
    LEFT JOIN prestamo_cubiculo p ON p.solicitud_id = s.id"""

def listar_solicitudes_cubiculo(matricula=None, estado=None):
    condiciones, args = [], []
    if matricula: condiciones.append("s.alumno_matricula = ?"); args.append(matricula)
    if estado: condiciones.append("s.estado = ?"); args.append(estado)
    sql = SOLICITUD_CUBICULO_SQL
    if condiciones: sql += " WHERE " + " AND ".join(condiciones)
    
    salida = rows(sql + " ORDER BY s.fecha DESC, s.hora_inicio DESC, s.id DESC", args)
    
    # Calcular si está vencido
    fecha_hoy = hoy()
    for s in salida:
        s["vencido"] = bool(s["estado"] == "autorizada" and s["fecha"] < fecha_hoy and not s["hora_salida"])
        
    return salida

@app.post("/api/solicitudes-cubiculo")
@requiere("alumno")
def solicitar_cubiculo():
    d = cuerpo()
    cid = entero(d.get("cubiculo_id"), "Elige un cubículo.")
    try: fecha = dt.date.fromisoformat(d.get("fecha") or "")
    except ValueError: raise ApiError("Fecha no válida.")
    if fecha < dt.date.today(): raise ApiError("La fecha no puede ser anterior a hoy.")
    inicio, fin = hhmm(d.get("hora_inicio")), hhmm(d.get("hora_fin"))
    if fin <= inicio: raise ApiError("La hora de fin debe ser posterior a la de inicio.")
    if (fin - inicio).total_seconds() > MAX_HORAS_CUBICULO * 3600: raise ApiError(f"El máximo es de {MAX_HORAS_CUBICULO} horas por solicitud.")
    inicio_s, fin_s = inicio.strftime("%H:%M"), fin.strftime("%H:%M")
    verificar_disponibilidad_cubiculo(cid, fecha.isoformat(), inicio_s, fin_s)
    cur = db().cursor()
    cur.execute("""INSERT INTO solicitud_cubiculo(alumno_matricula, cubiculo_id, fecha, hora_inicio, hora_fin, creada_en) OUTPUT INSERTED.id VALUES (?, ?, ?, ?, ?, ?)""", (usuario_actual()["id"], cid, fecha.isoformat(), inicio_s, fin_s, dt.datetime.now().isoformat()))
    sid = cur.fetchone()[0]
    return jsonify({"id": sid, "estado": "pendiente"}), 201

@app.get("/api/solicitudes-cubiculo")
@requiere("alumno", "administrador")
def solicitudes_cubiculo():
    u = usuario_actual()
    matricula = u["id"] if u["rol"] == "alumno" else None
    return jsonify(listar_solicitudes_cubiculo(matricula, request.args.get("estado")))

@app.post("/api/solicitudes-cubiculo/<int:sid>/resolver")
@requiere("administrador")
def resolver_solicitud_cubiculo(sid):
    s = q("SELECT * FROM solicitud_cubiculo WHERE id = ?", (sid,), True)
    if not s: raise ApiError("La solicitud no existe.", 404)
    if s["estado"] != "pendiente": raise ApiError("La solicitud ya fue resuelta.", 409)
    d = cuerpo()
    if d.get("decision") == "autorizar":
        verificar_disponibilidad_cubiculo(s["cubiculo_id"], s["fecha"], s["hora_inicio"], s["hora_fin"], excluir=sid)
        ex("UPDATE solicitud_cubiculo SET estado = 'autorizada', resuelta_por = ? WHERE id = ?", (usuario_actual()["id"], sid))
        ex("INSERT INTO prestamo_cubiculo(solicitud_id) VALUES (?)", (sid,))
    elif d.get("decision") == "rechazar":
        ex("UPDATE solicitud_cubiculo SET estado = 'rechazada', motivo_rechazo = ?, resuelta_por = ? WHERE id = ?", ((d.get("motivo") or "").strip() or None, usuario_actual()["id"], sid))
    else: raise ApiError("La decisión debe ser autorizar o rechazar.")
    return jsonify({"ok": True})

@app.post("/api/prestamos-cubiculo/<int:pid>/<accion>")
@requiere("administrador")
def entrada_salida(pid, accion):
    if accion not in ("entrada", "salida"): raise ApiError("Acción no válida.", 404)
    p = q("""SELECT p.*, s.fecha, s.cubiculo_id FROM prestamo_cubiculo p JOIN solicitud_cubiculo s ON s.id = p.solicitud_id WHERE p.id = ?""", (pid,), True)
    if not p: raise ApiError("El préstamo no existe.", 404)
    if accion == "entrada":
        if p["hora_entrada"]: raise ApiError("La entrada ya fue registrada.", 409)
        ocupado = q("""SELECT 1 FROM prestamo_cubiculo p2 JOIN solicitud_cubiculo s2 ON s2.id = p2.solicitud_id WHERE s2.cubiculo_id = ? AND p2.hora_entrada IS NOT NULL AND p2.hora_salida IS NULL""", (p["cubiculo_id"],), True)
        if ocupado: raise ApiError("El cubículo sigue en uso: registra primero la salida anterior.", 409)
        ex("UPDATE prestamo_cubiculo SET hora_entrada = ? WHERE id = ?", (ahora_hhmm(), pid))
    else:
        if not p["hora_entrada"]: raise ApiError("Primero hay que registrar la entrada.", 409)
        if p["hora_salida"]: raise ApiError("La salida ya fue registrada.", 409)
        ex("UPDATE prestamo_cubiculo SET hora_salida = ? WHERE id = ?", (ahora_hhmm(), pid))
        ex("UPDATE solicitud_cubiculo SET estado = 'finalizada' WHERE id = ?", (p["solicitud_id"],))
    return jsonify({"ok": True})

@app.post("/api/solicitudes-cubiculo/<int:sid>/cancelar")
@requiere("alumno")
def cancelar_solicitud_cubiculo(sid):
    s = q("SELECT * FROM solicitud_cubiculo WHERE id = ?", (sid,), True)
    if not s: raise ApiError("La solicitud no existe.", 404)
    if s["alumno_matricula"] != usuario_actual()["id"]: raise ApiError("Solo puedes cancelar tus propias solicitudes.", 403)
    if s["estado"] != "pendiente": raise ApiError("Solo se pueden cancelar solicitudes pendientes.", 409)
    ex("UPDATE solicitud_cubiculo SET estado = 'cancelada' WHERE id = ?", (sid,))
    return jsonify({"ok": True})

# =====================================================================
# Módulo de componentes
# =====================================================================
@app.get("/api/centros")
@requiere()
def centros():
    return jsonify(rows("SELECT * FROM centro_acopio ORDER BY id"))

@app.get("/api/componentes")
@requiere()
def componentes():
    centro = request.args.get("centro_id")
    u = usuario_actual()
    if u["rol"] == "encargado": centro = u["centro_id"]
    sql = """SELECT id, codigo, nombre, descripcion, cantidad_total, cantidad_disponible, cantidad_total - cantidad_disponible AS en_uso, centro_id FROM componente"""
    args = []
    if centro: sql += " WHERE centro_id = ?"; args.append(centro)
    return jsonify(rows(sql + " ORDER BY nombre", args))

def datos_componente(d):
    codigo = (d.get("codigo") or "").strip()
    nombre = (d.get("nombre") or "").strip()
    if not codigo or not nombre: raise ApiError("El código y el nombre son obligatorios.")
    total = entero(d.get("cantidad_total"), "La cantidad debe ser un número.")
    if total < 0: raise ApiError("La cantidad no puede ser negativa.")
    return codigo, nombre, (d.get("descripcion") or "").strip(), total

@app.post("/api/componentes")
@requiere("encargado")
def alta_componente():
    codigo, nombre, descripcion, total = datos_componente(cuerpo())
    cid = ex("""INSERT INTO componente(codigo, nombre, descripcion, cantidad_total, cantidad_disponible, centro_id) VALUES (?, ?, ?, ?, ?, ?)""", (codigo, nombre, descripcion, total, total, usuario_actual()["centro_id"]))
    return jsonify({"id": cid}), 201

def componente_del_encargado(cid):
    c = q("SELECT * FROM componente WHERE id = ? AND centro_id = ?", (cid, usuario_actual()["centro_id"]), True)
    if not c: raise ApiError("El componente no existe en tu centro de acopio.", 404)
    return c

@app.put("/api/componentes/<int:cid>")
@requiere("encargado")
def cambio_componente(cid):
    c = componente_del_encargado(cid)
    codigo, nombre, descripcion, total = datos_componente(cuerpo())
    en_uso = c["cantidad_total"] - c["cantidad_disponible"]
    if total < en_uso: raise ApiError(f"No puedes dejar menos de {en_uso} piezas: están prestadas.", 409)
    ex("""UPDATE componente SET codigo = ?, nombre = ?, descripcion = ?, cantidad_total = ?, cantidad_disponible = ? WHERE id = ?""", (codigo, nombre, descripcion, total, total - en_uso, cid))
    return jsonify({"ok": True})

@app.delete("/api/componentes/<int:cid>")
@requiere("encargado")
def baja_componente(cid):
    c = componente_del_encargado(cid)
    if c["cantidad_total"] != c["cantidad_disponible"]: raise ApiError("No se puede eliminar: hay piezas prestadas.", 409)
    if q("SELECT 1 FROM detalle_solicitud WHERE componente_id = ?", (cid,), True): raise ApiError("No se puede eliminar: el componente aparece en solicitudes registradas.", 409)
    ex("DELETE FROM componente WHERE id = ?", (cid,))
    return jsonify({"ok": True})

def verificar_existencias(centro_id, pedido):
    for componente_id, cantidad in pedido.items():
        c = q("SELECT * FROM componente WHERE id = ? AND centro_id = ?", (componente_id, centro_id), True)
        if not c: raise ApiError("Un componente no pertenece a ese centro de acopio.", 404)
        if c["cantidad_disponible"] < cantidad: raise ApiError(f"No hay suficientes existencias de {c['nombre']} (disponibles: {c['cantidad_disponible']}).", 409)

def detalles_de(sid):
    return rows("""SELECT d.id, d.componente_id, c.codigo, c.nombre, d.cantidad, d.cantidad_perdida FROM detalle_solicitud d JOIN componente c ON c.id = d.componente_id WHERE d.solicitud_id = ? ORDER BY d.id""", (sid,))

def listar_solicitudes_componentes(matricula=None, estados=None, centro_id=None):
    condiciones, args = [], []
    if matricula: condiciones.append("s.alumno_matricula = ?"); args.append(matricula)
    if estados: condiciones.append("s.estado IN (%s)" % ",".join("?" * len(estados))); args.extend(estados)
    if centro_id: condiciones.append("s.centro_id = ?"); args.append(centro_id)
    sql = """SELECT s.id, s.alumno_matricula, a.nombre AS alumno, s.centro_id, ca.nombre AS centro, s.fecha, s.estado, s.motivo_rechazo, p.fecha_prestamo, p.fecha_limite, p.fecha_devolucion, p.observaciones FROM solicitud_componentes s JOIN alumno a ON a.matricula = s.alumno_matricula JOIN centro_acopio ca ON ca.id = s.centro_id LEFT JOIN prestamo_componentes p ON p.solicitud_id = s.id"""
    if condiciones: sql += " WHERE " + " AND ".join(condiciones)
    salida = rows(sql + " ORDER BY s.id DESC", args)
    for s in salida:
        s["detalles"] = detalles_de(s["id"])
        s["vencido"] = bool(s["estado"] == "entregada" and s["fecha_limite"] and s["fecha_limite"] < hoy())
    return salida

@app.post("/api/solicitudes-componentes")
@requiere("alumno")
def solicitar_componentes():
    d = cuerpo()
    centro = entero(d.get("centro_id"), "Elige un centro de acopio.")
    if not q("SELECT 1 FROM centro_acopio WHERE id = ?", (centro,), True): raise ApiError("El centro de acopio no existe.", 404)
    pedido = {}
    for it in d.get("items") or []:
        cid = entero(it.get("componente_id"), "Componente no válido.")
        cantidad = entero(it.get("cantidad"), "La cantidad debe ser un número.")
        if cantidad < 1: raise ApiError("La cantidad debe ser de al menos 1.")
        pedido[cid] = pedido.get(cid, 0) + cantidad
    if not pedido: raise ApiError("Selecciona al menos un componente.")
    verificar_existencias(centro, pedido)
    cur = db().cursor()
    cur.execute("""INSERT INTO solicitud_componentes(alumno_matricula, centro_id, fecha) OUTPUT INSERTED.id VALUES (?, ?, ?)""", (usuario_actual()["id"], centro, hoy()))
    sid = cur.fetchone()[0]
    for cid, cantidad in pedido.items():
        ex("INSERT INTO detalle_solicitud(solicitud_id, componente_id, cantidad) VALUES (?, ?, ?)", (sid, cid, cantidad))
    return jsonify({"id": sid, "estado": "pendiente"}), 201

@app.get("/api/solicitudes-componentes")
@requiere("alumno", "administrador", "encargado")
def solicitudes_componentes():
    u = usuario_actual()
    estado = request.args.get("estado")
    estados = [estado] if estado else None
    if u["rol"] == "alumno": return jsonify(listar_solicitudes_componentes(matricula=u["id"], estados=estados))
    if u["rol"] == "encargado":
        permitidos = ["autorizada", "entregada"]
        if estados: estados = [e for e in estados if e in permitidos]
        return jsonify(listar_solicitudes_componentes(estados=estados or permitidos, centro_id=u["centro_id"]))
    return jsonify(listar_solicitudes_componentes(estados=estados))

def solicitud_componentes_por_id(sid):
    s = q("SELECT * FROM solicitud_componentes WHERE id = ?", (sid,), True)
    if not s: raise ApiError("La solicitud no existe.", 404)
    return s

def pedido_de(sid):
    return {r["componente_id"]: r["cantidad"] for r in q("SELECT componente_id, cantidad FROM detalle_solicitud WHERE solicitud_id = ?", (sid,))}

@app.post("/api/solicitudes-componentes/<int:sid>/resolver")
@requiere("administrador")
def resolver_solicitud_componentes(sid):
    s = solicitud_componentes_por_id(sid)
    if s["estado"] != "pendiente": raise ApiError("La solicitud ya fue resuelta.", 409)
    d = cuerpo()
    if d.get("decision") == "autorizar":
        verificar_existencias(s["centro_id"], pedido_de(sid))
        ex("UPDATE solicitud_componentes SET estado = 'autorizada', resuelta_por = ? WHERE id = ?", (usuario_actual()["id"], sid))
    elif d.get("decision") == "rechazar":
        ex("UPDATE solicitud_componentes SET estado = 'rechazada', motivo_rechazo = ?, resuelta_por = ? WHERE id = ?", ((d.get("motivo") or "").strip() or None, usuario_actual()["id"], sid))
    else: raise ApiError("La decisión debe ser autorizar o rechazar.")
    return jsonify({"ok": True})

@app.post("/api/solicitudes-componentes/<int:sid>/entregar")
@requiere("encargado")
def entregar_componentes(sid):
    s = solicitud_componentes_por_id(sid)
    u = usuario_actual()
    if s["centro_id"] != u["centro_id"]: raise ApiError("Esta solicitud pertenece a otro centro de acopio.", 403)
    if s["estado"] != "autorizada": raise ApiError("Solo se pueden entregar solicitudes autorizadas.", 409)
    pedido = pedido_de(sid)
    verificar_existencias(s["centro_id"], pedido)
    for cid, cantidad in pedido.items():
        ex("UPDATE componente SET cantidad_disponible = cantidad_disponible - ? WHERE id = ?", (cantidad, cid))
    limite = (dt.date.today() + dt.timedelta(days=DIAS_PRESTAMO_COMPONENTES)).isoformat()
    ex("""INSERT INTO prestamo_componentes(solicitud_id, fecha_prestamo, fecha_limite, entregado_por) VALUES (?, ?, ?, ?)""", (sid, hoy(), limite, u["id"]))
    ex("UPDATE solicitud_componentes SET estado = 'entregada' WHERE id = ?", (sid,))
    return jsonify({"ok": True, "fecha_limite": limite})

@app.post("/api/solicitudes-componentes/<int:sid>/devolver")
@requiere("encargado")
def devolver_componentes(sid):
    s = solicitud_componentes_por_id(sid)
    u = usuario_actual()
    if s["centro_id"] != u["centro_id"]: raise ApiError("Esta solicitud pertenece a otro centro de acopio.", 403)
    if s["estado"] != "entregada": raise ApiError("Solo se puede registrar la devolución de un préstamo entregado.", 409)
    d = cuerpo()
    perdidas = d.get("perdidas") or {}
    for det in q("SELECT * FROM detalle_solicitud WHERE solicitud_id = ?", (sid,)):
        perdida = entero(perdidas.get(str(det["id"]), 0), "La cantidad dañada o faltante debe ser un número.")
        if perdida < 0 or perdida > det["cantidad"]: raise ApiError("La cantidad dañada o faltante no puede ser mayor a la prestada.")
        ex("""UPDATE componente SET cantidad_disponible = cantidad_disponible + ?, cantidad_total = cantidad_total - ? WHERE id = ?""", (det["cantidad"] - perdida, perdida, det["componente_id"]))
        ex("UPDATE detalle_solicitud SET cantidad_perdida = ? WHERE id = ?", (perdida, det["id"]))
    ex("UPDATE prestamo_componentes SET fecha_devolucion = ?, observaciones = ? WHERE solicitud_id = ?", (hoy(), (d.get("observaciones") or "").strip() or None, sid))
    ex("UPDATE solicitud_componentes SET estado = 'devuelta' WHERE id = ?", (sid,))
    return jsonify({"ok": True})

@app.post("/api/solicitudes-componentes/<int:sid>/cancelar")
@requiere("alumno")
def cancelar_solicitud_componentes(sid):
    s = solicitud_componentes_por_id(sid)
    if s["alumno_matricula"] != usuario_actual()["id"]: raise ApiError("Solo puedes cancelar tus propias solicitudes.", 403)
    if s["estado"] != "pendiente": raise ApiError("Solo se pueden cancelar solicitudes pendientes.", 409)
    ex("UPDATE solicitud_componentes SET estado = 'cancelada' WHERE id = ?", (sid,))
    return jsonify({"ok": True})

# =====================================================================
# CU-02 Historial
# =====================================================================
@app.get("/api/historial")
@requiere("alumno", "administrador")
def historial():
    u = usuario_actual()
    busqueda = request.args.get("matricula") or None
    if u["rol"] == "alumno":
        return jsonify({"cubiculos": listar_solicitudes_cubiculo(matricula=u["id"]), "componentes": listar_solicitudes_componentes(matricula=u["id"])})
    if busqueda:
        alumno_encontrado = q("SELECT matricula FROM alumno WHERE matricula LIKE ? OR nombre LIKE ?", (f"%{busqueda}%", f"%{busqueda}%"), True)
        if alumno_encontrado:
            return jsonify({"cubiculos": listar_solicitudes_cubiculo(matricula=alumno_encontrado["matricula"]), "componentes": listar_solicitudes_componentes(matricula=alumno_encontrado["matricula"])})
        else:
            personal = q("SELECT id, nombre FROM usuario WHERE nombre LIKE ? OR usuario LIKE ?", (f"%{busqueda}%", f"%{busqueda}%"), True)
            if personal: return jsonify({"cubiculos": [], "componentes": []})
            return jsonify({"cubiculos": [], "componentes": []})
    return jsonify({"cubiculos": listar_solicitudes_cubiculo(), "componentes": listar_solicitudes_componentes()})

# =====================================================================
# Módulo de Administración de Usuarios
# =====================================================================
@app.get("/api/usuarios")
@requiere("administrador")
def listar_usuarios():
    alumnos = rows("SELECT matricula AS id, nombre, 'alumno' AS rol, contrasena AS contrasena_plana FROM alumno")
    docentes = rows("SELECT clave AS id, nombre, 'docente' AS rol, contrasena AS contrasena_plana FROM docente")
    personal = rows("SELECT id, nombre, rol, contrasena AS contrasena_plana FROM usuario")
    return jsonify(alumnos + docentes + personal)

@app.post("/api/usuarios")
@requiere("administrador")
def crear_usuario():
    d = cuerpo()
    rol = d.get("rol")
    nombre = (d.get("nombre") or "").strip()
    ident = (d.get("identificador") or "").strip()
    contrasena = d.get("contrasena") or ""
    
    if not contrasena: raise ApiError("La contraseña es obligatoria.")
    if not nombre or not ident: raise ApiError("El nombre y el identificador son obligatorios.")
    
    if rol == "alumno":
        ex("INSERT INTO alumno(matricula, nombre, carrera, correo, contrasena) VALUES (?, ?, ?, ?, ?)", (ident, nombre, d.get("carrera", "Informática"), d.get("correo", ""), contrasena))
    elif rol == "docente":
        ex("INSERT INTO docente(clave, nombre, correo, contrasena) VALUES (?, ?, ?, ?)", (ident, nombre, d.get("correo", ""), contrasena))
    elif rol in ("administrador", "encargado"):
        hash_pw = generate_password_hash(contrasena)
        centro_id = d.get("centro_id") if rol == "encargado" else None
        ex("INSERT INTO usuario(nombre, usuario, contrasena_hash, rol, centro_id, contrasena) VALUES (?, ?, ?, ?, ?, ?)", (nombre, ident, hash_pw, rol, centro_id, contrasena))
    else: raise ApiError("Rol no válido.")
    return jsonify({"ok": True}), 201

@app.put("/api/usuarios/<int:uid>")
@requiere("administrador")
def editar_usuario(uid):
    d = cuerpo()
    nombre = (d.get("nombre") or "").strip()
    ident = (d.get("identificador") or "").strip()
    contrasena = d.get("contrasena") or ""
    if not nombre or not ident: raise ApiError("El nombre y el identificador son obligatorios.")
    u = q("SELECT * FROM usuario WHERE id = ?", (uid,), True)
    if not u: raise ApiError("Usuario no encontrado.", 404)
    if contrasena:
        hash_pw = generate_password_hash(contrasena)
        ex("UPDATE usuario SET nombre = ?, usuario = ?, contrasena_hash = ? WHERE id = ?", (nombre, ident, hash_pw, uid))
    else:
        ex("UPDATE usuario SET nombre = ?, usuario = ? WHERE id = ?", (nombre, ident, uid))
    return jsonify({"ok": True})

@app.delete("/api/usuarios/<int:uid>")
@requiere("administrador")
def eliminar_usuario(uid):
    if uid == usuario_actual()["id"]: raise ApiError("No puedes eliminar tu propio usuario.", 409)
    if not q("SELECT 1 FROM usuario WHERE id = ?", (uid,), True): raise ApiError("Usuario no encontrado.", 404)
    ex("DELETE FROM usuario WHERE id = ?", (uid,))
    return jsonify({"ok": True})

@app.put("/api/usuarios/alumno/<string:matricula>")
@requiere("administrador")
def editar_alumno(matricula):
    d = cuerpo()
    nombre = (d.get("nombre") or "").strip()
    if not nombre: raise ApiError("El nombre es obligatorio.")
    ex("UPDATE alumno SET nombre = ? WHERE matricula = ?", (nombre, matricula))
    return jsonify({"ok": True})

@app.delete("/api/usuarios/alumno/<string:matricula>")
@requiere("administrador")
def eliminar_alumno(matricula):
    # 1. Buscar si tiene préstamos de componentes activos y devolverlos al inventario
    prestamos_activos = q("""SELECT d.componente_id, d.cantidad 
                             FROM detalle_solicitud d 
                             JOIN solicitud_componentes s ON s.id = d.solicitud_id 
                             WHERE s.alumno_matricula = ? AND s.estado = 'entregada'""", (matricula,))
    for p in prestamos_activos:
        ex("UPDATE componente SET cantidad_disponible = cantidad_disponible + ? WHERE id = ?", (p["cantidad"], p["componente_id"]))

    # 2. Borrar registros de componentes asociados al alumno
    ex("""DELETE FROM detalle_solicitud WHERE solicitud_id IN (SELECT id FROM solicitud_componentes WHERE alumno_matricula = ?)""", (matricula,))
    ex("""DELETE FROM prestamo_componentes WHERE solicitud_id IN (SELECT id FROM solicitud_componentes WHERE alumno_matricula = ?)""", (matricula,))
    ex("DELETE FROM solicitud_componentes WHERE alumno_matricula = ?", (matricula,))
    
    # 3. Borrar registros de cubículos asociados al alumno
    ex("""DELETE FROM prestamo_cubiculo WHERE solicitud_id IN (SELECT id FROM solicitud_cubiculo WHERE alumno_matricula = ?)""", (matricula,))
    ex("DELETE FROM solicitud_cubiculo WHERE alumno_matricula = ?", (matricula,))
    
    # 4. Finalmente, borrar al alumno
    ex("DELETE FROM alumno WHERE matricula = ?", (matricula,))
    return jsonify({"ok": True})

@app.put("/api/usuarios/docente/<string:clave>")
@requiere("administrador")
def editar_docente(clave):
    d = cuerpo()
    nombre = (d.get("nombre") or "").strip()
    if not nombre: raise ApiError("El nombre es obligatorio.")
    ex("UPDATE docente SET nombre = ? WHERE clave = ?", (nombre, clave))
    return jsonify({"ok": True})

@app.delete("/api/usuarios/docente/<string:clave>")
@requiere("administrador")
def eliminar_docente(clave):
    if q("SELECT 1 FROM cubiculo WHERE docente_clave = ?", (clave,), True):
        raise ApiError("No se puede eliminar: el docente tiene cubículos asignados.", 409)
    ex("DELETE FROM docente WHERE clave = ?", (clave,))
    return jsonify({"ok": True})

@app.get("/api/dashboard")
@requiere("administrador")
def dashboard():
    r1 = q("SELECT COUNT(*) AS total FROM solicitud_cubiculo WHERE estado = 'pendiente'", one=True)
    r2 = q("SELECT COUNT(*) AS total FROM prestamo_cubiculo p JOIN solicitud_cubiculo s ON s.id = p.solicitud_id WHERE p.hora_entrada IS NOT NULL AND p.hora_salida IS NULL", one=True)
    r3 = q("SELECT COUNT(*) AS total FROM solicitud_componentes WHERE estado = 'pendiente'", one=True)
    r4 = q("SELECT COUNT(*) AS total FROM prestamo_componentes WHERE fecha_devolucion IS NULL", one=True)
    return jsonify({
        "pend_cub": r1["total"] if r1 else 0,
        "en_uso": r2["total"] if r2 else 0,
        "pend_comp": r3["total"] if r3 else 0,
        "activos_comp": r4["total"] if r4 else 0
    })

@app.get("/")
def inicio():
    return app.send_static_file("index.html")

if __name__ == "__main__":
    with app.app_context():
        init_db()
    app.run(debug=True, port=int(os.environ.get("PORT", 5000)))