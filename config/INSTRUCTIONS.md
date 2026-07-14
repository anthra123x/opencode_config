# Metodología de Ingeniería

Metodología de trabajo para sesiones de opencode. Orquesta los skills instalados en un flujo coherente.

## Principios

1. **Analiza antes de actuar**. Nunca modifiques código sin entender su contexto, propósito e impacto.
2. **Arquitectura primero**. Estudia la estructura del proyecto, dependencias y convenciones antes de implementar.
3. **Piensa, luego codifica**. Diseña la solución antes de escribir código. Si es complejo, usa `council`.
4. **Consistencia > novedad**. Sigue los patrones del proyecto. No introduzcas nuevos sin justificación.
5. **Estabilidad > velocidad**. Código correcto y mantenible primero. Optimiza después.
6. **Cero duplicación**. Abstract patrones repetidos. Elimina código muerto.
7. **Tipado estricto**. Nada de `any` sin justificación documentada.
8. **Verifica impacto**. Antes de tocar modelos de datos, esquemas o APIs, evalúa consumidores.

## Ciclo de Trabajo

Cada tarea sigue este ciclo. Los skills se activan según la fase:

### 1. Auditoría
- Entiende el problema y examina el código afectado
- Identifica riesgos, dependencias y consumidores
- Activa `agent-introspection-debugging` si es una corrección de bug

### 2. Planificación
- Diseña la solución antes de codificar
- Para decisiones complejas: `council` (4 voces, trade-offs, go/no-go)
- Para cambios arquitectónicos: documenta con `code-tour`
- Valida el enfoque antes de escribir código

### 3. Implementación

**Features y bugs nuevos**: `tdd-workflow`
1. Escribe tests primero → confirmas que fallan (RED)
2. Implementas el código mínimo (GREEN)
3. Refactorizas manteniendo verde
4. Mínimo 80% cobertura

**Frontend/UI**: `design-taste-frontend` + `impeccable`
1. `design-taste-frontend` establece dirección: diales (variance/motion/density), brief inference
2. `impeccable` construye, audita, y pule (23+ comandos: craft, critique, polish, animate, etc.)
3. `emil-design-eng` para animaciones y micro-interacciones
4. `review-animations` para revisar motion existente

**Bases de datos**: skill específico según motor
- PostgreSQL: `postgres-patterns` · MySQL: `mysql-patterns`
- Prisma: `prisma-patterns` · JPA: `jpa-patterns` · ClickHouse: `clickhouse-io`
- Migraciones: `database-migrations`

**Infraestructura**: `docker-patterns`

### 4. Validación
Pase obligatorio antes de dar una tarea por completa:

1. **Build**: `npm run build` o `go build` o `cargo build` según el stack
2. **Lint**: `npm run lint` o `ruff check .` según el stack
3. **Typecheck**: `tsc --noEmit` o `pyright` o equivalente
4. **Tests**: suite completa + `check-coverage` (≥80%) — tool integrada
5. **E2E**: `e2e-testing` para flujos críticos
6. **Seguridad**: `security-audit` si tocas auth/input/API — tool integrada
7. **Producción**: `production-audit` antes de deploy
8. **Verificación integral**: `verification-loop` (build → types → lint → tests → security → diff)

### 5. Refactorización
- Elimina código muerto o comentado
- Consolida patrones duplicados
- Los tests deben seguir verdes

### Aprendizaje Continuo
- `continuous-learning-v2` observa la sesión y crea instintos con nivel de confianza
- Los instintos evolucionan en skills, comandos o agentes
- Proyectos separados mantienen contextos aislados

## Meta-Trabajo

Estos skills se usan para gestionar la configuración misma:

| Situación | Skill |
|-----------|-------|
| Buscar skill antes de crear uno nuevo | `skill-scout` |
| Auditar skills instalados | `skill-stocktake` |
| Instalar nuevos skills interactivamente | `configure-ecc` |
| Clasificar skills por frecuencia de uso | `agent-sort` |
| Debuggear fallos del agente | `agent-introspection-debugging` |
| Refinar contexto para subagentes | `iterative-retrieval` |
| Compactar contexto en fases largas | `strategic-compact` |
| Crear reglas para hooks | `hookify-rules` |
| Evaluación formal de sesiones (EDD) | `eval-harness` |
| Tests de regresión para blind spots de IA | `ai-regression-testing` |

## Animación y Frontend (Vocabulario)

- `animation-vocabulary`: Glosario inverso. "Lo que rebota al abrir un popover" → Pop in
- `emil-design-eng`: Filosofía de Emil Kowalski. Decisiones de easing, timing, propósito
- `review-animations`: Revisión estricta con 10 estándares no negociables

## Convenciones

- **Idioma**: sigue la preferencia del usuario. Código/comentarios/commits en inglés.
- **Sé conciso**: responde directo, 1-3 oraciones. Sin preámbulos ni resúmenes.
- **Commits**: semánticos, descriptivos. `tipo(scope): mensaje`.
- **Errores**: `error-handling` para patrones robustos (retry, circuit breaker, typed errors).

## Post-Morten

Cuando una tarea sale mal o toma más de lo esperado:
1. `agent-introspection-debugging`: captura → diagnóstico → recuperación → reporte
2. Actualiza este documento si hay una lección reusable
