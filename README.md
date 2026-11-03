# Despensa familiar: ES2 + API ES3

Aplicación Django para administrar el stock de una despensa y el historial de retiros. Conserva las pantallas HTML de ES2 y añade una API REST bajo `/api/`, sobre los mismos modelos, servicios y base de datos SQLite.

## Requisitos e instalación

Se requiere Python 3.12 o superior.

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
python manage.py migrate
python manage.py crear_roles
python manage.py createsuperuser
python manage.py runserver
```

`importar_datos_json` solo se ejecuta si se necesita recuperar el historial legado de `datos.json`; se detiene cuando ya existen retiros en la base de datos. Después de crear el superusuario, asígnale los grupos desde Django Admin y crea usuarios en los grupos `admin`, `normal` o `viewer`.

Si necesitas recuperar el historial legado en una base que todavía no tenga retiros, ejecuta por separado:

```powershell
python manage.py importar_datos_json
```

La migración de `rest_framework.authtoken` y de la lista negra de refresh tokens se aplica con `python manage.py migrate`. El archivo `.env` y `db.sqlite3` son locales y no se incluyen en la entrega.

## Interfaz HTML

- `http://127.0.0.1:8000/login/`: inicio de sesión de la ES2.
- `http://127.0.0.1:8000/registros/`: inventario e historial.
- `http://127.0.0.1:8000/admin/`: administración de Django para cuentas staff.

## API

La API acepta JWT con access tokens de 15 minutos y refresh tokens de 7 días; no acepta los tokens estáticos de DRF. El endpoint de refresh rota el refresh token y bloquea el anterior. Las solicitudes de datos mandan el access token en la cabecera `Authorization: Bearer <access>`. Nunca pongas tokens en la URL ni guardes credenciales o tokens reales en el código o en la documentación.

### Endpoints

| Método | Ruta | Uso | Permiso |
| --- | --- | --- | --- |
| POST | `/api/token/` | Obtener par de tokens con usuario y contraseña de Django | Público; requiere credenciales válidas |
| POST | `/api/token/refresh/` | Rotar refresh token y obtener un nuevo par | Público; requiere refresh válido |
| POST | `/api/token/verify/` | Verificar un access token | Público; requiere token en el cuerpo |
| POST | `/api/token/blacklist/` | Revocar un refresh token | Público; requiere refresh válido |
| GET | `/api/registros/` | Listar retiros vigentes; 10 por página | Cualquier usuario autenticado |
| POST | `/api/registros/` | Registrar una solicitud de retiro | Grupo `normal` o `admin` |
| GET | `/api/registros/{id}/` | Consultar un retiro vigente | Cualquier usuario autenticado |
| PUT | `/api/registros/{id}/` | Reemplazar producto y cantidad | Grupo `admin` |
| PATCH | `/api/registros/{id}/` | Cambiar producto o cantidad | Grupo `admin` |
| DELETE | `/api/registros/{id}/` | Ocultar el retiro y restaurar stock si se descontó | Grupo `admin` |
| GET | `/api/schema/` | Esquema OpenAPI | Público; solo metadatos |
| GET | `/api/docs/` | Documentación Swagger interactiva | Público; solo metadatos |
| GET | `/api/redoc/` | Documentación ReDoc | Público; solo metadatos |

`GET /api/registros/` responde una estructura paginada con `count`, `next`, `previous` y `results`. Para obtener otra página, usa `?page=2`.

### Recurso y regla de negocio

El serializer publica únicamente `id`, `producto`, `cantidad_solicitada`, `resultado` y `fecha`. El cliente puede enviar producto y cantidad; el servidor calcula el resultado con `solucion.decidir()` mediante los servicios compartidos con la interfaz HTML. `resultado`, `fecha` e `id` son de solo lectura. La API no publica `afecta_stock` ni los indicadores internos de borrado lógico.

Ejemplo de solicitud:

```powershell
curl.exe -X POST http://127.0.0.1:8000/api/registros/ `
  -H "Authorization: Bearer <access>" `
  -H "Content-Type: application/json" `
  -d '{"producto":"arroz","cantidad_solicitada":1}'
```

Los retiros rechazados por producto inexistente o falta de stock se guardan como intentos y responden `201 Created`, igual que en ES2. Las cantidades `0` o negativas también se registran con el resultado `Error: Cantidad inválida`, conforme a la regla existente. En cambio, un JSON mal formado o un campo que no pasa validación responde `400 Bad Request` con el detalle del error.

### Códigos HTTP

| Código | Significado |
| --- | --- |
| 200 | Lectura, actualización o verificación exitosa |
| 201 | Solicitud de retiro registrada |
| 204 | Eliminación lógica exitosa, sin cuerpo de respuesta |
| 400 | JSON o campos inválidos |
| 401 | Falta autenticación o las credenciales/token no son válidos |
| 403 | Usuario autenticado sin permiso para ese método |
| 404 | El retiro no existe o está eliminado |

### Decisiones de configuración

- Se usa JWT en lugar de la sesión de navegador porque los clientes de la API envían una credencial en cada solicitud; los tokens cortos reducen el tiempo de exposición y el refresh permite renovar el acceso.
- El refresh rota y bloquea el token anterior para que una credencial reutilizada no siga siendo válida después de la rotación.
- La paginación de 10 registros limita el tamaño de respuestas y sigue el valor solicitado por la pauta.
- Las transacciones SQLite de inventario comienzan en modo `IMMEDIATE`, para que los retiros concurrentes lean el stock después de que termine la operación anterior.
- `IsAuthenticated` es el permiso global; el ViewSet añade permisos por método y rol, y el serializer mantiene el resultado de negocio fuera del control del cliente.

## Evidencia y documentación

Las solicitudes HTTP y sus códigos de respuesta se guardan en [`pruebas/`](pruebas/). La documentación generada está disponible en `/api/docs/` y `/api/redoc/` cuando el servidor está activo.

## Uso crítico de IA

El registro de consultas, decisiones de seguridad y cambios realizados para ES2 y ES3 está en [`ia.md`](ia.md).
