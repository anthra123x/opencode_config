# opencode Configuration

Configuración portable y profesional para [opencode](https://opencode.ai) / Claude Code.
Incluye 33 skills ECC especializados, metodología de ingeniería, servidores MCP y un CLI de gestión.

```
  ╔══════════════════════════════════════╗
  ║       opencode Configuration         ║
  ║          📦 ECC Manager v1           ║
  ╚══════════════════════════════════════╝
```

## Quickstart

```bash
git clone https://github.com/anthra123x/opencode_config.git
cd opencode_config
./install.sh
```

## Requisitos

- **bash >= 4** (casi todos los sistemas lo tienen)
- **whiptail** (para interfaz TUI — fallback a texto plano si no está)
- **opencode** o **Claude Code** en PATH
- **(Opcional)** [codebase-memory-mcp](https://github.com/anomalyco/codebase-memory-mcp)

Instalar whiptail si hace falta:

```bash
# Debian/Ubuntu
sudo apt install whiptail

# macOS
brew install newt

# Arch Linux
sudo pacman -S libnewt
```

## CLI: `ecc`

Después de instalar, el comando `ecc` está disponible:

| Comando | Descripción |
|---------|-------------|
| `ecc doctor` | Diagnóstico completo del sistema |
| `ecc status` | Estado de la instalación |
| `ecc validate` | Verifica integridad de archivos |
| `ecc configure` | Re-ejecuta el wizard de configuración |
| `ecc update` | Trae la última versión del repo |
| `ecc uninstall` | Remueve todo con backup |

Ejemplos:

```bash
# Verificar que todo funciona
ecc doctor

# Ver qué skills están instalados
ecc status

# Re-configurar paths o preferencias
ecc configure
```

Si `ecc` no está en tu PATH después de instalar:

```bash
export PATH="$PATH:$HOME/.local/bin"
# Agrega esa línea a ~/.bashrc, ~/.zshrc o equivalente
```

## Instalación: dos modos

### Quickstart (recomendado)

Modo con mínimas preguntas. Ideal si piensas pedirle a tu agente AI que configure todo:

```bash
./install.sh
# → Responde [Yes] a Quickstart
# → Ingresa tu nombre y GitHub username
# → Listo. El agente cargará las instrucciones automáticamente
```

### Manual

Control total sobre cada componente:

```bash
./install.sh
# → Responde [No] a Quickstart
# → Selecciona componentes (config, skills, MCP, etc.)
# → Configura paths personalizados
```

## Arquitectura

```
repo/
├── ecc                        ← CLI tool (se instala en ~/.local/bin)
├── install.sh                 ← Instalador TUI (whiptail)
├── lib/
│   ├── ui.sh                  ← Terminal UI (whiptail + fallback)
│   ├── paths.sh               ← Resolución de rutas
│   └── utils.sh               ← Utilidades comunes
├── scripts/
│   ├── configure.sh           ← Wizard de configuración
│   └── uninstall.sh           ← Remoción limpia
├── templates/                 ← Perfiles de instalación
├── config/
│   ├── opencode.jsonc         ← Punto de entrada
│   ├── opencode.json          ← Servidores MCP
│   ├── INSTRUCTIONS.md        ← Metodología de ingeniería
│   ├── AGENTS.md              ← Reglas del grafo de conocimiento
│   └── commands/
│       └── graph-brain.md     ← Comando /graph-brain
└── skills/                    ← 33 skills ECC
    ├── tdd-workflow/
    ├── impeccable/
    ├── postgres-patterns/
    └── ...
```

Flujo: `opencode.jsonc` declara instrucciones y skills paths. `INSTRUCTIONS.md` se inyecta como system prompt orquestando los skills según la fase de trabajo.

## Skills incluidos

### Desarrollo general
- **tdd-workflow** — TDD con cobertura ≥80%. RED → GREEN → REFACTOR
- **error-handling** — Patrones robustos: errores tipados, retry, circuit breaker
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
- **impeccable** — Skill de diseño completo. 23+ comandos (craft, critique, polish, animate...). OKLCH, WCAG AA, sin slop
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
- **continuous-learning-v2** — Aprendizaje por instintos con nivel de confianza

### Plataforma
- **windows-desktop-e2e** — E2E para apps Windows nativas (pywinauto)

## Comandos personalizados

- `/graph-brain` — Indexa el proyecto en el grafo de conocimiento y muestra estadísticas

## Servidores MCP

### codebase-memory-mcp

Grafo de conocimiento del código vía AST. 14 herramientas: `search_graph`, `trace_path`, `get_code_snippet`, `query_graph`, `get_architecture`.

```bash
# Instalar
curl -L https://github.com/anomalyco/codebase-memory-mcp/releases/latest/download/codebase-memory-mcp-$(uname -s)-$(uname -m).tar.gz | tar xz
mv codebase-memory-mcp ~/.local/bin/
```

UI disponible en `http://localhost:9749`.

## Personalización

1. Edita `config/INSTRUCTIONS.md` para cambiar la metodología
2. Edita `config/opencode.jsonc` para rutas de skills o permisos
3. Corre `ecc configure` para re-generar config con nuevos valores
4. Agrega/quita skills del directorio `skills/` antes de ejecutar `install.sh`

## Migración desde versión anterior

Si ya tenías una instalación previa:

```bash
# El instalador crea backups automáticos
./install.sh

# Verificar que todo está bien
ecc doctor

# Los backups están en:
#   ~/.config/opencode.bak.<timestamp>/
#   ~/.opencode/skills.bak.<timestamp>/
```

---

© anthra123x
