---
codigo: SALESX-E5
evidencia: 5 de 7
titulo: Contrato de licencia de software
descripcion: Condiciones bajo las cuales la empresa contratante puede utilizar el sistema SALES-X. El contrato distingue expresamente entre ser dueño del software y tener derecho a usarlo, que no son lo mismo.
metadatos:
  - Objeto | Licencia de uso del software SALES-X
  - Titularidad | Del equipo desarrollador (EL LICENCIANTE)
  - Tipo de licencia | No exclusiva · uso interno · no transferible
  - Duración | Indefinida, sujeta a las causales de terminación
  - Territorio | República de Colombia
  - Finalidad | Académica (asignatura Integración de Aplicaciones)
pie: SALES-X · Evidencia 5 de 7 · Contrato de licencia de software · Modelo contractual académico; los campos entre corchetes deben diligenciarse antes de firmar. No sustituye la asesoría de un abogado.
---

> **Naturaleza del documento.** Modelo contractual de carácter académico para el proyecto SALES-X. Los campos entre corchetes **[ ]** deben diligenciarse antes de firmar. No sustituye la asesoría de un abogado.

# Comparecientes

| | **EL LICENCIANTE** | **LA EMPRESA** |
|---|---|---|
| Nombre o razón social | Julio Cesar Velasquez Arango | [Nombre de la organización usuaria] |
| Documento / NIT | [ ] | [ ] |
| Representante | Julio Cesar Velasquez Arango | [ ] |
| Correo para notificaciones | [ ] | [ ] |

Las partes acuerdan celebrar el presente contrato de licencia de uso de **SALES-X — Gestión de ventas y pedidos** (en adelante, **EL SOFTWARE**), que se rige por las siguientes cláusulas.

# Antecedentes: ser dueño no es lo mismo que tener derecho a usar

EL SOFTWARE es creación del equipo desarrollador. **Comprar o recibir una copia no convierte a LA EMPRESA en dueña**: le da el derecho de usarlo en las condiciones de este contrato. Esa diferencia —titularidad frente a licencia— es la razón de ser de este documento. Las licencias de los componentes de terceros que contiene EL SOFTWARE se describen en la Evidencia 4 y **siguen siendo de sus respectivos titulares**.

# Cláusulas

## PRIMERA — Objeto
EL LICENCIANTE otorga a LA EMPRESA una licencia **no exclusiva, intransferible y no sublicenciable** para usar EL SOFTWARE, en la versión y con los módulos descritos en el Anexo A, para la gestión interna de sus ventas y pedidos.

## SEGUNDA — Alcance de la licencia
1. **Usuarios:** hasta **[número]** usuarios internos activos (roles *vendedor* y *admin*).
2. **Instalaciones:** **[una]** instalación de producción y **[una]** de pruebas.
3. **Territorio:** República de Colombia.
4. **Duración:** indefinida, sujeta a las causales de terminación de la cláusula UNDÉCIMA.

## TERCERA — Titularidad y propiedad intelectual
1. EL SOFTWARE, su código fuente, documentación y diagramas son propiedad del equipo desarrollador, conforme a la Ley 23 de 1982 y a la Decisión Andina 351 de 1993. Esta licencia **no transfiere la titularidad**.
2. EL SOFTWARE incorpora componentes de terceros con licencias de código abierto, relacionados en la **Matriz de propiedad intelectual (Evidencia 4)**; cada uno conserva su propia licencia.
3. Los **datos** que LA EMPRESA ingrese (clientes, pedidos, reportes, usuarios) son de su exclusiva propiedad.

## CUARTA — Restricciones
LA EMPRESA **no podrá**:
1. Comercializar EL SOFTWARE: venderlo, alquilarlo, licenciarlo, sublicenciarlo o cederlo a terceros, total o parcialmente.
2. Ofrecerlo como servicio a terceros (por ejemplo, vender el uso de SALES-X a otras empresas).
3. Retirar, ocultar o alterar los avisos de autoría, de titularidad o de licencia que acompañan al software.
4. Usar el nombre o las marcas de EL LICENCIANTE para promocionar productos o servicios sin autorización escrita.
5. Eludir las medidas de seguridad del software o utilizarlo para fines ilícitos, incluido el tratamiento indebido de datos personales.
6. Descompilar o modificar el código para crear obras derivadas, salvo autorización escrita.
7. Compartir las credenciales de acceso ni las claves de integración fuera de la organización.

## QUINTA — Entregables
Código ejecutable y fuente [según acuerdo], scripts SQL, manual de usuario, guía de operación y las evidencias de documentación técnica (Evidencias 1 a 7).

## SEXTA — Nivel de servicio y soporte

| Concepto | Compromiso |
|---|---|
| Disponibilidad objetivo | ≥ **95 %** mensual (RNF-03), excluyendo mantenimientos programados avisados con 48 h. |
| Tiempo de respuesta de la aplicación | Menos de 3 s en el percentil 95 en condiciones normales (RNF-01). |
| Incidentes críticos | Respuesta en [4] horas hábiles. |
| Incidentes menores | Respuesta en [2] días hábiles. |
| Canal de soporte | [correo / mesa de ayuda] |
| Copias de seguridad | A cargo de LA EMPRESA según la guía de operación; verificación de restauración [trimestral]. |

## SÉPTIMA — Protección de datos personales
Cada parte cumplirá la **Ley 1581 de 2012** y sus decretos reglamentarios. LA EMPRESA actúa como **responsable** del tratamiento y EL LICENCIANTE, cuando acceda a datos por razones de soporte, como **encargado**, solo para ese fin y con deber de confidencialidad. EL SOFTWARE aplica minimización de datos: guarda únicamente nombre, correo y contraseña cifrada de los usuarios internos, y el identificador de los clientes.

## OCTAVA — Seguridad
LA EMPRESA se obliga a: definir los secretos de producción (EL SOFTWARE se niega a iniciar en producción con claves por defecto), cambiar las contraseñas iniciales, servir el sistema detrás de HTTPS y mantener actualizado su entorno. EL LICENCIANTE corregirá las vulnerabilidades que se le reporten conforme al informe de auditoría y a su estado de remediación.

## NOVENA — Garantía y limitación de responsabilidad
1. EL LICENCIANTE garantiza que EL SOFTWARE funciona sustancialmente conforme a la Especificación de Requisitos (Evidencia 3) durante [90] días desde la entrega.
2. Fuera de esa garantía, EL SOFTWARE se entrega «tal cual». La responsabilidad total de EL LICENCIANTE se limita al valor pagado por la licencia y no incluye lucro cesante ni daños indirectos.
3. EL LICENCIANTE no responde por fallos de servicios de terceros (Clientes, Productos, infraestructura de LA EMPRESA).

## DÉCIMA — Precio y forma de pago
Valor de la licencia: **$[ ]** COP [más IVA]. Forma de pago: [ ]. *(En el contexto académico puede pactarse sin contraprestación económica.)*

## UNDÉCIMA — Duración y terminación
El contrato termina por: **1.** mutuo acuerdo por escrito; **2.** incumplimiento de las obligaciones de la cláusula CUARTA que no se subsane en [15] días tras notificación escrita; **3.** decisión unilateral de LA EMPRESA, comunicada por escrito y sin penalidad.

> **Cláusula importante: los datos no desaparecen por terminar el contrato.** Al terminar, LA EMPRESA deja de usar EL SOFTWARE pero **conserva todos sus datos**. EL LICENCIANTE entregará una exportación completa (SQL o CSV) en un plazo de [10] días y no conservará copias, salvo obligación legal.

## DUODÉCIMA — Confidencialidad
Las partes mantendrán reserva sobre la información no pública intercambiada durante la ejecución del contrato y durante [2] años después de terminado.

## DECIMOTERCERA — Ley aplicable y solución de controversias
Rige la ley colombiana. Las diferencias se buscarán resolver por arreglo directo; de no lograrse, mediante conciliación en [centro de conciliación] y, en última instancia, ante los jueces de [ciudad].

# Firmas

| EL LICENCIANTE | LA EMPRESA |
|---|---|
| | |
| Nombre: ______________________ | Nombre: ______________________ |
| C.C. / NIT: ____________________ | C.C. / NIT: ____________________ |
| Fecha: _______________________ | Fecha: _______________________ |

# Anexo A — Descripción del software licenciado

| Elemento | Detalle |
|---|---|
| Producto y versión | SALES-X 1.2.0 |
| Módulos | Pedidos (registro, modificación, cancelación, estados, auditoría), historial, reportes de ventas, consulta de disponibilidad, servicios de integración, administración de usuarios y de claves de integración. |
| Requisitos técnicos | Servidor con 2 vCPU, 4 GB de RAM y 20 GB de disco (mínimo); PostgreSQL 14+; Docker o Python 3.12+. |
| Integraciones | Servicios REST de Clientes y Productos de INTEGRAX (contrato en la Evidencia 2). |

# Anexo B — Resumen de la licencia en una página

| Pregunta | Respuesta |
|---|---|
| ¿Quién es dueño de SALES-X? | El equipo desarrollador. |
| ¿Qué puede hacer LA EMPRESA? | Usarlo internamente, en Colombia, con los usuarios e instalaciones pactados. |
| ¿Puede venderlo, alquilarlo o ceder la licencia? | **No.** |
| ¿Puede ofrecerlo como servicio a otras empresas? | **No.** |
| ¿Puede modificarlo? | Solo con autorización escrita. |
| ¿De quién son los datos? | **De LA EMPRESA**, siempre. |
| ¿Qué pasa con los datos si termina el contrato? | LA EMPRESA los conserva; EL LICENCIANTE entrega una exportación completa. |
| ¿Y los componentes de código abierto? | Conservan su licencia y sus avisos (Evidencia 4). |
| ¿Cuánto dura? | Indefinida, hasta que se termine por acuerdo, incumplimiento o decisión de LA EMPRESA. |
| ¿Qué disponibilidad se promete? | 95 % mensual y respuesta de menos de 3 s (p95). |
