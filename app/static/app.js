'use strict';
/* SALES-X - interfaz web (JS puro; sin estilos/scripts en línea por la CSP). */
const API = '/api/v1';
const $ = (s, r = document) => r.querySelector(s);
const $$ = (s, r = document) => [...r.querySelectorAll(s)];
const esc = s => String(s ?? '').replace(/[&<>"']/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
const nf = new Intl.NumberFormat('es-CO', { style: 'currency', currency: 'COP', minimumFractionDigits: 0, maximumFractionDigits: 0 });
const money = v => nf.format(Number(v));
const fdate = iso => {
  if (!iso) return '';
  const s = /([zZ]|[+-]\d\d:?\d\d)$/.test(iso) ? iso : iso + 'Z'; // SQLite devuelve fechas UTC sin zona
  return new Date(s).toLocaleString('es-CO', { dateStyle: 'medium', timeStyle: 'short' });
};
const ymd = d => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`;
const badge = e => `<span class="badge b-${esc(String(e).replace(/ /g, '-'))}">${esc(e)}</span>`;

const TRANS = {
  'Pendiente': ['Confirmado', 'Cancelado'], 'Confirmado': ['En preparación', 'Cancelado'],
  'En preparación': ['Enviado', 'Cancelado'], 'Enviado': ['Entregado'], 'Entregado': [], 'Cancelado': [],
};
const ESTADOS = Object.keys(TRANS);
// La sesión vive en una cookie HttpOnly (el JavaScript no puede leerla); solo se lee la cookie CSRF.
const S = { user: null, iva: 0.19, cMap: new Map(), pMap: new Map() };
const cookie = n => document.cookie.split('; ').find(c => c.startsWith(n + '='))?.split('=')[1] ?? '';

const view = $('#view');

/* ---------- utilidades ---------- */
function toast(msg, err = false) {
  const t = $('#toast'); t.textContent = msg; t.className = 'toast' + (err ? ' err' : '');
  clearTimeout(toast.h); toast.h = setTimeout(() => t.classList.add('hidden'), 4200);
}
function errMsg(d, status) {
  if (!d) return 'Error ' + status;
  if (typeof d.detail === 'string') return d.detail;
  if (Array.isArray(d.detail)) return d.detail.map(e => `${(e.loc || []).slice(1).join('.')}: ${e.msg}`).join('; ');
  return 'Error ' + status;
}
async function api(path, { method = 'GET', body, raw = false } = {}) {
  const headers = {};
  if (body) headers['Content-Type'] = 'application/json';
  if (method !== 'GET') headers['X-CSRF-Token'] = decodeURIComponent(cookie('salesx_csrf'));
  const r = await fetch(API + path, { method, headers, credentials: 'same-origin', body: body ? JSON.stringify(body) : undefined });
  if (r.status === 401 && !path.startsWith('/auth/login') && !path.startsWith('/auth/me')) { showLogin(); throw new Error('Sesión expirada, ingrese de nuevo'); }
  if (raw && r.ok) return r;
  const data = await r.json().catch(() => null);
  if (!r.ok) throw new Error(errMsg(data, r.status));
  return data;
}
function ask(title, bodyHtml, okText = 'Aceptar') {
  return new Promise(res => {
    const d = $('#dlg'), form = $('#dlg-form');
    if (d.open) d.close();
    $('#dlg-title').textContent = title; $('#dlg-body').innerHTML = bodyHtml; $('#dlg-ok').textContent = okText;
    $('#dlg-cancel').formNoValidate = true; d.returnValue = '';
    let done = false;
    // Se resuelve al enviar el formulario o al cerrarse (Esc); el aplazamiento deja que el diálogo termine de cerrarse
    // antes de que el código siguiente pueda abrir otro.
    const finish = ok => { if (done) return; done = true; setTimeout(() => res(ok), 0); };
    form.onsubmit = e => finish(e.submitter?.value === 'ok');
    d.onclose = () => finish(d.returnValue === 'ok');
    d.showModal();
    const f = $('#dlg-body input,#dlg-body textarea'); if (f) f.focus();
  });
}
const cName = id => S.cMap.get(id)?.nombre ?? id.slice(0, 8) + '…';
const pName = id => S.pMap.get(id)?.nombre ?? id.slice(0, 8) + '…';
const animateBars = () => $$('.bar-fill', view).forEach(el => { el.style.width = el.dataset.w + '%'; });
const barsHtml = (rows, fmtV = v => v) => {
  const max = Math.max(1, ...rows.map(r => r.v));
  return `<div class="bars">${rows.map(r => `<div class="bar-row"><span>${esc(r.k)}</span><div class="bar-track"><div class="bar-fill" data-w="${(r.v / max) * 100}"></div></div><span class="right">${esc(fmtV(r.v))}</span></div>`).join('')}</div>`;
};

/* ---------- sesión ---------- */
async function boot() {
  try { sessionStorage.removeItem('sx_token'); } catch { /* resto de la v1.0: el token ya no se guarda en el navegador */ }
  try { const h = await (await fetch('/health')).json(); if (h.iva_rate != null) S.iva = h.iva_rate; } catch { /* ignorar */ }
  try {
    S.user = await api('/auth/me');
    await entrar();
  } catch { showLogin(); }
}
async function entrar() {
  if (S.user.debe_cambiar_contrasena) {  // contraseña inicial/restablecida: debe definir una propia antes de operar
    if (!await cambiarContrasena(true)) return salir();
    S.user = await api('/auth/me');
  }
  await loadCatalog();
  showShell();
}
async function cambiarContrasena(forzado = false) {
  for (;;) {
    const ok = await ask(forzado ? 'Debe cambiar su contraseña' : 'Cambiar mi contraseña',
      `${forzado ? '<p class="muted">Por seguridad debe definir una contraseña propia antes de continuar.</p>' : ''}
       <label>Contraseña actual<input id="c-act" type="password" required autocomplete="current-password"></label>
       <label>Nueva contraseña (mín. 10, con letras y números)<input id="c-new" type="password" required minlength="10" maxlength="128" autocomplete="new-password"></label>
       <label>Repetir la nueva contraseña<input id="c-rep" type="password" required autocomplete="new-password"></label>`, 'Guardar');
    if (!ok) return false;
    if ($('#c-new').value !== $('#c-rep').value) { toast('Las contraseñas nuevas no coinciden', true); continue; }
    try {
      await api('/auth/cambiar-contrasena', { method: 'POST', body: { actual: $('#c-act').value, nueva: $('#c-new').value } });
      toast('Contraseña actualizada'); return true;
    } catch (e) { toast(e.message, true); }
  }
}
async function loadCatalog() {
  const [c, p] = await Promise.all([api('/catalogo/clientes'), api('/catalogo/productos')]);
  S.cMap = new Map(c.map(x => [x.cliente_id, x])); S.pMap = new Map(p.map(x => [x.producto_id, x]));
}
function showLogin() {
  S.user = null;
  $('#shell').classList.add('hidden'); $('#login').classList.remove('hidden'); $('#l-pass').value = '';
}
function showShell() {
  $('#login').classList.add('hidden'); $('#shell').classList.remove('hidden');
  $('#who').innerHTML = `<strong>${esc(S.user.nombre)}</strong><br><span class="muted">${esc(S.user.rol)}</span>`;
  $$('.admin-only').forEach(a => a.classList.toggle('hidden', S.user.rol !== 'admin'));
  route();
}
async function salir() {
  try { await api('/auth/logout', { method: 'POST' }); } catch { /* la sesión ya no existe */ }
  showLogin();
}
$('#login-form').addEventListener('submit', async e => {
  e.preventDefault();
  const err = $('#l-error'); err.classList.add('hidden');
  try {
    await api('/auth/login', { method: 'POST', body: { correo: $('#l-correo').value, contrasena: $('#l-pass').value } });
    S.user = await api('/auth/me'); await entrar();
  } catch (ex) { err.textContent = ex.message; err.classList.remove('hidden'); }
});
$('#logout').addEventListener('click', salir);
$('#chpw').addEventListener('click', () => cambiarContrasena(false));

/* ---------- router ---------- */
const routes = { dashboard: viewDashboard, pedidos: viewPedidos, nuevo: () => viewForm(), editar: id => viewForm(id), pedido: viewDetalle, reportes: viewReportes, usuarios: viewUsuarios, integraciones: viewIntegraciones };
async function route() {
  if (!S.user) return;
  const [r, arg] = location.hash.replace(/^#\//, '').split('/');
  const name = routes[r] ? r : 'dashboard';
  const active = { pedido: 'pedidos', editar: 'pedidos' }[name] || name;
  $$('#nav a').forEach(a => a.classList.toggle('active', a.dataset.r === active));
  view.innerHTML = '<p class="muted">Cargando…</p>';
  try { await routes[name](arg); animateBars(); } catch (e) { view.innerHTML = `<div class="card"><p class="error">${esc(e.message)}</p></div>`; }
  window.scrollTo(0, 0);
}
window.addEventListener('hashchange', route);

/* ---------- Panel ---------- */
async function viewDashboard() {
  const hoy = new Date(), ini = new Date(hoy.getFullYear(), hoy.getMonth(), 1), man = new Date(hoy.getTime() + 864e5);
  const [rep, ped, sol] = await Promise.all([
    api(`/reportes/ventas?desde=${ymd(ini)}&hasta=${ymd(man)}`), api('/pedidos?size=8'), api('/pedidos/solicitudes?limit=6')]);
  const estados = ESTADOS.map(k => ({ k, v: rep.por_estado[k] || 0 }));
  view.innerHTML = `
    <div class="head"><div><h1>Panel de ventas</h1><p class="muted">Resumen del mes en curso</p></div>
      <a class="btn primary" href="#/nuevo">+ Nuevo pedido</a></div>
    <div class="grid g4">
      <div class="card kpi"><div class="label">Ventas del mes</div><div class="value">${money(rep.total_ventas)}</div></div>
      <div class="card kpi"><div class="label">Pedidos</div><div class="value">${rep.total_pedidos}</div></div>
      <div class="card kpi"><div class="label">Ticket promedio</div><div class="value">${money(rep.ticket_promedio)}</div></div>
      <div class="card kpi"><div class="label">Cancelados</div><div class="value">${rep.pedidos_cancelados}</div></div>
    </div>
    <div class="grid g3-2 mt">
      <div class="card"><h2>Últimos pedidos</h2>${tablaPedidos(ped.items)}</div>
      <div class="grid">
        <div class="card"><h2>Pedidos por estado</h2>${barsHtml(estados)}</div>
        <div class="card"><h2>Solicitudes de clientes</h2>${sol.length ? `<ul class="timeline">${sol.map(s => `
          <li class="req"><a href="#/pedido/${s.pedido_id}"><strong>${esc(s.accion.replace('SOLICITUD_', '').toLowerCase())}</strong></a>
          <div class="small">${esc(s.descripcion)}</div><div class="small muted">${fdate(s.fecha)}</div></li>`).join('')}</ul>`
      : '<p class="muted">No hay solicitudes recientes.</p>'}</div>
      </div>
    </div>`;
  bindRows();
}
function tablaPedidos(items) {
  if (!items.length) return '<div class="empty">No hay pedidos para mostrar.</div>';
  return `<div class="scroll"><table><thead><tr><th>Pedido</th><th>Cliente</th><th>Fecha</th><th>Estado</th><th class="right">Total</th></tr></thead><tbody>
    ${items.map(p => `<tr class="click" data-id="${p.pedido_id}"><td class="mono">${p.pedido_id.slice(0, 8)}</td><td>${esc(cName(p.cliente_id))}</td>
    <td>${fdate(p.fecha_creacion)}</td><td>${badge(p.estado)}</td><td class="right">${money(p.total)}</td></tr>`).join('')}</tbody></table></div>`;
}
const bindRows = () => $$('tr.click', view).forEach(tr => tr.addEventListener('click', () => { location.hash = '#/pedido/' + tr.dataset.id; }));

/* ---------- Pedidos (lista) ---------- */
async function viewPedidos() {
  const f = viewPedidos.f || (viewPedidos.f = { estado: '', cliente_id: '', desde: '', hasta: '', page: 1 });
  const qs = new URLSearchParams({ page: f.page, size: 15 });
  ['estado', 'cliente_id', 'desde', 'hasta'].forEach(k => f[k] && qs.set(k, f[k]));
  const data = await api('/pedidos?' + qs);
  const pages = Math.max(1, Math.ceil(data.total / data.size));
  view.innerHTML = `
    <div class="head"><div><h1>Pedidos</h1><p class="muted">${data.total} pedido(s) encontrado(s)</p></div><a class="btn primary" href="#/nuevo">+ Nuevo pedido</a></div>
    <div class="card">
      <form id="ff" class="filters">
        <label>Estado<select name="estado"><option value="">Todos</option>${ESTADOS.map(e => `<option ${f.estado === e ? 'selected' : ''}>${esc(e)}</option>`).join('')}</select></label>
        <label>Cliente<select name="cliente_id"><option value="">Todos</option>${[...S.cMap.values()].map(c => `<option value="${c.cliente_id}" ${f.cliente_id === c.cliente_id ? 'selected' : ''}>${esc(c.nombre)}</option>`).join('')}</select></label>
        <label>Desde<input type="date" name="desde" value="${esc(f.desde)}"></label>
        <label>Hasta<input type="date" name="hasta" value="${esc(f.hasta)}"></label>
        <div class="actions"><button class="btn primary">Filtrar</button><button type="button" class="btn" id="fclear">Limpiar</button></div>
      </form>
      ${tablaPedidos(data.items)}
      <div class="pager"><span class="muted small">Página ${data.page} de ${pages}</span>
        <div class="actions"><button class="btn small" id="pp" ${f.page <= 1 ? 'disabled' : ''}>Anterior</button><button class="btn small" id="pn" ${f.page >= pages ? 'disabled' : ''}>Siguiente</button></div></div>
    </div>`;
  $('#ff').addEventListener('submit', e => { e.preventDefault(); Object.assign(f, Object.fromEntries(new FormData(e.target)), { page: 1 }); route(); });
  $('#fclear').addEventListener('click', () => { viewPedidos.f = null; route(); });
  $('#pp').addEventListener('click', () => { f.page--; route(); });
  $('#pn').addEventListener('click', () => { f.page++; route(); });
  bindRows();
}

/* ---------- Detalle de pedido ---------- */
async function viewDetalle(id) {
  const [p, aud] = await Promise.all([api('/pedidos/' + id), api(`/pedidos/${id}/auditoria`)]);
  const sig = TRANS[p.estado].filter(e => e !== 'Cancelado');
  const puedeEditar = ['Pendiente', 'Confirmado'].includes(p.estado);
  view.innerHTML = `
    <div class="head"><div><a href="#/pedidos" class="small">← Pedidos</a><h1>Pedido <span class="mono">${p.pedido_id.slice(0, 8)}</span> ${badge(p.estado)}</h1>
      <p class="muted">${esc(cName(p.cliente_id))} · ${fdate(p.fecha_creacion)}</p></div>
      <div class="actions">
        ${sig.map(e => `<button class="btn primary" data-state="${esc(e)}">Pasar a «${esc(e)}»</button>`).join('')}
        ${puedeEditar ? `<a class="btn" href="#/editar/${p.pedido_id}">Modificar</a>` : ''}
        ${TRANS[p.estado].includes('Cancelado') ? '<button class="btn danger" id="cancel">Cancelar pedido</button>' : ''}
      </div></div>
    ${p.descripcion ? `<div class="alert">${esc(p.descripcion)}</div>` : ''}
    <div class="grid g3-2">
      <div class="card"><h2>Productos</h2><div class="scroll"><table><thead><tr><th>Producto</th><th class="right">Cant.</th><th class="right">Precio</th><th class="right">Subtotal</th></tr></thead><tbody>
        ${p.detalles.map(d => `<tr><td>${esc(pName(d.producto_id))}</td><td class="right">${d.cantidad}</td><td class="right">${money(d.precio_unitario)}</td><td class="right">${money(d.subtotal)}</td></tr>`).join('')}</tbody></table></div>
        <div class="totals mt"><div><span>Subtotal</span><span>${money(p.subtotal)}</span></div><div><span>Impuestos</span><span>${money(p.impuestos)}</span></div><div class="grand"><span>Total</span><span>${money(p.total)}</span></div></div></div>
      <div class="card"><h2>Auditoría</h2><ul class="timeline">${aud.map(a => `<li class="${a.accion.startsWith('SOLICITUD') ? 'req' : ''}"><strong>${esc(a.accion.replace('_', ' '))}</strong>
        <div class="small">${esc(a.descripcion)}</div><div class="small muted">${esc(a.usuario)} · ${fdate(a.fecha)}</div></li>`).join('')}</ul></div>
    </div>`;
  $$('[data-state]', view).forEach(b => b.addEventListener('click', async () => {
    const ok = await ask('Cambiar estado', `<p>¿Pasar el pedido a <strong>${esc(b.dataset.state)}</strong>?</p><label>Comentario (opcional)<input id="d-com" maxlength="300"></label>`);
    if (!ok) return;
    try { await api(`/pedidos/${id}/estado`, { method: 'PATCH', body: { estado: b.dataset.state, comentario: $('#d-com').value || null } }); toast('Estado actualizado'); route(); }
    catch (e) { toast(e.message, true); }
  }));
  const c = $('#cancel');
  if (c) c.addEventListener('click', async () => {
    const ok = await ask('Cancelar pedido', '<label>Motivo de la cancelación<input id="d-mot" required minlength="3" maxlength="300"></label>', 'Cancelar pedido');
    if (!ok) return;
    try { await api(`/pedidos/${id}/cancelar`, { method: 'POST', body: { motivo: $('#d-mot').value } }); toast('Pedido cancelado'); route(); }
    catch (e) { toast(e.message, true); }
  });
}

/* ---------- Nuevo / Modificar pedido ---------- */
async function viewForm(id) {
  let items = [], desc = '', cliente = '';
  if (id) {
    const p = await api('/pedidos/' + id);
    if (!['Pendiente', 'Confirmado'].includes(p.estado)) throw new Error(`El pedido está en estado '${p.estado}' y no se puede modificar`);
    items = p.detalles.map(d => ({ producto_id: d.producto_id, cantidad: d.cantidad })); desc = p.descripcion || ''; cliente = p.cliente_id;
  }
  const productos = [...S.pMap.values()];
  view.innerHTML = `
    <div class="head"><div><a href="${id ? '#/pedido/' + id : '#/pedidos'}" class="small">← Volver</a><h1>${id ? 'Modificar pedido' : 'Nuevo pedido'}</h1></div></div>
    <div class="grid g3-2">
      <div class="card">
        <label>Cliente<select id="f-cliente" ${id ? 'disabled' : ''}><option value="">Seleccione un cliente…</option>
          ${[...S.cMap.values()].map(c => `<option value="${c.cliente_id}" ${cliente === c.cliente_id ? 'selected' : ''}>${esc(c.nombre)} — ${esc(c.documento || '')}</option>`).join('')}</select></label>
        <div class="filters mt"><label>Producto<select id="f-prod"><option value="">Seleccione un producto…</option>
          ${productos.map(p => `<option value="${p.producto_id}" ${(!p.activo || p.disponible < 1) ? 'disabled' : ''}>${esc(p.nombre)} · ${money(p.precio)} · ${p.disponible > 0 ? 'disp. ' + p.disponible : 'AGOTADO'}</option>`).join('')}</select></label>
          <label>Cantidad<input id="f-qty" type="number" min="1" value="1"></label><div><button class="btn" id="f-add" type="button">Agregar</button></div></div>
        <div id="f-items"></div>
        <label class="mt">Observaciones<textarea id="f-desc" rows="2" maxlength="500">${esc(desc)}</textarea></label>
      </div>
      <div class="card"><h2>Resumen</h2><div id="f-tot" class="totals"></div><p class="muted small mt">El precio y la disponibilidad se validan en el servidor al guardar. IVA ${(S.iva * 100).toFixed(0)}%.</p>
        <div class="actions mt"><button class="btn primary" id="f-save">${id ? 'Guardar cambios' : 'Registrar pedido'}</button></div></div>
    </div>`;
  const pintar = () => {
    let sub = 0;
    $('#f-items').innerHTML = items.length ? `<div class="scroll mt"><table><thead><tr><th>Producto</th><th class="right">Precio</th><th>Cantidad</th><th class="right">Subtotal</th><th></th></tr></thead><tbody>
      ${items.map((it, i) => { const p = S.pMap.get(it.producto_id); const st = (p ? Number(p.precio) : 0) * it.cantidad; sub += st;
        return `<tr><td>${esc(pName(it.producto_id))}${p && it.cantidad > p.disponible ? '<div class="error small">Supera la disponibilidad (' + p.disponible + ')</div>' : ''}</td><td class="right">${p ? money(p.precio) : '-'}</td>
        <td><input class="qty" type="number" min="1" max="10000" value="${it.cantidad}" data-i="${i}"></td><td class="right">${money(st)}</td><td><button class="btn small ghost" data-rm="${i}" type="button">Quitar</button></td></tr>`; }).join('')}</tbody></table></div>`
      : '<div class="empty">Agregue al menos un producto.</div>';
    const iva = Math.round(sub * S.iva * 100) / 100;
    $('#f-tot').innerHTML = `<div><span>Subtotal</span><span>${money(sub)}</span></div><div><span>Impuestos</span><span>${money(iva)}</span></div><div class="grand"><span>Total</span><span>${money(sub + iva)}</span></div>`;
    $$('[data-rm]', view).forEach(b => b.addEventListener('click', () => { items.splice(+b.dataset.rm, 1); pintar(); }));
    $$('input[data-i]', view).forEach(inp => inp.addEventListener('change', () => { items[+inp.dataset.i].cantidad = Math.max(1, parseInt(inp.value) || 1); pintar(); }));
  };
  $('#f-add').addEventListener('click', () => {
    const pid = $('#f-prod').value, q = Math.max(1, parseInt($('#f-qty').value) || 1);
    if (!pid) return toast('Seleccione un producto', true);
    const ex = items.find(i => i.producto_id === pid); ex ? ex.cantidad += q : items.push({ producto_id: pid, cantidad: q });
    $('#f-qty').value = 1; pintar();
  });
  $('#f-save').addEventListener('click', async () => {
    const btn = $('#f-save'); const cli = $('#f-cliente').value;
    if (!id && !cli) return toast('Seleccione un cliente', true);
    if (!items.length) return toast('Agregue al menos un producto', true);
    btn.disabled = true;
    try {
      const body = id ? { descripcion: $('#f-desc').value, items } : { cliente_id: cli, descripcion: $('#f-desc').value || null, items };
      const p = await api(id ? '/pedidos/' + id : '/pedidos', { method: id ? 'PUT' : 'POST', body });
      toast(id ? 'Pedido modificado' : 'Pedido registrado'); location.hash = '#/pedido/' + p.pedido_id;
    } catch (e) { toast(e.message, true); btn.disabled = false; }
  });
  pintar();
}

/* ---------- Reportes ---------- */
async function viewReportes() {
  const hoy = new Date(), ini = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
  const f = viewReportes.f || (viewReportes.f = { desde: ymd(ini), hasta: ymd(hoy), agrupar: 'dia' });
  const qs = () => new URLSearchParams({ desde: f.desde, hasta: f.hasta, agrupar: f.agrupar });
  const r = await api('/reportes/ventas?' + qs());
  view.innerHTML = `
    <div class="head"><div><h1>Reporte de ventas</h1><p class="muted">Excluye pedidos cancelados</p></div><div class="actions"><button class="btn" id="csv">Descargar CSV</button><button class="btn" id="print">Imprimir</button></div></div>
    <div class="card"><form id="rf" class="filters">
      <label>Desde<input type="date" name="desde" value="${esc(f.desde)}" required></label><label>Hasta<input type="date" name="hasta" value="${esc(f.hasta)}" required></label>
      <label>Agrupar por<select name="agrupar"><option value="dia" ${f.agrupar === 'dia' ? 'selected' : ''}>Día</option><option value="mes" ${f.agrupar === 'mes' ? 'selected' : ''}>Mes</option></select></label>
      <div><button class="btn primary">Generar</button></div></form></div>
    <div class="grid g4 mt">
      <div class="card kpi"><div class="label">Ventas totales</div><div class="value">${money(r.total_ventas)}</div></div>
      <div class="card kpi"><div class="label">Subtotal</div><div class="value">${money(r.subtotal)}</div></div>
      <div class="card kpi"><div class="label">Impuestos</div><div class="value">${money(r.impuestos)}</div></div>
      <div class="card kpi"><div class="label">Ticket promedio</div><div class="value">${money(r.ticket_promedio)}</div></div></div>
    <div class="grid g2 mt">
      <div class="card"><h2>Ventas por ${f.agrupar === 'mes' ? 'mes' : 'día'}</h2>${r.serie.length ? barsHtml(r.serie.map(s => ({ k: s.periodo, v: Number(s.total) })), money) : '<div class="empty">Sin ventas en el período.</div>'}</div>
      <div class="card"><h2>Detalle</h2>${r.serie.length ? `<div class="scroll"><table><thead><tr><th>Período</th><th class="right">Pedidos</th><th class="right">Total</th></tr></thead><tbody>${r.serie.map(s => `<tr><td>${esc(s.periodo)}</td><td class="right">${s.pedidos}</td><td class="right">${money(s.total)}</td></tr>`).join('')}</tbody></table></div>` : '<div class="empty">—</div>'}</div></div>`;
  $('#rf').addEventListener('submit', e => { e.preventDefault(); Object.assign(f, Object.fromEntries(new FormData(e.target))); route(); });
  $('#print').addEventListener('click', () => window.print());
  $('#csv').addEventListener('click', async () => {
    try {
      const resp = await api('/reportes/ventas.csv?' + qs(), { raw: true }); const url = URL.createObjectURL(await resp.blob());
      const a = Object.assign(document.createElement('a'), { href: url, download: `reporte_ventas_${f.desde}_${f.hasta}.csv` }); a.click(); URL.revokeObjectURL(url);
    } catch (e) { toast(e.message, true); }
  });
}

/* ---------- Usuarios (admin) ---------- */
async function viewUsuarios() {
  if (S.user.rol !== 'admin') throw new Error('Se requiere rol administrador');
  const us = await api('/vendedores');
  view.innerHTML = `
    <div class="head"><div><h1>Usuarios</h1><p class="muted">Gestión de vendedores y administradores</p></div></div>
    <div class="grid g3-2"><div class="card"><div class="scroll"><table><thead><tr><th>Nombre</th><th>Correo</th><th>Rol</th><th>Estado</th><th></th></tr></thead><tbody>
      ${us.map(u => `<tr><td>${esc(u.nombre)}</td><td>${esc(u.correo)}</td><td>${esc(u.rol)}</td><td>${u.activo ? '<span class="badge b-Entregado">Activo</span>' : '<span class="badge b-Cancelado">Inactivo</span>'}</td>
      <td class="right actions"><button class="btn small" data-pw="${u.vendedor_id}">Cambiar contraseña</button><button class="btn small" data-tog="${u.vendedor_id}" data-act="${u.activo}">${u.activo ? 'Desactivar' : 'Activar'}</button></td></tr>`).join('')}</tbody></table></div></div>
      <div class="card"><h2>Nuevo usuario</h2><form id="uf" class="grid">
        <label>Nombre<input name="nombre" required minlength="2" maxlength="120"></label><label>Correo<input name="correo" type="email" required></label>
        <label>Contraseña inicial (mín. 10, letras y números)<input name="contrasena" type="password" required minlength="10" autocomplete="new-password"></label>
        <p class="muted small">El usuario deberá cambiarla en su primer ingreso.</p>
        <label>Rol<select name="rol"><option value="vendedor">Vendedor</option><option value="admin">Administrador</option></select></label>
        <button class="btn primary">Crear usuario</button></form></div></div>`;
  $('#uf').addEventListener('submit', async e => {
    e.preventDefault();
    try { await api('/vendedores', { method: 'POST', body: Object.fromEntries(new FormData(e.target)) }); toast('Usuario creado'); route(); } catch (x) { toast(x.message, true); }
  });
  $$('[data-pw]', view).forEach(b => b.addEventListener('click', async () => {
    const ok = await ask('Cambiar contraseña', '<label>Contraseña temporal (mín. 10, letras y números)<input id="d-pw" type="password" required minlength="10" maxlength="128" autocomplete="new-password"></label><p class="muted small">El usuario deberá cambiarla al ingresar.</p>');
    if (!ok) return;
    try { await api('/vendedores/' + b.dataset.pw, { method: 'PATCH', body: { contrasena: $('#d-pw').value } }); toast('Contraseña actualizada'); } catch (x) { toast(x.message, true); }
  }));
  $$('[data-tog]', view).forEach(b => b.addEventListener('click', async () => {
    try { await api('/vendedores/' + b.dataset.tog, { method: 'PATCH', body: { activo: b.dataset.act !== 'true' } }); route(); } catch (x) { toast(x.message, true); }
  }));
}

/* ---------- Integraciones: consumidores y claves (admin) ---------- */
async function viewIntegraciones() {
  if (S.user.rol !== 'admin') throw new Error('Se requiere rol administrador');
  const cs = await api('/consumidores');
  const fx = iso => iso ? fdate(iso) : '—';
  view.innerHTML = `
    <div class="head"><div><h1>Integraciones</h1><p class="muted">Una clave por sistema consumidor: se puede revocar y su uso queda registrado</p></div></div>
    <div class="grid g3-2"><div class="card"><div class="scroll"><table><thead><tr><th>Consumidor</th><th>Estado</th><th>Expira</th><th>Último uso</th><th></th></tr></thead><tbody>
      ${cs.map(c => `<tr><td>${esc(c.nombre)}</td><td>${c.activo ? '<span class="badge b-Entregado">Activa</span>' : '<span class="badge b-Cancelado">Revocada</span>'}</td>
      <td>${fx(c.expira)}</td><td>${fx(c.ultimo_uso)}</td>
      <td class="right"><button class="btn small" data-tog="${c.consumidor_id}" data-act="${c.activo}">${c.activo ? 'Revocar' : 'Reactivar'}</button></td></tr>`).join('')}</tbody></table></div>
      <p class="muted small mt">Para rotar una clave: cree un consumidor nuevo, configure el sistema con la clave nueva y revoque la anterior.</p></div>
      <div class="card"><h2>Nuevo consumidor</h2><form id="cf" class="grid">
        <label>Nombre del sistema<input name="nombre" required minlength="3" maxlength="80" placeholder="p. ej. Clientes-INTEGRAX"></label>
        <label>Expira (opcional)<input name="expira" type="date"></label>
        <button class="btn primary">Generar clave</button></form></div></div>`;
  $('#cf').addEventListener('submit', async e => {
    e.preventDefault();
    const f = Object.fromEntries(new FormData(e.target));
    const body = { nombre: f.nombre, expira: f.expira ? new Date(f.expira + 'T23:59:59').toISOString() : null };
    try {
      const r = await api('/consumidores', { method: 'POST', body });
      await ask('Clave generada', `<p><strong>Cópiela ahora:</strong> no se volverá a mostrar.</p><label>Clave de «${esc(r.nombre)}»<input readonly value="${esc(r.clave)}" class="mono"></label>
        <p class="muted small">Se envía en la cabecera <span class="mono">X-API-Key</span>.</p>`, 'Ya la copié');
      route();
    } catch (x) { toast(x.message, true); }
  });
  $$('[data-tog]', view).forEach(b => b.addEventListener('click', async () => {
    try { await api('/consumidores/' + b.dataset.tog, { method: 'PATCH', body: { activo: b.dataset.act !== 'true' } }); route(); } catch (x) { toast(x.message, true); }
  }));
}

boot();
