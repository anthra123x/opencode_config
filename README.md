# ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫

<div align="center">

[![OpenCode Compatible](https://img.shields.io/badge/OpenCode-v1.18.29+-blueviolet?style=for-the-badge&logo=code)](https://opencode.ai)
[![Multi-Agent](https://img.shields.io/badge/Architecture-Multi--Agent_Swarm-cyan?style=for-the-badge&logo=diagram)](./agents)
[![MCP Native](https://img.shields.io/badge/MCP-SQLite_FTS5-blue?style=for-the-badge&logo=sqlite)](./mcp)
[![Theme](https://img.shields.io/badge/TUI_Theme-TokyoNight-purple?style=for-the-badge&logo=visualstudiocode)](./config/tui.json)
[![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)](./LICENSE)

**Transforma OpenCode vanilla en una suite de ingeniería de software multi-agente con persistencia cross-sesión, coordinación por bus MCP y estética visual estilizada.**

```text
╭──────────────────────────────────────────────────────────────╮
│   ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫                              │
│   🛡️  Multi-Agent Architecture & Persistent Context Memory    │
╰──────────────────────────────────────────────────────────────╯
```

</div>

---

## 📑 Tabla de Contenidos

- [🌟 ¿Qué es OpenCode Swarm?](#-qué-es-opencode-swarm)
- [🎨 Identidad Visual y Transformación TUI](#-identidad-visual-y-transformación-tui)
- [👥 Roster de Sub-Agentes Especializados](#-roster-de-sub-agentes-especializados)
- [🧠 Servidores MCP Nativos](#-servidores-mcp-nativos)
  - [1. Memoria Persistente de Contexto (`context-memory`)](#1-memoria-persistente-de-contexto-context-memory)
  - [2. Bus de Coordinación y Tareas (`team-collab`)](#2-bus-de-coordinación-y-tareas-team-collab)
- [⚡ Slash Commands Disponibles](#-slash-commands-disponibles)
- [🚀 Instalación y Puesta en Marcha](#-instalación-y-puesta-en-marcha)
- [🛠️ CLI de Gestión: `ecc`](#️-cli-de-gestión-ecc)
- [🔄 Flujo de Trabajo y Ciclo Cross-Sesión](#-flujo-de-trabajo-y-ciclo-cross-sesión)
- [🧪 Simulación de Sesión y Verificación](#-simulación-de-sesión-y-verificación)
- [📂 Estructura del Repositorio](#-estructura-del-repositorio)
- [📋 Requisitos del Sistema](#-requisitos-del-sistema)

---

## 🌟 ¿Qué es OpenCode Swarm?

**OpenCode Swarm Edition** es una capa de configuración e inteligencia global diseñada para evolucionar OpenCode más allá de un asistente conversacional estándar, convirtiéndolo en un **equipo autónomo de ingeniería de software**.

### Pilares Fundamentales:
- **Persistencia Cross-Sesión por Proyecto**: El equipo no pierde el hilo al cerrar OpenCode. Recuerda las decisiones de arquitectura, los contratos de API y el progreso de las tareas entre diferentes sesiones de trabajo en el mismo proyecto.
- **División de Responsabilidades (SoC)**: Seis sub-agentes especializados con roles, permisos y skills acotados para garantizar calidad de código sin alucinaciones ni atajos descuidados.
- **Handoffs Transparentes por MCP**: Cuando `@backend` termina un modelo o API, publica el contrato en el bus para que `@frontend` lo consuma de inmediato sin pedir aclaraciones al usuario.
- **Cero Dependencias Externas**: Los servidores MCP operan sobre **Python 3 puro y SQLite FTS5 nativo**, sin requerir daemons en segundo plano ni paquetes pesados de Node/Docker.

---

## 🎨 Identidad Visual y Transformación TUI

OpenCode Swarm no solo amplía la inteligencia, sino que transforma completamente la presencia visual de la herramienta para acentuar que **ya no es la versión vanilla**:

- **Tipografía Estilizada**: Encabezados, saludos y dashboards decorados con tipografía en versalitas: `⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫`.
- **Integración con la Pestaña del Terminal**: Secuencias ANSI OSC que renombran dinámicamente tu terminal/pestaña a `⚡ ᴏᴘᴇɴᴄᴏᴅᴇ [ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ] — <nombre-proyecto>`.
- **Tema TokyoNight (`config/tui.json`)**: Paleta oscura de alto contraste con diffs apilados (`diff_style: "stacked"`), navegación acelerada y soporte de ratón.
- **Lanzador Wrapper (`templates/opencode-wrapper.sh` -> `~/.local/bin/opencode`)**: Intercepta la llamada a OpenCode para inyectar los metadatos visuales y presentar el banner de bienvenida antes del TUI.
- **Plugin Swarm HUD (`config/plugins/team-hud.ts`)**: Inyecta en el ciclo de vida de OpenCode el estado de los agentes activos y la configuración por defecto.

---

## 👥 Roster de Sub-Agentes Especializados

Cada agente cuenta con su propio color de distintivo en el TUI, prompt operacional y paquete de skills:

| Agente | Color | Modo | Rol & Responsabilidad | Skills Clave Integrados |
|---|---|---|---|---|
| **`@orchestrator`** | `#8B5CF6` (Morado) | `primary` (TAB) | **Líder Técnico & Arquitecto**: Coordina el enjambre, desglosa épicas en tareas, gestiona memoria y sintetiza entregables. | `council`, `code-tour`, `strategic-compact`, `agent-sort` |
| **`@backend`** | `#3B82F6` (Azul) | `primary` (TAB) | **Ingeniero Backend & BD**: APIs REST/GraphQL, esquemas relacionales, migraciones y TDD estricto. | `postgres-patterns`, `prisma-patterns`, `mysql-patterns`, `database-migrations`, `tdd-workflow` |
| **`@frontend`** | `#EC4899` (Rosa Neón) | `primary` (TAB) | **Ingeniero UI/UX & Motion**: Interfaces accesibles, diseño anti-slop, animaciones fluidas con resortes y tokens de diseño. | `impeccable`, `design-taste-frontend`, `emil-design-eng`, `review-animations`, `animation-vocabulary` |
| **`@git-flow`** | `#10B981` (Verde Esmeralda) | `primary` (TAB) | **Control de Flujo Git & GitHub**: Commits semánticos, ramas seguras, resolución de conflictos y resúmenes de PR. | `git-flow-pro`, `verification-loop` |
| **`@qa-auditor`** | `#F59E0B` (Ámbar) | `primary` (TAB) | **Auditor de Calidad & Test**: Loop de verificación en 6 etapas, cobertura $\ge$ 80%, auditorías OWASP y regresiones IA. | `verification-loop`, `production-audit`, `ai-regression-testing`, `eval-harness` |
| **`@devops`** | `#06B6D4` (Cian) | `subagent` | **Infraestructura & Contenedores**: Dockerfiles multi-stage, rootless, Compose, CI/CD y despliegues reproducibles. | `docker-patterns`, `lint-format` |

### ⌨️ Conmutación Interactiva con la Tecla TAB
En el prompt interactivo de OpenCode, simplemente presiona **`TAB`** para alternar de forma instantánea entre los roles principales:

$$\text{[orchestrator]} \xrightarrow{\text{TAB}} \text{[backend]} \xrightarrow{\text{TAB}} \text{[frontend]} \xrightarrow{\text{TAB}} \text{[git-flow]} \xrightarrow{\text{TAB}} \text{[qa-auditor]}$$

Cada especialista cuenta con sus criterios de dominio y se sincroniza en tiempo real a través del bus MCP (`team-collab`) y memoria persistente (`context-memory`).

---

## 🧠 Servidores MCP Nativos

La coordinación y persistencia se fundamentan en dos servidores MCP creados desde cero, ubicados en `mcp/` y registrados en `config/opencode.json`:

```
                    ┌─────────────────────────┐
                    │      @orchestrator      │
                    └────────────┬────────────┘
                                 │
           ┌─────────────────────┴─────────────────────┐
           ▼                                           ▼
┌──────────────────────┐                   ┌──────────────────────┐
│    context-memory    │                   │     team-collab      │
│  (SQLite FTS5 + DB)  │                   │  (Swarm Bus & Tasks) │
├──────────────────────┤                   ├──────────────────────┤
│ • remember           │                   │ • team_post_task     │
│ • recall             │                   │ • team_claim_task    │
│ • get_active_context │                   │ • team_handoff       │
│ • get_session_boot.. │                   │ • team_share_artif.. │
│ • list_memories      │                   │ • team_get_status    │
└──────────────────────┘                   └──────────────────────┘
           ▲                                           ▲
           │                                           │
 ┌─────────┴─────────┐                       ┌─────────┴─────────┐
 │     @backend      │ ──[ team_handoff ]──> │     @frontend     │
 └───────────────────┘                       └───────────────────┘
```

### 1. Memoria Persistente de Contexto (`context-memory`)
- **Ubicación de base de datos**: `~/.opencode/memory/context_memory.db`.
- **Motor de indexación**: SQLite **FTS5** para búsquedas de texto completo de alta velocidad.
- **Aislamiento por proyecto**: Diferencia entre memorias `global` (para todas las sesiones) y de proyecto (detectadas por el directorio de trabajo o rama Git).
- **Herramientas**:
  - `remember`: Almacena decisiones (`architecture`, `convention`, `decision`, `learning`, `user_preference`).
  - `recall`: Búsqueda semántica y FTS5 con cálculo de relevancia BM25.
  - `get_active_context`: Carga el resumen de decisiones vigentes del proyecto.
  - `get_session_bootstrap`: Inicializa una sesión inyectando contexto previo y estado de tareas.
  - `list_memories`: Catálogo paginado por categoría.

### 2. Bus de Coordinación y Tareas (`team-collab`)
- **Ubicación de base de datos**: `~/.opencode/team/team_collab.db`.
- **Tablero de tareas cross-sesión**: Mantiene tareas con estados `todo`, `in_progress`, `blocked`, `completed` y prioridades `low`, `normal`, `high`, `urgent`.
- **Intercambio de contratos**: Los agentes comparten artefactos tipados (`api_spec`, `schema`, `design_token`, `test_report`).
- **Handoffs formales**: Traspaso documentado entre agentes (`@backend` $\rightarrow$ `@frontend`).
- **Herramientas**:
  - `team_post_task`, `team_claim_task`, `team_update_task`, `team_list_tasks`.
  - `team_share_artifact`, `team_get_artifact`, `team_list_artifacts`.
  - `team_handoff`: Entrega directa de responsabilidades con notas y enlaces a artefactos.
  - `team_broadcast`, `team_read_feed`: Feed de anuncios y bloqueos entre agentes.
  - `team_get_status`: Dashboard visual del enjambre.

---

## ⚡ Slash Commands Disponibles

Puedes ejecutar estos comandos directamente dentro de la interfaz de OpenCode:

| Comando | Acción |
|---|---|
| `/live` | Monitor multi-ventana en tiempo real. Muestra qué ventana y tarea tiene cada especialista al instante. |
| `/brain` | Enlaces de acceso directo y estado del Swarm Cockpit & GetBrain Web Dashboard. |
| `/team` | Despliega el dashboard completo del enjambre, estado de los 6 agentes y el tablero de tareas. |
| `/tasks` | Consulta el tablero interactivo de tareas del proyecto actual. |
| `/memory [query]` | Realiza una búsqueda o muestra el contexto activo persistido en SQLite FTS5. |
| `/handoff` | Asiste en el traspaso documentado de una tarea entre dos especialistas. |
| `/graph-brain` | Indexa y mapea la arquitectura del código fuente mediante AST. |

> [!TIP]
> Los comandos `/backend`, `/frontend`, `/git-flow` y `/qa` ya no son necesarios: ahora puedes alternar directamente entre los especialistas presionando **`TAB`** en el prompt.

---

## 🚀 Instalación y Puesta en Marcha

### Instalación Rápida:

```bash
git clone https://github.com/anthra123x/opencode_config.git
cd opencode_config
./install.sh
```

El instalador interactivo (`install.sh`):
1. Detecta tu entorno (OpenCode, Python 3 con FTS5, Bash y Git).
2. Pregunta si deseas instalación **Quickstart** (recomendada) o **Personalizada**.
3. Instala los 6 agentes en `~/.config/opencode/agents/`.
4. Instala y valida los servidores MCP nativos en `~/.config/opencode/mcp/`.
5. Configura `opencode.jsonc`, `opencode.json`, `tui.json`, `AGENTS.md` e `INSTRUCTIONS.md`.
6. Enlaza los ejecutables de soporte (`ecc`, `opencode-context-memory`, `opencode-team-collab`) en `~/.local/bin/`.
7. Instala el servidor web local y GetBrain en `~/.config/opencode/web/`.
8. Instala el wrapper visual con la tipografía estilizada.

---

## 🛠️ CLI de Gestión: `ecc`

El comando `ecc` queda instalado en tu `$PATH` (`~/.local/bin/ecc`) para controlar el enjambre directamente desde la terminal:

```bash
# Diagnóstico completo de componentes, agentes y servidores MCP
ecc doctor

# Iniciar el servidor web local con el Swarm Cockpit y GetBrain (abre tu navegador)
ecc web --open

# Monitor en tiempo real multi-ventana en terminal (auto-refresco cada 2 segundos)
ecc live --watch

# Ver el tablero del equipo y tareas activas en el directorio actual
ecc team

# Consultar la memoria persistente del proyecto o buscar un tema
ecc memory "auth endpoints"

# Vista general del estado de instalación
ecc status

# Validar la sintaxis e integridad de todos los archivos de configuración
ecc validate

# Re-ejecutar el asistente interactivo de configuración
ecc configure

# Actualizar el repositorio a la última versión
ecc update
```

---

## 🧠 Swarm Cockpit & GetBrain: Sesiones Web Dedicadas por Proyecto

OpenCode Swarm incluye un **servidor web local multi-hilo** (`web/server.py`) que **se inicia de forma 100% automática y silenciosa en segundo plano cada vez que abres OpenCode** en tu terminal, gestionando **sesiones dedicadas y aisladas por proyecto**:

### 🎯 Sesiones Dedicadas & Asignación Dinámica de Puertos:
- **Aislamiento Total por Proyecto**: Cada proyecto en el que trabajes obtiene su propia instancia de servidor web con un puerto dedicado (rango `4040` - `4060`).
  - Proyecto A (`opencodeconfig`): se ejecuta en `http://localhost:4040` con su rama Git (`main`), sus tareas y sus archivos en el GetBrain.
  - Proyecto B (`mi-app-web`): al abrir OpenCode en otra carpeta, detecta automáticamente el nuevo proyecto y levanta una sesión independiente en `http://localhost:4041`, visualizando únicamente los archivos, ramas y módulos de ese proyecto.
- **Compartición Inteligente Cross-Terminal**: Si abres múltiples ventanas o terminales dentro del *mismo* proyecto (ej. una para `@backend` y otra para `@frontend`), ambas detectan y reutilizan el mismo puerto sin crear servidores duplicados ni colisiones.

### 💡 Integración Nativa en la Pantalla Central de OpenCode:
Para evitar ventanas emergentes o textos fugaces que desaparecen antes de que puedas interactuar, los accesos al servidor están integrados **directamente dentro de la interfaz central de OpenCode**:
1. **Recuadro de Tips en el Home (`home_bottom`)**: En el centro de la pantalla inicial de OpenCode, la sección de tips te ofrece de inmediato los enlaces activos con el puerto exacto de tu proyecto:
   - `💡 Monitorea el flujo de los agentes en http://localhost:<puerto>`
   - `🧠 Grafo de conocimiento GetBrain: http://localhost:<puerto>/#brain`
2. **Encabezado del Agente Activo**: En el selector central de agentes, la descripción de `@orchestrator` se actualiza dinámicamente con el enlace directo al panel del proyecto activo.
3. **Banner Informativo al Abrir**: El plugin `team-hud` despliega en la terminal el recuadro con la URL y puerto asignado a ese proyecto específico.

Si deseas forzar la apertura del navegador desde tu terminal en cualquier momento:
```bash
ecc web --open
```

### Características de la Suite Web:
1. **Swarm Cockpit (Pestaña 1 - `http://localhost:<puerto>`)**:
   - **Roster en Tiempo Real**: Tarjetas visuales de los 6 especialistas (`@orchestrator`, `@backend`, `@frontend`, `@git-flow`, `@qa-auditor`, `@devops`) con indicadores de pulso verde en vivo, identificador de ventana de terminal (`term-1-backend`), tarea en curso y tiempo transcurrido.
   - **Tablero Kanban de Flujo de Trabajo**: Vista sincronizada de tareas Por Hacer, En Curso, Revisión y Completadas con prioridades y notas. Interfaz limpia enfocada en supervisión en vivo.
   - **Feed de Actividad en Vivo**: Transmisión instantánea mediante **Server-Sent Events (SSE)** de todos los avisos y pases de guardia que ocurren en tus terminales de OpenCode para ese proyecto.
   - **Contratos & Memorias**: Explorador de especificaciones de API, esquemas y decisiones de arquitectura guardadas en SQLite FTS5.

2. **GetBrain Knowledge Graph (Pestaña 2 - `http://localhost:<puerto>/#brain`)**:
   - **Escáner de Arquitectura Multi-Capa**: Analiza en profundidad la estructura de código real del proyecto en curso (manifiestos, modelos Prisma/SQL, componentes UI, rutas API, servicios y suites de tests), vinculándolos dinámicamente con las decisiones tomadas en memoria.
   - **Motor de Física 2D Interactivo**: Visualizador en Canvas HTML5 con simulación de fuerzas gravitatorias y resortes, auto-ajuste de escala y partículas de energía que fluyen por los enlaces activos.
   - **Botón `💾 Checkpoint`**: Permite congelar un punto de control de contexto en cualquier momento, guardando el estado y decisiones en SQLite sin pérdida de contexto.
   - **Botón `🔄 Escanear`**: Re-analiza la base de código del proyecto activo y sincroniza automáticamente las dependencias y tecnologías detectadas.
   - **Inspector Lateral de Nodos**: Haz clic en cualquier nodo para ver su especificación técnica, contenido completo, creador y conexiones vinculadas.
   - **Filtros Dinámicos & Búsqueda**: Filtra por tipo de nodo (Agentes, Tareas, Contratos, Memorias/Checkpoints, Código) o busca por nombre.

---

## ⚡ Motor Zero-Compaction & Persistencia de Memoria de Contexto

Uno de los problemas más comunes en sesiones largas con modelos de lenguaje es la **compactación destructiva de contexto**, donde OpenCode trunca o resume agresivamente los mensajes anteriores perdiendo detalles de rutas de archivos, esquemas y decisiones tomadas.

OpenCode Swarm soluciona esto con una arquitectura **Zero-Compaction** nativa:

1. **Desactivación de Compactación Destructiva**:
   En `config/opencode.jsonc`, se configura `"compaction": { "auto": false, "tail_turns": 80 }`. OpenCode no compacta de manera forzada el historial de turnos.
2. **Checkpoints de Sesión (`checkpoint_session`)**:
   Los agentes o el usuario (desde la UI web) guardan puntos de control estructurados con resumen de avances, decisiones tomadas, tarea activa, próximos pasos y archivos modificados.
3. **Reanudación Instantánea (`get_session_checkpoint`)**:
   Cualquier agente que retoma el proyecto recupera el último checkpoint con 100% de fidelidad sin necesidad de cargar cientos de mensajes en el contexto conversacional.
4. **Sincronización Automática (`auto_sync_project_memory`)**:
   Detecta automáticamente el framework, librerías y modelos del proyecto persistiendo el mapa arquitectónico en SQLite FTS5.

---

## 🖥️ Flujo Multi-Ventana en Tiempo Real (Anti-Vuelco & Zero Locks)

OpenCode Swarm está diseñado para el flujo de trabajo profesional con **múltiples ventanas/terminales de OpenCode corriendo simultáneamente en el mismo proyecto**:

- **Ventana 1**: `@backend` (construyendo endpoints, bases de datos y migraciones).
- **Ventana 2**: `@frontend` (maquetando interfaces y consumiendo contratos).
- **Ventana 3**: `@git-flow` (controlando ramas, commits convencionales y pull requests).
- **Ventana 4**: `ecc live --watch` (monitor en vivo en un split de terminal o tmux).

### ¿Cómo se comunican en tiempo real?
1. **Consciencia Instantánea**: Cada vez que un agente recibe una instrucción, ejecuta `team_get_live_activity()` para saber quién está activo en las otras terminales, qué archivos están tocando y si hay tareas en curso.
2. **Identificador de Ventana y Heartbeats**: Cada sesión se registra con su identificador de ventana (`window_id`), emitiendo pulsos periódicos y marcas de tiempo relativas (*"hace 10s"*, *"hace 1m"*).
3. **Contratos Inmediatos**: Cuando `@backend` termina un endpoint, publica el contrato en `team_share_artifact` y difunde el aviso por `team_broadcast`. `@frontend` en la Ventana 2 lo detecta de inmediato y lo consume con `team_get_artifact`.

### ¿Por qué OpenCode NUNCA se vuelca con este flujo?
Cuando varios procesos intentan escribir al mismo tiempo en SQLite en modo tradicional, ocurre el error fatal `database is locked` y la aplicación se congela o cae. OpenCode Swarm previene esto con una arquitectura industrial:
- **Modo WAL (Write-Ahead Logging)**: Lectores y escritores no se bloquean mutuamente.
- **Busy Timeout de 30s**: `PRAGMA busy_timeout = 30000;`.
- **Bloqueo Inmediato Exclusivo (`BEGIN IMMEDIATE`)**: Previene bloqueos mortales (deadlocks) encolando las transacciones de escritura limpiamente.
- **Exponential Backoff & Jitter**: Reintentos inteligentes automáticos (hasta 10 intentos con pausa aleatoria).

---

## 🔄 Flujo de Trabajo y Ciclo Cross-Sesión

### Ejemplo de Vida Real en el Mismo Proyecto:

#### 🌅 Sesión 1 (Lunes):
1. Abres OpenCode en tu proyecto: `opencode`
2. El título de tu pestaña cambia a `⚡ ᴏᴘᴇɴᴄᴏᴅᴇ [ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ] — ecommerce`.
3. `@orchestrator` te saluda con el banner estilizado e inicializa el contexto del proyecto.
4. Solicitas: *"Necesitamos implementar el catálogo de productos con base de datos y carrito animado"*.
5. `@orchestrator` desglosa el trabajo en tareas en el tablero MCP.
6. `@backend` reclama la tarea, aplica `tdd-workflow` y `postgres-patterns`, genera los endpoints y almacena el contrato `catalog-api-v1`.
7. `@backend` hace el handoff formal a `@frontend`:
   ```python
   team_handoff(from_agent="backend", to_agent="frontend", task_id=1, notes="API lista al 89% de cobertura. Contrato en 'catalog-api-v1'.")
   ```
8. Cierras tu terminal y terminas tu jornada.

#### 🌄 Sesión 2 (Martes - Reanudación Automática):
1. Abres OpenCode nuevamente en la misma carpeta: `opencode`
2. `@orchestrator` ejecuta `get_session_bootstrap()` y te recibe:
   > *"⚡ Bienvenido de nuevo a **ecommerce**. En la sesión anterior, `@backend` completó la Tarea #1 y realizó el handoff con el artefacto `catalog-api-v1`. `@frontend` tiene la Tarea #2 lista para comenzar. ¿Deseas que `@frontend` inicie?"*
3. `@frontend` lee el artefacto `catalog-api-v1` directamente del MCP, implementa los componentes con micro-interacciones sin pedirte que repitas ningún endpoint.
4. `@qa-auditor` ejecuta el loop de verificación en 6 etapas.
5. `@git-flow` prepara el commit semántico (`feat(catalog): ...`) listo para push.

---

## 🧪 Simulación de Sesión y Verificación

El repositorio incluye una suite de pruebas y simulación integral para validar el funcionamiento de todos los componentes antes de usarlos en proyectos reales:

```bash
# Ejecutar la simulación completa de 7 turnos (Skills + MCPs + UI)
python3 scripts/test_swarm_session.py

# Ejecutar las pruebas unitarias de los servidores MCP
python3 mcp/context-memory/test_server.py
python3 mcp/team-collab/test_server.py
```

Salida esperada de la simulación:
```text
╔══════════════════════════════════════════════════════════════╗
║       ⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫ — SESSION SIMULATION     ║
║       Project: ecommerce-core           Branch: feature/catalog-v1 ║
╚══════════════════════════════════════════════════════════════╝

  ✓ Turno 1: Hidratación de contexto y bootstrap cross-sesión
  ✓ Turno 2: Configuración del tablero de tareas del enjambre
  ✓ Turno 3: @backend (TDD, PostgreSQL, Prisma, contrato y handoff)
  ✓ Turno 4: @frontend (Consumo de contrato, OKLCH, física de resortes)
  ✓ Turno 5: @qa-auditor (Loop de 6 etapas y sign-off de calidad)
  ✓ Turno 6: @git-flow (Conventional Commits 1.0 y resumen de PR)
  ✓ Turno 7: @orchestrator (Persistencia duradera y dashboard final)

✨ SIMULATION COMPLETED SUCCESSFULLY! All sub-agents, MCPs, and skills verified.
```

---

## 📂 Estructura del Repositorio

```text
opencode_config/
├── ecc                           # CLI de gestión del Swarm (~/.local/bin/ecc)
├── install.sh                    # Instalador interactivo con TUI y soporte fallback
├── README.md                     # Documentación principal del proyecto
├── agents/                       # Definiciones de los 6 sub-agentes especializados
│   ├── orchestrator.md           # @orchestrator (Morado #8B5CF6)
│   ├── backend.md                # @backend (Azul #3B82F6)
│   ├── frontend.md               # @frontend (Rosa #EC4899)
│   ├── git-flow.md               # @git-flow (Verde #10B981)
│   ├── qa-auditor.md             # @qa-auditor (Ámbar #F59E0B)
│   └── devops.md                 # @devops (Cian #06B6D4)
├── mcp/                          # Servidores MCP nativos (Python 3 + SQLite FTS5)
│   ├── context-memory/           # Memoria persistente de contexto
│   │   ├── server.py
│   │   └── test_server.py
│   └── team-collab/              # Bus de coordinación y tablero multi-agente
│       ├── server.py
│       └── test_server.py
├── config/                       # Archivos maestros de configuración OpenCode
│   ├── opencode.jsonc            # Declaración de agentes, permisos y compresión
│   ├── opencode.json             # Registro de servidores MCP
│   ├── tui.json                  # Tema visual TokyoNight y diffs apilados
│   ├── INSTRUCTIONS.md           # Metodología de ingeniería de software Swarm
│   ├── AGENTS.md                 # Protocolos operacionales de agentes y memoria
│   ├── plugins/
│   │   └── team-hud.ts           # Plugin de OpenCode para títulos y banner HUD
│   └── commands/                 # Slash commands (/team, /memory, /tasks, etc.)
├── skills/                       # Catálogo de 35 skills especializados
│   ├── git-flow-pro/             # Conventional Commits 1.0 y gestión de ramas
│   ├── postgres-patterns/        # Patrones avanzados de PostgreSQL
│   ├── prisma-patterns/          # Optimización de esquemas Prisma
│   ├── impeccable/               # Pulido de componentes frontend
│   ├── emil-design-eng/          # Animaciones y física de resortes
│   ├── verification-loop/        # Loop riguroso de pruebas y compilación
│   └── ...
├── web/                          # Servidor local multi-hilo y suite visual
│   ├── server.py                 # Servidor HTTP con API REST y SSE en tiempo real
│   ├── brain_builder.py          # Generador y sintetizador del grafo GetBrain
│   └── public/                   # Frontend SPA TokyoNight (HTML5, Vanilla CSS, JS)
│       ├── index.html            # Dashboard Swarm y visualizador GetBrain
│       ├── style.css             # Glassmorphism, animaciones y tokens oscuros
│       └── app.js                # Motor de física 2D en Canvas y cliente SSE
├── templates/
│   └── opencode-wrapper.sh       # Wrapper ejecutable con branding tipográfico
├── scripts/
│   ├── configure.sh              # Asistente de configuración de componentes
│   ├── test_swarm_session.py     # Suite de simulación de 7 turnos
│   └── uninstall.sh              # Desinstalador limpio con respaldo
└── lib/                          # Funciones auxiliares de Bash (ui, paths, utils)
```

---

## 📋 Requisitos del Sistema

- **Sistema Operativo**: Linux (Ubuntu, Debian, Fedora, Arch, etc.) o macOS.
- **Python**: $\ge$ 3.10 con soporte estándar de `sqlite3` (incluido por defecto).
- **Bash**: $\ge$ 4.0.
- **OpenCode**: Versión $\ge$ 1.18 instalado en el sistema.
- **Git**: $\ge$ 2.25.
- **whiptail** *(opcional)*: Para ventanas visuales durante la instalación (con fallback automático a texto plano).

---

<div align="center">

**⚡ ᴏᴘᴇɴᴄᴏᴅᴇ ⟪ ꜱᴡᴀʀᴍ ᴇᴅɪᴛɪᴏɴ ⟫**
Hecho con precisión técnica para equipos y desarrolladores de alto rendimiento.

</div>
