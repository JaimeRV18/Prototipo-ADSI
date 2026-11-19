const $ = (s, r = document) => r.querySelector(s);
const main = $("#contenido");
const esc = (s) => String(s ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
const hoy = () => new Date().toLocaleDateString("en-CA");

let yo = null;
let vistaActual = null;
let pisoActual = null;
let centroActual = null;

async function api(ruta, metodo = "GET", cuerpo) {
  const r = await fetch("/api" + ruta, {
    method: metodo,
    headers: { "Content-Type": "application/json" },
    body: cuerpo !== undefined ? JSON.stringify(cuerpo) : undefined,
  });
  const datos = await r.json().catch(() => null);
  if (!r.ok) throw new Error((datos && datos.error) || "Ocurrió un error.");
  return datos;
}

let temporizador;
function aviso(texto, ok = true) {
  const el = $("#aviso");
  el.textContent = texto;
  el.className = ok ? "" : "error";
  el.hidden = false;
  clearTimeout(temporizador);
  temporizador = setTimeout(() => (el.hidden = true), 4000);
}

const nombreEstado = { en_uso: "en uso", asignado: "asignado a docente", finalizada: "finalizada" };const etiqueta = (e) => `<span class="etiqueta ${esc(e)}">${esc(nombreEstado[e] || e)}</span>`;
const lista = (d) => d.detalles.map((x) =>
  `${x.cantidad} × ${esc(x.nombre)}${x.cantidad_perdida ? ` <em>(${x.cantidad_perdida} dañadas o faltantes)</em>` : ""}`).join("<br>");
const cubTexto = (s) => `Piso ${esc(s.piso)} · ${esc(s.numero)} (${esc(s.lado)})`;

function tabla(columnas, filas, vacio = "No hay registros.") {
  if (!filas.length) return `<div class="vacio">${vacio}</div>`;
  return `<table><thead><tr>${columnas.map((c) => `<th>${c}</th>`).join("")}</tr></thead>
    <tbody>${filas.map((f) => `<tr>${f.map((c) => `<td>${c}</td>`).join("")}</tr>`).join("")}</tbody></table>`;
}
const boton = (texto, acc, datos = {}, clase = "chico") =>
  `<button class="${clase}" data-acc="${acc}" ${Object.entries(datos).map(([k, v]) => `data-${k}="${esc(v)}"`).join(" ")}>${texto}</button>`;

const MENUS = {
  alumno: [["mapa", "Mapa de cubículos"], ["componentes", "Solicitar componentes"], ["historial", "Mi historial"]],
  docente: [["mapa", "Mapa de cubículos"]],
  administrador: [["dashboard", "Dashboard"], ["mapa", "Mapa de cubículos"], ["solcub", "Solicitudes de cubículo"], ["uso", "Entradas y salidas"],
    ["solcomp", "Solicitudes de componentes"], ["cubiculos", "Administrar cubículos"], ["usuarios", "Usuarios"], ["historial", "Historial"]],
  encargado: [["recibidas", "Solicitudes recibidas"], ["inventario", "Inventario"]],
};
const VISTAS = { dashboard: vDashboard, mapa: vMapa, componentes: vComponentes, historial: vHistorial, solcub: vSolCub, uso: vUso,
  solcomp: vSolComp, cubiculos: vCubiculos, recibidas: vRecibidas, inventario: vInventario, usuarios: vUsuarios };

function dibujarMenu() {
  const menu = $("#menu");
  menu.innerHTML = MENUS[yo.rol].map(([id, texto]) =>
    `<button data-vista="${id}" class="${id === vistaActual ? "activo" : ""}">${texto}</button>`).join("");
  menu.hidden = false;
}

async function ir(id) {
  vistaActual = id;
  dibujarMenu();
  main.innerHTML = "";
  try { await VISTAS[id](); } catch (e) { aviso(e.message, false); }
}

function vLogin() {
  $("#menu").hidden = true;
  $("#sesion").hidden = true;
  
  $("#quien").textContent = "";
  $("#menu").innerHTML = "";
  main.innerHTML = "";

  main.innerHTML = `<div class="tarjeta login"><h2>Iniciar sesión</h2>
    <form data-form="login">
      <div class="campo"><label for="rol">Entro como</label>
        <select id="rol" name="rol">
          <option value="alumno">Alumno</option><option value="docente">Docente</option>
          <option value="administrador">Administración</option><option value="encargado">Encargado del centro de acopio</option>
        </select></div>
      <div class="campo"><label for="ident" id="lbl-ident">Matrícula</label><input id="ident" name="identificador" required autocomplete="username"></div>
<div class="campo" id="campo-pw">
  <label for="pw">Contraseña</label>
  <div style="display: flex; gap: 5px;">
    <input id="pw" name="contrasena" type="password" autocomplete="current-password" style="flex: 1;">
<button type="button" id="btn-ver-pass" style="padding: 0 12px; background: #fff; color: #2457a6; border: 1px solid #d9dee5; display: flex; align-items: center; justify-content: center; border-radius: 6px;">
  <svg id="svg-ver" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" style="width: 20px; height: 20px; fill: currentColor;">
    <path d="M320 96C239.2 96 174.5 132.8 127.4 176.6C80.6 220.1 49.3 272 34.4 307.7C31.1 315.6 31.1 324.4 34.4 332.3C49.3 368 80.6 420 127.4 463.4C174.5 507.1 239.2 544 320 544C400.8 544 465.5 507.2 512.6 463.4C559.4 419.9 590.7 368 605.6 332.3C608.9 324.4 608.9 315.6 605.6 307.7C590.7 272 559.4 220 512.6 176.6C465.5 132.9 400.8 96 320 96zM176 320C176 240.5 240.5 176 320 176C399.5 176 464 240.5 464 320C464 399.5 399.5 464 320 464C240.5 464 176 399.5 176 320zM320 256C320 291.3 291.3 320 256 320C244.5 320 233.7 317 224.3 311.6C223.3 322.5 224.2 333.7 227.2 344.8C240.9 396 293.6 426.4 344.8 412.7C396 399 426.4 346.3 412.7 295.1C400.5 249.4 357.2 220.3 311.6 224.3C316.9 233.6 320 244.4 320 256z"/>
  </svg>
  <svg id="svg-ocultar" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" style="width: 20px; height: 20px; fill: currentColor; display: none;">
    <path d="M73 39.1C63.6 29.7 48.4 29.7 39.1 39.1C29.8 48.5 29.7 63.7 39 73.1L567 601.1C576.4 610.5 591.6 610.5 600.9 601.1C610.2 591.7 610.3 576.5 600.9 567.2L504.5 470.8C507.2 468.4 509.9 466 512.5 463.6C559.3 420.1 590.6 368.2 605.5 332.5C608.8 324.6 608.8 315.8 605.5 307.9C590.6 272.2 559.3 220.2 512.5 176.8C465.4 133.1 400.7 96.2 319.9 96.2C263.1 96.2 214.3 114.4 173.9 140.4L73 39.1zM236.5 202.7C260 185.9 288.9 176 320 176C399.5 176 464 240.5 464 320C464 351.1 454.1 379.9 437.3 403.5L402.6 368.8C415.3 347.4 419.6 321.1 412.7 295.1C399 243.9 346.3 213.5 295.1 227.2C286.5 229.5 278.4 232.9 271.1 237.2L236.4 202.5zM357.3 459.1C345.4 462.3 332.9 464 320 464C240.5 464 176 399.5 176 320C176 307.1 177.7 294.6 180.9 282.7L101.4 203.2C68.8 240 46.4 279 34.5 307.7C31.2 315.6 31.2 324.4 34.5 332.3C49.4 368 80.7 420 127.5 463.4C174.6 507.1 239.3 544 320.1 544C357.4 544 391.3 536.1 421.6 523.4L357.4 459.2z"/>
  </svg>
</button>
  </div>
</div>
      <button type="submit">Entrar</button>
    </form>
    <div class="demo"><strong>Datos de ejemplo</strong><br>
      Alumno: <code>2023001</code> · Docente: <code>D001</code><br>
      Administración: <code>admin</code> / <code>admin123</code><br>
      Encargado: <code>acopio1</code> o <code>acopio2</code> / <code>acopio123</code></div></div>`;
}

async function vMapa() {
  const pisos = await api("/pisos");
  if (!pisos.includes(pisoActual)) pisoActual = pisos[0];
  const cubs = await api("/cubiculos?piso=" + pisoActual);
  const lado = (l) => cubs.filter((c) => c.lado === l).map((c) => {
    const clic = yo.rol === "alumno" && c.estado === "disponible";
    const texto = c.estado === "asignado" ? esc(c.docente) : c.estado === "en_uso" ? "En uso" : c.estado === "mi_reserva" ? "Tu reserva" : "Disponible";
    return `<div class="cub ${c.estado} ${clic ? "clic" : ""}" ${clic ? `data-acc="elegir-cub" data-id="${c.id}" data-numero="${esc(c.numero)}" title="Clic para solicitarlo"` : ""}>
      <strong>${esc(c.numero)}</strong><small>${texto}</small></div>`;
  }).join("") || '<div class="vacio">Sin cubículos</div>';
  main.innerHTML = `<div class="tarjeta"><h2>Mapa de cubículos</h2>
    <div class="fila"><div class="campo"><label for="piso">Piso</label>
      <select id="piso" data-cambio="piso">${pisos.map((p) => `<option ${p === pisoActual ? "selected" : ""}>${p}</option>`).join("")}</select></div></div>
    <div class="leyenda"><span class="l-disponible">Disponible</span><span class="l-en_uso">En uso</span><span class="l-asignado">Asignado a docente</span></div>
    <div class="mapa">
      <div class="col-titulo">Lado izquierdo</div><div></div><div class="col-titulo">Lado derecho</div>
      <div class="lado">${lado("izquierdo")}</div><div class="pasillo">Pasillo</div><div class="lado">${lado("derecho")}</div>
    </div>
    ${yo.rol === "alumno" ? '<p class="nota">Haz clic en un cubículo disponible para solicitarlo.</p>' : ""}
  </div><div id="panel"></div>`;
}

function formSolicitudCubiculo(id, numero) {
  $("#panel").innerHTML = `<div class="tarjeta"><h2>Solicitar cubículo ${esc(numero)} (piso ${esc(pisoActual)})</h2>
    <form data-form="solicitar-cub" class="fila">
      <input type="hidden" name="cubiculo_id" value="${esc(id)}">
      <div class="campo"><label>Fecha</label><input type="date" name="fecha" value="${hoy()}" min="${hoy()}" required></div>
      <div class="campo"><label>Hora de inicio</label><input type="time" name="hora_inicio" value="10:00" required></div>
      <div class="campo"><label>Hora de fin</label><input type="time" name="hora_fin" value="12:00" required></div>
      <button type="submit">Enviar solicitud</button>
    </form>
    <p class="nota">La solicitud queda pendiente hasta que la Administración la autorice. Máximo 3 horas.</p></div>`;
  $("#panel").scrollIntoView({ behavior: "smooth" });
}

async function vHistorial(matricula = "") {
  const admin = yo.rol === "administrador";
  const h = await api("/historial" + (matricula ? "?matricula=" + encodeURIComponent(matricula) : ""));
  
  const cols = (extra) => (admin ? ["Alumno"] : []).concat(extra);
  const al = (s) => (admin ? [`${esc(s.alumno)}<br><small>${esc(s.alumno_matricula)}</small>`] : []);
  
  const cub = tabla(cols(["Fecha", "Horario", "Cubículo", "Estado", "Entrada", "Salida", ""]), h.cubiculos.map((s) => {
    const cancelar = (yo.rol === "alumno" && s.estado === "pendiente") ? boton("Cancelar", "cancelar-cub", { id: s.id }, "chico peligro") : "";
    return al(s).concat([
      esc(s.fecha), `${esc(s.hora_inicio)} – ${esc(s.hora_fin)}`, cubTexto(s),
      etiqueta(s.estado) + (s.vencido ? ` <span style="background: #b3261e; color: white; padding: 2px 8px; border-radius: 10px; font-size: 0.75rem; font-weight: bold;">VENCIDO</span>` : "") + (s.motivo_rechazo ? `<br><small>${esc(s.motivo_rechazo)}</small>` : ""),
      s.hora_entrada ? esc(s.hora_entrada) : '<span style="color:#999">—</span>', 
      s.hora_salida ? esc(s.hora_salida) : '<span style="color:#999">—</span>', 
      cancelar]);  }), "Sin solicitudes de cubículo.");
  
  const comp = tabla(cols(["Folio", "Fecha", "Centro", "Componentes", "Estado", "Fecha límite", "Devolución", ""]), h.componentes.map((s) => {
    const cancelar = (yo.rol === "alumno" && s.estado === "pendiente") ? boton("Cancelar", "cancelar-comp", { id: s.id }, "chico peligro") : "";
    return al(s).concat([
      `#${s.id}`, esc(s.fecha), esc(s.centro), lista(s),
      etiqueta(s.estado) + (s.vencido ? " " + etiqueta("vencido") : "") + (s.motivo_rechazo ? `<br><small>${esc(s.motivo_rechazo)}</small>` : ""),
      esc(s.fecha_limite || "—"), esc(s.fecha_devolucion || "—") + (s.observaciones ? `<br><small>${esc(s.observaciones)}</small>` : ""), cancelar]);
  }), "Sin solicitudes de componentes.");
  
  main.innerHTML = `<div class="tarjeta">
    <h2>${admin ? "Historial de préstamos" : "Mi historial"}</h2>
    ${admin ? `<form data-form="filtro-hist" class="fila"><div class="campo"><label>Buscar por matrícula o nombre</label>
      <input name="matricula" value="${esc(matricula)}" placeholder="Ej. Juan o 2023001"></div><button type="submit" class="secundario">Buscar</button></form>` : ""}
    <h3>Cubículos</h3>${cub}<h3>Componentes electrónicos</h3>${comp}</div>`;
}


async function vSolCub() {
  const s = await api("/solicitudes-cubiculo?estado=pendiente");
  main.innerHTML = `<div class="tarjeta"><h2>Solicitudes de cubículo pendientes</h2>` +
    tabla(["Alumno", "Cubículo", "Fecha", "Horario", ""], s.map((x) => [
      `${esc(x.alumno)}<br><small>${esc(x.alumno_matricula)}</small>`, cubTexto(x), esc(x.fecha), `${esc(x.hora_inicio)} – ${esc(x.hora_fin)}`,
      boton("Autorizar", "resolver-cub", { id: x.id, decision: "autorizar" }) + boton("Rechazar", "resolver-cub", { id: x.id, decision: "rechazar" }, "chico peligro")]),
      "No hay solicitudes pendientes.") + "</div><div id='panel'></div>"; 
}

async function vUso() {
  const s = (await api("/solicitudes-cubiculo?estado=autorizada")).filter((x) => !x.hora_salida)
    .sort((a, b) => (a.fecha + a.hora_inicio).localeCompare(b.fecha + b.hora_inicio));
  main.innerHTML = `<div class="tarjeta"><h2>Entradas y salidas de cubículos</h2>
    <p class="nota">Reservas autorizadas que aún no terminan. La entrada solo se registra el día de la reserva.</p>` +
    tabla(["Alumno", "Cubículo", "Fecha", "Horario", "Entrada", ""], s.map((x) => {
      const tieneEntrada = x.hora_entrada && x.hora_entrada.trim() !== "";
      
      return [
        `${esc(x.alumno)}<br><small>${esc(x.alumno_matricula)}</small>`, 
        cubTexto(x), 
        esc(x.fecha), 
        `${esc(x.hora_inicio)} – ${esc(x.hora_fin)}`,
        esc(x.hora_entrada || "—"),
        !tieneEntrada 
          ? (x.fecha <= hoy() ? boton(x.fecha < hoy() ? "Registrar entrada (Atrasada)" : "Registrar entrada", "entrada-cub", { id: x.prestamo_id }) : `<small>Reservado para ${esc(x.fecha)}</small>`)
          : boton("Registrar salida", "salida-cub", { id: x.prestamo_id })
      ];
    }), "No hay reservas activas.") + "</div>";
}

async function vSolComp() {
  const s = await api("/solicitudes-componentes?estado=pendiente");
  main.innerHTML = `<div class="tarjeta"><h2>Solicitudes de componentes pendientes</h2>
    <p class="nota">Al autorizar, la solicitud se envía a la computadora del centro de acopio.</p>` +
    tabla(["Folio", "Alumno", "Centro de acopio", "Componentes", ""], s.map((x) => [
      `#${x.id}`, `${esc(x.alumno)}<br><small>${esc(x.alumno_matricula)}</small>`, esc(x.centro), lista(x),
      boton("Autorizar", "resolver-comp", { id: x.id, decision: "autorizar" }) + boton("Rechazar", "resolver-comp", { id: x.id, decision: "rechazar" }, "chico peligro")]),
      "No hay solicitudes pendientes.") + "</div><div id='panel'></div>";
}

async function vCubiculos() {
  const [cubs, docs] = await Promise.all([api("/cubiculos"), api("/docentes")]);
  const opciones = (sel) => `<option value="">— Ninguno —</option>` + docs.map((d) => `<option value="${esc(d.clave)}" ${d.clave === sel ? "selected" : ""}>${esc(d.nombre)}</option>`).join("");
  main.innerHTML = `<div class="tarjeta"><h2>Agregar cubículo</h2>
    <form data-form="alta-cub" class="fila">
      <div class="campo"><label>Piso</label><input name="piso" type="number" min="1" value="1" required style="width:80px"></div>
      <div class="campo"><label>Número</label><input name="numero" required style="width:100px"></div>
      <div class="campo"><label>Lado</label><select name="lado"><option value="izquierdo">Izquierdo</option><option value="derecho">Derecho</option></select></div>
      <div class="campo"><label>Docente asignado</label><select name="docente_clave">${opciones("")}</select></div>
      <button type="submit">Agregar</button></form></div>
    <div class="tarjeta"><h2>Cubículos registrados</h2>
    <p class="nota">Asignar un docente cambia el cubículo a "asignado a docente" (ya no se puede solicitar). Elige "Ninguno" para liberarlo.</p>` +
    tabla(["Piso", "Número", "Lado", "Estado", "Docente asignado", ""], cubs.map((c) => [
      esc(c.piso), esc(c.numero), esc(c.lado), etiqueta(c.estado),
      `<select data-campo="docente_clave">${opciones(c.docente_clave)}</select>`,
      boton("Guardar", "guardar-cub", { id: c.id, piso: c.piso, numero: c.numero, lado: c.lado }) + boton("Eliminar", "baja-cub", { id: c.id, numero: c.numero }, "chico peligro")])) + "</div>";
}

async function vComponentes() {
  const centros = await api("/centros");
  if (!centros.some((c) => c.id === centroActual)) centroActual = centros[0].id;
  const comps = await api("/componentes?centro_id=" + centroActual);
  main.innerHTML = `<div class="tarjeta"><h2>Componentes electrónicos disponibles</h2>
    <div class="fila"><div class="campo"><label for="centro">Centro de acopio</label>
      <select id="centro" data-cambio="centro">${centros.map((c) => `<option value="${c.id}" ${c.id === centroActual ? "selected" : ""}>${esc(c.nombre)}</option>`).join("")}</select></div></div>
    <p class="nota">${esc(centros.find((c) => c.id === centroActual).ubicacion)}. Escribe la cantidad que necesitas y envía la solicitud.</p>
    <form data-form="solicitar-comp" class="carrito"><input type="hidden" name="centro_id" value="${centroActual}">` +
    tabla(["Código", "Componente", "Disponibles", "En uso", "Cantidad"], comps.map((c) => [
      esc(c.codigo), `${esc(c.nombre)}${c.descripcion ? `<br><small>${esc(c.descripcion)}</small>` : ""}`, c.cantidad_disponible, c.en_uso,
      `<input type="number" name="c_${c.id}" min="0" max="${c.cantidad_disponible}" value="0" ${c.cantidad_disponible ? "" : "disabled"}>`])) +
    `<p><button type="submit">Enviar solicitud</button></p></form></div>`;
}

let RECIBIDAS = [];
async function vRecibidas() {
  RECIBIDAS = await api("/solicitudes-componentes");
  main.innerHTML = `<div class="tarjeta"><h2>Solicitudes recibidas en el centro de acopio</h2>
    <p class="nota">Llegan aquí cuando la Administración las autoriza. Al entregar se descuentan las existencias; al devolver se vuelven a sumar.</p>` +
    tabla(["Folio", "Alumno", "Componentes", "Estado", "Fecha límite", ""], RECIBIDAS.map((x) => [
      `#${x.id}`, `${esc(x.alumno)}<br><small>${esc(x.alumno_matricula)}</small>`, lista(x),
      etiqueta(x.estado) + (x.vencido ? " " + etiqueta("vencido") : ""), esc(x.fecha_limite || "—"),
      x.estado === "autorizada" ? boton("Entregar", "entregar", { id: x.id }) : boton("Registrar devolución", "abrir-devolucion", { id: x.id })]),
      "No hay solicitudes por atender.") + `</div><div id="panel"></div>`;
}

async function vInventario() {
  const comps = await api("/componentes");
  function dibujarTabla(filtro = "") {
    const filtrados = comps.filter(c => 
      c.nombre.toLowerCase().includes(filtro.toLowerCase()) || 
      c.codigo.toLowerCase().includes(filtro.toLowerCase())
    );
    return tabla(["Código", "Nombre", "Descripción", "Total", "Disponibles", "En uso", ""], filtrados.map((c) => [
      `<input data-campo="codigo" value="${esc(c.codigo)}" style="width:80px">`, 
      `<input data-campo="nombre" value="${esc(c.nombre)}">`,
      `<input data-campo="descripcion" value="${esc(c.descripcion)}">`, 
      `<input data-campo="cantidad_total" type="number" min="0" value="${c.cantidad_total}" style="width:80px">`,
      c.cantidad_disponible, c.en_uso,
      boton("Guardar", "guardar-comp", { id: c.id }) + boton("Eliminar", "baja-comp", { id: c.id, nombre: c.nombre }, "chico peligro")
    ]));
  }

  main.innerHTML = `<div class="tarjeta"><h2>Agregar componente</h2>
    <form data-form="alta-comp" class="fila">
      <div class="campo"><label>Código</label><input name="codigo" required style="width:100px"></div>
      <div class="campo"><label>Nombre</label><input name="nombre" required></div>
      <div class="campo"><label>Descripción</label><input name="descripcion"></div>
      <div class="campo"><label>Cantidad</label><input name="cantidad_total" type="number" min="0" value="1" required style="width:90px"></div>
      <button type="submit">Agregar</button></form></div>
    <div class="tarjeta"><h2>Inventario del centro de acopio</h2>
    <div class="fila" style="margin-bottom: 15px;">
      <input type="text" id="buscador-comp" placeholder="Buscar componente por nombre o código..." style="width: 300px;">
    </div>
    <div id="tabla-inventario">${dibujarTabla()}</div></div>`;

  document.getElementById("buscador-comp").addEventListener("input", (e) => {
    const texto = e.target.value;
    document.getElementById("tabla-inventario").innerHTML = dibujarTabla(texto);
  });
}

async function vUsuarios() {
  const users = await api("/usuarios");
  main.innerHTML = `<div class="tarjeta"><h2>Agregar nuevo usuario</h2>
    <form data-form="alta-user" class="fila">
      <div class="campo"><label>Rol</label><select name="rol">
        <option value="alumno">Alumno</option><option value="docente">Docente</option>
        <option value="administrador">Administrador</option><option value="encargado">Encargado de acopio</option>
      </select></div>
      <div class="campo"><label>Matrícula / Clave / Usuario</label><input name="identificador" required></div>
      <div class="campo"><label>Nombre completo</label><input name="nombre" required></div>
      
      <div class="campo">
        <label>Contraseña</label>
        <div style="display: flex; gap: 5px;">
          <input name="contrasena" type="password" required style="flex: 1;" id="pass-alta">
          <button type="button" id="btn-ver-pass-alta" onclick="togglePass('pass-alta', this)" style="padding: 0 12px; background: #fff; color: #2457a6; border: 1px solid #d9dee5; display: flex; align-items: center; justify-content: center; border-radius: 6px;">
            <svg id="svg-ver-alta" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" style="width: 20px; height: 20px; fill: currentColor;">
              <path d="M320 96C239.2 96 174.5 132.8 127.4 176.6C80.6 220.1 49.3 272 34.4 307.7C31.1 315.6 31.1 324.4 34.4 332.3C49.3 368 80.6 420 127.4 463.4C174.5 507.1 239.2 544 320 544C400.8 544 465.5 507.2 512.6 463.4C559.4 419.9 590.7 368 605.6 332.3C608.9 324.4 608.9 315.6 605.6 307.7C590.7 272 559.4 220 512.6 176.6C465.5 132.9 400.8 96 320 96zM176 320C176 240.5 240.5 176 320 176C399.5 176 464 240.5 464 320C464 399.5 399.5 464 320 464C240.5 464 176 399.5 176 320zM320 256C320 291.3 291.3 320 256 320C244.5 320 233.7 317 224.3 311.6C223.3 322.5 224.2 333.7 227.2 344.8C240.9 396 293.6 426.4 344.8 412.7C396 399 426.4 346.3 412.7 295.1C400.5 249.4 357.2 220.3 311.6 224.3C316.9 233.6 320 244.4 320 256z"/>
            </svg>
            <svg id="svg-ocultar-alta" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 640 640" style="width: 20px; height: 20px; fill: currentColor; display: none;">
              <path d="M73 39.1C63.6 29.7 48.4 29.7 39.1 39.1C29.8 48.5 29.7 63.7 39 73.1L567 601.1C576.4 610.5 591.6 610.5 600.9 601.1C610.2 591.7 610.3 576.5 600.9 567.2L504.5 470.8C507.2 468.4 509.9 466 512.5 463.6C559.3 420.1 590.6 368.2 605.5 332.5C608.8 324.6 608.8 315.8 605.5 307.9C590.6 272.2 559.3 220.2 512.5 176.8C465.4 133.1 400.7 96.2 319.9 96.2C263.1 96.2 214.3 114.4 173.9 140.4L73 39.1zM236.5 202.7C260 185.9 288.9 176 320 176C399.5 176 464 240.5 464 320C464 351.1 454.1 379.9 437.3 403.5L402.6 368.8C415.3 347.4 419.6 321.1 412.7 295.1C399 243.9 346.3 213.5 295.1 227.2C286.5 229.5 278.4 232.9 271.1 237.2L236.4 202.5zM357.3 459.1C345.4 462.3 332.9 464 320 464C240.5 464 176 399.5 176 320C176 307.1 177.7 294.6 180.9 282.7L101.4 203.2C68.8 240 46.4 279 34.5 307.7C31.2 315.6 31.2 324.4 34.5 332.3C49.4 368 80.7 420 127.5 463.4C174.6 507.1 239.3 544 320.1 544C357.4 544 391.3 536.1 421.6 523.4L357.4 459.2z"/>
            </svg>
          </button>
        </div>
      </div>
      
      <button type="submit">Agregar</button></form></div>
    
    <div class="tarjeta"><h2>Usuarios registrados</h2>` +
    tabla(["Rol", "Identificador", "Nombre", "Contraseña", "Acciones"], users.map((u) => {
      let acciones = "—";
      if (u.rol === "administrador" || u.rol === "encargado") {
        acciones = `<button class="chico peligro" onclick="eliminarUsuario(${u.id})">Eliminar</button>`;
      } else if (u.rol === "alumno") {
        acciones = `<button class="chico peligro" onclick="eliminarAlumno('${esc(u.id)}')">Eliminar</button>`;
      } else if (u.rol === "docente") {
        acciones = `<button class="chico peligro" onclick="eliminarDocente('${esc(u.id)}')">Eliminar</button>`;
      }
      
      // Mostramos la contraseña (en texto plano si es que existe, o un guion si no)
      const passTexto = u.contrasena_plana ? u.contrasena_plana : "—";
      
      return [
        etiqueta(u.rol), esc(u.id), esc(u.nombre), passTexto, acciones
      ];
    })) + "</div>";
}

async function vDashboard() {
  const stats = await api("/dashboard");
  main.innerHTML = `<div class="tarjeta"><h2>Panel de Control</h2>
    <p class="nota">Resumen general del sistema hoy.</p>
    
    <div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin-top: 20px;">
      
      <div style="background: #fff1cc; padding: 20px; border-radius: 10px; border-left: 5px solid #d9534f; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h3 style="margin: 0; font-size: 2rem; color: #b3261e;">${stats.pend_cub}</h3>
        <p style="margin: 5px 0 0; color: #5b6675;">Solicitudes de cubículo pendientes</p>
      </div>

      <div style="background: #f9d9d5; padding: 20px; border-radius: 10px; border-left: 5px solid #b3261e; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h3 style="margin: 0; font-size: 2rem; color: #b3261e;">${stats.en_uso}</h3>
        <p style="margin: 5px 0 0; color: #5b6675;">Cubículos en uso ahora</p>
      </div>

      <div style="background: #d8e5f8; padding: 20px; border-radius: 10px; border-left: 5px solid #3a7bd5; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h3 style="margin: 0; font-size: 2rem; color: #1d4a8f;">${stats.pend_comp}</h3>
        <p style="margin: 5px 0 0; color: #5b6675;">Solicitudes de componentes pendientes</p>
      </div>

      <div style="background: #d8f1df; padding: 20px; border-radius: 10px; border-left: 5px solid #4fae6a; box-shadow: 0 2px 5px rgba(0,0,0,0.1);">
        <h3 style="margin: 0; font-size: 2rem; color: #1f7a3d;">${stats.activos_comp}</h3>
        <p style="margin: 5px 0 0; color: #5b6675;">Préstamos de componentes activos</p>
      </div>
      
    </div>
  </div>`;
}

window.eliminarUsuario = async function(id) {
  if (!confirm("¿Seguro que deseas eliminar a este usuario?")) return;
  try {
    await api(`/usuarios/${id}`, "DELETE");
    aviso("Usuario eliminado correctamente.");
    ir("usuarios");
  } catch (e) { aviso(e.message, false); }
};

window.eliminarAlumno = async function(matricula) {
  if (!confirm(`¿Seguro que deseas eliminar al alumno con matrícula ${matricula}?`)) return;
  try {
    await api(`/usuarios/alumno/${matricula}`, "DELETE");
    aviso("Alumno eliminado.");
    ir("usuarios");
  } catch (e) { aviso(e.message, false); }
};

window.eliminarDocente = async function(clave) {
  if (!confirm(`¿Seguro que deseas eliminar al docente con clave ${clave}?`)) return;
  try {
    await api(`/usuarios/docente/${clave}`, "DELETE");
    aviso("Docente eliminado.");
    ir("usuarios");
  } catch (e) { aviso(e.message, false); }
};

const recargar = () => ir(vistaActual);
const ACCIONES = {
  "elegir-cub": (d) => formSolicitudCubiculo(d.id, d.numero),
    "resolver-cub": async (d) => {
    if (d.decision === "rechazar") { 
      abrirModalRechazo("cub", d.id); 
      return; 
    }
    await api(`/solicitudes-cubiculo/${d.id}/resolver`, "POST", { decision: d.decision });
    aviso("Solicitud autorizada."); recargar();
  },
  "resolver-comp": async (d) => {
    if (d.decision === "rechazar") { 
      abrirModalRechazo("comp", d.id); 
      return; 
    }
    await api(`/solicitudes-componentes/${d.id}/resolver`, "POST", { decision: d.decision });
    aviso("Autorizada: enviada al centro de acopio."); recargar();
  },
  "guardar-cub": async (d, b) => {
    const docente = b.closest("tr").querySelector('[data-campo="docente_clave"]').value;
    await api(`/cubiculos/${d.id}`, "PUT", { piso: d.piso, numero: d.numero, lado: d.lado, docente_clave: docente });
    aviso("Cubículo actualizado."); recargar();
  },
  "baja-cub": async (d) => {
    if (!confirm(`¿Eliminar el cubículo ${d.numero}?`)) return;
    await api(`/cubiculos/${d.id}`, "DELETE"); aviso("Cubículo eliminado."); recargar();
  },
  "entregar": async (d) => {
    const r = await api(`/solicitudes-componentes/${d.id}/entregar`, "POST");
    aviso(`Entrega registrada. Fecha límite de devolución: ${r.fecha_limite}.`); recargar();
  },
  "abrir-devolucion": (d) => {
    const s = RECIBIDAS.find((x) => x.id === Number(d.id));
    $("#panel").innerHTML = `<div class="tarjeta"><h2>Registrar devolución de la solicitud #${esc(d.id)}</h2>
      <form data-form="devolver"><input type="hidden" name="id" value="${esc(d.id)}">` +
      tabla(["Componente", "Prestadas", "Dañadas o faltantes"], s.detalles.map((x) => [
        esc(x.nombre), x.cantidad, `<input type="number" name="p_${x.id}" min="0" max="${x.cantidad}" value="0" style="width:80px">`])) +
      `<div class="campo" style="margin:12px 0"><label>Observaciones (opcional)</label><input name="observaciones" style="width:100%"></div>
       <button type="submit">Confirmar devolución</button></form>
      <p class="nota">Lo dañado o faltante sale del inventario; el resto vuelve a quedar disponible.</p></div>`;
    $("#panel").scrollIntoView({ behavior: "smooth" });
  },
  "guardar-comp": async (d, b) => {
    const cuerpo = {};
    b.closest("tr").querySelectorAll("[data-campo]").forEach((i) => (cuerpo[i.dataset.campo] = i.value));
    await api(`/componentes/${d.id}`, "PUT", cuerpo); aviso("Componente actualizado."); recargar();
  },
  "baja-comp": async (d) => {
    if (!confirm(`¿Eliminar "${d.nombre}" del inventario?`)) return;
    await api(`/componentes/${d.id}`, "DELETE"); aviso("Componente eliminado."); recargar();
  },
  "cancelar-cub": async (d) => {
    if (!confirm("¿Cancelar esta solicitud de cubículo?")) return;
    await api(`/solicitudes-cubiculo/${d.id}/cancelar`, "POST"); aviso("Solicitud cancelada."); recargar();
  },
  "cancelar-comp": async (d) => {
    if (!confirm("¿Cancelar esta solicitud de componentes?")) return;
    await api(`/solicitudes-componentes/${d.id}/cancelar`, "POST"); aviso("Solicitud cancelada."); recargar();
  },
    "entrada-cub": async (d) => { 
    await api(`/prestamos-cubiculo/${d.id}/entrada`, "POST"); 
    aviso("Entrada registrada."); 
    recargar(); 
  },
  "salida-cub": async (d) => { 
    await api(`/prestamos-cubiculo/${d.id}/salida`, "POST"); 
    aviso("Salida registrada."); 
    recargar(); 
  },

};

function abrirModalRechazo(tipo, id) {
  const panel = $("#panel");
  if (!panel) return aviso("Error interno: no se encontró el panel.", false);
  
  const titulo = tipo === "cub" ? "cubículo" : "componentes";
  panel.innerHTML = `
    <div class="tarjeta" style="margin-top: 20px; border-left: 4px solid #b3261e;">
      <h3>Rechazar solicitud de ${titulo} #${id}</h3>
      <form data-form="rechazar-${tipo}">
        <input type="hidden" name="id" value="${id}">
        <div class="campo" style="margin-bottom: 10px;">
          <label>Motivo del rechazo (opcional)</label>
          <input name="motivo" placeholder="Ej. Cubículo en mantenimiento..." style="width: 100%; max-width: 400px;">
        </div>
        <button type="submit" class="peligro">Confirmar Rechazo</button>
        <button type="button" class="secundario" onclick="document.getElementById('panel').innerHTML=''">Cancelar</button>
      </form>
    </div>
  `;
  panel.scrollIntoView({ behavior: "smooth" });
}


const FORMS = {
  login: async (f) => { yo = await api("/login", "POST", Object.fromEntries(f)); entrar(); },
  "solicitar-cub": async (f) => {
    await api("/solicitudes-cubiculo", "POST", Object.fromEntries(f));
    aviso("Solicitud enviada. Queda pendiente de autorización."); $("#panel").innerHTML = "";
  },
  "filtro-hist": (f) => vHistorial(f.get("matricula").trim()),
  "alta-cub": async (f) => { await api("/cubiculos", "POST", Object.fromEntries(f)); aviso("Cubículo agregado."); recargar(); },
  "solicitar-comp": async (f) => {
    const items = [...f.entries()].filter(([k, v]) => k.startsWith("c_") && Number(v) > 0)
      .map(([k, v]) => ({ componente_id: Number(k.slice(2)), cantidad: Number(v) }));
    await api("/solicitudes-componentes", "POST", { centro_id: Number(f.get("centro_id")), items });
    aviso("Solicitud enviada a la Administración para su autorización."); recargar();
  },
  devolver: async (f) => {
    const perdidas = {};
    for (const [k, v] of f.entries()) if (k.startsWith("p_")) perdidas[k.slice(2)] = Number(v);
    await api(`/solicitudes-componentes/${f.get("id")}/devolver`, "POST", { perdidas, observaciones: f.get("observaciones") });
    aviso("Devolución registrada."); recargar();
  },
  "alta-comp": async (f) => { 
    await api("/componentes", "POST", Object.fromEntries(f)); 
    aviso("Componente agregado."); 
    recargar(); 
  },
  "alta-user": async (f) => {
    await api("/usuarios", "POST", Object.fromEntries(f));
    aviso("Usuario agregado correctamente.");
    recargar();
  }, 
  "rechazar-cub": async (f) => {
    const id = f.get("id");
    const motivo = f.get("motivo");
    await api(`/solicitudes-cubiculo/${id}/resolver`, "POST", { decision: "rechazar", motivo });
    aviso("Solicitud rechazada.");
    recargar();
  },
  "rechazar-comp": async (f) => {
    const id = f.get("id");
    const motivo = f.get("motivo");
    await api(`/solicitudes-componentes/${id}/resolver`, "POST", { decision: "rechazar", motivo });
    aviso("Solicitud rechazada.");
    recargar();
  },

};


async function protegido(fn) { try { await fn(); } catch (e) { aviso(e.message, false); } }
main.addEventListener("click", (e) => {
  const b = e.target.closest("[data-acc]");
  if (b) protegido(() => ACCIONES[b.dataset.acc](b.dataset, b));
});
main.addEventListener("submit", (e) => {
  e.preventDefault();
  const f = e.target;
  protegido(() => FORMS[f.dataset.form](new FormData(f), f));
});
main.addEventListener("change", (e) => {
  const t = e.target;
  if (t.dataset.cambio === "piso") { pisoActual = Number(t.value); ir("mapa"); }
  if (t.dataset.cambio === "centro") { centroActual = Number(t.value); ir("componentes"); }
  if (t.id === "rol") {
    $("#lbl-ident").textContent = { alumno: "Matrícula", docente: "Clave de docente" }[t.value] || "Usuario";
    $("#campo-pw").hidden = false;
    $("#pw").required = true;
  }
});
$("#menu").addEventListener("click", (e) => { const b = e.target.closest("[data-vista]"); if (b) ir(b.dataset.vista); });
$("#btn-salir").addEventListener("click", async () => { await api("/logout", "POST"); yo = null; vistaActual = null; vLogin(); });

function entrar() {
  $("#quien").textContent = `${yo.nombre} (${{ alumno: "alumno", docente: "docente", administrador: "administración", encargado: "encargado de acopio" }[yo.rol]})`;
  $("#sesion").hidden = false;
  ir(MENUS[yo.rol][0][0]);
}
(async () => {
  try { yo = await api("/yo"); } catch { yo = null; }
  yo ? entrar() : vLogin();
})();

document.addEventListener("click", (e) => {
  const btn = e.target.closest("#btn-ver-pass");
  if (btn) {
    const inputPass = document.getElementById("pw");
    const svgVer = document.getElementById("svg-ver");
    const svgOcultar = document.getElementById("svg-ocultar");

    if (inputPass.type === "password") {
      inputPass.type = "text";
      btn.style.color = "#b3261e";
      btn.style.background = "#fdecea";
      svgVer.style.display = "none";
      svgOcultar.style.display = "block";
    } else {
      inputPass.type = "password";
      btn.style.color = "#2457a6";
      btn.style.background = "#fff";
      svgVer.style.display = "block";
      svgOcultar.style.display = "none";
    }
  }
});

window.togglePass = function(inputId, btn) {
  const input = document.getElementById(inputId);
  const sufijo = inputId === "pw" ? "" : "-alta";
  const svgVer = document.getElementById("svg-ver" + sufijo);
  const svgOcultar = document.getElementById("svg-ocultar" + sufijo);

  if (input.type === "password") {
    input.type = "text";
    btn.style.color = "#b3261e";
    btn.style.background = "#fdecea";
    if (svgVer) svgVer.style.display = "none";
    if (svgOcultar) svgOcultar.style.display = "block";
  } else {
    input.type = "password";
    btn.style.color = "#2457a6";
    btn.style.background = "#fff";
    if (svgVer) svgVer.style.display = "block";
    if (svgOcultar) svgOcultar.style.display = "none";
  }
};