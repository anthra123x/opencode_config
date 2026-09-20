# Multi-Agent Coordination & Knowledge Architecture

Este documento define los protocolos operacionales para los agentes de OpenCode, la memoria persistente de contexto y el bus de colaboración del equipo.

---

## 1. Team Swarm Bus Protocol (`team-collab`)

Todos los agentes especializados (`@orchestrator`, `@backend`, `@frontend`, `@git-flow`, `@qa-auditor`, `@devops`) forman un equipo cohesionado y sincronizado a través de este MCP.

### Reglas de Sincronización:
1. **Registro de Estado**: Al iniciar o cambiar de tarea, el agente DEBE actualizar su estado:
   ```python
   team_set_status(agent_name="backend", status="working", current_task="Building user auth endpoints")
   ```
   Estados válidos: `working`, `blocked`, `ready_for_review`, `idle`.

2. **Handoffs y Contratos entre Agentes**:
   - Cuando `@backend` termine un modelo de datos o endpoints, DEBE compartir el contrato antes de que `@frontend` empiece a consumir endpoints ciegamente:
     ```python
     team_share_artifact(creator="backend", artifact_key="auth-api-v1", title="Auth Endpoints Contract", artifact_type="api_spec", content="...")
     ```
   - `@frontend` recupera el contrato usando `team_get_artifact(artifact_key="auth-api-v1")`.

3. **Anuncios y Bloqueos**:
   - Si un agente se encuentra bloqueado o requiere intervención de otro dominio, publica un mensaje con categoría `warning` o `question`:
     ```python
     team_broadcast(sender="frontend", message="Blocked: Need updated JWT schema in auth-api-v1", category="warning", priority="high")
     ```

4. **Tablero de Tareas**:
   - El `@orchestrator` publica las metas con `team_post_task()`.
   - Los especialistas reclaman sus tareas con `team_claim_task()` y las marcan completadas con `team_update_task()`.

---

## 2. Persistent Context Memory Protocol (`context-memory`)

La memoria persistente permite conservar contexto, reglas de negocio, preferencias del usuario y decisiones arquitectónicas a través de diferentes sesiones y proyectos.

### Prioridad de Consulta:
1. Al comenzar una sesión o recibir una instrucción compleja:
   ```python
   get_active_context(project="global")
   ```
2. Para resolver dudas técnicas sobre convenciones pasadas o cómo se implementó un módulo:
   ```python
   recall(query="jwt secret rotation", category="architecture")
   ```

### Cuándo Registrar en Memoria (`remember`):
- **Decisiones Arquitectónicas**: Decisiones clave sobre bibliotecas, frameworks, patrones (ej: "usar Zustand para estado global", "PostgreSQL con UUIDv7").
- **Preferencias del Usuario**: Estilos de codificación, stack preferido, diseño oscuro, convenciones de nombres.
- **Resolución de Bugs Críticos**: Causa raíz de un fallo sutil y cómo evitar que se repita.
- **Convenciones de Proyecto**: Formato de rutas, estructura de carpetas, reglas de validación.

---

## 3. Codebase Knowledge Graph (`codebase-memory-mcp`)

*Nota: Requiere que `codebase-memory-mcp` esté instalado y habilitado. Si retorna "tool not found", recurre inmediatamente a grep/glob o a las herramientas nativas.*

Herramientas disponibles si el servidor está activo:
- `search_graph`: Búsqueda de símbolos por patrón (funciones, clases, rutas).
- `trace_path`: Análisis de llamadas entrantes y salientes.
- `get_code_snippet`: Extracción del cuerpo de una función o clase.
- `query_graph`: Consultas Cypher para relaciones complejas.
