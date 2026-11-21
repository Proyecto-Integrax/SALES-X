/* SALES-X · API de demostración (solo para GitHub Pages).
 * Reemplaza fetch() para las rutas /api/v1/* y /health con una API simulada que corre en el navegador:
 * mismas reglas de negocio que el servidor (IVA 19 %, máquina de estados, auditoría, disponibilidad).
 * Los datos viven en memoria (se guardan en localStorage de este navegador); no hay base de datos ni servidor. */
window.SALESX_DEMO = true;
(() => {
  const IVA = 0.19;
  const KEY = 'salesx_demo_v1';
  const realFetch = window.fetch.bind(window);

  const CLIENTES = [
    ['02006d74-9779-5593-8084-1fe75a84bebb', 'Comercial La Estrella S.A.S.', '900123456-1', 'compras@laestrella.example'],
    ['9945e3c9-c272-522c-9c1b-aa9372a4e2f5', 'Distribuidora Andina Ltda.', '800987654-3', 'pedidos@andina.example'],
    ['67250094-229f-5789-8276-292f0f2f94a6', 'Papelería El Punto', '1020304050', 'contacto@elpunto.example'],
    ['fbcd674f-b797-5197-bb55-c8dd3024e55e', 'Supermercado Central', '901555222-7', 'admin@supercentral.example'],
    ['f752788f-6078-5ad9-b1ef-864aa9df2f97', 'María Fernanda Gómez', '43123456', 'mafe.gomez@example.com'],
  ].map(([cliente_id, nombre, documento, correo]) => ({ cliente_id, nombre, documento, correo }));

  const PRODUCTOS = [
    ['6d9e8a98-0924-57de-8be7-8c0e5a20b4a3', 'Laptop 14" Core i5', 'TEC-001', 2850000, 25],
    ['23053c32-62a3-50b8-9a14-6bfeb677a03d', 'Mouse inalámbrico', 'TEC-002', 55000, 300],
    ['8276651c-a512-5523-be2e-e68f3961ce77', 'Teclado mecánico', 'TEC-003', 189000, 80],
    ['2f18116c-32f4-5680-93c8-71188f0a71e0', 'Monitor 24" Full HD', 'TEC-004', 720000, 40],
    ['24adb39d-424e-5891-ad4c-83f55886c300', 'Impresora multifuncional', 'OFI-001', 540000, 15],
    ['c6ab99d7-5d20-5fb4-bd03-c5624532f40b', 'Resma papel carta x500', 'OFI-002', 18500, 1200],
    ['a991a43c-3ada-5028-84a7-5eacc3b808ab', 'Silla ergonómica', 'MOB-001', 430000, 20],
    ['c66790f2-9abb-5622-b651-775c9e671c6e', 'Escritorio 120x60', 'MOB-002', 390000, 12],
    ['05ee63ed-fc1e-521d-b351-958146552be3', 'Cable HDMI 2m', 'ACC-001', 22000, 500],
    ['4f2d1e74-7dce-5a80-b7f0-a41bd734890d', 'Disco SSD 1TB', 'TEC-005', 310000, 0],
  ].map(([producto_id, nombre, sku, precio, disponible]) => ({ producto_id, nombre, sku, precio, disponible, activo: true }));

  const ESTADOS = ['Pendiente', 'Confirmado', 'En preparación', 'Enviado', 'Entregado', 'Cancelado'];
  const TRANS = {
    'Pendiente': ['Confirmado', 'Cancelado'], 'Confirmado': ['En preparación', 'Cancelado'],
    'En preparación': ['Enviado', 'Cancelado'], 'Enviado': ['Entregado'], 'Entregado': [], 'Cancelado': [],
  };
  const ESTADO_ID = Object.fromEntries(ESTADOS.map((e, i) => [e, `00000000-0000-4000-8000-00000000000${i + 1}`]));

  const uuid = () => (crypto.randomUUID ? crypto.randomUUID() : 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => { const r = Math.random() * 16 | 0; return (c === 'x' ? r : (r & 3 | 8)).toString(16); }));
  const money = n => Math.round(n * 100) / 100;
  const iso = d => new Date(d).toISOString();
  const cli = id => CLIENTES.find(c => c.cliente_id === id);
  const prod = id => PRODUCTOS.find(p => p.producto_id === id);

  function rng(seed) { return () => { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }

  function nuevoPedido(vend, cliente_id, descripcion, items, fecha) {
    const detalles = items.map(i => { const p = prod(i.producto_id); const sub = money(p.precio * i.cantidad);
      return { detalle_pedido_id: uuid(), producto_id: p.producto_id, cantidad: i.cantidad, precio_unitario: money(p.precio), subtotal: sub }; });
    const ped = { pedido_id: uuid(), cliente_id, estado: 'Pendiente', vendedor_id: vend.vendedor_id, descripcion: descripcion || null,
      fecha_creacion: iso(fecha), detalles };
    totales(ped);
    return ped;
  }
  function totales(p) {
    p.subtotal = money(p.detalles.reduce((s, d) => s + d.subtotal, 0));
    p.impuestos = money(p.subtotal * IVA); p.total = money(p.subtotal + p.impuestos);
  }

  function semilla() {
    const admin = { vendedor_id: '464d5b34-f621-44d0-a52f-cefea015a9f8', nombre: 'Administrador SALES-X', correo: 'admin@salesx.local', rol: 'admin', activo: true, debe_cambiar_contrasena: false, clave: 'Admin2026*' };
    const vend = { vendedor_id: '705f9970-1bd1-4b73-ab22-54d90f933460', nombre: 'Vendedor Demo', correo: 'vendedor@salesx.local', rol: 'vendedor', activo: true, debe_cambiar_contrasena: false, clave: 'Ventas2026*' };
    const st = { vendedores: [admin, vend], pedidos: [], auditoria: [] };
    const r = rng(2026), ahora = Date.now(), disponibles = PRODUCTOS.filter(p => p.disponible > 0);
    for (let n = 0; n < 40; n++) {
      const v = r() < .5 ? admin : vend;
      const fecha = ahora - Math.floor(r() * 29 * 864e5) - Math.floor(r() * 864e5 * .5);
      const k = 1 + Math.floor(r() * 3), usados = new Set(), items = [];
      while (items.length < k) { const p = disponibles[Math.floor(r() * disponibles.length)]; if (!usados.has(p.producto_id)) { usados.add(p.producto_id); items.push({ producto_id: p.producto_id, cantidad: 1 + Math.floor(r() * 4) }); } }
      const ped = nuevoPedido(v, CLIENTES[Math.floor(r() * CLIENTES.length)].cliente_id, [null, 'Entrega en bodega', 'Cliente frecuente', 'Urgente'][Math.floor(r() * 4)], items, fecha);
      st.pedidos.push(ped);
      aud(st, ped, v, 'CREAR', `Pedido creado con ${ped.detalles.length} producto(s). Total ${ped.total.toFixed(2)}`, fecha);
      const meta = Math.floor(r() * 7); // 0 = queda Pendiente ... 4 = Entregado, 5-6 = cancelado
      let t = fecha;
      const cadena = ['Confirmado', 'En preparación', 'Enviado', 'Entregado'];
      const pasos = meta >= 5 ? Math.floor(r() * 3) : meta;
      for (let i = 0; i < pasos; i++) { t += 15 * 60e3; aud(st, ped, v, 'CAMBIO_ESTADO', `${ped.estado} -> ${cadena[i]}`, t); ped.estado = cadena[i]; }
      if (meta >= 5 && ped.estado !== 'Entregado') { t += 15 * 60e3; aud(st, ped, v, 'CANCELAR', `${ped.estado} -> Cancelado. Motivo: Cliente desistió de la compra`, t); ped.estado = 'Cancelado'; }
    }
    // solicitudes de sistemas externos (CU-05)
    const cand = st.pedidos.filter(p => !['Entregado', 'Cancelado'].includes(p.estado)).slice(0, 2);
    cand.forEach((p, i) => aud(st, p, null, i ? 'SOLICITUD_MODIFICACION' : 'SOLICITUD_CANCELACION',
      i ? 'El cliente solicita cambiar la dirección de entrega' : 'El cliente solicita cancelar el pedido', ahora - (i + 1) * 36e5, 'Sistema externo'));
    return st;
  }
  function aud(st, ped, v, accion, descripcion, fecha, usuario) {
    st.auditoria.push({ auditoria_id: uuid(), pedido_id: ped.pedido_id, accion, descripcion, fecha: iso(fecha), usuario: usuario || (v ? v.nombre : 'Sistema externo') });
  }

  let S;
  const cargar = () => { try { const s = JSON.parse(localStorage.getItem(KEY)); if (s && s.pedidos) return s; } catch { /* sin almacenamiento */ } return null; };
  const guardar = () => { try { localStorage.setItem(KEY, JSON.stringify(S)); } catch { /* ignorar */ } };
  let sesion = null; try { sesion = sessionStorage.getItem(KEY + '_u'); } catch { /* ignorar */ }
  S = cargar() || semilla(); guardar();
  const setSesion = id => { sesion = id; try { id ? sessionStorage.setItem(KEY + '_u', id) : sessionStorage.removeItem(KEY + '_u'); } catch { /* ignorar */ } };
  const yo = () => S.vendedores.find(v => v.vendedor_id === sesion && v.activo);
  const pub = v => ({ vendedor_id: v.vendedor_id, nombre: v.nombre, correo: v.correo, rol: v.rol, activo: v.activo, debe_cambiar_contrasena: v.debe_cambiar_contrasena });

  class Err extends Error { constructor(status, detail) { super(detail); this.status = status; this.detail = detail; } }
  const claveValida = (c, correo) => {
    if (c.length < 10) throw new Err(422, 'La contraseña debe tener al menos 10 caracteres');
    if (!/[A-Za-z]/.test(c) || !/\d/.test(c)) throw new Err(422, 'La contraseña debe incluir letras y números');
    const loc = (correo || '').split('@')[0].toLowerCase();
    if (loc.length >= 4 && c.toLowerCase().includes(loc)) throw new Err(422, 'La contraseña no debe contener su usuario');
  };
  const pedidoOut = p => ({ ...p, estado_id: ESTADO_ID[p.estado] });
  const resumen = p => { const { pedido_id, cliente_id, estado, subtotal, impuestos, total, fecha_creacion } = p; return { pedido_id, cliente_id, estado, subtotal, impuestos, total, fecha_creacion }; };
  const getPed = id => { const p = S.pedidos.find(x => x.pedido_id === id); if (!p) throw new Err(404, 'Pedido no encontrado'); return p; };
  const ymd = d => { const x = new Date(d); return `${x.getFullYear()}-${String(x.getMonth() + 1).padStart(2, '0')}-${String(x.getDate()).padStart(2, '0')}`; };

  function lineas(items) {
    if (!Array.isArray(items) || !items.length) throw new Err(422, 'items: debe incluir al menos un producto');
    const acum = new Map();
    items.forEach(i => { if (!(i.cantidad > 0)) throw new Err(422, 'items.cantidad: debe ser mayor que 0'); acum.set(i.producto_id, (acum.get(i.producto_id) || 0) + i.cantidad); });
    return [...acum].map(([producto_id, cantidad]) => {
      const p = prod(producto_id);
      if (!p) throw new Err(422, `Producto ${producto_id} no existe en el catálogo`);
      if (p.disponible < cantidad) throw new Err(409, `Disponibilidad insuficiente para '${p.nombre}': solicitado ${cantidad}, disponible ${p.disponible}`);
      return { detalle_pedido_id: uuid(), producto_id, cantidad, precio_unitario: money(p.precio), subtotal: money(p.precio * cantidad) };
    });
  }

  function reporte(q) {
    const desde = q.get('desde'), hasta = q.get('hasta'), agrupar = q.get('agrupar') || 'dia';
    const lista = S.pedidos.filter(p => (!desde || ymd(p.fecha_creacion) >= desde) && (!hasta || ymd(p.fecha_creacion) <= hasta)).sort((a, b) => a.fecha_creacion.localeCompare(b.fecha_creacion));
    const por_estado = {}, serie = new Map(); let sub = 0, imp = 0, tot = 0, vend = 0;
    lista.forEach(p => {
      por_estado[p.estado] = (por_estado[p.estado] || 0) + 1;
      if (p.estado === 'Cancelado') return;
      vend++; sub += p.subtotal; imp += p.impuestos; tot += p.total;
      const d = ymd(p.fecha_creacion), k = agrupar === 'mes' ? d.slice(0, 7) : d;
      const f = serie.get(k) || { periodo: k, pedidos: 0, subtotal: 0, impuestos: 0, total: 0 };
      f.pedidos++; f.subtotal = money(f.subtotal + p.subtotal); f.impuestos = money(f.impuestos + p.impuestos); f.total = money(f.total + p.total); serie.set(k, f);
    });
    return { desde, hasta, agrupar, total_pedidos: lista.length, pedidos_cancelados: por_estado['Cancelado'] || 0, subtotal: money(sub), impuestos: money(imp),
      total_ventas: money(tot), ticket_promedio: vend ? money(tot / vend) : 0, por_estado, serie: [...serie.values()], generado: iso(Date.now()) };
  }

  function ruta(method, path, q, body) {
    const m = (re) => path.match(re);
    let x;
    if (path === '/auth/login' && method === 'POST') {
      const v = S.vendedores.find(u => u.correo === String(body.correo || '').trim().toLowerCase());
      if (!v || v.clave !== body.contrasena || !v.activo) throw new Err(401, 'Credenciales inválidas');
      setSesion(v.vendedor_id); return { access_token: 'demo', token_type: 'bearer', expires_in: 28800 };
    }
    if (path === '/auth/logout') { setSesion(null); return null; }
    const u = yo(); if (!u) throw new Err(401, 'No autenticado');
    if (path === '/auth/me') return pub(u);
    if (path === '/auth/cambiar-contrasena' && method === 'POST') {
      if (body.actual !== u.clave) throw new Err(400, 'La contraseña actual no es correcta');
      claveValida(body.nueva, u.correo); if (body.nueva === u.clave) throw new Err(422, 'La nueva contraseña debe ser distinta de la actual');
      u.clave = body.nueva; u.debe_cambiar_contrasena = false; guardar(); return null;
    }
    if (path === '/catalogo/clientes') return CLIENTES;
    if (path === '/catalogo/productos') return PRODUCTOS;
    if (path === '/pedidos/solicitudes') return S.auditoria.filter(a => a.accion.startsWith('SOLICITUD_')).sort((a, b) => b.fecha.localeCompare(a.fecha)).slice(0, +q.get('limit') || 30);
    if (path === '/pedidos' && method === 'GET') {
      const est = q.get('estado'), c = q.get('cliente_id'), d = q.get('desde'), h = q.get('hasta'), page = +q.get('page') || 1, size = +q.get('size') || 20;
      const l = S.pedidos.filter(p => (!est || p.estado === est) && (!c || p.cliente_id === c) && (!d || ymd(p.fecha_creacion) >= d) && (!h || ymd(p.fecha_creacion) <= h))
        .sort((a, b) => b.fecha_creacion.localeCompare(a.fecha_creacion));
      return { items: l.slice((page - 1) * size, page * size).map(resumen), total: l.length, page, size };
    }
    if (path === '/pedidos' && method === 'POST') {
      if (!cli(body.cliente_id)) throw new Err(422, `Cliente ${body.cliente_id} no existe en el catálogo`);
      const ped = nuevoPedido(u, body.cliente_id, body.descripcion, [], Date.now()); ped.detalles = lineas(body.items); totales(ped);
      S.pedidos.push(ped); aud(S, ped, u, 'CREAR', `Pedido creado con ${ped.detalles.length} producto(s). Total ${ped.total.toFixed(2)}`, Date.now()); guardar(); return pedidoOut(ped);
    }
    if ((x = m(/^\/pedidos\/([\w-]+)\/auditoria$/))) { getPed(x[1]); return S.auditoria.filter(a => a.pedido_id === x[1]).sort((a, b) => a.fecha.localeCompare(b.fecha)); }
    if ((x = m(/^\/pedidos\/([\w-]+)\/estado$/)) && method === 'PATCH') {
      const p = getPed(x[1]), nuevo = body.estado;
      if (!TRANS[nuevo]) throw new Err(422, `Estado '${nuevo}' no válido`);
      if (!TRANS[p.estado].includes(nuevo)) throw new Err(409, `Transición no permitida: ${p.estado} -> ${nuevo}. Permitidas: ${TRANS[p.estado].join(', ') || 'ninguna (estado final)'}`);
      aud(S, p, u, 'CAMBIO_ESTADO', `${p.estado} -> ${nuevo}` + (body.comentario ? `. ${body.comentario}` : ''), Date.now()); p.estado = nuevo; guardar(); return pedidoOut(p);
    }
    if ((x = m(/^\/pedidos\/([\w-]+)\/cancelar$/)) && method === 'POST') {
      const p = getPed(x[1]);
      if (!TRANS[p.estado].includes('Cancelado')) throw new Err(409, `No se puede cancelar un pedido en estado '${p.estado}'`);
      aud(S, p, u, 'CANCELAR', `${p.estado} -> Cancelado. Motivo: ${body.motivo}`, Date.now()); p.estado = 'Cancelado'; guardar(); return pedidoOut(p);
    }
    if ((x = m(/^\/pedidos\/([\w-]+)$/))) {
      const p = getPed(x[1]);
      if (method === 'GET') return pedidoOut(p);
      if (method === 'PUT') {
        if (!['Pendiente', 'Confirmado'].includes(p.estado)) throw new Err(409, `El pedido está en estado '${p.estado}' y no se puede modificar`);
        const cambios = [];
        if (body.descripcion !== undefined && body.descripcion !== p.descripcion) { p.descripcion = body.descripcion; cambios.push('descripción actualizada'); }
        if (body.items) { const ant = p.total; p.detalles = lineas(body.items); totales(p); cambios.push(`productos reemplazados (${p.detalles.length}); total ${ant.toFixed(2)} -> ${p.total.toFixed(2)}`); }
        aud(S, p, u, 'MODIFICAR', cambios.join('; ') || 'sin cambios', Date.now()); guardar(); return pedidoOut(p);
      }
    }
    if (path === '/reportes/ventas') return reporte(q);
    if (path === '/reportes/ventas.csv') {
      const r = reporte(q);
      return { __csv: 'periodo,pedidos,subtotal,impuestos,total\n' + r.serie.map(s => [s.periodo, s.pedidos, s.subtotal, s.impuestos, s.total].join(',')).join('\n') + '\n' };
    }
    if (path.startsWith('/vendedores')) {
      if (u.rol !== 'admin') throw new Err(403, 'Se requiere rol administrador');
      if (path === '/vendedores' && method === 'GET') return S.vendedores.map(pub);
      if (path === '/vendedores' && method === 'POST') {
        const correo = String(body.correo || '').trim().toLowerCase();
        if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(correo)) throw new Err(422, 'correo: formato no válido');
        if (!body.nombre || body.nombre.length < 2) throw new Err(422, 'nombre: mínimo 2 caracteres');
        claveValida(body.contrasena || '', correo);
        if (S.vendedores.some(v => v.correo === correo)) throw new Err(409, 'Ya existe un usuario con ese correo');
        const v = { vendedor_id: uuid(), nombre: body.nombre, correo, rol: body.rol === 'admin' ? 'admin' : 'vendedor', activo: true, debe_cambiar_contrasena: true, clave: body.contrasena };
        S.vendedores.push(v); guardar(); return pub(v);
      }
      if ((x = m(/^\/vendedores\/([\w-]+)$/)) && method === 'PATCH') {
        const v = S.vendedores.find(t => t.vendedor_id === x[1]); if (!v) throw new Err(404, 'Usuario no encontrado');
        if (body.activo === false && v.vendedor_id === u.vendedor_id) throw new Err(409, 'No puede desactivarse a sí mismo');
        if (body.activo !== undefined) v.activo = !!body.activo;
        if (body.contrasena != null) { claveValida(body.contrasena, v.correo); v.clave = body.contrasena; v.debe_cambiar_contrasena = v.vendedor_id !== u.vendedor_id; }
        guardar(); return pub(v);
      }
    }
    throw new Err(404, 'Ruta no disponible en la demostración');
  }

  window.fetch = async (input, init = {}) => {
    const url = new URL(typeof input === 'string' ? input : input.url, location.href);
    const esApi = url.pathname.includes('/api/v1/'), esHealth = url.pathname.endsWith('/health');
    if (!esApi && !esHealth) return realFetch(input, init);
    await new Promise(r => setTimeout(r, 60)); // latencia mínima para que se note la carga
    const json = (data, status = 200) => new Response(status === 204 ? null : JSON.stringify(data), { status, headers: { 'Content-Type': 'application/json' } });
    if (esHealth) return json({ status: 'ok', database: 'demo', version: 'demo', iva_rate: IVA });
    try {
      const path = url.pathname.slice(url.pathname.indexOf('/api/v1') + 7);
      const body = init.body ? JSON.parse(init.body) : {};
      const out = ruta((init.method || 'GET').toUpperCase(), path, url.searchParams, body);
      if (out && out.__csv) return new Response(out.__csv, { status: 200, headers: { 'Content-Type': 'text/csv' } });
      return out === null ? json(null, 204) : json(out);
    } catch (e) {
      if (e instanceof Err) return json({ detail: e.detail }, e.status);
      console.error(e); return json({ detail: 'Error interno de la demostración' }, 500);
    }
  };

  // Barra superior de la demostración
  document.addEventListener('DOMContentLoaded', () => {
    const b = document.createElement('div');
    b.id = 'demo-bar';
    b.innerHTML = '<span><strong>Demostración</strong> · los datos se simulan en su navegador (no hay servidor ni base de datos). Entre con <code>admin@salesx.local</code> / <code>Admin2026*</code> o <code>vendedor@salesx.local</code> / <code>Ventas2026*</code>.</span>' +
      '<span><a href="documentos.html">Documentación</a> <button type="button" id="demo-reset">Restablecer datos</button></span>';
    const st = document.createElement('style');
    st.textContent = '#demo-bar{display:flex;flex-wrap:wrap;gap:8px 16px;justify-content:space-between;align-items:center;background:#fff8e1;color:#5c4400;border-bottom:1px solid #f0d98a;padding:8px 16px;font-size:13px}#demo-bar code{background:#fff;padding:1px 5px;border-radius:4px}#demo-bar a{color:#2457d6;margin-right:10px}#demo-bar button{font:inherit;padding:3px 10px;border:1px solid #c9a93f;background:#fff;border-radius:6px;cursor:pointer}';
    document.head.appendChild(st);
    document.body.prepend(b);
    document.getElementById('demo-reset').addEventListener('click', () => { try { localStorage.removeItem(KEY); sessionStorage.removeItem(KEY + '_u'); } catch { /* ignorar */ } location.reload(); });
  });
})();
