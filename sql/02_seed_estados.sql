-- Estados de pedido (la aplicación los inserta automáticamente si faltan).
INSERT INTO estado_pedido (nombre, descripcion) VALUES
    ('Pendiente',      'Pedido registrado, pendiente de confirmación'),
    ('Confirmado',     'Pedido confirmado con el cliente'),
    ('En preparación', 'Pedido en alistamiento'),
    ('Enviado',        'Pedido despachado al cliente'),
    ('Entregado',      'Pedido recibido por el cliente'),
    ('Cancelado',      'Pedido cancelado')
ON CONFLICT (nombre) DO NOTHING;
-- Los usuarios iniciales los crea la aplicación (contraseñas con bcrypt) a partir de ADMIN_EMAIL / ADMIN_PASSWORD.
