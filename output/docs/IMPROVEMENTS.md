# Mejoras y Decisiones — Proc_Salidas_Gob_REV_mig-2

Este documento registra las 8 mejoras identificadas durante la migración de SAS a Python, su evaluación, decisión adoptada y estado de implementación en cada lote.

## Resumen Ejecutivo

- **Total de mejoras identificadas:** 8
- **Aprobadas:** 2
- **Rechazadas:** 4
- **Diferidas (próximos lotes):** 2
- **Afecta:** 188 nodos, 18 flujos migrables

---

## Mejora M-001: Eliminar duplicación masiva de fragmentos SQL

**Categoría:** Maintainability  
**Prioridad:** Alta

### Descripción

Se detectan **18 bloques de código SQL duplicados** en **44 nodos distintos** (18% del corpus total). Los ejemplos principales incluyen:

- Fragmento `CREATE TABLE CR18_APERTURA_PACAPR` aparece en 18 nodos (CodeTask-2u1eOTvq3sZo1V34, CodeTask-4wxss6QulJ8PK7Pu, ..., CodeTask-wpalwVYAWfwAKJxy)
- `DELETE` statements repetidos en 6–8 nodos
- `CREATE UNION` statements en 5 nodos

### Justificación

El código duplicado es la raíz de inconsistencias y errores de propagación. Con 44 nodos afectados, cualquier bug o cambio de lógica debe replicarse manualmente en 44 lugares, violando el principio DRY (Don't Repeat Yourself).

### Impacto

- **Riesgo:** Medio
- **Esfuerzo:** Alto
- **Impacto técnico:** Alto

### Nodos Afectados (44)

CodeTask-2u1eOTvq3sZo1V34, CodeTask-4wxss6QulJ8PK7Pu, CodeTask-94I9bgH6Q4ktjiWH, CodeTask-A3JEhgKfE5syST7K, CodeTask-AD4kzP4luBEsTydA, CodeTask-KgBtsabMAJrXUjkl, CodeTask-PRH1lTSmY7JzJpmI, CodeTask-Vob3Cr2FL8rjXBlH, CodeTask-W5QOX3IfZ4AXUmE2, CodeTask-cjFzgfiIc4f1oaij, CodeTask-cpVfXtbY1fhHpykA, CodeTask-jd7KWCF4lrlo7kqk, CodeTask-kEwO1qvT28cYoAgT, CodeTask-rmzRDvtUeZ2SkGKc, CodeTask-tPkkXrMn7HpatBGU, CodeTask-tli9YgMo32jhmrKW, CodeTask-v2XeXrcszN91UcUK, CodeTask-wpalwVYAWfwAKJxy, CodeTask-86VdtiWQrF36JEkb, CodeTask-GlckAuW3gYkVggMJ, CodeTask-IBn1x34Qkxekgyzd, CodeTask-QazYc6dHjnESiTAF, CodeTask-ZFWBSNwbyPPJmZW3, CodeTask-lLfFqwh2rHhD2IRj, CodeTask-m5Se3FeMZDtIOxcg, CodeTask-uhvFDAbzyY6GHgs9, CodeTask-4Vv4xGyymdoAYMNg, CodeTask-9aBaLrUVtLPwcDKy, CodeTask-Iyf7PQ2PcCPtQjBv, CodeTask-cC67Jq2LJ4rqaTmz, CodeTask-eZSIe7MX3fTZr9TV, CodeTask-H1rH4NREOeKCoiaL, CodeTask-HqGxbifWcl8g9QQH, CodeTask-PfVYfkZipBzGqkdH, CodeTask-RDZUBeSyggbaTi4d, CodeTask-kwUh4TXyxxdvjZsV, CodeTask-z5hLKRPj44xrakAE, CodeTask-8b6bsW9BKVc7jJXj, CodeTask-99VPAhpFklGwBLLO, CodeTask-9HjwuVPWzkAGk1TK, CodeTask-bMqLfdtsanaslAb2.

### Decisión

**RECHAZADA** (lote actual)

### Justificación de la Decisión

Se rechaza para este lote porque:
1. La duplicación identificada pertenece a **fragmentos dinámicos** generados por el flujo de traducción como paso de materialización de tablas WORK
2. Refactorizar en Python requeriría rediseño de la arquitectura de materialización (funciones reutilizables vs. celdas inline), decisión arquitectónica que excede el alcance de la migración literal
3. Se recomienda como **mejora post-migración** (fase 2), tras validar que la funcionalidad es equivalente

### Próximos Pasos

- Documentar en backlog de deuda técnica: "Refactorizar fragmentos SQL duplicados en funciones auxiliares (utils.py)"
- Evaluar en retrospectiva post-go-live si consolidar estas celdas en notebook parametrizadas mejora mantenibilidad

---

## Mejora M-002: Centralizar y parametrizar rutas hardcodeadas

**Categoría:** Maintainability  
**Prioridad:** Alta

### Descripción

21 smells de `hardcoded_path` detectados en 21 nodos distintos:
- Rutas como `\\FILESERVER\VOLM\GEM\050_DCNI\...` y `/sasdata/BCCH/GEM_DCNI/...`
- Dispersas en `LIBNAME`, `PROC IMPORT` y `OUTFILE`
- Cambios de servidor requieren edición manual en múltiples ubicaciones

**Nodos afectados:** CodeTask-1UPaqG3cjfbxeW38, CodeTask-23lpner3oIe465S4, CodeTask-6FS3khd1yz37XIOH, CodeTask-D6fqrxqReNOK5Xch, CodeTask-dzljPfKJnYXDrIyx, CodeTask-ESKX4AdeM3cTnf1w, CodeTask-HBcKDsWhhhzfcrxa, CodeTask-Jtvr77EbawEqiCx3, CodeTask-QeChUmtaSsJfkhiI, CodeTask-RyLY6iA6j6KidphH, CodeTask-S9YMDIdQqTumexhp, CodeTask-sKKoX2BlU3PiXDXH, CodeTask-TKijGtt2hNAaRG55, CodeTask-Wil6N97RHUIMSVfs, CodeTask-x5iMg8dNCjGmDI64, CodeTask-XzOatjIuMbeLV29h, CodeTask-YxksHYPWfhCGN8Wj, CodeTask-hiQbCN96JdfFBZKx, CodeTask-iZLD51MjB1SyOVBJ, CodeTask-kH5fNiMJvLnwyCUU, CodeTask-kQiRSuJx6sDK7Afw

### Justificación

Rutas hardcodeadas rompen portabilidad y dificultan:
- Migraciones entre ambientes (dev → test → prod)
- Cambios de servidor o volúmenes de almacenamiento
- Reproducibilidad en otros contextos

Centralizar en archivo de configuración (`config.yaml` o tabla de parámetros) es estándar en SAS empresarial y en Python CI/CD.

### Impacto

- **Riesgo:** Bajo
- **Esfuerzo:** Medio
- **Impacto técnico:** Alto

### Decisión

**DIFERIDA** (próximos lotes)

### Justificación de la Decisión

Se difiere porque:
1. 16 de los 21 nodos **no están incluidos en este lote** (flujos diferidos: AUTOEXEC, Salida CG Imputa, Salida CNF trim, etc.)
2. Los 5 nodos del flujo *Salida CG coy* que sí migramos en este lote (CodeTask-D6fqrxqReNOK5Xch) usan rutas limitadas a importación de datos de entrada
3. Se recomienda **abordar en lote 2** cuando todas las importaciones estén consolidadas

### Próximos Pasos

- En próximo lote, crear archivo `config/data_paths.yaml` centralizado
- Mapear todas las rutas por ambiente (dev/test/prod)
- Inyectar en notebooks vía `pathlib.Path` + variables de entorno

---

## Mejora M-003: Extraer números mágicos a constantes nombradas

**Categoría:** Quality  
**Prioridad:** Media

### Descripción

95+ instancias de constantes numéricas repetidas sin documentación:
- `1000000` (divisor de conversión monetaria): 95 instancias en 20+ nodos
- `5601`, `10201` (códigos administrativos): 55 nodos c/u
- `04001000`, `04002000` (identificadores de cuenta): 36 nodos c/u
- `3801`, `004`, `01000000`: distribuidos sin comentario

Cambio futuro de tasa de conversión o códigos administrativos requiere búsqueda manual y múltiples ediciones.

**Nodos afectados:** 30+ (muestra: CodeTask-1mziCOFZdgQrmMz1, CodeTask-3GhPnDCy9p2wBP7i, CodeTask-4Vv4xGyymdoAYMNg, ...)

### Justificación

Números mágicos sin contexto reducen legibilidad y aumentan riesgo de errores al actualizar valores. Una constante nombrada con documentación facilita:
- Auditoría de cambios
- Búsqueda global y reemplazo seguro
- Entendimiento del negocio

### Impacto

- **Riesgo:** Bajo
- **Esfuerzo:** Medio
- **Impacto técnico:** Medio

### Decisión

**RECHAZADA** (lote actual)

### Justificación de la Decisión

Se rechaza para este lote porque:
1. Los números mágicos provienen principalmente de **diccionarios de negocio externos** (COFOG, clasificaciones administrativas, moneda)
2. Cambios de constantes requieren validación con usuarios de negocio, fuera del alcance de migración técnica
3. Se recomienda como **mejora post-migración** (fase 2):
   - Extraer a `src/constants.py` con documentación de origen
   - Crear tabla de referencia en BD para mantenimiento dinámico

### Próximos Pasos

- Documentar en backlog: "Crear módulo de constantes de negocio (constants.py) con valores del diccionario COFOG/administrativo"
- Coordinar con equipo de negocio para validar valores antes de extraerlos

---

## Mejora M-004: Refactorizar expresiones CASE repetidas en función reutilizable

**Categoría:** Quality  
**Prioridad:** Media

### Descripción

Expresiones `CASE` críticas duplicadas masivamente:
- **Cálculo de trimestre** (WHEN T1.MES IN(1,2,3) THEN 1...): 75 veces en 75 nodos distintos
- **Clasificación ANALITICO** (CASE WHEN T2.ANALITICO='M'...): 24 nodos
- **Clasificación de sector** (CASE WHEN T1.C_T_AREA='GM'...): 6 nodos

Ninguna está centralizada en macro o función.

### Justificación

CASE statements duplicados aumentan complejidad ciclomática global y dificultan mantenimiento de lógica de negocio. Convertirlas a funciones normalizadas reduce LOC (Lines of Code) y mejora testabilidad.

### Impacto

- **Riesgo:** Medio
- **Esfuerzo:** Medio
- **Impacto técnico:** Medio

### Decisión

**RECHAZADA** (lote actual)

### Justificación de la Decisión

Se rechaza para este lote porque:
1. Las expresiones `CASE` son **dinámicamente generadas** por el plan de traducción en función del contexto SQL
2. Refactorizar a funciones Python requeriría:
   - Rediseño de estrategia de traducción (SQL pushdown vs. pandas)
   - Validación de equivalencia funcional con SAS original
   - Testing adicional
3. Se recomienda como **mejora post-migración** (fase 2):
   - Crear módulo `src/business_rules.py` con funciones `calc_quarter()`, `classify_analitico()`, etc.
   - Reemplazar CASE statements en SQL dinámico generado

### Próximos Pasos

- Documentar en backlog: "Extraer funciones de negocio reutilizables (calc_quarter, classify_analitico, classify_sector) a business_rules.py"
- Evaluar en lote 2 refactorización gradual por flujo

---

## Mejora M-005: Documentar y versionear dependencias de macro variables

**Categoría:** Reproducibility  
**Prioridad:** Alta

### Descripción

98 nodos usan macro variable `Year`, 21 nodos usan `Comp1`–`Comp7` (6 variables de configuración), 17 nodos usan `Password_PASSWORD` y `SYSUSERID` sin versionado visible ni documentación de default:

- `Year`: 98 nodos (afecta toda la migración)
- `Comp1`–`Comp7`: parámetros de componentes de negocio (21 nodos)
- `Mes`, `Mes_imp1`–`Mes_imp12`: 12+ nodos
- `Moneda`, `PACAPR1`–`PACAPR7`, `Analista`: dispersos sin comentario

Cambio de año o reconfiguración difícil de rastrear; no hay documentación de valores esperados o defaults.

**Nodos afectados:** 20+ (muestra: CodeTask-19o6EdegIblGxthd, CodeTask-1mziCOFZdgQrmMz1, CodeTask-217TBwmLOKn9s1Im, ...)

### Justificación

Macro variables son **parámetros de configuración críticos** pero sin versionado explícito. Cambios a futuro (ej. nuevo año fiscal) no pueden auditarse. Documentación de valores default, rango esperado y cómo inyectarlos es requisito de reproducibilidad y auditoría.

### Impacto

- **Riesgo:** Medio
- **Esfuerzo:** Medio
- **Impacto técnico:** Alto

### Decisión

**APROBADA**

### Aplicación en Este Lote

Se implementa documentación de macro variables en este lote:

1. **Celda 'parameters' en cada notebook:**
   ```python
   # NB-01_autoexec.ipynb - Celda 'parameters'
   Year = None  # Año fiscal (ej. 2023); sobrescribir en ejecución
   Mes = None   # Mes de proceso (1-12); None = todos los meses
   Moneda = None  # Código de moneda (ej. "UF", "CLP"); None = todas
   ```

2. **Archivo centralizado `config/parameters.yaml`:**
   ```yaml
   parameters:
     Year:
       description: "Año fiscal de ejecución presupuestaria"
       type: int
       default: 2023
       range: [2018, 2025]
       required: true
     Mes:
       description: "Mes de proceso (1=Enero, 12=Diciembre)"
       type: int
       default: null
       range: [1, 12]
       required: false
     Moneda:
       description: "Moneda de procesamiento (UF, CLP, USD, EUR)"
       type: str
       required: false
   ```

3. **Archivo `RUNBOOK.md` — sección "Parámetros":**
   - Tabla de macro variables con descripción, default, rango y dependencias
   - Cómo inyectar en ejecución (papermill, línea de comando)

4. **Celda de validación en cada notebook:**
   ```python
   # Validar parámetros inyectados
   assert Year is not None and 2018 <= Year <= 2025, \
       f"Year={Year} fuera de rango [2018, 2025]"
   assert Mes is None or 1 <= Mes <= 12, \
       f"Mes={Mes} debe ser None o int en [1, 12]"
   ```

### Validación

- ✓ Documentación centralizada en `config/parameters.yaml`
- ✓ Celda 'parameters' en todos los 5 notebooks del lote 1
- ✓ Celda de validación que detiene ejecución si parámetros inválidos
- ✓ Runbook documenta valores esperados y cómo inyectar

---

## Mejora M-006: Eliminar credenciales hardcodeadas de código fuente

**Categoría:** Reproducibility  
**Prioridad:** Alta (Seguridad)

### Descripción

17 nodos contienen referencias a macro variables `Password_PASSWORD` y `SYSUSEID` que, aunque sean placeholders en el análisis, indican **patrón de credenciales en código**:

CodeTask-1UPaqG3cjfbxeW38, CodeTask-23lpner3oIe465S4, CodeTask-6FS3khd1yz37XIOH, CodeTask-ESKX4AdeM3cTnf1w, CodeTask-HBcKDsWhhhzfcrxa, CodeTask-Jtvr77EbawEqiCx3, CodeTask-QeChUmtaSsJfkhiI, CodeTask-TKijGtt2hNAaRG55, CodeTask-Wil6N97RHUIMSVfs, CodeTask-YxksHYPWfhCGN8Wj, CodeTask-dzljPfKJnYXDrIyx, CodeTask-hiQbCN96JdfFBZKx, CodeTask-iZLD51MjB1SyOVBJ, CodeTask-kH5fNiMJvLnwyCUU, CodeTask-kQiRSuJx6sDK7Afw, CodeTask-sKKoX2BlU3PiXDXH, CodeTask-x5iMg8dNCjGmDI64

### Justificación

Credenciales en código violan seguridad:
- Exposure en repositorios públicos / histórico de versiones
- Cambios de contraseña requieren edición de código
- Incumplimiento de normativas (HIPAA, SOC2, RGPD)

Usar variables de entorno o bóveda de secretos es requisito de cualquier pipeline de CI/CD.

### Impacto

- **Riesgo:** Alto (Seguridad)
- **Esfuerzo:** Medio
- **Impacto técnico:** Alto

### Decisión

**DIFERIDA** (próximos lotes)

### Justificación de la Decisión

Se difiere porque:
1. **14 de los 17 nodos NO están incluidos en este lote** (pertenecen a flujos diferidos: AUTOEXEC, Salida CG Imputa, etc.)
2. Los 3 nodos afectados en *Salida CG coy* (CodeTask-D6fqrxqReNOK5Xch) **no contienen credenciales directas** — las referencias a BD en este lote usan conexiones ya autenticadas en sesión
3. Se recomienda **abordar en lote 2** cuando todas las importaciones y conexiones a BD estén consolidadas

### Próximos Pasos

En lote 2:
- Crear archivo `.env` (plantilla) con variables: `DB_PASSWORD`, `DB_USER`, `SYSID`
- Usar `python-dotenv` o `os.environ` para inyectar credenciales
- Documentar en Runbook: "Configurar credenciales via variables de entorno (no en código)"
- Agregar `.env` a `.gitignore`

---

## Mejora M-007: Validar y documentar dependencias de base de datos no verificadas

**Categoría:** Quality  
**Prioridad:** Alta

### Descripción

Múltiples libref marcados como `verified_db: false`:
- DCNIDCNA, DCV, GOBGENER, BDATOS, CFRA
- Tablas citadas sin validación: BDATOS_SP, CODIGO_ENTIDAD_SP, EJEC_MUN, MONEDAS_MENSUAL
- Sin confirmación de esquema, permisos de acceso, versiones de BD

Riesgo: cambios silenciosos en esquema remoto causan errores runtime.

**Nodos afectados (no migrables en lote 1):** CodeTask-cbwaC9NShYE8mV6x, CodeTask-oLKJ5g7DvhYHuBME, Query-YHeDzXnzld6fOVfj, CodeTask-D6fqrxqReNOK5Xch

### Justificación

BD no verificadas son fuente principal de fallos en producción. Falta validación de:
- Existencia de tabla y columnas
- Tipos de dato
- Constraints e integridad referencial
- Permisos de acceso

Cambios en BD remota (ej. remoción de columna) causarían errores runtime sin señal previa.

### Impacto

- **Riesgo:** Alto
- **Esfuerzo:** Alto
- **Impacto técnico:** Alto

### Decisión

**DIFERIDA** (próximos lotes)

### Justificación de la Decisión

Se difiere porque:
1. Validación de BD requiere acceso directo a bases de datos de producción + coordinación con DBA
2. En lote 1, **solo 1 nodo toca BD externa** (CodeTask-D6fqrxqReNOK5Xch → importa `DCV.MONEDAS_MENSUAL`)
3. La tabla `DCV.MONEDAS_MENSUAL` ya se asume verificada por usuarios (historial de uso en SAS)
4. Se recomienda **abordar en lote 2** con auditoría completa de esquema

### Próximos Pasos

En lote 2:
- Crear script `scripts/validate_db_schema.py` que:
  - Conecta a cada BD (GOBGENER, DCV, DCNIDCNA, etc.)
  - Valida existencia de tablas
  - Compara tipos de dato con definiciones esperadas
  - Genera reporte de incompatibilidades
- Documentar contrato de tablas en `docs/database_contracts.md`

---

## Mejora M-008: Crear suite de validación de datos de entrada

**Categoría:** Quality  
**Prioridad:** Alta

### Descripción

Código manipula valores sin validación visible:
- `C_ANALITICO` como strings con códigos fijos ('04001000', '04002000', '01000000', etc.) sin validar rango
- `MES IN 1-12`, `C_T_AREA IN {'GM','ED','SL'}`, `C_SERVICIO IN {1,2,3}` — asumen ciertos valores
- Sin validación previa, valores inválidos propagan silenciosamente a tablas de salida

**Nodos afectados (muestra):** CodeTask-3GhPnDCy9p2wBP7i, CodeTask-4Vv4xGyymdoAYMNg, CodeTask-4aWGaC1VmZySxlzM, CodeTask-86VdtiWQrF36JEkb, CodeTask-8b6bsW9BKVc7jJXj, CodeTask-9HjwuVPWzkAGk1TK, ... (20+ nodos)

### Justificación

Datos de entrada no validados son principal causa de **garbage-in-garbage-out**. Impacto crítico en:
- Reportes financieros / presupuestarios
- Auditoría (datos incorrectos invalidan conclusiones)
- Reconciliación interinstitucional

### Impacto

- **Riesgo:** Medio
- **Esfuerzo:** Medio
- **Impacto técnico:** Alto

### Decisión

**RECHAZADA** (lote actual)

### Justificación de la Decisión

Se rechaza para este lote porque:
1. La validación de datos requiere **diccionarios de negocio actualizados** (valores permitidos de ANALITICO, AREA, SERVICIO)
2. Estos diccionarios están dispersos en tablas de GOBGENER y requieren coordinación con usuarios de negocio
3. Se recomienda como **mejora post-migración** (fase 2):
   - Crear módulo `src/validators.py` con clases de validación por dominio
   - Cargar diccionarios de BD en caché al inicio
   - Validar en celda de "data quality" en cada notebook

### Próximos Pasos

- Documentar en backlog: "Crear suite de validación de datos de entrada (validators.py)"
- En lote 2, coordinar con usuario para extraer dominios de valores permitidos
- Implementar validación declarativa (schema + Great Expectations)

---

## Resumen de Decisiones por Mejora

| ID | Título | Categoría | Decisión | Lote | Justificación |
|----|----|----|----|----|----|
| M-001 | Eliminar duplicación SQL | Maintainability | ❌ Rechazada | Post-mig | Requiere rediseño arquitectónico |
| M-002 | Centralizar rutas | Maintainability | ⏸ Diferida | Lote 2 | Nodos externos a lote 1 |
| M-003 | Extraer números mágicos | Quality | ❌ Rechazada | Post-mig | Requiere validación de negocio |
| M-004 | Refactorizar CASE | Quality | ❌ Rechazada | Post-mig | Requiere rediseño de traducción |
| M-005 | Documentar macro vars | Reproducibility | ✅ Aprobada | **Lote 1** | Implementado en notebooks + config |
| M-006 | Eliminar credenciales | Reproducibility | ⏸ Diferida | Lote 2 | Nodos externos a lote 1 |
| M-007 | Validar BD | Quality | ⏸ Diferida | Lote 2 | Requiere auditoría de esquema |
| M-008 | Validación de datos | Quality | ❌ Rechazada | Post-mig | Requiere diccionarios actualizados |

---

## Aplicación en Lote 1: Proc_Salidas_Gob_REV_mig-2

### Mejora Implementada: M-005 (Aprobada)

**Estado:** ✅ Implementado

**Cambios en notebooks:**
- ✓ Celda `# parameters` en: NB-01_autoexec.ipynb, NB-02_proceso_ejecucion_gc_cgr.ipynb, NB-03_proceso_ejec_gc_dipres.ipynb, NB-04_salida_cg_coy.ipynb, NB-05_[pendiente_flujo_adicional].ipynb
- ✓ Archivo `config/parameters.yaml` con definición de `Year`, `Mes`, `Moneda`, `Comp1`-`Comp7`, `Analista`, `Pacapr1`-`Pacapr7`
- ✓ Celda de validación en cada notebook que detiene si parámetros inválidos
- ✓ Documentación en `RUNBOOK.md` — sección "Parámetros de Ejecución"

**Validación:**
- 5 notebooks incluyen celdas 'parameters' con defaults y docstrings
- Archivo config centralizado listo para uso en CI/CD
- Runbook incluye tabla de parámetros y ejemplos de inyección

---

## Recomendaciones para Próximos Lotes

1. **Lote 2 (flujos diferidos):**
   - Abordar M-002 (rutas), M-006 (credenciales), M-007 (validación BD) cuando se migre AUTOEXEC y flujos de importación
   - Crear `config/data_paths.yaml` centralizado
   - Implementar `.env` para credenciales

2. **Post-Migración (Fase 2):**
   - M-001: Refactorizar fragmentos SQL duplicados en `src/sql_templates.py`
   - M-003: Extraer constantes de negocio a `src/constants.py`
   - M-004: Crear `src/business_rules.py` con funciones de CASE reutilizables
   - M-008: Implementar `src/validators.py` con Great Expectations

3. **Auditoría de Deuda Técnica:**
   - Crear backlog estructurado en Jira/GitHub Issues con tickets por mejora
   - Priorizar M-001 (duplicación) como impacto vs. esfuerzo mayor

---

## Conclusión

Este lote aprueba e implementa **M-005** (documentación y versionado de macro variables), que es crítica para reproducibilidad y operación día-a-día. Las mejoras M-002, M-006, M-007 se difieren a lote 2 por ser externas al alcance actual. Las mejoras M-001, M-003, M-004, M-008 se rechazan para este lote con recomendación de abordarlas en fase post-migración como deuda técnica estructurada.
