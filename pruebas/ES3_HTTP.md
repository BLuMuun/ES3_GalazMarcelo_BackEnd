# Evidencia HTTP — ES3

Las solicitudes se hicieron con `curl.exe` contra `127.0.0.1` el 3 de noviembre de 2026. El servidor usó una SQLite temporal con usuarios de prueba en los grupos `admin`, `normal` y `viewer`; esa base se eliminó al terminar. No se guardaron contraseñas ni valores de access/refresh tokens.

## Rutas de negocio

| Solicitud | Resultado HTTP | Evidencia observada |
| --- | --- | --- |
| `GET /api/registros/` sin token | `401` | El endpoint no entrega datos anónimamente. |
| `GET /api/registros/` con token de `normal` | `200` | Lista paginada. |
| `POST /api/registros/` con token de `normal` | `201` | Retiro creado; el servidor calculó `Aceptado: Producto retirado` aunque la petición incluía un `resultado` falso. |
| `GET /api/registros/{id}/` | `200` | Se pudo consultar el registro creado. |
| `PATCH /api/registros/{id}/` con token de `normal` | `403` | La edición quedó restringida al rol `admin`. |
| `POST /api/registros/` con token de `viewer` | `403` | El rol `viewer` quedó en solo lectura. |
| `DELETE /api/registros/{id}/` con token de `normal` | `403` | El borrado quedó restringido al rol `admin`. |
| `PATCH /api/registros/{id}/` con token de `admin` | `200` | Producto y cantidad actualizados mediante el servicio compartido. |
| `POST /api/registros/` con cantidad `10001` | `400` | Validación del campo `cantidad_solicitada`. |
| `GET /api/registros/999999/` con token válido | `404` | El identificador inexistente se rechazó correctamente. |
| `DELETE /api/registros/{id}/` con token de `admin` | `204` | Se ocultó el retiro y se restauró el stock correspondiente. |
| `GET /api/registros/{id}/` después de eliminar | `404` | El registro oculto no volvió a exponerse. |

Tras crear un retiro de 2 unidades de arroz, editarlo a 1 unidad de fideos y eliminarlo, el inventario temporal volvió a `arroz: 5`, `fideos: 3`, `aceite: 1`.

## Tokens y documentación

| Solicitud | Resultado HTTP | Evidencia observada |
| --- | --- | --- |
| `POST /api/token/` | `200` | Se obtuvo el par JWT; los valores se omitieron. |
| `POST /api/token/verify/` | `200` | El access token de prueba fue verificado. |
| `POST /api/token/refresh/` | `200` | Refresh rotado; se omitieron los valores. |
| Reutilizar el refresh anterior | `401` | El token anterior quedó bloqueado tras la rotación. |
| `POST /api/token/blacklist/` | `200` | Refresh revocado. |
| Intentar renovar el refresh revocado | `401` | El token revocado fue rechazado. |
| `GET /api/schema/` | `200` | Esquema OpenAPI disponible. |
| `GET /api/docs/` con `Accept: text/html` | `200` | Swagger UI disponible. |
| `GET /api/redoc/` con `Accept: text/html` | `200` | ReDoc disponible. |

Comandos representativos; `<access>` es un marcador y no un token real:

```powershell
curl.exe -i http://127.0.0.1:8000/api/registros/
curl.exe -i -H "Authorization: Bearer <access>" http://127.0.0.1:8000/api/registros/
curl.exe -i -X POST http://127.0.0.1:8000/api/registros/ `
  -H "Authorization: Bearer <access>" `
  -H "Content-Type: application/json" `
  -d '{"producto":"arroz","cantidad_solicitada":1}'
```
