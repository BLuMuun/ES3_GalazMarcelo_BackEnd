# Proyecto: Control de Despensa Familiar

## Problema y solución

En casa no siempre se sabe qué productos quedan disponibles. El sistema mantiene el inventario y registra cada solicitud de retiro, indicando si fue inválida, si el producto no existe, si falta stock o si el retiro fue aceptado.

La aplicación usa Django y SQLite. Cada producto tiene un stock disponible y cada solicitud queda en el historial, incluso cuando se rechaza. Los retiros aceptados descuentan stock. Editar un retiro recalcula el resultado y ajusta el inventario; eliminarlo lo oculta del historial y revierte el descuento cuando el movimiento lo había aplicado.

## Alcance

### Must

- Mantener productos y cantidades en SQLite.
- Registrar y consultar solicitudes de retiro con fecha y resultado.
- Aplicar las cuatro decisiones de negocio desde una sola función compartida.
- Permitir crear retiros a los roles `admin` y `normal`.
- Permitir editar y eliminar lógicamente retiros solo al rol `admin`.
- Exigir inicio de sesión para consultar la aplicación y proteger el acceso con permisos verificados en el servidor.
- Ofrecer el administrador de Django para gestionar productos y revisar el historial.

### Should

- Gestionar el catálogo y ajustar el stock desde Django Admin.
- Mantener los retiros eliminados en la base de datos, con fecha de eliminación.

### Could

- Clasificar productos por secciones y filtrar el historial.
- Añadir alertas de stock bajo.

### Won't

- Gestionar vencimientos, escanear códigos de barras o conectarse a supermercados.
- Guardar contraseñas en modelos propios; la autenticación corresponde a Django.

## Regla de decisión

La función `decidir()` de `solucion.py` conserva este orden y estos cuatro resultados:

1. Cantidad menor o igual a cero: `Error: Cantidad inválida`.
2. Producto ausente del inventario: `Rechazo: Producto no encontrado`.
3. Cantidad mayor al stock disponible: `Rechazo: Fuera de stock`.
4. Producto disponible y stock suficiente: `Aceptado: Producto retirado`.

Las vistas de creación y edición reutilizan esa función; no duplican las condiciones. El comando `mostrar_despensa` presenta el inventario de SQLite en consola usando `tabulate`.

## Datos y roles

- `Producto` guarda el nombre y el stock actual.
- `Registro` guarda el producto solicitado, la cantidad, el resultado, la fecha y los indicadores de borrado lógico.
- `datos.json` es solo la fuente para la importación inicial del historial legado. La aplicación no lo usa como almacenamiento de trabajo.
- La primera migración crea arroz (3), fideos (5) y aceite (1), que eran los valores iniciales del inventario anterior.
- `mostrar_despensa` muestra el stock vigente desde SQLite; no mantiene una copia separada en memoria.
- `admin`: puede registrar, editar y eliminar retiros; un superusuario puede entrar también a `/admin/`.
- `normal`: puede consultar y registrar retiros.
- `viewer`: puede consultar el inventario y el historial.

## Puesta en marcha

Con Python 3.12 o superior:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
python manage.py migrate
python manage.py crear_roles
# Solo si la base está vacía y necesitas recuperar historial legado:
# python manage.py importar_datos_json
python manage.py createsuperuser
python manage.py mostrar_despensa
python manage.py runserver
```

La importación de `datos.json` es de una sola vez y se detiene si ya hay registros en SQLite, para evitar duplicados. Como el JSON legado no tenía fecha, los registros importados reciben la fecha de importación. Después de crear el superusuario, asígnale los grupos desde Django Admin y crea usuarios para los grupos `normal` y `viewer`.

## Persistencia

SQLite es la fuente de verdad para el inventario y el historial. `db.sqlite3` y `.env` son archivos locales ignorados por Git; `.env.example` sirve como plantilla de configuración.

## Extensión ES3: API REST

La API vive en paralelo bajo `/api/`; las rutas HTML, los modelos y la regla de negocio de ES2 se mantienen. `core/serializers.py` declara los campos expuestos y deja `resultado`, `fecha` e `id` como solo lectura. `core/api_views.py` publica el CRUD REST con router, paginación por página y permisos por método. Las operaciones delegan en los mismos servicios de stock que usa la interfaz HTML.

La autenticación usa JWT con access tokens de 15 minutos y refresh tokens de 7 días. La rotación bloquea el refresh anterior. El grupo `normal` puede crear; `admin` puede crear, editar y eliminar; cualquier usuario autenticado puede consultar. OpenAPI/Swagger documenta el contrato. La guía de instalación, tabla de endpoints, códigos HTTP y decisiones de configuración están en `README.md`; las pruebas de cliente HTTP se guardan en `pruebas/` y el uso crítico de IA se registra en `ia.md`.
