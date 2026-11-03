# Uso crítico de IA — ES3

**Estudiante:** Marcelo  
**Asignatura:** Programación Backend  
**Herramienta:** OpenAI Codex

## Qué le pedí

Implementar en el proyecto existente los requisitos de ES3, manteniendo la aplicación HTML y adaptando los ejemplos del PDF a los retiros de una despensa. Pregunta de seguridad revisada durante el análisis: «¿Cómo cierro las rutas de datos con tokens y evito que el cliente decida el resultado del retiro?».

## Qué respondió

La propuesta fue añadir Django REST Framework con un `ModelSerializer`, un `ModelViewSet` y un router bajo `/api/`; configurar autenticación JWT, permisos por rol, paginación de 10 elementos, documentación OpenAPI y refresh tokens con expiración. También recomendó que el servidor calcule el resultado del retiro y que las pruebas HTTP incluyan peticiones no autorizadas y datos inválidos.

## Qué estaba mal o qué descarté

Los ejemplos de la guía usan `nombre`, `edad` y `cupos_libres()`, que no existen en esta despensa. Aplicarlos sin adaptación habría omitido `solucion.decidir()` y el ajuste de inventario. También descarté el borrado físico estándar de `ModelViewSet`, porque los retiros deben ocultarse lógicamente y devolver el stock cuando corresponda. No acepté `AllowAny` para las rutas de datos: solo los endpoints de emisión, renovación y documentación son públicos; las operaciones de inventario exigen autenticación.

## Qué hice yo

Declaré solo `id`, `producto`, `cantidad_solicitada`, `resultado` y `fecha`; `resultado`, `fecha` e `id` son de solo lectura. Crear, editar y borrar llaman a los servicios existentes para mantener la regla y el stock. `normal` puede crear, `admin` puede editar y eliminar, y cualquier usuario autenticado puede consultar. Configuré access tokens de 15 minutos, refresh tokens de 7 días, rotación y lista negra.

Verifiqué los flujos con `curl.exe` contra una SQLite temporal: CRUD, permisos, `400`, `401`, `403`, `404`, Swagger/ReDoc, renovación y revocación de JWT. Los valores de tokens se omitieron y la base temporal se eliminó. Django y el esquema OpenAPI pasan sus comprobaciones; no se modificó la base local del proyecto.
