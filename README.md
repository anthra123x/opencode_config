# opencode Configuration

Configuración portable y profesional para [opencode](https://opencode.ai). Incluye metodología de ingeniería, 33 skills especializados y servidores MCP.

## Instalación

```bash
git clone https://github.com/anthra123x/opencode_config.git
cd opencode_config
./install.sh
```

### Requisitos

- [opencode](https://opencode.ai) CLI
- (Opcional) [codebase-memory-mcp](https://github.com/anomalyco/codebase-memory-mcp) — debe estar en tu PATH

## Arquitectura

```
repo/
├── install.sh                  ← Instalador
├── config/
│   ├── opencode.jsonc          ← Punto de entrada (instrucciones, skills, permisos)
│   ├── opencode.json           ← Servidores MCP
│   ├── INSTRUCTIONS.md         ← Metodología de ingeniería (orquesta skills)
│   ├── AGENTS.md               ← Reglas del grafo de conocimiento
│   └── commands/
│       └── graph-brain.md      ← Comando /graph-brain
└── skills/                     ← 33 skills ECC
    ├── tdd-workflow/
    ├── impeccable/
    ├── postgres-patterns/
    └── ...
```

El flujo: `opencode.jsonc` declara instrucciones y rutas de skills. `INSTRUCTIONS.md` se inyecta como system prompt y orquesta los skills según la fase de trabajo.

## Skills incluidos

### Desarrollo general
- **error-handling** — Patrones robustos: errores tipados, retry, circuit breaker
- **tdd-workflow** — TDD con cobertura ≥80%. RED → GREEN → REFACTOR
- **strategic-compact** — Compactación de contexto en fases largas

### Calidad y testing
- **e2e-testing** — Playwright: POM, CI/CD, flaky tests
- **lint-format** — ESLint + Prettier + Biome. Pre-commit hooks
- **plankton-code-quality** — Calidad en tiempo de escritura via hooks
- **verification-loop** — Build → types → lint → tests → security → diff
- **eval-harness** — Eval-driven development (EDD)
- **ai-regression-testing** — Detección de blind spots en IA

### Bases de datos
- **postgres-patterns** — PostgreSQL: queries, esquemas, indexing, seguridad
- **prisma-patterns** — Prisma ORM: schema, queries, transacciones
- **mysql-patterns** — MySQL/MariaDB: schema, queries, replicación
- **jpa-patterns** — JPA/Hibernate: entities, relationships, Spring Boot
- **database-migrations** — Migraciones multi-motor con rollbacks
- **clickhouse-io** — ClickHouse: analytics, data engineering

### Infraestructura
- **docker-patterns** — Multi-stage builds, Docker Compose, no-root

### Diseño y frontend
- **impeccable** — Skill de diseño completo. 23+ comandos (craft, critique, polish, animate, etc.). OKLCH, WCAG AA, sin slop
- **design-taste-frontend** — Anti-slop frontend. 3 diales: VARIANCE / MOTION / DENSITY
- **emil-design-eng** — Filosofía de Emil Kowalski (ex-Vercel). Easing, springs, clip-path
- **review-animations** — Revisión estricta de motion. 10 estándares no negociables
- **animation-vocabulary** — Glosario inverso de términos de animación

### Arquitectura y planificación
- **council** — 4 voces para decisiones ambiguas y trade-offs
- **code-tour** — Walkthroughs con anclas a archivos y líneas
- **production-audit** — Auditoría de readiness para producción

### Meta-habilidades
- **agent-sort** — Clasifica skills en DAILY vs LIBRARY
- **agent-introspection-debugging** — Debugging estructurado de fallos del agente
- **skill-scout** — Busca skills existentes antes de crear uno nuevo
- **skill-stocktake** — Auditoría de skills instalados
- **hookify-rules** — Reglas para hooks de opencode
- **iterative-retrieval** — Refinamiento de contexto para subagentes
- **configure-ecc** — Instalación interactiva de skills ECC

### Plataforma
- **windows-desktop-e2e** — E2E para apps Windows nativas (pywinauto)

## Comandos personalizados

- `/graph-brain` — Indexa el proyecto en el grafo de conocimiento y muestra estadísticas

## Servidores MCP

### codebase-memory-mcp

Grafo de conocimiento del código vía AST. 14 herramientas: `search_graph`, `trace_path`, `get_code_snippet`, `query_graph`, `get_architecture`.

Descargar desde [github.com/anomalyco/codebase-memory-mcp](https://github.com/anomalyco/codebase-memory-mcp) y colocar en un directorio en tu PATH (ej: `~/.local/bin/`).

UI disponible en `http://localhost:9749`.

## Personalización

1. Edita `config/INSTRUCTIONS.md` para cambiar la metodología
2. Edita `config/opencode.jsonc` para rutas de skills o permisos
3. Agrega/quita skills del directorio `skills/` antes de ejecutar `install.sh`

---

© anthra123x
